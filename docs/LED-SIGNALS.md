# M01K43 Signal LED Monitor

## Overview

The signal LED monitor (`/usr/bin/signal-led-monitor`) is a procd service that polls the modem's signal status every 15 seconds and drives the status and signal LEDs accordingly.

## LED Behavior

### Top Status LEDs (GPIO 5 blue + GPIO 6 red)

| State | Blue | Red | Visual |
|-------|------|-----|--------|
| 5G connected | ON | OFF | Solid blue |
| 4G connected | ON | ON | Purple |
| Offline/error | OFF | ON | Solid red |

No flashing or heartbeat. LEDs are always solid.

### Side Signal LEDs

| LED | GPIO | Color | Meaning |
|-----|------|-------|---------|
| Signal 5G | 11 | Blue | 5G signal good (RSRP > -100 dBm) |
| Signal 5G | 12 | Yellow | 5G signal weak (RSRP <= -100 dBm) |
| Signal 4G | 13 | Blue | 4G signal good (RSRP > -100 dBm) |
| Signal 4G | 10 | Yellow | 4G signal weak (RSRP <= -100 dBm) |

Only the LEDs matching the current connection type light up. If connected to 5G, the 4G LEDs stay off and vice versa.

## How It Works

1. Service checks for `/dev/cdc-wdm0` (QMI control device)
2. Runs `uqmi -d /dev/cdc-wdm0 --get-signal-info`
3. Parses the JSON response for `type` (5gnr, lte) and `rsrp` (signal strength)
4. Sets LED brightness via sysfs (`/sys/class/leds/*/brightness`)
5. Sleeps 15 seconds, repeats

## Service Management

```bash
# Check status
/etc/init.d/signal-led status

# Stop
/etc/init.d/signal-led stop

# Start
/etc/init.d/signal-led start

# Disable at boot
/etc/init.d/signal-led disable
```

## UCI LED Triggers

In addition to the signal monitor, these LEDs have UCI triggers configured by `30-leds`:

| LED | Trigger | Behavior |
|-----|---------|----------|
| WiFi | phy0radio | Solid on when radio is active |
| WAN | netdev wwan0 | On when wwan0 has link |
| LAN2 | netdev lan2 | On when LAN2 has link |
| LAN3 | netdev lan3 | On when LAN3 has link |

## RSRP Signal Strength Reference

| RSRP (dBm) | Quality | LED Color |
|-------------|---------|-----------|
| > -80 | Excellent | Blue |
| -80 to -100 | Good | Blue |
| -100 to -110 | Fair | Yellow |
| < -110 | Poor | Yellow |
