# M01K43 Build Guide

## Prerequisites

- Linux build machine (Ubuntu 22.04+ recommended, or any distro with OpenWrt build deps)
- ~15GB disk space for build tree
- ~2GB RAM minimum

Install OpenWrt build dependencies:
```bash
sudo apt update
sudo apt install build-essential clang flex bison g++ gawk gcc-multilib \
  gettext git libncurses-dev libssl-dev python3-distutils python3-setuptools \
  rsync swig unzip zlib1g-dev file wget
```

## Clone and Setup

```bash
git clone https://git.openwrt.org/openwrt/openwrt.git
cd openwrt
./scripts/feeds update -a
./scripts/feeds install -a
```

## Add M01K43 Board Support

The M01K43 is now in **OpenWrt mainline** (commit `db7d264e`). Building the
stock image no longer requires copying a DTS into the tree or hand-patching
`filogic.mk` -- the device, its DTS, and the `filogic.mk` device block already
ship with OpenWrt.

### Stock image

Just select the device:

```bash
make menuconfig
#   Target System:  MediaTek Ralink ARM
#   Subtarget:      Filogic 8xx (MT798x)
#   Target Profile: AlwayLink M01K43
```

...or drop in the provided build config instead of clicking through menuconfig:

```bash
cp /path/to/m01k43-openwrt/config/diffconfig .config
make defconfig
```

### PMOD daily-driver variant

The PMOD build adds modem power control (`gpio-export` for GPIO 25 power / GPIO 2
pwrkey) plus the signal-LED and recovery overlay. To build it:

1. Replace the in-tree DTS with the PMOD DTS:

   ```bash
   cp /path/to/m01k43-openwrt/dts/mt7981b-alwaylink-m01k43.dts \
      target/linux/mediatek/dts/
   ```

   ...or regenerate it from the in-tree (canonical) DTS with the generator:

   ```bash
   python3 /path/to/m01k43-openwrt/tools/generate-pmod-dts.py \
     target/linux/mediatek/dts/mt7981b-alwaylink-m01k43.dts \
     -o target/linux/mediatek/dts/mt7981b-alwaylink-m01k43.dts
   ```

2. Copy the overlay files:

   ```bash
   cp -r /path/to/m01k43-openwrt/files/ files/
   ```

   This includes uci-defaults scripts, signal LED monitor, recovery tools, and
   package feed config.

3. (optional) Custom banner -- edit `package/base-files/files/etc/banner` and
   add after the version line:

   ```
    M01K43-PMOD | Didneywhorl Edition
   ```

4. Configure with the provided build config:

   ```bash
   cp /path/to/m01k43-openwrt/config/diffconfig .config
   make defconfig
   ```

## Build

**Important:** The kernel MUST compile with `-j1` due to a BPF verifier race condition at higher parallelism. Packages can use full parallelism.

### Full build (first time):
```bash
make target/linux/compile V=s -j1
make package/compile package/install target/install V=s -j$(nproc)
```

### Package-only rebuild (no kernel/DTS changes):
```bash
make package/compile package/install target/install V=s -j$(nproc)
```

### Image-only rebuild (no package changes):
```bash
make package/install target/install V=s -j$(nproc)
```

Build time: ~20 minutes for full build on a 4-core machine.

## Output

Images are in `bin/targets/mediatek/filogic/`:

| File | Purpose |
|------|---------|
| `*-sysupgrade.bin` | Flash from existing OpenWrt |
| `*-factory.bin` | Flash from OEM firmware |
| `*-initramfs-kernel.bin` | RAM-only boot for testing |

## Build Tips

- If you change DEVICE_PACKAGES, you need: `package/compile` + `package/install` + `target/install`
- If `packages.adb` gets corrupted: delete `staging_dir/packages/mediatek/packages.adb`, then run `make package/install`
- New kmod packages require `target/linux/compile` (kernel config is generated from kmod KCONFIG entries)
- DEVICE_PACKAGES entries must be `=y` in `.config`, not `=m`. `=m` compiles but does NOT include in the image.
