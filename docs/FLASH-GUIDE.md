# M01K43 Flash Guide

## From Existing OpenWrt

If the router is already running OpenWrt:

```bash
# Copy image to router
scp -O openwrt-mediatek-filogic-alwaylink_m01k43-squashfs-sysupgrade.bin \
  root@192.168.1.1:/tmp/sysupgrade.bin

# Flash with clean config
ssh root@192.168.1.1 'sysupgrade -n /tmp/sysupgrade.bin'
```

The `-n` flag does a clean flash (no config preserved). All settings are restored from uci-defaults on first boot.

### Board Rename (first flash from m10k43 to m01k43)

If upgrading from an older build with a different board name, add `-F` (force):

```bash
ssh root@192.168.1.1 'sysupgrade -n -F /tmp/sysupgrade.bin'
```

## From OEM Firmware

If the router is running stock OEM firmware:

1. Gain SSH/telnet access to the OEM firmware
2. Transfer the `factory.bin` image to the router
3. Flash using the OEM's MTD tools or U-Boot TFTP

Details depend on the specific OEM firmware version. The factory.bin image is a raw UBI image suitable for direct NAND programming.

## From U-Boot (serial console)

If you have UART access (serial console at 115200 baud):

1. Connect UART to the board's serial header
2. Interrupt U-Boot autoboot
3. Use TFTP or XMODEM to transfer the image
4. Write to NAND via U-Boot commands

## After Flashing

On first boot after a clean flash (`-n`):

1. uci-defaults scripts run automatically (WiFi, QMI, LEDs, password, MAC, hostname)
2. Scripts self-delete after execution
3. Signal LED monitor starts (procd service)
4. QMI connection establishes within ~30 seconds
5. Router is accessible at `192.168.1.1`

**Default credentials:**
- Web UI: http://192.168.1.1 (root / internet)
- SSH: root@192.168.1.1 (password: internet)
- WiFi: SSID `M01K43-PMOD`, password in `20-network-wifi`

## SCP Notes

- SCP to this router requires the `-O` flag (legacy SCP protocol mode)
- Example: `scp -O file.bin root@192.168.1.1:/tmp/`
