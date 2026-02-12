#!/usr/bin/env python3
"""
Regenerate INDEX.md from all metadata.json files in published/source/.

Usage:
    python update_index.py
"""

import json
from pathlib import Path


def update_index():
    """Scan all metadata.json files and regenerate INDEX.md."""

    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / 'published' / 'source'

    if not source_dir.exists():
        print("⚠️  No published/source/ directory found")
        return

    # Collect all metadata
    articles = []
    for metadata_path in source_dir.glob('*/metadata.json'):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            metadata['_slug'] = metadata_path.parent.name
            articles.append(metadata)

    if not articles:
        print("⚠️  No metadata.json files found in published/source/")
        return

    # Sort by published_date descending
    articles.sort(key=lambda x: x['published_date'], reverse=True)

    # Generate INDEX.md
    index_path = base_dir / 'published' / 'INDEX.md'

    header = """# Published Articles

This index is auto-generated from metadata.json files in `published/source/`.

**Total articles**: {count}

---

""".format(count=len(articles))

    entries = []
    for article in articles:
        geo_badge = f" (GEO: {article['geo_score']}/100)" if article.get('geo_score') else ""
        slug = article['_slug']

        entry = f"""## {article['published_date']}: {article['title']}{geo_badge}

- **Project**: {article['project']}
- **Medium**: [{article['title']}]({article['medium_url']})
- **Source**: [source/{slug}/](source/{slug}/)
- **PDF Archive**: [{Path(article['pdf_path']).name}]({article['pdf_path']})
{f"- **GitHub Pages**: {article['github_pages_url']}" if article.get('github_pages_url') else ""}

"""
        entries.append(entry)

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(header + '\n'.join(entries))

    print(f"✅ INDEX.md regenerated: {index_path}")
    print(f"   {len(articles)} articles indexed")


if __name__ == '__main__':
    update_index()
