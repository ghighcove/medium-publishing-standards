#!/usr/bin/env python3
"""
Regenerate INDEX.md and index.html from all metadata.json files in published/source/.

Usage:
    python update_index.py
"""

import json
import sys
from pathlib import Path

# Import HTML dashboard generator
try:
    from medium_tracker import generate_html_dashboard, Article
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    print("⚠️  medium_tracker.py not found - HTML dashboard will not be generated")


def update_index():
    """Scan all metadata.json files and regenerate INDEX.md and index.html."""

    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / 'published' / 'source'

    if not source_dir.exists():
        print("⚠️  No published/source/ directory found")
        return

    # Collect all metadata
    articles_metadata = []
    for metadata_path in source_dir.glob('*/metadata.json'):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            metadata['_slug'] = metadata_path.parent.name
            articles_metadata.append(metadata)

    if not articles_metadata:
        print("⚠️  No metadata.json files found in published/source/")
        return

    # Sort by published_date descending
    articles_metadata.sort(key=lambda x: x['published_date'], reverse=True)

    # Generate INDEX.md
    index_path = base_dir / 'published' / 'INDEX.md'

    header = """# Published Articles

This index is auto-generated from metadata.json files in `published/source/`.

**Total articles**: {count}

---

""".format(count=len(articles))

    entries = []
    for article in articles_metadata:
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
    print(f"   {len(articles_metadata)} articles indexed")

    # Generate HTML dashboard
    if HTML_AVAILABLE:
        # Convert metadata to Article objects for HTML generation
        article_objects = []
        for metadata in articles_metadata:
            # Parse GEO score
            geo_score = None
            if metadata.get('geo_score'):
                try:
                    geo_score = int(str(metadata['geo_score']).split('/')[0])
                except (ValueError, IndexError):
                    pass

            article_objects.append(Article(
                title=metadata.get('title', 'Unknown'),
                project=metadata.get('project', 'Unknown'),
                status='published',
                medium_url=metadata.get('medium_url'),
                github_pages_url=metadata.get('github_pages_url'),
                published_date=metadata.get('published_date'),
                geo_score=geo_score,
                source_path=metadata.get('source_file'),
                metadata_path=str(source_dir / metadata['_slug'] / 'metadata.json')
            ))

        html_output_path = base_dir / 'published' / 'index.html'
        generate_html_dashboard(article_objects, output_path=html_output_path)
    else:
        print("⚠️  Skipping HTML dashboard generation (medium_tracker.py not available)")


if __name__ == '__main__':
    update_index()
