#!/usr/bin/env python3
"""
自动抓取工具的最新版本和文档信息。
当前实现为 GitHub API 基础版，后续可扩展 Bioconductor / PyPI 支持。
"""
import os
import sys
import json
import urllib.request
from datetime import datetime
import yaml

# 工具名到 GitHub owner/repo 的映射
GITHUB_REPOS = {
    'macs2': 'macs3-project/MACS',
    'bowtie2': 'BenLangmead/bowtie2',
}


def fetch_github_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'multiomics-kg-fetcher/1.0',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return {
            'latest_version': data.get('tag_name', 'unknown'),
            'release_url': data.get('html_url', ''),
            'published_at': data.get('published_at', ''),
        }
    except urllib.error.HTTPError as e:
        print(f"Warning: HTTP {e.code} {e.reason} for {repo}", file=sys.stderr)
        return {'error': f"HTTP {e.code} {e.reason}"}
    except Exception as e:
        print(f"Warning: {e} for {repo}", file=sys.stderr)
        return {'error': str(e)}


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auto_dir = os.path.join(base_dir, 'content', 'tools_auto')
    os.makedirs(auto_dir, exist_ok=True)

    failures = 0
    for tool_id, repo in GITHUB_REPOS.items():
        print(f"Fetching {tool_id} from {repo} ...")
        info = fetch_github_latest_release(repo)
        if 'error' in info:
            failures += 1
        output_path = os.path.join(auto_dir, f"{tool_id}_auto.yaml")
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                {
                    'tool_id': tool_id,
                    'github_repo': repo,
                    'fetched_at': datetime.now().isoformat(),
                    'data': info,
                },
                f,
                allow_unicode=True,
                sort_keys=False,
            )
        print(f"  Saved to {output_path}")

    if failures:
        print(f"{failures} fetch(es) failed.", file=sys.stderr)
        sys.exit(1)

    print("Done.")


if __name__ == '__main__':
    main()
