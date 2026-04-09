---
name: openhue
description: Control Philips Hue lights, rooms, and scenes via the OpenHue CLI — brightness, color, temperature, and scheduling.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["smart-home", "hue", "lights", "automation"]
platforms: [macos, linux]
---

# Philips Hue Control (OpenHue)

Use this skill to control Philips Hue smart lights.

## When to Use

- User wants to control their Hue lights
- User needs to adjust brightness, color, or temperature
- User wants to activate scenes
- User needs to schedule lighting changes

## Installation

```bash
pip install openhue-cli
openhue setup  # Pair with Hue Bridge
```

## Operations

### List Lights
```bash
openhue get lights
```

### Control Light
```bash
openhue set light "Desk Lamp" --on
openhue set light "Desk Lamp" --brightness 80
openhue set light "Desk Lamp" --color "#ff6600"
openhue set light "Desk Lamp" --ct 350  # Color temperature in mireds
```

### Scenes
```bash
openhue get scenes
openhue set scene "Relax" --room "Living Room"
```

### Rooms
```bash
openhue get rooms
openhue set room "Office" --brightness 100
```

## Process

1. **Identify**: What lighting change does the user want?
2. **Discover**: List available lights/rooms if needed
3. **Execute**: Apply the lighting change
4. **Confirm**: Report the new state
