---
name: nano-pdf
description: Edit PDFs with natural-language instructions using the nano-pdf CLI tool.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "pdf", "editing", "documents"]
---

# Nano PDF Editor

Use this skill to edit PDF files with natural-language instructions.

## When to Use

- User wants to edit a PDF file
- User needs to merge, split, or rearrange PDF pages
- User wants to add text, images, or watermarks to PDFs
- User needs to extract text or images from PDFs

## Installation

```bash
pip install nano-pdf
```

## Usage

```bash
nano-pdf edit input.pdf "Remove the second page and add a watermark 'DRAFT' on all pages"
nano-pdf merge file1.pdf file2.pdf -o combined.pdf
nano-pdf split input.pdf -o output_dir/
nano-pdf extract-text input.pdf
```

## Process

1. **Understand**: What PDF operation does the user need?
2. **Check File**: Verify the PDF exists and is readable
3. **Execute**: Run the appropriate nano-pdf command
4. **Verify**: Confirm the operation succeeded
5. **Deliver**: Provide the output file path
