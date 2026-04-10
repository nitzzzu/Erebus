---
name: ocr-and-documents
description: Extract text from PDFs, images, DOCX, and PPTX using pymupdf, marker-pdf, and python-docx.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["productivity", "ocr", "pdf", "documents", "extraction"]
---

# OCR & Document Extraction

Use this skill to extract text from various document formats.

## When to Use

- User uploads or references a PDF that needs text extraction
- User has scanned documents or images with text
- User needs to read DOCX or PPTX files
- User wants to convert documents to markdown

## Tools

### pymupdf (lightweight, fast)
```bash
pip install pymupdf
python3 -c "
import fitz
doc = fitz.open('document.pdf')
for page in doc:
    print(page.get_text())
"
```

### marker-pdf (OCR for complex layouts)
```bash
pip install marker-pdf
marker_single document.pdf output_dir/
```

### python-docx (Word documents)
```bash
pip install python-docx
python3 -c "
from docx import Document
doc = Document('file.docx')
for para in doc.paragraphs:
    print(para.text)
"
```

## Process

1. **Identify Format**: Determine the document type
2. **Choose Tool**: Select the best extraction method
3. **Extract**: Run the extraction
4. **Clean**: Post-process the extracted text
5. **Present**: Return the content in a readable format
