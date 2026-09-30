import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
IST = ZoneInfo("Asia/Kolkata")
NOW_UTC = datetime.now(timezone.utc)
NOW_IST = NOW_UTC.astimezone(IST)

CATEGORIES = [
    "AI & Agents",
    "Google Ads",
    "Meta Ads",
    "Microsoft Ads",
    "Search & SEO",
    "Analytics",
    "Creative AI",
    "MarTech & Automation",
    "Ecommerce",
]

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "date": {"type": "string"},
        "lead": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "deck": {"type": "string"},
                "url": {"type": "string"},
                "source": {"type": "string"},
                "when": {"type": "string"},
            },
            "required": ["title", "deck", "url", "source", "when"],
        },
        "note": {"type": "string"},
        "ticker": {"type": "array", "items": {"type": "string"}, "minItems": 4, "maxItems": 10},
        "sections": {
            "type": "array",
            "minItems": 9,
            "maxItems": 9,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "stories": {
                        "type": "array",
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "title": {"type": "string"},
                                "summary": {"type": "string"},
                                "source": {"type": "string"},
                                "when": {"type": "string"},
                                "url": {"type": "string"},
                            },
                            "required": ["title", "summary", "source", "when", "url"],
                        },
                    },
                },
                "required": ["name", "stories"],
            },
        },
    },
    "required": ["date", "lead", "note", "ticker", "sections"],
}

SYSTEM = """You are the editor of AI Marketing Daily, a specialist daily newspaper for digital and performance marketers.

Editorial mission:
Find the most significant NEW developments from roughly the last 36 hours, prioritizing primary/official sources and high-quality reporting. Cover AI, generative AI, agentic AI, LLMs, AI search, ad-tech, mar-tech, automation, APIs/SDKs, MCP/tool calling, analytics, creative technology, ecommerce and advertising platforms.

The publication is for practitioners managing Google Ads, Microsoft Ads, Meta Ads, SEO/AEO/GEO, analytics/attribution, CRO, ecommerce, creative production and marketing automation.

Hard rules:
- Do not invent news.
- Do not turn old announcements into today's news.
- Prefer official company/platform announcements for product changes; use reputable reporting for independently reported developments.
- Every story must have an exact source URL that came from the web research. Never fabricate or guess a URL.
- If a category has no meaningful development, leave its stories array empty.
- Do not pad the edition with minor or generic AI stories.
- Separate facts from interpretation. Avoid hype.
- Explain practical marketing impact, not technical trivia.
- Do not include political or electoral content unless it is directly a neutral technology/business development relevant to marketers.
- Headlines should be newspaper-like, specific and useful.
- Summaries should be 2 concise sentences: what happened, then why it matters to marketers.
- "when" should be a compact date such as "30 Sep 2026" or "29 Sep 2026".
- Select one lead story that has the broadest practical significance for digital/performance marketing.
- Keep the entire edition concise: normally 1-3 strong stories per category, maximum 4.
"""

def clean_url(value):
    value = (value or "").strip()
    if not re.match(r"^https?://", value):
        return ""
    return value

def validate(payload):
    if payload.get("date") != NOW_IST.strftime("%-d %B %Y"):
        raise ValueError(f"Unexpected edition date: {payload.get('date')}")
    if len(payload.get("sections", [])) != len(CATEGORIES):
        raise ValueError("Expected exactly 9 sections")

    names = [s.get("name") for s in payload["sections"]]
    if names != CATEGORIES:
        raise ValueError(f"Unexpected section order: {names}")

    stories = [story for section in payload["sections"] for story in section["stories"]]
    if not stories:
        raise ValueError("The model returned no stories")

    for story in stories:
        story["url"] = clean_url(story["url"])
        if not story["url"]:
            raise ValueError(f"Invalid source URL for: {story.get('title')}")
        if len(story["title"]) < 8 or len(story["summary"]) < 40:
            raise ValueError(f"Story too thin: {story.get('title')}")

    payload["lead"]["url"] = clean_url(payload["lead"]["url"])
    if not payload["lead"]["url"]:
        raise ValueError("Invalid lead source URL")
    return payload

def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not configured")

    previous = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    prompt = f"""Prepare the edition dated {NOW_IST.strftime('%-d %B %Y')}.

Current time: {NOW_IST.isoformat()}.

Research the web for significant developments published or announced recently. Search broadly, then verify important stories against primary sources where possible.

Prioritize:
1. OpenAI, Anthropic, Google, Microsoft, Meta, Amazon, TikTok, LinkedIn, Perplexity and other major AI/search companies.
2. Google Ads, Microsoft Advertising, Meta Ads and other major advertising-platform product updates.
3. Search/SEO/AEO/GEO changes and AI search.
4. Analytics, attribution, measurement, CRM, CRO and ecommerce technology.
5. New AI creative, automation, agent, API, SDK and MCP capabilities that marketers can actually use.

Avoid repeating stories already present in the previous edition unless there is a genuinely new update.

Previous edition structure:
{json.dumps(previous, ensure_ascii=False)[:12000]}

Return only the requested structured JSON. Use exact source URLs from your web research."""

    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search", "search_context_size": "high"}],
        input=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "ai_marketing_daily_edition",
                "description": "A verified daily AI and digital marketing newspaper edition.",
                "schema": SCHEMA,
                "strict": True,
            }
        },
    )

    payload = json.loads(response.output_text)
    payload = validate(payload)
    payload["generated_at"] = NOW_IST.isoformat()
    payload["engine"] = {
        "model": MODEL,
        "research": "OpenAI Responses API web search",
        "window": "approximately last 36 hours",
    }

    DATA_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Published {len([x for s in payload['sections'] for x in s['stories']])} stories for {payload['date']}")

if __name__ == "__main__":
    main()
