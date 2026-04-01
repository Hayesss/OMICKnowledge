#!/usr/bin/env python3
"""
自动抓取工具的最新版本和文档信息。
当前实现为 GitHub API 基础版，后续可扩展 Bioconductor / PyPI 支持。
"""
import os
import sys
import json
import urllib.request
import yaml

# 工具名到 GitHub owner/repo 的映射
GITHUB_REPOS = {
    'macs2': 'macs3-project/MACS',
    'bowtie2': 'BenLangmead/bowtie2',
}


def fetch_github_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        return {
            'latest_version': data.get('tag_name', 'unknown'),
            'release_url': data.get('html_url', ''),
            'published_at': data.get('published_at', ''),
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    auto_dir = os.path.join(base_dir, 'content', 'tools_auto')
    os.makedirs(auto_dir, exist_ok=True)

    for tool_id, repo in GITHUB_REPOS.items():
        print(f"Fetching {tool_id} from {repo} ...")
        info = fetch_github_latest_release(repo)
        output_path = os.path.join(auto_dir, f"{tool_id}_auto.yaml")
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                {
                    'tool_id': tool_id,
                    'github_repo': repo,
                    'fetched_at': __import__('datetime').datetime.now().isoformat(),
                    'data': info,
                },
                f,
                allow_unicode=True,
                sort_keys=False,
            )
        print(f"  Saved to {output_path}")

    print("Done.")


if __name__ == '__main__':
    main()
