import json
import re
import html
import ssl
from urllib.parse import urljoin, quote_plus
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
IST = ZoneInfo("Asia/Kolkata")
NOW_UTC = datetime.now(timezone.utc)
NOW_IST = NOW_UTC.astimezone(IST)
WINDOW = NOW_UTC - timedelta(hours=36)

CATEGORIES = [
    "AI & Agents",
    "Google Ads",
    "Meta Ads",
    "Microsoft Ads",
    "TikTok Ads",
    "Search & SEO",
    "Analytics",
    "Creative AI & Design",
    "MarTech & Automation",
    "Ecommerce",
]

QUERIES = {
    "AI & Agents": [
        '"AI agent" marketing OR advertising OR business',
        'generative AI agents APIs MCP marketing',
        'OpenAI OR Anthropic OR Google AI OR Meta AI OR Microsoft AI agent',
    ],
    "Google Ads": [
        'Google Ads update OR announcement OR AI Max',
        'site:blog.google/products/ads-commerce Google Ads',
        'site:support.google.com/google-ads "2026" AI',
    ],
    "Meta Ads": [
        'Meta Ads update OR announcement OR advertising AI',
        'Meta Muse marketing business agent',
        'site:about.fb.com/news advertising AI Meta',
    ],
    "Microsoft Ads": [
        'Microsoft Advertising update OR announcement AI Max',
        'Microsoft Advertising MCP agent',
        'site:about.ads.microsoft.com advertising AI',
    ],
    "TikTok Ads": [
        'TikTok Ads update OR announcement AI advertising',
        'TikTok One Content Suite API',
        'site:ads.tiktok.com/business advertising AI',
    ],
    "Search & SEO": [
        'Google Search update OR AI search SEO',
        'AI Overviews OR AI Mode SEO search update',
        'site:developers.google.com/search "2026" update',
    ],
    "Analytics": [
        'marketing analytics attribution conversion AI update',
        'GA4 analytics measurement update 2026',
        'advertising attribution API update',
    ],
    "Creative AI & Design": [
        'AI creative advertising image video design update',
        'generative video ads creative AI launch',
        'AI design tool marketing update',
    ],
    "MarTech & Automation": [
        'marketing automation AI MCP API update',
        'CRM martech AI agent announcement',
        'workflow automation AI agents marketing',
    ],
    "Ecommerce": [
        'ecommerce AI agents shopping advertising update',
        'agentic commerce retail AI announcement',
        'Amazon Ads ecommerce AI update',
    ],
}

TRUSTED_DOMAINS = (
    "blog.google", "support.google.com", "developers.google.com",
    "about.ads.microsoft.com", "learn.microsoft.com",
    "about.fb.com", "ads.tiktok.com", "advertising.amazon.com",
    "openai.com", "anthropic.com", "perplexity.ai",
    "reuters.com", "techcrunch.com", "axios.com", "wsj.com",
    "searchengineland.com", "searchenginejournal.com", "martech.org",
)

def clean_url(value):
    value = html.unescape((value or "").strip())
    if not re.match(r"^https?://", value):
        return ""
    return value

def source_name(url, fallback="News"):
    host = urlparse(url).netloc.lower().replace("www.", "")
    mapping = {
        "blog.google": "Google",
        "support.google.com": "Google",
        "developers.google.com": "Google",
        "about.ads.microsoft.com": "Microsoft Advertising",
        "learn.microsoft.com": "Microsoft Advertising",
        "about.fb.com": "Meta",
        "ads.tiktok.com": "TikTok",
        "advertising.amazon.com": "Amazon Ads",
        "openai.com": "OpenAI",
        "anthropic.com": "Anthropic",
        "reuters.com": "Reuters",
        "techcrunch.com": "TechCrunch",
        "axios.com": "Axios",
        "wsj.com": "The Wall Street Journal",
        "searchengineland.com": "Search Engine Land",
        "searchenginejournal.com": "Search Engine Journal",
        "martech.org": "MarTech",
    }
    return mapping.get(host, host.split(".")[0].title() if host else fallback)

def resolve_url(url):
    url = clean_url(url)
    if not url:
        return ""
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (AI-Marketing-Daily/1.0)"})
        with urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
            return response.geturl()
    except Exception:
        return url

def parse_date(value):
    if not value:
        return None
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def google_news_feed(query):
    rss = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
    request = Request(rss, headers={"User-Agent": "Mozilla/5.0 (AI-Marketing-Daily/1.0)"})
    with urlopen(request, timeout=20, context=ssl.create_default_context()) as response:
        return response.read()

def fetch_feed_items(query):
    try:
        root = ET.fromstring(google_news_feed(query))
    except Exception:
        return []
    items = []
    for node in root.findall(".//item"):
        title = html.unescape((node.findtext("title") or "").strip())
        raw_link = (node.findtext("link") or "").strip()
        description = html.unescape(re.sub(r"<[^>]+>", " ", node.findtext("description") or "")).strip()
        published = parse_date(node.findtext("pubDate") or "")
        if not title or not raw_link or not published or published < WINDOW:
            continue
        link = resolve_url(raw_link)
        if not link:
            continue
        source = source_name(link)
        if source == "News":
            source_node = node.find("source")
            source = (source_node.text or "News").strip() if source_node is not None else "News"
        items.append({
            "title": re.sub(r"\s+", " ", title),
            "description": re.sub(r"\s+", " ", description),
            "url": link,
            "source": source,
            "published": published,
        })
    return items

def tokens(text):
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    stop = {"the","and","for","with","from","that","this","into","will","about","after","over","says","said","new","more","than","its","are","has","have","how","what","why","you","their","they","can"}
    return {w for w in words if w not in stop}

def relevance(item):
    text = (item["title"] + " " + item["description"]).lower()
    score = 0
    for term in ["launch","announc","update","rollout","available","introduc","api","agent","ai","ads","advertis","search","marketing","automation","mcp"]:
        if term in text:
            score += 2
    if any(domain in item["url"] for domain in TRUSTED_DOMAINS):
        score += 5
    return score

def dedupe(items):
    chosen = {}
    for item in sorted(items, key=lambda x: (relevance(x), x["published"]), reverse=True):
        key = re.sub(r"[^a-z0-9]+", " ", item["title"].lower()).strip()
        key = " ".join(key.split()[:14])
        if key not in chosen:
            chosen[key] = item
    return list(chosen.values())

def compact_description(text):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "A recent development relevant to digital and performance marketing."
    parts = re.split(r"(?<=[.!?])\s+", text)
    useful = [p.strip() for p in parts if len(p.strip()) > 35]
    return " ".join(useful[:2])[:420]

def marketing_impact(category, title, description):
    text = (title + " " + description).lower()
    if category in ("Google Ads", "Microsoft Ads", "Meta Ads", "TikTok Ads"):
        return "For marketers, the practical impact is how this changes campaign setup, automation, measurement, creative control or optimization workflows."
    if category == "Search & SEO":
        return "For search teams, the key implication is how this changes visibility, query behavior, content strategy, or measurement in AI-driven search."
    if category == "Analytics":
        return "For performance teams, the important question is how this changes attribution, conversion quality, reporting or optimization signals."
    if category == "Ecommerce":
        return "For ecommerce teams, this can affect discovery, product feeds, agentic shopping, conversion paths or advertising efficiency."
    return "For marketers, the useful angle is whether this creates a practical new capability, workflow, integration or automation opportunity."

def make_story(item, category):
    desc = compact_description(item["description"])
    summary = desc
    impact = marketing_impact(category, item["title"], desc)
    if not summary.endswith((".", "!", "?")):
        summary += "."
    summary += " " + impact
    return {
        "title": item["title"],
        "summary": summary[:900],
        "source": item["source"],
        "when": item["published"].astimezone(IST).strftime("%-d %b %Y"),
        "url": item["url"],
        "published_dt": item["published"],
    }

def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 35]

def build_cross_source_summary(all_items):
    clusters = []
    for item in all_items:
        title_tokens = tokens(item["title"])
        best = None
        best_score = 0
        for cluster in clusters:
            score = len(title_tokens & cluster["tokens"])
            if score >= 2 and score > best_score:
                best = cluster
                best_score = score
        if best:
            best["items"].append(item)
            best["tokens"] |= title_tokens
        else:
            clusters.append({"tokens": set(title_tokens), "items": [item]})

    topics = []
    for cluster in clusters:
        if len(cluster["items"]) < 2:
            continue
        cluster_items = sorted(cluster["items"], key=lambda x: x["published"], reverse=True)
        topic = cluster_items[0]["title"]
        common = cluster_items[0]["description"] or cluster_items[0]["title"]
        unique_points = []
        corpus = [tokens(x["title"] + " " + x["description"]) for x in cluster_items]
        for idx, item in enumerate(cluster_items[:4]):
            sentences = split_sentences(item["description"]) or [item["title"]]
            best_sentence = sentences[0]
            best_unique = -1
            for sentence in sentences:
                st = tokens(sentence)
                overlap = max([len(st & other) for j, other in enumerate(corpus) if j != idx] or [0])
                score = len(st) - overlap
                if score > best_unique:
                    best_unique = score
                    best_sentence = sentence
            unique_points.append({
                "source": item["source"],
                "when": item["published"].astimezone(IST).strftime("%-d %b %Y"),
                "point": best_sentence[:500],
                "url": item["url"],
            })
        topics.append({
            "topic": topic,
            "status": "Cross-source coverage",
            "common_context": compact_description(common),
            "unique_points": unique_points,
            "bottom_line": "The coverage overlaps on the core development, but the points above are the incremental details surfaced by each source. Treat the source-specific details as the items to verify before acting.",
        })
    return {
        "title": "Summary — What’s Actually New",
        "intro": "Repeated facts are compressed so the edition highlights what each source adds beyond the common story.",
        "topics": topics[:6],
    }

def fetch_og_image(url):
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Marketing-Daily/1.0)"})
        with urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
            if "text/html" not in response.headers.get("content-type", ""):
                return ""
            raw = response.read(500000).decode("utf-8", errors="ignore")
        patterns = [
            r"""<meta[^>]+property=["'](?:og:image|og:image:url)["'][^>]+content=["']([^"']+)["']""",
            r"""<meta[^>]+content=["']([^"']+)["'][^>]+property=["'](?:og:image|og:image:url)["']""",
            r"""<meta[^>]+name=["'](?:twitter:image|twitter:image:src)["'][^>]+content=["']([^"']+)["']""",
            r"""<meta[^>]+content=["']([^"']+)["'][^>]+name=["'](?:twitter:image|twitter:image:src)["']""",
        ]
        for pattern in patterns:
            match = re.search(pattern, raw, flags=re.I)
            if match:
                image = urljoin(url, html.unescape(match.group(1).strip()))
                if re.match(r"^https?://", image):
                    return image
    except Exception:
        pass
    return ""

def fetch_relevant_image(title, source=""):
    try:
        query = f"{title} {source}".strip()
        api = ("https://commons.wikimedia.org/w/api.php?action=query&generator=search"
               f"&gsrsearch={quote_plus(query)}&gsrnamespace=6&gsrlimit=5"
               "&prop=imageinfo&iiprop=url&iiurlwidth=1200&format=json&origin=*")
        request = Request(api, headers={"User-Agent": "AI-Marketing-Daily/1.0"})
        with urlopen(request, timeout=12, context=ssl.create_default_context()) as response:
            data = json.loads(response.read(1000000).decode("utf-8", errors="ignore"))
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            image = info.get("thumburl") or info.get("url")
            if image and re.match(r"^https?://", image):
                return image
    except Exception:
        pass
    return ""

def add_images(payload):
    cache = {}
    items = [payload["lead"]] + [story for section in payload["sections"] for story in section["stories"]]
    for item in items:
        url = clean_url(item.get("url"))
        if url not in cache:
            cache[url] = fetch_og_image(url) if url else ""
            if not cache[url]:
                cache[url] = fetch_relevant_image(item.get("title", ""), item.get("source", ""))
        item["image"] = cache[url]
    return payload

def validate(payload):
    if len(payload.get("sections", [])) != len(CATEGORIES):
        raise ValueError("Expected exactly 10 sections")
    names = [s.get("name") for s in payload["sections"]]
    if names != CATEGORIES:
        raise ValueError(f"Unexpected section order: {names}")
    stories = [story for section in payload["sections"] for story in section["stories"]]
    if not stories:
        raise ValueError("No current stories were found")
    for story in stories:
        story["url"] = clean_url(story["url"])
        if not story["url"]:
            raise ValueError(f"Invalid source URL for: {story.get('title')}")
    payload["lead"]["url"] = clean_url(payload["lead"]["url"])
    if not payload["lead"]["url"]:
        raise ValueError("Invalid lead source URL")
    return payload

def main():
    collected = {category: [] for category in CATEGORIES}
    for category, queries in QUERIES.items():
        for query in queries:
            collected[category].extend(fetch_feed_items(query))
        collected[category] = dedupe(collected[category])[:4]

    stories_by_category = {}
    all_items = []
    for category in CATEGORIES:
        stories = [make_story(item, category) for item in collected[category]]
        stories_by_category[category] = stories
        all_items.extend(collected[category])

    all_items = dedupe(all_items)
    all_story_items = [make_story(item, next((c for c in CATEGORIES if item in collected[c]), "AI & Agents")) for item in all_items]

    if not all_story_items:
        raise RuntimeError("No recent stories could be retrieved from Google News RSS")

    lead_story = max(all_story_items, key=lambda x: relevance({
        "title": x["title"], "description": x["summary"], "url": x["url"]
    }))

    payload = {
        "date": NOW_IST.strftime("%-d %B %Y"),
        "lead": {
            "title": lead_story["title"],
            "deck": lead_story["summary"],
            "url": lead_story["url"],
            "source": lead_story["source"],
            "when": lead_story["when"],
        },
        "note": "Edition generated from recent RSS news coverage. Primary/official sources are prioritized when surfaced by the feeds; verify important changes at the linked source.",
        "ticker": [x["title"] for x in all_story_items[:8]],
        "sections": [
            {"name": category, "stories": stories_by_category[category][:4]}
            for category in CATEGORIES
        ],
        "summary": build_cross_source_summary(all_items),
        "generated_at": NOW_IST.isoformat(),
        "engine": {
            "model": "none",
            "research": "Google News RSS + source-page metadata",
            "window": "approximately last 36 hours",
            "api_credits_required": False,
        },
    }

    # Remove internal datetime objects before serialization.
    for section in payload["sections"]:
        for story in section["stories"]:
            story.pop("published_dt", None)

    payload = validate(payload)
    payload = add_images(payload)
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = len([x for s in payload["sections"] for x in s["stories"]])
    print(f"Published {count} stories for {payload['date']} without an AI API dependency")

if __name__ == "__main__":
    main()
