# Skill: YouTube Review Research

- **Name**: youtube-review-research
- **Description**: Search, extract, and synthesize video reviews, spoken transcripts, and top comments to derive hands-on product feedback.

## When to Use
Use this skill during Stage 5 of the pipeline to discover video evaluations, long-term durability assessments, and creator teardowns.

## Step by Step Procedure
1. Construct targeted search queries combining canonical brand, model, and keywords: "review", "long term", "pros cons", "problems".
2. Search via YouTube Data API v3 if `YOUTUBE_API_KEY` is present; otherwise fall back to search scraping.
3. Select top 3 to 5 candidate videos based on relevance and view counts, filtering out pure promotional shorts.
4. Attempt transcript extraction using `youtube-transcript-api`.
5. If transcript is unavailable or disabled by creator, fall back to extracting video title, full description, and top viewer comments.
6. Check for sponsorship indicators: look for "#ad", "sponsored by", "sent by brand for review", or paid promotion disclosures.
7. Synthesize pros, cons, durability notes, and consensus sentiment score.
8. Store video metadata, URL, and summary in the database.

## Code Patterns
```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript_text(video_id: str) -> str | None:
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry["text"] for entry in transcript_list])
    except Exception:
        return None
```

## Pitfalls
- Exceeding YouTube Data API v3 quota (10,000 units/day) by making excessive search calls: cache video IDs per product.
- Relying entirely on transcripts when many videos have captions disabled: always provide the title, description, and comment fallback.
- Confusing sponsored creator previews with independent long-term reviews.

## Done Checklist
- [ ] Fallback to title and description when transcript fails.
- [ ] Sponsorship disclosures checked and flagged.
- [ ] Video URL and timestamped evidence linked.
- [ ] Zero emojis or unicode dashes in synthesized summary copy.
