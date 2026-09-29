import csv, glob, json

SNAPSHOT = "2026-09-28"
FIELDS = ["repo_id", "full_name", "owner_type", "language", "created_at", "pushed_at",
          "updated_at", "stars", "forks", "open_issues", "size_kb", "license", "topics",
          "topic_count", "description", "has_homepage", "has_wiki", "has_pages",
          "has_discussions", "archived", "snapshot_date"]

rows = []
for path in sorted(glob.glob("raw/*.json")):
    for it in json.load(open(path)).get("items", []):
        lic = it.get("license") or {}
        topics = it.get("topics") or []
        rows.append({
            "repo_id": it["id"],
            "full_name": it["full_name"],
            "owner_type": it["owner"]["type"],
            "language": it.get("language"),
            "created_at": it["created_at"],
            "pushed_at": it["pushed_at"],
            "updated_at": it["updated_at"],
            "stars": it["stargazers_count"],
            "forks": it["forks_count"],
            "open_issues": it["open_issues_count"],
            "size_kb": it["size"],
            "license": lic.get("spdx_id"),
            "topics": ";".join(topics),
            "topic_count": len(topics),
            "description": (it.get("description") or "").replace("\r", " ").replace("\n", " ").strip() or None,
            "has_homepage": bool(it.get("homepage")),
            "has_wiki": it.get("has_wiki"),
            "has_pages": it.get("has_pages"),
            "has_discussions": it.get("has_discussions"),
            "archived": it.get("archived"),
            "snapshot_date": SNAPSHOT,
        })

with open("github_repos_2019_2025.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print(len(rows), "rows")
