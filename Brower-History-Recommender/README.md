# Reading Recommendation CLI (Chrome History)

This prototype reads your Chrome history database and recommends older pages based on topics you’ve read recently.

## How it works
- Builds a short-term interest profile from titles/URLs visited in the last N days.
- Scores older pages by cosine similarity to that interest profile.
- Outputs a ranked list of URLs to revisit.

## Usage

1) Find your Chrome `History` file:
- macOS: `~/Library/Application Support/Google/Chrome/Default/History`
- macOS (Chrome Beta): `~/Library/Application Support/Google/Chrome Beta/Default/History`

2) Run:

```bash
./recommend.py \
  --history "~/Library/Application Support/Google/Chrome/Default/History" \
  --recent-days 14 \
  --since 2025-01-01 \
  --limit 15 \
  --min-visits 1 \
  --dedupe-host \
  --format table
```

You can also use a profile name instead of a full path:

```bash
./recommend.py \
  --profile "Profile 1" \
  --recent-days 14 \
  --limit 15 \
  --min-visits 1 \
  --dedupe-host \
  --format table
```

## Output Formats
- `--format table` (default): human-readable table with topic clusters and “why” tokens.
- `--format json`: machine-readable clusters and items.
- `--format csv`: flat rows with a `cluster` column.

## Explanations and Clusters
- Each recommendation includes a `why` field showing the top contributing tokens.
- By default, results are grouped into topic clusters based on the strongest `why` token.
- Disable grouping with `--no-cluster`.
- Each cluster includes a small summary of top tokens and item count (table header, JSON `summary`, CSV `cluster_summary`).

## Notes
- Chrome locks the DB while running. The script copies it to a temp file before reading.
- Recommendations are based on titles, domains, and URL paths.
- Try adjusting `--recent-days` and `--min-visits` if results are sparse.
- Use `--since YYYY-MM-DD` to only consider history on or after that date.
- If `--history` is not provided, the script uses `Default` or the `--profile` folder.
- A default reading-centric filter removes common auth/social/login pages. Disable with `--no-reading-filter`.
- Add more exclusions with `--exclude-hosts` or `--exclude-url-pattern`.

## Example Output
```
score  last_visit  visits  title                                     url                                      why
-----  ----------  ------  ----------------------------------------  ---------------------------------------  ----------------------------
0.812  2024-11-21  3       How to tune Postgres indexes              https://example.com/postgres-indexes     postgres, indexes, tuning
0.761  2023-10-03  2       Batching tips for async Python             https://example.com/async-batching       async, batching, python
```

## Example JSON
```json
{
  "clusters": [
    {
      "name": "postgres",
      "items": [
        {
          "cluster": "postgres",
          "score": "0.812",
          "last_visit": "2024-11-21",
          "visits": "3",
          "title": "How to tune Postgres indexes",
          "url": "https://example.com/postgres-indexes",
          "host": "example.com",
          "why": "postgres, indexes, tuning",
          "why_tokens": ["postgres", "indexes", "tuning"]
        }
      ]
    }
  ]
}
```
