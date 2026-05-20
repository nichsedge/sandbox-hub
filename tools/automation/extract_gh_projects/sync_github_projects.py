#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Sync GitHub repositories metadata into JSON/JSONL/CSV datasets.

- Uses GitHub GraphQL via `gh api graphql`.
- Exports repos for the authenticated `gh` user.
- Includes OWNER + COLLABORATOR + ORGANIZATION_MEMBER affiliations.

Outputs:
  <base_dir>/<date>/github_repos_all.json
  <base_dir>/<date>/github_repos_all.jsonl
  <base_dir>/<date>/github_repos_all.csv
  <base_dir>/latest/<same files>

Usage:
  uv run sync_github_projects.py --base-dir /home/al/Projects/.data/github-projects-dataset
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import subprocess
from typing import Any, Dict, List, Optional

QUERY = r'''
query($after:String){
  viewer {
    login
    repositories(
      first: 30,
      after: $after,
      affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER],
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id
        name
        nameWithOwner
        url
        description
        homepageUrl
        isPrivate
        isFork
        isArchived
        isTemplate
        isDisabled
        createdAt
        updatedAt
        pushedAt
        primaryLanguage { name }
        defaultBranchRef { name }
        stargazerCount
        forkCount
        watchers { totalCount }
        issues(states: OPEN) { totalCount }
        pullRequests(states: OPEN) { totalCount }
        defaultBranchRef {
          name
          target {
            __typename
            ... on Commit { oid }
          }
        }
        repositoryTopics(first: 50) {
          nodes { topic { name } }
        }
        licenseInfo { spdxId name }
        owner {
          __typename
          login
          url
        }
      }
    }
  }
}
'''


def run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def gh_graphql(after: Optional[str]) -> Dict[str, Any]:
    # `gh api graphql` supports -F for variables.
    cmd = ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"after={(after if after is not None else 'null')}"]
    p = run(cmd)
    if p.returncode != 0:
        raise SystemExit(f"gh api graphql failed (code={p.returncode})\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Failed to parse JSON from gh output: {e}\nOutput head:\n{p.stdout[:2000]}")


def iso_utc_today() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def write_json(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def flatten_repo(n: Dict[str, Any]) -> Dict[str, Any]:
    topics = []
    for t in ((n.get("repositoryTopics") or {}).get("nodes") or []):
        name = ((t or {}).get("topic") or {}).get("name")
        if name:
            topics.append(name)

    primary_language = (n.get("primaryLanguage") or {}).get("name")

    dbr = n.get("defaultBranchRef") or {}
    default_branch = dbr.get("name")
    default_branch_oid = None
    target = dbr.get("target") or {}
    if target.get("__typename") == "Commit":
        default_branch_oid = target.get("oid")

    license_info = n.get("licenseInfo") or {}

    owner = n.get("owner") or {}

    return {
        "id": n.get("id"),
        "name": n.get("name"),
        "full_name": n.get("nameWithOwner"),
        "owner_login": owner.get("login"),
        "owner_url": owner.get("url"),
        "html_url": n.get("url"),
        "homepage": n.get("homepageUrl"),
        "description": n.get("description"),
        "topics": topics,
        "language": primary_language,
        "private": n.get("isPrivate"),
        "fork": n.get("isFork"),
        "archived": n.get("isArchived"),
        "template": n.get("isTemplate"),
        "disabled": n.get("isDisabled"),
        "created_at": n.get("createdAt"),
        "updated_at": n.get("updatedAt"),
        "pushed_at": n.get("pushedAt"),
        "default_branch": default_branch,
        "default_branch_oid": default_branch_oid,
        "stargazers_count": n.get("stargazerCount"),
        "watchers_count": (n.get("watchers") or {}).get("totalCount"),
        "forks_count": n.get("forkCount"),
        "open_issues_count": (n.get("issues") or {}).get("totalCount"),
        "open_prs_count": (n.get("pullRequests") or {}).get("totalCount"),
        "license_spdx": license_info.get("spdxId"),
        "license_name": license_info.get("name"),
    }


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "name",
        "full_name",
        "owner_login",
        "html_url",
        "homepage",
        "description",
        "language",
        "private",
        "fork",
        "archived",
        "template",
        "disabled",
        "created_at",
        "updated_at",
        "pushed_at",
        "default_branch",
        "default_branch_oid",
        "stargazers_count",
        "watchers_count",
        "forks_count",
        "open_issues_count",
        "open_prs_count",
        "license_spdx",
        "topics",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            out = {k: r.get(k) for k in fieldnames}
            out["topics"] = ",".join(r.get("topics") or [])
            w.writerow(out)


def copy_latest(latest_dir: str, paths: List[str]) -> None:
    ensure_dir(latest_dir)
    for p in paths:
        base = os.path.basename(p)
        dst = os.path.join(latest_dir, base)
        with open(p, "rb") as src_f, open(dst, "wb") as dst_f:
            dst_f.write(src_f.read())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-dir", default=os.path.expanduser("~/Projects/.data/github-projects-dataset"))
    args = ap.parse_args()

    base_dir = os.path.abspath(args.base_dir)
    ensure_dir(base_dir)

    date_str = iso_utc_today()
    out_dir = os.path.join(base_dir, date_str)
    ensure_dir(out_dir)

    # Collect nodes
    all_nodes: List[Dict[str, Any]] = []
    after: Optional[str] = None

    for _ in range(200):
        data = gh_graphql(after)
        if "errors" in data:
            raise SystemExit(f"GraphQL returned errors: {json.dumps(data['errors'], indent=2)}")
        repos = data["data"]["viewer"]["repositories"]
        nodes = repos.get("nodes") or []
        all_nodes.extend(nodes)

        if not repos["pageInfo"]["hasNextPage"]:
            break
        after = repos["pageInfo"]["endCursor"]
    else:
        raise SystemExit("Pagination exceeded 200 pages; aborting")

    rows = [flatten_repo(n) for n in all_nodes]

    meta = {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "gh api graphql",
        "affiliations": ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"],
        "count": len(rows),
    }

    json_path = os.path.join(out_dir, "github_repos_all.json")
    jsonl_path = os.path.join(out_dir, "github_repos_all.jsonl")
    csv_path = os.path.join(out_dir, "github_repos_all.csv")

    write_json(json_path, {**meta, "repos": rows})
    write_jsonl(jsonl_path, rows)
    write_csv(csv_path, rows)

    copy_latest(os.path.join(base_dir, "latest"), [json_path, jsonl_path, csv_path])

    print("OK")
    print("out_dir=", out_dir)
    print("count=", len(rows))
    print("latest_dir=", os.path.join(base_dir, "latest"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
