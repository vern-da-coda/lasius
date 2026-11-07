#!/usr/bin/env python3
"""
Internal Markdown & Documentation Link Integrity Validator.

Scans all Markdown documentation files throughout the Hexapod:Lasius
repository and verifies that all relative hyperlinks and targets resolve
to existing files. Returns exit code 1 if any broken links are discovered.
"""

import os
import re
import sys
from pathlib import Path

# Find project root (2 levels up from scripts/dev/)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "dist",
}

LINK_REGEX = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')


def get_all_markdown_files(root: Path):
    md_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for f in filenames:
            if f.endswith(".md"):
                md_files.append(Path(dirpath) / f)
    return sorted(md_files)


def validate_links():
    md_files = get_all_markdown_files(ROOT_DIR)
    print(f"🔍 Validating links across {len(md_files)} Markdown files...\n")

    broken_count = 0
    total_links = 0

    for md_path in md_files:
        rel_path = md_path.relative_to(ROOT_DIR)
        parent_dir = md_path.parent

        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"❌ Error reading {rel_path}: {e}")
            broken_count += 1
            continue

        links = LINK_REGEX.findall(content)
        file_broken = 0

        for text, target in links:
            target = target.strip()
            # Ignore web links, anchors, and mailto
            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("mailto:")
                or target.startswith("#")
            ):
                continue

            total_links += 1
            # Strip target anchors like file.md#section
            clean_target = target.split("#")[0]
            if not clean_target:
                continue

            resolved = (parent_dir / clean_target).resolve()
            if not resolved.exists():
                if file_broken == 0:
                    print(f"📄 In {rel_path}:")
                print(f"   ❌ Broken link: [{text}]({target})")
                print(f"      Resolved to: {resolved}")
                file_broken += 1
                broken_count += 1

    print("\n" + "=" * 60)
    print(f"📊 Link Validation Summary:")
    print(f"   Checked Files: {len(md_files)}")
    print(f"   Checked Links: {total_links}")
    print(f"   Broken Links:  {broken_count}")
    print("=" * 60)

    if broken_count > 0:
        print(f"\n❌ FAILED: {broken_count} broken links detected!")
        sys.exit(1)
    else:
        print("\n✅ SUCCESS: All documentation links are valid!")
        sys.exit(0)


if __name__ == "__main__":
    validate_links()
