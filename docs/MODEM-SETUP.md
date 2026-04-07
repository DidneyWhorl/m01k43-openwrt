# M01K43 Modem Setup

## Quectel RM551E-GL Configuration

The modem ships with default settings that may not work for USB QMI data. Three AT commands control the data path:

### Required Modem Settings

Connect to the modem via minicom (`minicom -D /dev/ttyUSB2`) or AT terminal and set:

```
AT+QCFG="pcie/mode",1
AT+QCFG="usbnet",0
AT+QCFG="data_interface",1,1
```

Then reboot the modem (power cycle the router, not `AT+CFUN=1,1`).

### What Each Command Does

#### AT+QCFG="pcie/mode",\<mode\>

Controls PCIe role:
- **0 = Endpoint (EP):** Modem acts as PCIe device. Only 4 USB serial interfaces (no data).
- **1 = Root Complex (RC):** Modem acts as PCIe host. Exposes 5th USB interface for QMI data.

**Must be 1 for USB QMI on this board.**

#### AT+QCFG="usbnet",\<mode\>

Controls USB network protocol:
- **0 = QMI** (recommended, used by uqmi)
- 1 = ECM
- 2 = MBIM
- 3 = RNDIS

#### AT+QCFG="data_interface",\<network\>,\<diag\>

Controls which bus carries data:
- network: 0=USB, 1=PCIe
- diag: 0=USB (only documented value)

## QMI Connection (automatic)

The uci-defaults script (`20-network-wifi`) configures QMI to auto-connect on boot:

```
interface wwan
  proto qmi
  device /dev/cdc-wdm0
  apn fast.T-Mobile.com
  pdptype ipv4v6
  autoconnect 1
```

The `wwan` interface is added to the `wan` firewall zone with masquerading.

## Manual QMI Commands

```bash
# Check registration
uqmi -d /dev/cdc-wdm0 --get-serving-system

# Get signal info
uqmi -d /dev/cdc-wdm0 --get-signal-info

# Start data connection
uqmi -d /dev/cdc-wdm0 --start-network --apn fast.T-Mobile.com --ip-family ipv4

# Get data status
uqmi -d /dev/cdc-wdm0 --get-data-status
```

## APN Configuration

Set the APN for your carrier:

| Carrier | APN |
|---------|-----|
| T-Mobile | fast.T-Mobile.com |
| AT&T | broadband |
| Verizon | vzwinternet |

Edit `files/etc/uci-defaults/20-network-wifi` to change the APN before building, or configure via LuCI after boot.

## Troubleshooting

**No /dev/cdc-wdm0:** Check `AT+QCFG="pcie/mode"` is set to 1. In EP mode (0), the QMI interface is not exposed over USB.

**SIM not detected:** Power cycle the router (not just modem reboot). The bootloader has a specific GPIO power-on sequence that can't be replicated from Linux userspace.

**No data connection:** Verify APN is correct for your carrier. Check `uqmi -d /dev/cdc-wdm0 --get-serving-system` shows "registered".

**AT commands unreliable via echo:** Don't use `echo AT > /dev/ttyUSB2`. Use minicom or a proper serial tool instead.
