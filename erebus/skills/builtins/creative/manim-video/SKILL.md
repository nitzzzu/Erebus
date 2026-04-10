---
name: manim-video
description: Create educational math and technical animations using the Manim library for video generation.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["creative", "animation", "math", "video", "education"]
---

# Manim Video Generator

Use this skill to create educational animations using Manim (Mathematical Animation Engine).

## When to Use

- User wants animated math explanations
- User needs algorithm visualizations
- User wants educational video content
- User asks for animated diagrams or proofs

## Setup

```bash
pip install manim
# For LaTeX support: ensure texlive is installed
```

## Example Scene

```python
from manim import *

class ExampleScene(Scene):
    def construct(self):
        title = Text("Hello Manim!", font_size=48)
        self.play(Write(title))
        self.wait()

        circle = Circle(radius=2, color=BLUE)
        self.play(Transform(title, circle))
        self.wait()
```

## Render

```bash
manim -pql scene.py ExampleScene  # Preview quality
manim -pqh scene.py ExampleScene  # High quality
```

## Process

1. **Plan Scene**: Outline the animation sequence
2. **Write Code**: Create a Manim Scene class
3. **Test**: Render at preview quality first
4. **Refine**: Adjust timing, colors, transitions
5. **Export**: Render at final quality
