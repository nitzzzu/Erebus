---
name: youtube-content
description: Fetch YouTube video transcripts and transform them into chapters, summaries, blog posts, or threads.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["media", "youtube", "transcripts", "content"]
---

# YouTube Content Extractor

Use this skill to extract and repurpose YouTube video content.

## When to Use

- User shares a YouTube URL and wants a summary
- User needs the transcript of a video
- User wants to create blog posts or threads from video content
- User needs chapters or timestamps from a video

## Installation

```bash
pip install youtube-transcript-api
```

## Usage

```python
from youtube_transcript_api import YouTubeTranscriptApi

transcript = YouTubeTranscriptApi.get_transcript("VIDEO_ID")
full_text = " ".join([entry['text'] for entry in transcript])
```

## Transformations

- **Summary**: Concise overview of the video content
- **Chapters**: Break into logical sections with timestamps
- **Blog Post**: Restructure as a written article
- **Thread**: Break into tweet-sized points
- **Key Quotes**: Extract notable statements

## Process

1. **Extract**: Get the transcript from the YouTube video
2. **Analyze**: Identify key topics and structure
3. **Transform**: Convert to the requested format
4. **Deliver**: Present the final content
