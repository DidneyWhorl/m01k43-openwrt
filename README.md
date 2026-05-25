# AlwayLink M01K43 - OpenWrt Build

Custom OpenWrt firmware for the **AlwayLink M01K43** 5G CPE router, turning a budget Alibaba router into a fully functional 5G WiFi gateway.

**Mainline status:** Merged into OpenWrt on 2026-05-25 (commit `db7d264e`, [openwrt/openwrt#22818](https://github.com/openwrt/openwrt/pull/22818)).

## Hardware

| Spec | Detail |
|------|--------|
| SoC | MediaTek MT7981B (Filogic 820), dual Cortex-A53 |
| RAM | 256MB DDR3 |
| Flash | 128MB SPI-NAND (UBI) + 4MB SPI-NOR |
| Ethernet | 4x GbE LAN + 1x 2.5GbE WAN (MT7531 DSA switch) |
| WiFi | MT7981 2x2 802.11ax (2.4GHz + 5GHz) |
| Modem | M.2 slot, Quectel RM551E-GL 5G (USB 2.0, QMI) |
| LEDs | 10 GPIOs (status, WAN, LAN, WiFi, signal bars) |
| Buttons | WPS, Reset, RFKill |
| PCB | M01K43 v5.0 |

## What Works

- 5G NR-SA via QMI (auto-connects on boot, dual-stack IPv4+IPv6)
- WiFi 2.4GHz + 5GHz (802.11ax, SAE-mixed)
- LAN switch (4 ports, GbE)
- WAN (2.5GbE via managed RTL8221B PHY, auto-negotiation)
- LuCI web interface
- Signal LED monitor (top LED shows 5G/4G/offline, side LEDs show signal strength)
- Recovery system (known-good image in ubi2, restore via failsafe mode)
- Factory reset survival (all configs re-applied from uci-defaults)
- MAC address from factory partition (ledeinfo)

## Quick Start

See [docs/BUILD-GUIDE.md](docs/BUILD-GUIDE.md) for full instructions. Summary:

```bash
# Clone OpenWrt (the M01K43 is in mainline as of commit db7d264e)
git clone https://git.openwrt.org/openwrt/openwrt.git
cd openwrt

# Select the board: make menuconfig ->
#   Target System: MediaTek Ralink ARM
#   Subtarget:     Filogic 8xx (MT798x)
#   Target Profile: AlwayLink M01K43
# ...or just drop in the provided build config:
cp /path/to/m01k43-openwrt/config/diffconfig .config
make defconfig

# Build (kernel must use -j1)
make target/linux/compile V=s -j1
make package/compile package/install target/install V=s -j$(nproc)

# Flash
scp -O bin/targets/mediatek/filogic/*sysupgrade.bin root@192.168.1.1:/tmp/
ssh root@192.168.1.1 'sysupgrade -n /tmp/*sysupgrade.bin'
```

For the **PMOD daily-driver** variant (modem power control via gpio-export, plus
the signal-LED/recovery overlay), replace the in-tree DTS with the PMOD DTS and
add the overlay before building:

```bash
cp /path/to/m01k43-openwrt/dts/mt7981b-alwaylink-m01k43.dts target/linux/mediatek/dts/
# ...or regenerate it from the canonical DTS:
# python3 /path/to/m01k43-openwrt/tools/generate-pmod-dts.py \
#   target/linux/mediatek/dts/mt7981b-alwaylink-m01k43.dts -o /tmp/pmod.dts
cp -r /path/to/m01k43-openwrt/files/ files/
```

## Repo Structure

```
files/          PMOD overlay (uci-defaults, signal LED monitor, recovery tools)
dts/            Device tree sources (PMOD + upstream-clean versions)
config/         Build configuration (diffconfig)
patches/        filogic.mk device block
docs/           Guides (hardware, build, modem, flash, recovery, LEDs)
```

## PMOD Features

This build includes customizations beyond upstream OpenWrt:

- **Signal LED monitor** - procd service that polls modem signal and drives status/signal LEDs
- **Recovery system** - known-good image stored in ubi2, restorable via failsafe mode
- **gpio-export** - modem power control (GPIO 25) and pwrkey (GPIO 2) via sysfs
- **Auto-config** - WiFi, QMI, firewall, LEDs, security all configured via uci-defaults
- **Custom banner** - M01K43-PMOD | Didneywhorl Edition

## Key Hardware Notes

- **PCIe is not routed** on this PCB. The M.2 slot only connects USB 2.0 (480 Mbps).
- **Modem must be in RC mode** (`AT+QCFG="pcie/mode",1`) to expose the QMI data interface over USB. EP mode only gives 4 serial ports with no data.
- **USB 3.0 SuperSpeed is not routed.** The xHCI controller runs in USB 2.0-only mode (`u3p-dis-msk`).
- **MAC address** is in the `ledeinfo` partition on SPI-NOR at offset 0x18.

## Docs

- [Hardware Reference](docs/HARDWARE.md) - Specs, GPIO map, LED map, flash layout
- [Build Guide](docs/BUILD-GUIDE.md) - Step-by-step build instructions
- [Modem Setup](docs/MODEM-SETUP.md) - AT commands, QMI config, USB mode
- [Flash Guide](docs/FLASH-GUIDE.md) - How to flash from OEM or OpenWrt
- [Recovery System](docs/RECOVERY.md) - Recovery tools and failsafe restore
- [LED Signals](docs/LED-SIGNALS.md) - Signal LED monitor behavior

## License

GPL-2.0-or-later (same as OpenWrt)
