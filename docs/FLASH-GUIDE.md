# Flashing OpenWrt onto the AlwayLink M01K43

How to convert an AlwayLink **M01K43** (MediaTek MT7981B / Filogic 820, 256 MB RAM,
128 MB SPI-NAND + 4 MB SPI-NOR) from its stock firmware (QWRT / "MEHS+" family) to
mainline OpenWrt.

> **Mainline status:** M01K43 support is **merged into OpenWrt** (commit `db7d264e`,
> PR openwrt/openwrt#22818). You can build it from the current OpenWrt source tree, or
> download a **SNAPSHOT** image from the [firmware selector](https://firmware-selector.openwrt.org)
> once the buildbot picks it up (search "M01K43", channel **SNAPSHOT**).

> ⚠️ **Read this whole guide first. Flashing can brick a device. Do it at your own risk.**
> The good news: on this board, `sysupgrade` only writes the NAND, never the SPI-NOR boot
> chain — so U-Boot recovery is always available as a last resort (see Method C).

---

## The catch: the OEM signature lock

The stock firmware's own updater verifies an **RSA signature (`wtcheck`)** and **refuses
unsigned images**. So you cannot simply `sysupgrade` an OpenWrt image on a stock unit —
the stock `sysupgrade` rejects it. You have three ways around this, in order of preference:

| Method | What it needs | When to use |
|--------|---------------|-------------|
| **A — Software (recommended)** | SSH to the stock firmware + the included `platform.sh` | Default path. No hardware needed. |
| **B — NAND programmer (fallback)** | CH341A / RT809H + chip clip or desolder | If A fails, or the unit won't boot stock firmware. Guaranteed. |
| **C — U-Boot UART + TFTP (fallback)** | 3.3 V USB-UART adapter + TFTP server | Recovery if a flash leaves the unit unbootable. |

---

## Before you flash: back up per-unit data (do NOT skip)

Two partitions hold **per-unit data that cannot be regenerated** — WiFi calibration and the
MAC address / board ID. Back them up and keep the files safe.

```sh
ssh root@192.168.100.1          # stock default: user root / password admin
dd if=/dev/mtd3 of=/tmp/factory.bin  bs=1 count=655360   # WiFi cal / EEPROM
dd if=/dev/mtd6 of=/tmp/ledeinfo.bin bs=1 count=65536    # MAC / board ID
exit
# from your PC:
scp root@192.168.100.1:/tmp/factory.bin  .
scp root@192.168.100.1:/tmp/ledeinfo.bin .
```

> MAC addresses on OpenWrt are read from `ledeinfo` (mtd6) at offset `0x18`. If you ever
> wipe that partition you lose your unit's MAC — keep `ledeinfo.bin`.

### What cannot brick the device

| Partition | Where | Touched by sysupgrade? |
|-----------|-------|------------------------|
| BL2 (mtd1) | SPI-NOR | **No** — bootloader always safe |
| FIP / ATF + U-Boot (mtd4) | SPI-NOR | **No** — always safe |
| UBI slot A (mtd8) | NAND | Yes |
| UBI slot B (mtd9) | NAND | Yes (written identically) |

Because the SPI-NOR boot chain is never written, the unit can **always** reach U-Boot —
so Method C is a reliable recovery path.

---

## Method A — Software flash (recommended)

Defeats `wtcheck` by replacing the stock `/lib/upgrade/platform.sh` (in RAM only) with the
version in this repo, which accepts an unsigned image and writes it to both NAND slots.

### Prerequisites
- Stock firmware reachable at **192.168.100.1**, SSH `root` / `admin`
- `flash/platform.sh` from this repo
- The OpenWrt **factory** image (a UBI image):
  `openwrt-mediatek-filogic-alwaylink_m01k43-squashfs-factory.bin`
  (from your build's `bin/targets/mediatek/filogic/`, or a SNAPSHOT download)

### Steps

```sh
# 1. Replace the stock upgrade script (RAM-only, non-persistent — fine):
scp flash/platform.sh root@192.168.100.1:/lib/upgrade/platform.sh

# 2. Upload the OpenWrt factory image:
scp openwrt-mediatek-filogic-alwaylink_m01k43-squashfs-factory.bin \
    root@192.168.100.1:/tmp/openwrt.bin

# 3. (Recommended) verify the upload:
ssh root@192.168.100.1 'md5sum /tmp/openwrt.bin'    # compare to the build's .md5

# 4. Flash (clean — discard OEM config):
ssh root@192.168.100.1 'sysupgrade -n /tmp/openwrt.bin'
```

`sysupgrade` calls our `platform.sh`, which `ubiformat`s the image onto mtd8 and mtd9 and
reboots. **The flash takes ~2–4 minutes; do not power-cycle during it.**

> The included `platform.sh` flashes whatever image you pass to `sysupgrade` (it is a
> parameterised, cleaned-up version of the OEM script). It contains no keys and no
> proprietary code — see the comments in `flash/platform.sh`.

Then jump to **Post-flash verification** below.

---

## Method B — NAND programmer (fallback, guaranteed)

If the stock firmware is unreachable, or Method A fails, write the image directly to the
SPI-NAND chip with a programmer. This always works.

1. Identify the SPI-NAND chip; attach a **CH341A** (with a NAND adapter) or **RT809H**
   via chip clip or by desoldering.
2. **Dump the original flash first** and keep it as a recovery image.
3. Write the OpenWrt **factory** image to the UBI region of the NAND.
   - **Do NOT erase the 4 MB SPI-NOR** (BL2 / u-boot-env / Factory / FIP / ledeinfo / nvram).
     Those are per-unit and live on a *separate* chip from the firmware NAND.
4. Reseat the chip and power on; the SPI-NOR bootloader loads the new kernel/rootfs from UBI.

---

## Method C — U-Boot UART + TFTP (recovery fallback)

Use this if a flash leaves the unit unbootable. The SPI-NOR boot chain is intact, so U-Boot
is reachable.

> **UART is 3.3 V TTL, 115200 8N1, no flow control.** Use a standard 3.3 V USB-UART adapter.
> (Earlier notes in this project claimed 1.8 V — that was wrong; the pad idles at 3.3 V.
> If a 3.3 V adapter that outputs ~3.6 V misbehaves on the RX line, add a simple resistor
> divider on the host TX→router RX line, but the device itself is a 3.3 V interface.)

1. Connect the UART header (TX / RX / GND) to a 3.3 V adapter; terminal at **115200 8N1**.
2. Power on. You have **~1 second** to press a key to interrupt autoboot and enter the
   U-Boot menu.
3. Set up a TFTP server on your PC at **192.168.2.88** (U-Boot expects this); the router's
   U-Boot IP is **192.168.2.1**. Put the factory image in the TFTP root.
4. From the U-Boot menu choose **"Upgrade ubi"** and follow the prompts to flash via TFTP.
5. The unit reboots into the new image.

---

## Post-flash verification

Allow ~90 seconds for first boot (OpenWrt runs first-boot scripts), then:

```sh
ping 192.168.1.1                      # OpenWrt default LAN IP
ssh root@192.168.1.1                  # default: root, no password — set one now:
passwd

# Confirm the board + MACs:
cat /proc/device-tree/model           # "AlwayLink M01K43"
ip -o link | grep -Ei 'eth|lan|wan'   # MACs derived from ledeinfo base + offsets
```

WiFi, the DSA switch (LAN1–4 + 2.5 GbE WAN via the RTL8221B PHY), and USB come up on a
stock mainline image. LuCI is included in the default build.

---

## Reverting to stock

Only possible if you kept a backup. With a full NAND dump (Method B), write it back with the
programmer. If you only have the OpenWrt sysupgrade route, you would need a signed stock
image from the vendor — the `wtcheck` lock applies in that direction too.

---

## Modem (Quectel) setup

Cellular configuration (QMI, APN, modem power) is covered separately in
[`docs/MODEM-SETUP.md`](MODEM-SETUP.md). *(Note: that guide is being revised against the
current mainline image — verify before relying on it.)*
