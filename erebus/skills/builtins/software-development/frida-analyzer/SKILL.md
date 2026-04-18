---
name: frida-analyzer
description: Frida dynamic instrumentation tools for the CodeAgent — mobile app analysis and SSL unpinning
---

# Frida Analyzer — CodeAgent Tools

## Overview

This skill extends the CodeAgent with Frida-based dynamic instrumentation
for Android and iOS app analysis.  Automate SSL unpinning, hook functions,
trace API calls, and dump runtime data.

Based on [frida-interception-and-unpinning](https://github.com/httptoolkit/frida-interception-and-unpinning).

## Setup

```bash
pip install frida-tools
# For Android: adb must be on PATH, device/emulator connected
```

## CodeAgent Functions

- `frida_devices()` — list connected Frida devices
- `frida_apps(device="usb")` — list installed apps on device
- `frida_spawn(package, script=None, device="usb")` — spawn app with optional script
- `frida_attach(target, script=None, device="usb")` — attach to running process
- `frida_unpin_ssl(package, device="usb")` — bypass SSL pinning
- `frida_trace(package, pattern, device="usb")` — trace function calls
- `frida_run_script(target, script_code, device="usb")` — inject custom JS

## Example

```python
# List connected devices
devices = frida_devices()
print(devices)

# List apps on USB device
apps = frida_apps()
for app in apps[:10]:
    print(f"  {app}")

# Bypass SSL pinning on an app
result = frida_unpin_ssl("com.example.app")
print(result)
```
