---
name: p5js
description: Create interactive generative art and visualizations using p5.js with 2D/3D rendering, particles, and shaders.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["creative", "generative-art", "p5js", "interactive", "visualization"]
---

# p5.js Generative Art

Use this skill to create interactive visual art and creative coding projects with p5.js.

## When to Use

- User wants generative art or creative coding
- User needs interactive visualizations
- User wants particle systems or visual effects
- User asks for creative web-based animations

## Template

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.9.0/p5.min.js"></script>
</head>
<body>
<script>
function setup() {
  createCanvas(800, 600);
  background(20);
}

function draw() {
  // Your generative art code here
}
</script>
</body>
</html>
```

## Techniques

- **Noise Fields**: Use `noise()` for organic patterns
- **Particle Systems**: Arrays of moving objects with physics
- **Fractals**: Recursive geometric patterns
- **Audio Reactive**: Use `p5.sound` for music visualization
- **3D**: Use `WEBGL` mode for 3D rendering
- **Shaders**: Custom GLSL fragment shaders

## Process

1. **Concept**: Define the visual idea
2. **Scaffold**: Create HTML + p5.js setup
3. **Implement**: Write the generative algorithm
4. **Tune**: Adjust parameters for visual quality
5. **Save**: Write to an HTML file the user can open
