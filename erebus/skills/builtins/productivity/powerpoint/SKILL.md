---
name: powerpoint
description: Create, edit, and read PowerPoint presentations with markitdown extraction and pptxgenjs generation.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "powerpoint", "presentations", "slides"]
---

# PowerPoint Generator

Use this skill to create and edit PowerPoint presentations.

## When to Use

- User wants to create a presentation
- User needs to extract content from a PPTX file
- User wants to edit existing slides
- User needs presentation design guidance

## Reading PPTX

```bash
pip install markitdown
markitdown presentation.pptx
```

## Creating PPTX

Use python-pptx:
```python
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[1])
title = slide.shapes.title
title.text = "My Presentation"
body = slide.placeholders[1]
body.text = "Key points here"
prs.save('output.pptx')
```

## Design Guidelines

- Max 6 bullet points per slide
- Font size: 28pt+ for titles, 18pt+ for body
- High contrast colors
- Consistent layout throughout
- One idea per slide

## Process

1. **Outline**: Create slide outline from content
2. **Design**: Choose layout and style
3. **Generate**: Create the PPTX file
4. **Review**: Check formatting and content
5. **Deliver**: Save and provide the file path
