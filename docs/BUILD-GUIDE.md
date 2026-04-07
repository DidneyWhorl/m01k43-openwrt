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

### 1. Copy DTS

```bash
cp /path/to/m01k43-openwrt/dts/mt7981b-alwaylink-m01k43.dts \
   target/linux/mediatek/dts/
```

Use the PMOD DTS (with gpio-export) for full modem power control, or the upstream version for a minimal build.

### 2. Add Device Block to filogic.mk

Edit `target/linux/mediatek/image/filogic.mk` and add the device block from `patches/filogic-device-block.txt` in alphabetical order (after `acelink`, before `acer`).

### 3. Copy Overlay Files

```bash
cp -r /path/to/m01k43-openwrt/files/ files/
```

This includes uci-defaults scripts, signal LED monitor, recovery tools, and package feed config.

### 4. Copy Banner (optional)

To get the custom "Didneywhorl Edition" banner, edit `package/base-files/files/etc/banner` and add after the version line:
```
 M01K43-PMOD | Didneywhorl Edition
```

### 5. Configure

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
