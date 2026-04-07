# M01K43 Recovery System

## Overview

The M01K43 includes a Tier 1 recovery system that stores a known-good firmware image in the `ubi2` partition. If a bad flash or configuration bricks the primary firmware, you can restore from recovery via OpenWrt's failsafe mode.

## Recovery Tools

Three utilities are included in the firmware:

### recovery-write

Stores a sysupgrade image as the recovery image in ubi2:

```bash
recovery-write /tmp/sysupgrade.bin
```

This formats ubi2, creates a static UBI volume, and writes the image. Run this after every successful build to keep the recovery image current.

### recovery-restore

Restores the system from the recovery image:

```bash
recovery-restore
```

This reads the recovery image from ubi2 and flashes it via `sysupgrade -n` (clean config). All settings are restored from uci-defaults on reboot.

### recovery-status

Checks the recovery system health:

```bash
recovery-status
```

Reports whether the recovery image is present and ready.

## Recovery Procedure

### When the router is accessible via SSH:

```bash
recovery-restore
```

### When the router is NOT accessible (bad config, broken services):

1. **Power off** the router
2. **Hold the reset button** while powering on
3. **Release after ~2 seconds** when LEDs change (failsafe mode)
4. **Connect via ethernet** to any LAN port
5. **SSH to 192.168.1.1:**
   ```bash
   ssh root@192.168.1.1
   ```
6. **Run recovery:**
   ```bash
   recovery-restore
   ```
7. Router will flash the recovery image and reboot

This is the standard OpenWrt failsafe mode. In failsafe, the router runs a minimal system with SSH access but no configuration applied.

## How It Works

- `ubi2` (mtd8, 56MB) is a separate UBI partition on the SPI-NAND
- `recovery-write` creates a static UBI volume named "recovery" containing a sysupgrade.bin
- `recovery-restore` attaches ubi2, reads the image to /tmp, then runs `sysupgrade -n`
- The `-n` flag ensures clean config, so uci-defaults scripts re-apply everything
- The recovery image itself survives the restore (ubi2 is a separate partition)

## Best Practices

- Run `recovery-write` after every successful build/flash
- Keep the recovery image reasonably current
- Test `recovery-status` periodically to verify the image is intact
- The recovery image should be a known-good build that you've verified boots correctly
