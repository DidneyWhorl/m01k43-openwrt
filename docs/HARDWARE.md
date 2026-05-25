# M01K43 Hardware Reference

## SoC and Memory

| Component | Detail |
|-----------|--------|
| SoC | MediaTek MT7981B (Filogic 820) |
| CPU | Dual-core ARM Cortex-A53 |
| RAM | 256MB DDR3 |
| SPI-NAND | 128MB (UBI rootfs, managed by NMBM) |
| SPI-NOR | 4MB W25Q32 (bootloader, factory data, config) |

## Flash Layout

### SPI-NAND (128MB, UBI)

| Partition | Offset | Size | Purpose |
|-----------|--------|------|---------|
| ubi | 0x0000000 | 56MB | Primary firmware (kernel + rootfs) |
| ubi2 | 0x3800000 | 56MB | Recovery image storage |

### SPI-NOR (4MB)

| Partition | Offset | Size | MTD | Purpose |
|-----------|--------|------|-----|---------|
| bl2 | 0x000000 | 256KB | mtd0 | BL2 bootloader (read-only) |
| u-boot-env | 0x040000 | 64KB | mtd1 | U-Boot environment |
| factory | 0x050000 | 704KB | mtd2 | WiFi EEPROM + calibration (read-only) |
| fip | 0x100000 | 2MB | mtd3 | FIP (U-Boot + TF-A, read-only) |
| woem | 0x300000 | 64KB | mtd4 | OEM crypto keys |
| ledeinfo | 0x310000 | 64KB | mtd5 | Factory provisioning (MAC at offset 0x18) |
| nvram | 0x320000 | 64KB | mtd6 | NVRAM config |

## Ethernet

- **Switch:** MediaTek MT7531 (DSA)
- **LAN:** 4x GbE ports (port 0-3)
- **WAN:** 1x 2.5GbE via RTL8221B-VB-CG PHY (managed, auto-negotiation 100M/1G/2.5G), on mdio-bus address 6 (port 5)
- **CPU port:** port 6, 2.5GbE uplink to SoC

## WiFi

- Integrated MT7981 radio (mt76 driver)
- 2.4GHz: 2x2 802.11ax (HE20)
- 5GHz: 2x2 802.11ax (HE80)
- EEPROM: factory partition on SPI-NOR, offset 0x0, size 0x5000

## USB and Modem

- xHCI controller, USB 2.0 only (USB 3.0 PHY not routed from M.2 slot)
- DTS: `u3p-dis-msk = <0x01>` disables USB3 port, frees TPHY for PCIe
- PCIe: controller present in SoC but lanes not physically routed on PCB

### Quectel RM551E-GL 5G Modem

- M.2 Key B slot
- Connected via USB 2.0 only (480 Mbps max)
- **Must be in RC mode** (`AT+QCFG="pcie/mode",1`) for USB QMI data

USB interfaces in RC mode (pcie/mode=1):
| Interface | Function |
|-----------|----------|
| ttyUSB0 | DIAG |
| ttyUSB1 | NMEA (GPS) |
| ttyUSB2 | AT commands |
| ttyUSB3 | Modem (PPP) |
| 1-1:1.4 | QMI data (wwan0) |

## GPIO Map

| GPIO | Function | Active | Notes |
|------|----------|--------|-------|
| 0 | WPS button | LOW | Input |
| 1 | Reset button | LOW | Input, claimed by gpio-keys |
| 2 | Modem PWRKEY | HIGH | Output, gpio-export |
| 4 | LED LAN2 | LOW | Blue |
| 5 | LED Status | HIGH | Blue |
| 6 | LED Status | HIGH | Red |
| 7 | RFKill button | LOW | Input |
| 8 | LED WAN | LOW | Blue |
| 9 | LED WiFi | HIGH | Blue |
| 10 | LED Signal 4G | HIGH | Yellow |
| 11 | LED Signal 5G | HIGH | Blue |
| 12 | LED Signal 5G | HIGH | Yellow |
| 13 | LED Signal 4G | HIGH | Blue |
| 22 | LED LAN3 | LOW | Blue |
| 25 | Modem Power | HIGH | Output, gpio-export |
| 38 | MT7531 interrupt | HIGH | Switch IRQ |
| 39 | MT7531 reset | HIGH | Switch reset |

## LEDs

| LED | GPIO | Color | Active | DTS Function |
|-----|------|-------|--------|--------------|
| WAN | 8 | Blue | LOW | LED_FUNCTION_WAN |
| LAN2 | 4 | Blue | LOW | LED_FUNCTION_LAN (enum 2) |
| LAN3 | 22 | Blue | LOW | LED_FUNCTION_LAN (enum 3) |
| Status | 5 | Blue | HIGH | LED_FUNCTION_STATUS |
| Status | 6 | Red | HIGH | LED_FUNCTION_STATUS (enum 1) |
| WiFi | 9 | Blue | HIGH | LED_FUNCTION_WLAN |
| Signal 4G | 10 | Yellow | HIGH | LED_FUNCTION_INDICATOR (enum 0) |
| Signal 5G | 11 | Blue | HIGH | LED_FUNCTION_INDICATOR (enum 1) |
| Signal 5G | 12 | Yellow | HIGH | LED_FUNCTION_INDICATOR (enum 2) |
| Signal 4G | 13 | Blue | HIGH | LED_FUNCTION_INDICATOR (enum 3) |

## Buttons

| Button | GPIO | Key Code | Function |
|--------|------|----------|----------|
| WPS | 0 | KEY_WPS_BUTTON | WPS pairing |
| Reset | 1 | KEY_RESTART | Factory reset (hold >5s) / failsafe (hold ~2s during boot) |
| RFKill | 7 | KEY_RFKILL | WiFi kill switch |
