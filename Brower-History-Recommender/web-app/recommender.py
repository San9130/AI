import datetime as dt
import json
import math
import os
import re
import shutil
import sqlite3
import tempfile
from urllib.parse import urlencode, urlparse

import requests
import feedparser

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "have",
    "if", "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "there",
    "to", "was", "were", "will", "with", "you", "your",
}

TOKEN_RE = re.compile(r"[a-z0-9]{3,}")

CHROME_EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)

DEFAULT_EXCLUDE_HOSTS = {
    "accounts.google.com",
    "auth.openai.com",
    "mail.google.com",
    "gmail.com",
    "login.microsoftonline.com",
    "login.live.com",
    "github.com",
    "x.com",
    "twitter.com",
    "www.linkedin.com",
    "linkedin.com",
    "facebook.com",
    "www.facebook.com",
}

DEFAULT_EXCLUDE_PATTERNS = re.compile(
    r"(login|signin|sign-in|sign_in|signup|sign-up|oauth|sso|account|accounts|auth|callback)",
    re.IGNORECASE,
)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
OPENAI_API_URL = "https://api.openai.com/v1/responses"
SEMANTIC_SCHOLAR_API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
CROSSREF_API_URL = "https://api.crossref.org/works"


def chrome_time_to_dt(value):
    if value is None:
        return None
    return CHROME_EPOCH + dt.timedelta(microseconds=value)


def tokenize(text):
    if not text:
        return []
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def build_docs(rows):
    docs = []
    for row in rows:
        url = row[1]
        title = row[2] or ""
        visit_count = row[3] or 0
        last_visit = chrome_time_to_dt(row[4])
        parsed = urlparse(url)
        host = parsed.hostname or ""
        path = parsed.path.replace("/", " ")
        tokens = tokenize(title) + tokenize(host) + tokenize(path)
        docs.append({
            "id": row[0],
            "url": url,
            "title": title,
            "visit_count": visit_count,
            "last_visit": last_visit,
            "host": host,
            "tokens": tokens,
        })
    return docs


def tfidf_vectors(docs):
    df = {}
    for doc in docs:
        seen = set(doc["tokens"])
        for t in seen:
            df[t] = df.get(t, 0) + 1

    n = len(docs)
    vectors = []
    for doc in docs:
        tf = {}
        for t in doc["tokens"]:
            tf[t] = tf.get(t, 0) + 1
        vec = {}
        for t, c in tf.items():
            idf = math.log((n + 1) / (1 + df.get(t, 0))) + 1.0
            vec[t] = c * idf
        vectors.append(vec)
    return vectors


def aggregate_vector(vectors, weights=None):
    agg = {}
    for i, vec in enumerate(vectors):
        w = 1.0 if not weights else weights[i]
        for k, v in vec.items():
            agg[k] = agg.get(k, 0.0) + v * w
    return agg


def load_history(history_path):
    if not os.path.exists(history_path):
        raise FileNotFoundError(f"History DB not found: {history_path}")

    with tempfile.TemporaryDirectory() as tmpdir:
        copy_path = os.path.join(tmpdir, "History")
        shutil.copy2(history_path, copy_path)
        conn = sqlite3.connect(copy_path)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, url, title, visit_count, last_visit_time
                FROM urls
                WHERE url LIKE 'http%'
                  AND title IS NOT NULL
                  AND title != ''
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()
    return rows


def resolve_history_path(profile):
    base = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    if profile:
        return os.path.join(base, profile, "History")
    return os.path.join(base, "Default", "History")


def parse_csv_list(value):
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def is_reading_candidate(doc, exclude_hosts, exclude_patterns):
    host = (doc.get("host") or "").lower()
    url = doc.get("url") or ""
    title = doc.get("title") or ""
    if host in exclude_hosts:
        return False
    if exclude_patterns.search(url) or exclude_patterns.search(title):
        return False
    return True


def top_interest_tokens(interest_vec, topn=8):
    ranked = sorted(interest_vec.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in ranked[:topn]]


def extract_response_text(payload):
    if not payload:
        return ""
    outputs = payload.get("output", [])
    chunks = []
    for out in outputs:
        for content in out.get("content", []):
            if content.get("type") == "output_text":
                chunks.append(content.get("text", ""))
            elif content.get("type") == "text":
                chunks.append(content.get("text", ""))
    return "\n".join(chunks).strip()

def extract_json_from_text(text):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def build_openai_prompt(interest_tokens, top_hosts):
    interest = ", ".join(interest_tokens) if interest_tokens else "general topics"
    hosts = ", ".join(top_hosts) if top_hosts else "n/a"
    return f"""
You are a research assistant. Given recent browsing interests, propose arXiv search queries.
Return JSON only with keys: queries (list of 3-6 concise query strings), topics (list of 4-8 short topics).
Keep queries short and focused.

Interests: {interest}
Top hosts: {hosts}
""".strip()


def openai_generate_queries(interest_tokens, top_hosts, model):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY is not set in the environment."}

    prompt = build_openai_prompt(interest_tokens, top_hosts)
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": "You must return JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    }

    payload["text"] = {"format": {"type": "json_object"}}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30)
    except requests.RequestException as exc:
        return {"error": f"OpenAI request failed: {exc}"}

    if response.status_code >= 400:
        return {"error": f"OpenAI API error: {response.status_code} {response.text}"}

    data = response.json()
    if data.get("refusal"):
        return {"error": f"OpenAI refusal: {data.get('refusal')}"}
    text = extract_response_text(data)
    if not text:
        return {"error": "OpenAI response was empty."}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = extract_json_from_text(text)
        if not parsed:
            return {"error": "OpenAI response was not valid JSON."}

    queries = parsed.get("queries", [])
    topics = parsed.get("topics", [])
    if not isinstance(queries, list) or not queries:
        return {"error": "OpenAI did not return queries."}

    return {
        "queries": [str(q).strip() for q in queries if str(q).strip()],
        "topics": [str(t).strip() for t in topics if str(t).strip()],
    }


def fetch_arxiv(query, max_results):
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API_URL}?{urlencode(params)}"
    headers = {"User-Agent": "reading-recs/1.0 (local app)"}
    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()
    return feedparser.parse(resp.text)

def fetch_crossref(query, rows, mailto):
    params = {
        "query": query,
        "rows": rows,
    }
    if mailto:
        params["mailto"] = mailto
    headers = {"User-Agent": "reading-recs/1.0 (local app)"}
    resp = requests.get(CROSSREF_API_URL, params=params, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_semantic_scholar(query, limit, fields, api_key):
    params = {
        "query": query,
        "limit": limit,
        "fields": ",".join(fields),
    }
    headers = {"User-Agent": "reading-recs/1.0 (local app)"}
    if api_key:
        headers["x-api-key"] = api_key
    resp = requests.get(SEMANTIC_SCHOLAR_API_URL, params=params, headers=headers, timeout=20)
    if resp.status_code == 429:
        return {"error": "Semantic Scholar rate limit hit. Add SEMANTIC_SCHOLAR_API_KEY or try again later."}
    if resp.status_code >= 400:
        return {"error": f"Semantic Scholar API error: {resp.status_code}"}
    return resp.json()


def score_item(item, interest_tokens):
    tokens = tokenize(item.get("title", "") + " " + item.get("summary", ""))
    if not tokens:
        return 0.0, []
    overlap = [t for t in interest_tokens if t in tokens]
    score = len(set(overlap)) / max(1, len(set(tokens)))
    return round(score, 3), overlap[:6]


def build_arxiv_recommendations(interest_tokens, query_payload, limit):
    queries = query_payload.get("queries", [])
    if not queries:
        return []
    combined_terms = " OR ".join([f"all:{q}" for q in queries[:6]])
    feed = fetch_arxiv(combined_terms, max_results=max(20, limit * 4))
    seen = set()
    items = []
    for entry in feed.entries:
        entry_id = entry.get("id")
        if not entry_id or entry_id in seen:
            continue
        seen.add(entry_id)
        authors = [a.name for a in entry.get("authors", [])]
        primary = None
        if entry.get("arxiv_primary_category"):
            primary = entry.arxiv_primary_category.get("term")
        pdf_link = ""
        for link in entry.get("links", []):
            if link.get("type") == "application/pdf":
                pdf_link = link.get("href")
                break
        item = {
            "title": entry.get("title", "").replace("\n", " ").strip(),
            "summary": entry.get("summary", "").replace("\n", " ").strip(),
            "url": entry.get("link"),
            "pdf_url": pdf_link,
            "authors": authors,
            "published": entry.get("published"),
            "primary_category": primary,
        }
        score, matched = score_item(item, interest_tokens)
        item["score"] = score
        item["why"] = ", ".join(matched)
        items.append(item)

    items.sort(key=lambda x: (x["score"], x.get("published") or ""), reverse=True)
    return items[:limit]


def build_crossref_recommendations(interest_tokens, query_payload, limit, mailto):
    queries = query_payload.get("queries", [])
    if not queries:
        return []
    combined = " ".join(queries[:6])
    payload = fetch_crossref(combined, rows=max(20, limit * 4), mailto=mailto)
    items = []
    for entry in payload.get("message", {}).get("items", []):
        title_list = entry.get("title") or []
        title = title_list[0] if title_list else ""
        authors = []
        for author in entry.get("author", []):
            name = " ".join([author.get("given", ""), author.get("family", "")]).strip()
            if name:
                authors.append(name)
        published = ""
        published_parts = entry.get("published-print") or entry.get("published-online") or {}
        date_parts = published_parts.get("date-parts", [])
        if date_parts:
            published = "-".join(str(p) for p in date_parts[0])
        item = {
            "title": title,
            "summary": "",
            "url": entry.get("URL", ""),
            "authors": authors,
            "published": published,
            "primary_category": entry.get("type", ""),
            "source": "Crossref",
        }
        score, matched = score_item(item, interest_tokens)
        item["score"] = score
        item["why"] = ", ".join(matched)
        items.append(item)

    items.sort(key=lambda x: (x["score"], x.get("published") or ""), reverse=True)
    return items[:limit]


def build_semantic_scholar_recommendations(interest_tokens, query_payload, limit, api_key):
    queries = query_payload.get("queries", [])
    if not queries:
        return [], ""
    combined = " ".join(queries[:6])
    fields = ["title", "url", "year", "abstract", "authors", "publicationDate", "openAccessPdf", "venue"]
    payload = fetch_semantic_scholar(combined, limit=max(20, limit * 4), fields=fields, api_key=api_key)
    if "error" in payload:
        return [], payload["error"]
    items = []
    for entry in payload.get("data", []):
        authors = [a.get("name", "") for a in entry.get("authors", []) if a.get("name")]
        pdf = entry.get("openAccessPdf") or {}
        item = {
            "title": entry.get("title", ""),
            "summary": entry.get("abstract", "") or "",
            "url": entry.get("url", "") or "",
            "pdf_url": pdf.get("url", ""),
            "authors": authors,
            "published": entry.get("publicationDate") or str(entry.get("year") or ""),
            "primary_category": entry.get("venue", ""),
            "source": "Semantic Scholar",
        }
        score, matched = score_item(item, interest_tokens)
        item["score"] = score
        item["why"] = ", ".join(matched)
        items.append(item)

    items.sort(key=lambda x: (x["score"], x.get("published") or ""), reverse=True)
    return items[:limit], ""


def recommend(params):
    history_path = params.get("history")
    profile = params.get("profile")
    limit = int(params.get("limit", 15))
    recent_days = int(params.get("recent_days", 14))
    min_visits = int(params.get("min_visits", 1))
    def to_bool(value, default=True):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return default

    openai_model = params.get("openai_model", "gpt-4o-mini")
    semantic_scholar_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    crossref_mailto = os.environ.get("CROSSREF_MAILTO")
    use_arxiv = to_bool(params.get("use_arxiv"), True)
    use_crossref = to_bool(params.get("use_crossref"), True)
    use_semantic_scholar = to_bool(params.get("use_semantic_scholar"), True)
    since = params.get("since")
    no_reading_filter = bool(params.get("no_reading_filter", False))
    exclude_hosts = params.get("exclude_hosts", "")
    exclude_url_pattern = params.get("exclude_url_pattern")

    if history_path:
        history_path = os.path.expanduser(history_path)
    else:
        history_path = resolve_history_path(profile)

    rows = load_history(history_path)
    if not rows:
        return {"error": "No history rows found."}

    docs = build_docs(rows)
    docs = [d for d in docs if d["visit_count"] >= min_visits]

    if since:
        try:
            since_local = dt.datetime.strptime(since, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid --since format. Use YYYY-MM-DD."}
        since_local = since_local.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        since_utc = since_local.astimezone(dt.timezone.utc)
        docs = [d for d in docs if d["last_visit"] and d["last_visit"] >= since_utc]

    exclude_hosts_set = set()
    exclude_patterns = None
    if not no_reading_filter:
        exclude_hosts_set.update(DEFAULT_EXCLUDE_HOSTS)
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS
    else:
        exclude_patterns = re.compile(r"$^")

    extra_hosts = parse_csv_list(exclude_hosts)
    exclude_hosts_set.update(h.lower() for h in extra_hosts)

    if exclude_url_pattern:
        try:
            user_pattern = re.compile(exclude_url_pattern, re.IGNORECASE)
        except re.error:
            return {"error": "Invalid exclude pattern regex."}
        if exclude_patterns.pattern == r"$^":
            exclude_patterns = user_pattern
        else:
            exclude_patterns = re.compile(
                f"(?:{exclude_patterns.pattern})|(?:{user_pattern.pattern})",
                re.IGNORECASE,
            )

    docs = [d for d in docs if is_reading_candidate(d, exclude_hosts_set, exclude_patterns)]

    if not docs:
        return {"error": "No history rows after filtering."}

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=recent_days)

    recent_docs = [d for d in docs if d["last_visit"] and d["last_visit"] >= cutoff]
    older_docs = [d for d in docs if not d["last_visit"] or d["last_visit"] < cutoff]

    if not recent_docs:
        return {"error": "Not enough recent history to build an interest profile."}

    vectors = tfidf_vectors(docs)
    doc_index = {d["id"]: i for i, d in enumerate(docs)}

    recent_vectors = [vectors[doc_index[d["id"]]] for d in recent_docs]
    interest = aggregate_vector(recent_vectors)
    interest_tokens = top_interest_tokens(interest, topn=8)

    top_hosts = [d["host"] for d in sorted(recent_docs, key=lambda x: x["visit_count"], reverse=True)[:5]]
    ai_payload = openai_generate_queries(interest_tokens, top_hosts, openai_model)
    if "error" in ai_payload:
        return ai_payload

    if not (use_arxiv or use_crossref or use_semantic_scholar):
        return {"error": "Select at least one source (arXiv, Crossref, or Semantic Scholar)."}

    warnings = []
    semantic_items = []
    if use_semantic_scholar:
        semantic_items, semantic_warning = build_semantic_scholar_recommendations(
            interest_tokens, ai_payload, limit, semantic_scholar_key
        )
        if semantic_warning:
            warnings.append(semantic_warning)

    new_recommendations = {
        "arxiv": build_arxiv_recommendations(interest_tokens, ai_payload, limit) if use_arxiv else [],
        "crossref": build_crossref_recommendations(interest_tokens, ai_payload, limit, crossref_mailto)
        if use_crossref
        else [],
        "semantic_scholar": semantic_items,
    }

    return {
        "interest_tokens": interest_tokens,
        "topics": ai_payload.get("topics", []),
        "queries": ai_payload.get("queries", []),
        "new_recommendations": new_recommendations,
        "warnings": warnings,
    }
