#!/usr/bin/env python3
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from urllib.parse import urlparse

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


def chrome_time_to_dt(value):
    # Chrome stores microseconds since 1601-01-01 UTC
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


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = 0.0
    for k, v in a.items():
        dot += v * b.get(k, 0.0)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


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


def explain_doc(interest_vec, doc_vec, topn):
    if topn <= 0:
        return []
    contributions = []
    for token, weight in doc_vec.items():
        contrib = weight * interest_vec.get(token, 0.0)
        if contrib > 0:
            contributions.append((contrib, token))
    contributions.sort(reverse=True)
    return [t for _, t in contributions[:topn]]


def format_row(score, doc, why_tokens):
    last_visit = doc["last_visit"]
    last_visit_str = last_visit.astimezone().strftime("%Y-%m-%d") if last_visit else ""
    title = doc["title"].strip()
    return {
        "score": f"{score:.3f}",
        "last_visit": last_visit_str,
        "visits": str(doc["visit_count"]),
        "title": title,
        "url": doc["url"],
        "host": doc["host"],
        "why": ", ".join(why_tokens),
        "why_tokens": why_tokens,
    }


def build_cluster_summary(rows, topn):
    clusters = {}
    for r in rows:
        name = r["cluster"]
        info = clusters.setdefault(name, {"count": 0, "tokens": {}})
        info["count"] += 1
        for t in r.get("why_tokens", []):
            info["tokens"][t] = info["tokens"].get(t, 0) + 1

    summaries = {}
    for name, info in clusters.items():
        token_counts = sorted(info["tokens"].items(), key=lambda x: (-x[1], x[0]))
        top_tokens = [t for t, _ in token_counts[:topn]]
        summaries[name] = {"count": info["count"], "top_tokens": top_tokens}
    return summaries


def print_table(rows, cluster_enabled, cluster_summaries):
    headers = ["score", "last_visit", "visits", "title", "url", "why"]
    col_widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            col_widths[h] = max(col_widths[h], len(r[h]))

    def fmt_row(r):
        return "  ".join(r[h].ljust(col_widths[h]) for h in headers)

    def print_header():
        print(fmt_row({h: h for h in headers}))
        print("  ".join("-" * col_widths[h] for h in headers))

    if not cluster_enabled:
        print_header()
        for r in rows:
            print(fmt_row(r))
        return

    print_header()
    last_cluster = None
    for r in rows:
        if r["cluster"] != last_cluster:
            summary = cluster_summaries.get(r["cluster"], {})
            top = ", ".join(summary.get("top_tokens", []))
            count = summary.get("count", 0)
            suffix = f" (top: {top}, items: {count})" if top else f" (items: {count})"
            print(f"\n# {r['cluster']}{suffix}")
            last_cluster = r["cluster"]
        print(fmt_row(r))


def print_csv(rows, cluster_summaries):
    fieldnames = ["cluster", "cluster_summary", "score", "last_visit", "visits", "title", "url", "why"]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        summary = cluster_summaries.get(r["cluster"], {})
        top = ", ".join(summary.get("top_tokens", []))
        count = summary.get("count", 0)
        cluster_summary = f"top: {top}; items: {count}" if top else f"items: {count}"
        row = dict(r)
        row["cluster_summary"] = cluster_summary
        writer.writerow({k: row.get(k, "") for k in fieldnames})


def print_json(rows, cluster_enabled, cluster_summaries):
    if not cluster_enabled:
        payload = {"items": rows}
    else:
        clusters = {}
        for r in rows:
            clusters.setdefault(r["cluster"], []).append(r)
        payload = {
            "clusters": [
                {
                    "name": name,
                    "summary": cluster_summaries.get(name, {"count": len(items), "top_tokens": []}),
                    "items": items,
                }
                for name, items in clusters.items()
            ]
        }
    print(json.dumps(payload, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Recommend reading based on Chrome browsing history.")
    parser.add_argument("--history", help="Path to Chrome History SQLite file.")
    parser.add_argument("--profile", help="Chrome profile folder name (e.g., 'Default', 'Profile 1').")
    parser.add_argument("--limit", type=int, default=15, help="Number of recommendations to return.")
    parser.add_argument("--recent-days", type=int, default=14, help="Use this many days as the recent-interest window.")
    parser.add_argument("--min-visits", type=int, default=1, help="Minimum total visits for a URL to be considered.")
    parser.add_argument("--dedupe-host", action="store_true", help="Only recommend one URL per host.")
    parser.add_argument(
        "--since",
        help="Only consider history on or after this date (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--no-reading-filter",
        action="store_true",
        help="Disable default filtering of auth/social/login pages.",
    )
    parser.add_argument(
        "--exclude-hosts",
        help="Comma-separated list of hosts to exclude.",
    )
    parser.add_argument(
        "--exclude-url-pattern",
        help="Regex pattern to exclude URLs/titles.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format.",
    )
    parser.add_argument(
        "--explain-top",
        type=int,
        default=5,
        help="Number of top contributing tokens to show for each recommendation.",
    )
    parser.add_argument(
        "--no-cluster",
        action="store_true",
        help="Disable topic clusters and show a flat list.",
    )
    args = parser.parse_args()

    if args.history:
        history_path = os.path.expanduser(args.history)
    else:
        history_path = resolve_history_path(args.profile)

    rows = load_history(history_path)
    if not rows:
        print("No history rows found.")
        return 1

    docs = build_docs(rows)
    docs = [d for d in docs if d["visit_count"] >= args.min_visits]
    if args.since:
        try:
            since_local = dt.datetime.strptime(args.since, "%Y-%m-%d")
        except ValueError:
            print("Invalid --since format. Use YYYY-MM-DD.")
            return 1
        # Interpret as local date start, convert to UTC for comparison
        since_local = since_local.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)
        since_utc = since_local.astimezone(dt.timezone.utc)
        docs = [d for d in docs if d["last_visit"] and d["last_visit"] >= since_utc]

    exclude_hosts = set()
    exclude_patterns = None
    if not args.no_reading_filter:
        exclude_hosts.update(DEFAULT_EXCLUDE_HOSTS)
        exclude_patterns = DEFAULT_EXCLUDE_PATTERNS
    else:
        exclude_patterns = re.compile(r"$^")

    extra_hosts = parse_csv_list(args.exclude_hosts)
    exclude_hosts.update(h.lower() for h in extra_hosts)

    if args.exclude_url_pattern:
        try:
            user_pattern = re.compile(args.exclude_url_pattern, re.IGNORECASE)
        except re.error:
            print("Invalid --exclude-url-pattern regex.")
            return 1
        if exclude_patterns.pattern == r"$^":
            exclude_patterns = user_pattern
        else:
            exclude_patterns = re.compile(
                f"(?:{exclude_patterns.pattern})|(?:{user_pattern.pattern})",
                re.IGNORECASE,
            )

    docs = [d for d in docs if is_reading_candidate(d, exclude_hosts, exclude_patterns)]
    if not docs:
        print("No history rows after filtering.")
        return 1

    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=args.recent_days)

    recent_docs = [d for d in docs if d["last_visit"] and d["last_visit"] >= cutoff]
    older_docs = [d for d in docs if not d["last_visit"] or d["last_visit"] < cutoff]

    if not recent_docs:
        print("Not enough recent history to build an interest profile.")
        return 1

    vectors = tfidf_vectors(docs)
    doc_index = {d["id"]: i for i, d in enumerate(docs)}

    recent_vectors = [vectors[doc_index[d["id"]]] for d in recent_docs]
    interest = aggregate_vector(recent_vectors)

    scored = []
    for d in older_docs:
        vec = vectors[doc_index[d["id"]]]
        score = cosine(interest, vec)
        if score <= 0.0:
            continue
        scored.append((score, d))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    seen_hosts = set()
    for score, doc in scored:
        if args.dedupe_host and doc["host"] in seen_hosts:
            continue
        seen_hosts.add(doc["host"])
        vec = vectors[doc_index[doc["id"]]]
        why_tokens = explain_doc(interest, vec, args.explain_top)
        results.append(format_row(score, doc, why_tokens))
        if len(results) >= args.limit:
            break

    if not results:
        print("No recommendations found.")
        return 1

    cluster_enabled = not args.no_cluster
    for r in results:
        r["cluster"] = r["why_tokens"][0] if (cluster_enabled and r["why_tokens"]) else (r["host"] or "other")

    cluster_summaries = build_cluster_summary(results, topn=5) if cluster_enabled else {}

    if args.format == "table":
        print_table(results, cluster_enabled, cluster_summaries)
    elif args.format == "csv":
        print_csv(results, cluster_summaries)
    else:
        print_json(results, cluster_enabled, cluster_summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
