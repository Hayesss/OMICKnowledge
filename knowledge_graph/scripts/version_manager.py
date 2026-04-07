#!/usr/bin/env python3
"""
Version manager for knowledge graph.
Handles versioning, tagging, and release notes.
"""

import os
import re
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List


class VersionManager:
    """Manage knowledge graph versions."""
    
    VERSION_FILE = Path(__file__).parent.parent / "VERSION"
    CHANGELOG_FILE = Path(__file__).parent.parent / "CHANGELOG.md"
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
    
    def get_current_version(self) -> str:
        """Get current version from VERSION file or git tags."""
        # Try VERSION file first
        if self.VERSION_FILE.exists():
            return self.VERSION_FILE.read_text().strip()
        
        # Try git tags
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
        except:
            pass
        
        return "0.1.0"
    
    def bump_version(self, bump_type: str = "patch") -> str:
        """Bump version number."""
        current = self.get_current_version()
        
        # Parse version
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', current)
        if not match:
            return "0.1.0"
        
        major, minor, patch = map(int, match.groups())
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        
        # Write VERSION file
        self.VERSION_FILE.write_text(new_version)
        
        return new_version
    
    def generate_changelog(self, since_tag: Optional[str] = None) -> str:
        """Generate changelog since last tag."""
        if not since_tag:
            since_tag = self._get_last_tag()
        
        # Get commits
        cmd = ["git", "log", "--pretty=format:%s|%h|%an|%ad", "--date=short"]
        if since_tag:
            cmd.append(f"{since_tag}..HEAD")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        if result.returncode != 0:
            return ""
        
        commits = result.stdout.strip().split('\n')
        
        # Categorize commits
        categories = {
            "content": [],
            "feature": [],
            "fix": [],
            "docs": [],
            "chore": [],
            "other": []
        }
        
        for commit in commits:
            if '|' not in commit:
                continue
            
            message, hash_, author, date = commit.split('|')
            
            if message.startswith("content:"):
                categories["content"].append((message, hash_, date))
            elif message.startswith("feat:"):
                categories["feature"].append((message, hash_, date))
            elif message.startswith("fix:"):
                categories["fix"].append((message, hash_, date))
            elif message.startswith("docs:"):
                categories["docs"].append((message, hash_, date))
            elif message.startswith("chore:"):
                categories["chore"].append((message, hash_, date))
            else:
                categories["other"].append((message, hash_, date))
        
        # Generate markdown
        lines = []
        lines.append(f"## Changelog - {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")
        
        if categories["content"]:
            lines.append("### 📚 Content Updates")
            for msg, hash_, date in categories["content"]:
                clean_msg = msg.replace("content:", "").strip()
                lines.append(f"- {clean_msg} ({hash_}, {date})")
            lines.append("")
        
        if categories["feature"]:
            lines.append("### ✨ New Features")
            for msg, hash_, date in categories["feature"]:
                clean_msg = msg.replace("feat:", "").strip()
                lines.append(f"- {clean_msg} ({hash_}, {date})")
            lines.append("")
        
        if categories["fix"]:
            lines.append("### 🐛 Bug Fixes")
            for msg, hash_, date in categories["fix"]:
                clean_msg = msg.replace("fix:", "").strip()
                lines.append(f"- {clean_msg} ({hash_}, {date})")
            lines.append("")
        
        if categories["docs"]:
            lines.append("### 📝 Documentation")
            for msg, hash_, date in categories["docs"]:
                clean_msg = msg.replace("docs:", "").strip()
                lines.append(f"- {clean_msg} ({hash_}, {date})")
            lines.append("")
        
        # Add stats
        lines.append("### 📊 Statistics")
        
        # Count content files
        content_count = len(list((self.project_root / "content").rglob("*.yaml")))
        lines.append(f"- Total entities: {content_count}")
        
        # Count edges
        edges_file = self.project_root / "edges" / "edges.yaml"
        if edges_file.exists():
            import yaml
            edges_data = yaml.safe_load(edges_file.read_text())
            if edges_data:
                lines.append(f"- Total relations: {len(edges_data.get('edges', []))}")
        
        lines.append("")
        
        return '\n'.join(lines)
    
    def create_release(self, version: str, changelog: str) -> None:
        """Create a new release."""
        # Create git tag
        tag_name = f"v{version}"
        
        subprocess.run(
            ["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"],
            cwd=self.project_root
        )
        
        print(f"🏷️  Created tag: {tag_name}")
        
        # Update CHANGELOG.md
        if self.CHANGELOG_FILE.exists():
            old_changelog = self.CHANGELOG_FILE.read_text()
            new_changelog = f"# Release {version}\n\n{changelog}\n---\n\n{old_changelog}"
        else:
            new_changelog = f"# Release {version}\n\n{changelog}"
        
        self.CHANGELOG_FILE.write_text(new_changelog)
        print(f"📝 Updated CHANGELOG.md")
    
    def _get_last_tag(self) -> Optional[str]:
        """Get last git tag."""
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    
    def get_content_diff(self) -> dict:
        """Get diff statistics for content."""
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD~1", "--", "content/"],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        
        added = 0
        modified = 0
        deleted = 0
        
        for line in result.stdout.split('\n'):
            if '|' in line and '.yaml' in line:
                if 'Bin' in line:  # Binary or new file
                    added += 1
                elif 'delete' in line.lower():
                    deleted += 1
                else:
                    modified += 1
        
        return {
            "added": added,
            "modified": modified,
            "deleted": deleted
        }


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Knowledge Graph Version Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Version command
    subparsers.add_parser('version', help='Show current version')
    
    # Bump command
    bump_parser = subparsers.add_parser('bump', help='Bump version')
    bump_parser.add_argument('type', choices=['major', 'minor', 'patch'], 
                            default='patch', nargs='?',
                            help='Version bump type')
    
    # Changelog command
    subparsers.add_parser('changelog', help='Generate changelog')
    
    # Release command
    release_parser = subparsers.add_parser('release', help='Create release')
    release_parser.add_argument('--version', help='Version number (auto if not specified)')
    release_parser.add_argument('--type', choices=['major', 'minor', 'patch'],
                               default='patch', help='Bump type')
    
    # Stats command
    subparsers.add_parser('stats', help='Show content statistics')
    
    args = parser.parse_args()
    
    manager = VersionManager()
    
    if args.command == 'version' or not args.command:
        print(f"Current version: {manager.get_current_version()}")
    
    elif args.command == 'bump':
        new_version = manager.bump_version(args.type)
        print(f"Version bumped: {manager.get_current_version()} -> {new_version}")
    
    elif args.command == 'changelog':
        changelog = manager.generate_changelog()
        print(changelog)
    
    elif args.command == 'release':
        if args.version:
            version = args.version
        else:
            version = manager.bump_version(args.type)
        
        changelog = manager.generate_changelog()
        manager.create_release(version, changelog)
        print(f"🎉 Released version {version}")
    
    elif args.command == 'stats':
        diff = manager.get_content_diff()
        print(f"Content changes since last commit:")
        print(f"  Added: {diff['added']}")
        print(f"  Modified: {diff['modified']}")
        print(f"  Deleted: {diff['deleted']}")


if __name__ == '__main__':
    main()
