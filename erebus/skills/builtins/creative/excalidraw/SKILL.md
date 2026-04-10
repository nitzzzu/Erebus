---
name: excalidraw
description: Create hand-drawn style diagrams using Excalidraw JSON format with shapes, arrows, and text labels.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["creative", "diagrams", "excalidraw", "visualization"]
---

# Excalidraw Diagram Generator

Use this skill to create hand-drawn style diagrams using the Excalidraw JSON format.

## When to Use

- User wants a visual diagram or flowchart
- User needs architecture or system diagrams
- User wants hand-drawn style visuals
- User asks for whiteboard-style illustrations

## Excalidraw JSON Format

Generate a `.excalidraw` JSON file with this structure:

```json
{
  "type": "excalidraw",
  "version": 2,
  "elements": [
    {
      "type": "rectangle",
      "x": 100, "y": 100,
      "width": 200, "height": 80,
      "strokeColor": "#1e1e1e",
      "backgroundColor": "#a5d8ff",
      "fillStyle": "hachure",
      "roundness": { "type": 3 },
      "id": "rect1"
    },
    {
      "type": "text",
      "x": 130, "y": 130,
      "text": "Component A",
      "fontSize": 16,
      "containerId": "rect1",
      "id": "text1"
    },
    {
      "type": "arrow",
      "x": 300, "y": 140,
      "width": 100, "height": 0,
      "startBinding": { "elementId": "rect1" },
      "endBinding": { "elementId": "rect2" },
      "id": "arrow1"
    }
  ]
}
```

## Process

1. **Understand Layout**: Determine what needs to be visualized
2. **Plan Positions**: Calculate x,y coordinates for elements
3. **Generate JSON**: Create the Excalidraw-compatible JSON
4. **Save File**: Write to a `.excalidraw` file
5. **Provide Link**: User can open at https://excalidraw.com
