---
name: ascii-art
description: Generate ASCII art using pyfiglet, cowsay, toilet, image-to-ASCII conversion, and LLM-powered freehand art.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["creative", "ascii", "art", "text"]
---

# ASCII Art Generator

Use this skill to create ASCII art in various styles.

## When to Use

- User wants ASCII art text banners
- User wants to convert images to ASCII
- User asks for creative text-based artwork
- User wants cowsay-style messages

## Tools

### pyfiglet — Text Banners (571+ fonts)
```bash
pip install pyfiglet
python3 -c "import pyfiglet; print(pyfiglet.figlet_format('Hello', font='slant'))"
```

### cowsay — Speech Bubbles
```bash
pip install cowsay
python3 -c "import cowsay; cowsay.cow('Hello World')"
```

### Image to ASCII
```bash
pip install ascii-magic
python3 -c "
import ascii_magic
art = ascii_magic.from_url('https://example.com/image.jpg', columns=80)
ascii_magic.to_terminal(art)
"
```

### LLM Freehand
For complex or custom ASCII art, use your creative abilities directly.

## Process

1. **Understand Request**: What kind of ASCII art does the user want?
2. **Choose Tool**: Select the best tool for the job
3. **Generate**: Create the ASCII art
4. **Present**: Display in a code block for proper formatting
