#!/usr/bin/env python3
"""
generate-pmod-dts.py â€” Derive the M01K43 PMOD daily-driver DTS from the canonical DTS.

The CANONICAL DTS (the version merged upstream as commit db7d264e, committed at HEAD
of branch upstream-m01k43) is the SINGLE SOURCE OF TRUTH. The PMOD variant is the
canonical DTS plus exactly TWO PMOD-specific additions:

  1. A `gpio-export` node (exports the modem GPIOs 5gpwrkey/5gpower), inserted
     immediately BEFORE the root-level `leds {` block.
  2. A `read-only;` property inside the `partition@300000` ("woem") node.

This script REPLACES hand-maintaining a second DTS by hand (which previously drifted
and caused a regression). It injects the two additions by ANCHOR matching (not by line
number), is IDEMPOTENT (re-running is a no-op), and is FAIL-LOUD: if an expected anchor
is missing (e.g. upstream restructured the DTS) it exits non-zero instead of emitting a
silently-wrong file.

Usage:
    generate-pmod-dts.py CANONICAL.dts [-o PMOD_OUTPUT.dts]
    generate-pmod-dts.py CANONICAL.dts            # writes PMOD DTS to stdout
"""

import argparse
import re
import sys

# --- The two PMOD additions, verbatim (tab-indented to match the DTS style) ---

# gpio-export node: one-tab indented opener (sibling of `leds`, child of root node).
GPIO_EXPORT_NODE = (
    "\tgpio-export {\n"
    "\t\tcompatible = \"gpio-export\";\n"
    "\t\t#size-cells = <0>;\n"
    "\n"
    "\t\tmodem-pwrkey {\n"
    "\t\t\tgpio-export,name = \"5gpwrkey\";\n"
    "\t\t\tgpio-export,output = <0>;\n"
    "\t\t\tgpios = <&pio 2 GPIO_ACTIVE_HIGH>;\n"
    "\t\t};\n"
    "\n"
    "\t\tmodem-power {\n"
    "\t\t\tgpio-export,name = \"5gpower\";\n"
    "\t\t\tgpio-export,output = <0>;\n"
    "\t\t\tgpios = <&pio 25 GPIO_ACTIVE_HIGH>;\n"
    "\t\t};\n"
    "\t};\n"
    "\n"
)

# Anchor: the root-level `leds {` block opener (exactly one leading tab).
LEDS_ANCHOR_RE = re.compile(r"^\tleds \{$", re.MULTILINE)

# read-only; line, four-tab indented (matches sibling properties in partition@300000).
READ_ONLY_LINE = "\t\t\t\tread-only;\n"

# Anchor: the partition@300000 node, capturing its full body up to its closing brace.
# Group 1 = node header+body (props), group 2 = the closing `\t\t\t};` line.
PARTITION_RE = re.compile(
    r"(\t\t\tpartition@300000 \{\n(?:\t\t\t\t.*\n)*?)(\t\t\t\};\n)"
)


def has_gpio_export(text):
    """True if the modem gpio-export node is already present."""
    return ('gpio-export,name = "5gpwrkey"' in text and
            'gpio-export,name = "5gpower"' in text)


def insert_gpio_export(text):
    """Insert the gpio-export node immediately before the root-level `leds {`."""
    if has_gpio_export(text):
        return text, False
    m = LEDS_ANCHOR_RE.search(text)
    if not m:
        sys.exit("ERROR: anchor not found: root-level `leds {` block. "
                 "Canonical DTS structure changed; refusing to emit a wrong file.")
    # Insert the node + its trailing blank line right before the leds opener.
    new = text[:m.start()] + GPIO_EXPORT_NODE + text[m.start():]
    return new, True


def add_read_only(text):
    """Add `read-only;` inside the partition@300000 ("woem") node."""
    m = PARTITION_RE.search(text)
    if not m:
        sys.exit("ERROR: anchor not found: `partition@300000` node. "
                 "Canonical DTS structure changed; refusing to emit a wrong file.")
    body = m.group(1)
    if "read-only;" in body:
        return text, False  # already present -> idempotent no-op
    # Append read-only; as the last property, before the node's closing brace.
    replacement = body + READ_ONLY_LINE + m.group(2)
    new = text[:m.start()] + replacement + text[m.end():]
    return new, True


def generate(canonical_text):
    text, _ = insert_gpio_export(canonical_text)
    text, _ = add_read_only(text)
    return text


def main():
    ap = argparse.ArgumentParser(
        description="Generate the M01K43 PMOD DTS from the canonical DTS.")
    ap.add_argument("canonical", help="path to the canonical (upstream-clean) DTS")
    ap.add_argument("-o", "--output",
                    help="output path for the PMOD DTS (default: stdout)")
    args = ap.parse_args()

    with open(args.canonical, "r", newline="") as f:
        canonical = f.read()

    pmod = generate(canonical)

    if args.output:
        with open(args.output, "w", newline="") as f:
            f.write(pmod)
        sys.stderr.write(f"Wrote PMOD DTS to {args.output}\n")
    else:
        sys.stdout.write(pmod)


if __name__ == "__main__":
    main()
