#
# /lib/upgrade/platform.sh  --  stock-firmware -> OpenWrt conversion helper
# for the AlwayLink M01K43 (MediaTek MT7981B / Filogic 820).
#
# WHAT THIS IS
#   The stock AlwayLink firmware (QWRT / "MEHS+" family) runs its own
#   sysupgrade flow that verifies an RSA signature ("wtcheck") and refuses
#   to install an unsigned image. This drop-in replacement for the stock
#   /lib/upgrade/platform.sh disables that check and writes a plain OpenWrt
#   UBI factory image directly to both NAND UBI slots.
#
#   It contains NO keys and NO proprietary code -- the only "bypass" is
#   platform_check_image() returning 0 (accept the image as-is). It is a
#   cleaned-up, parameterised derivative of the OEM upgrade script: the
#   original hardcoded a fixed image filename; this version flashes whatever
#   image you pass to `sysupgrade`.
#
# HOW TO USE  (run on the STOCK firmware, over SSH -- see docs/FLASH-GUIDE.md)
#   1. scp this file to the router:  /lib/upgrade/platform.sh   (RAM only;
#      it is not persistent and is gone on reboot -- that's fine)
#   2. scp the OpenWrt *factory* image to /tmp/ (it is a UBI image):
#        openwrt-mediatek-filogic-alwaylink_m01k43-squashfs-factory.bin
#   3. sysupgrade -n /tmp/openwrt-mediatek-filogic-alwaylink_m01k43-squashfs-factory.bin
#
# SAFETY
#   sysupgrade only writes the NAND UBI partitions (mtd8/mtd9). The SPI-NOR
#   boot chain (BL2 + FIP/U-Boot) is never touched, so U-Boot UART recovery
#   is always available if a flash goes wrong. Back up the per-unit
#   partitions (factory/WiFi-cal mtd3, ledeinfo/MAC mtd6) BEFORE flashing --
#   see docs/FLASH-GUIDE.md. Use entirely at your own risk.
#

RAMFS_COPY_BIN='mkfs.f2fs blkid blockdev fw_printenv fw_setenv dmsetup'
RAMFS_COPY_DATA="/etc/fw_env.config /var/lock/fw_printenv.lock"

PART_NAME=firmware

# SPI-NOR layout fallback (not used on the NAND M01K43, kept for completeness).
nor_do_upgrade() {
	sync
	echo 3 > /proc/sys/vm/drop_caches
	if [ -n "$UPGRADE_BACKUP" ]; then
		get_image "$1" "$2" | dd bs=64k skip=1 conv=sync 2>/dev/null | \
			mtd $MTD_ARGS $MTD_CONFIG_ARGS -j "$UPGRADE_BACKUP" write - "${PART_NAME:-image}"
	else
		get_image "$1" "$2" | dd bs=64k skip=1 conv=sync 2>/dev/null | \
			mtd $MTD_ARGS write - "${PART_NAME:-image}"
	fi
	[ $? -ne 0 ] && exit 1
}

# Write the given UBI image to both NAND UBI slots (mtd8 = "ubi", mtd9 = "ubi2").
# Both slots are written identically.
snand_do_upgrade() {
	local img="$1"

	ubidetach -m 8
	ubiformat /dev/mtd8 -y -f "$img" || exit 1

	ubidetach -m 9
	ubiformat /dev/mtd9 -y -f "$img" || exit 1
}

platform_do_upgrade() {
	# NAND units expose a "ubi2" partition; SPI-NOR units do not.
	if grep -q ubi2 /proc/mtd; then
		snand_do_upgrade "$1"
	else
		nor_do_upgrade "$1"
	fi
}

# Accept the image without signature verification. This is the single line
# that defeats the stock 'wtcheck' RSA gate. Returning 0 = "image OK".
platform_check_image() {
	return 0
}
