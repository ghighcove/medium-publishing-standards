#!/usr/bin/env python3
"""
Archive a published Medium article with PDF snapshot, source copy, and metadata.

Usage:
    python archive_article.py \\
        --source="<project>/article/medium_draft.md" \\
        --medium-url="https://medium.com/@user/article-slug-123" \\
        --project="project_name" \\
        --title="Article Title" \\
        --geo-score="97"
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def slugify(title: str) -> str:
    """Convert title to URL-safe slug."""
    import re
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '_', slug)
    return slug[:50]  # Limit length


def generate_pdf_from_url(url: str, output_path: Path):
    """
    Generate PDF from Medium URL.

    Requires wkhtmltopdf or similar tool installed.
    Falls back to creating a placeholder if tool not available.
    """
    try:
        # Try wkhtmltopdf first
        result = subprocess.run(
            ['wkhtmltopdf', url, str(output_path)],
            capture_output=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ PDF generated: {output_path}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: Create placeholder with instructions
    placeholder = f"""PDF Snapshot Placeholder

Article URL: {url}
Generated: {datetime.now().isoformat()}

To generate PDF manually:
1. Open article URL in browser
2. Print to PDF (Ctrl+P)
3. Save as: {output_path.name}
4. Replace this file

Or install wkhtmltopdf:
    choco install wkhtmltopdf (Windows)
    brew install wkhtmltopdf (Mac)
    apt-get install wkhtmltopdf (Linux)
"""
    output_path.write_text(placeholder, encoding='utf-8')
    print(f"⚠️  PDF placeholder created: {output_path}")
    print(f"    Install wkhtmltopdf or manually save PDF from browser")
    return False


def archive_article(
    source_path: str,
    medium_url: str,
    project: str,
    title: str,
    geo_score: str = None,
    github_pages_url: str = None
):
    """Archive published article with PDF, source, and metadata."""

    # Paths
    base_dir = Path(__file__).parent.parent
    source_path = Path(source_path)

    if not source_path.exists():
        print(f"❌ Source file not found: {source_path}")
        sys.exit(1)

    # Generate slug for directory name
    slug = slugify(title)
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Create archive directories
    pdf_path = base_dir / 'published' / 'pdfs' / f"{date_str}_{slug}.pdf"
    source_dir = base_dir / 'published' / 'source' / slug
    source_dir.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy source markdown
    shutil.copy(source_path, source_dir / 'medium_draft.md')
    print(f"✅ Source copied: {source_dir}/medium_draft.md")

    # Copy figures directory if exists
    figures_src = source_path.parent / 'figures'
    if figures_src.exists():
        figures_dest = source_dir / 'figures'
        if figures_dest.exists():
            shutil.rmtree(figures_dest)
        shutil.copytree(figures_src, figures_dest)
        print(f"✅ Figures copied: {figures_dest}")

    # Copy visualizations directory if exists
    viz_src = source_path.parent.parent / 'visualizations'
    if viz_src.exists() and viz_src.is_dir():
        viz_dest = source_dir / 'visualizations'
        if viz_dest.exists():
            shutil.rmtree(viz_dest)
        shutil.copytree(viz_src, viz_dest)
        print(f"✅ Visualizations copied: {viz_dest}")

    # Generate PDF from Medium URL
    pdf_generated = generate_pdf_from_url(medium_url, pdf_path)

    # Create metadata
    metadata = {
        'title': title,
        'project': project,
        'medium_url': medium_url,
        'github_pages_url': github_pages_url or '',
        'geo_score': geo_score or '',
        'published_date': date_str,
        'archived_date': datetime.now().isoformat(),
        'source_file': str(source_path),
        'pdf_path': str(pdf_path.relative_to(base_dir)),
        'source_dir': str(source_dir.relative_to(base_dir))
    }

    metadata_path = source_dir / 'metadata.json'
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved: {metadata_path}")

    # Update INDEX.md
    update_index(base_dir, metadata, slug)

    print("\n✅ Archive complete!")
    print(f"   PDF: {pdf_path}")
    print(f"   Source: {source_dir}")
    print(f"   Metadata: {metadata_path}")
    print(f"\nNext: Run `python tools/update_index.py` to regenerate full INDEX.md")


def update_index(base_dir: Path, metadata: dict, slug: str):
    """Update INDEX.md with new entry (prepends to top)."""

    index_path = base_dir / 'published' / 'INDEX.md'

    # Read existing index or create header
    if index_path.exists():
        existing = index_path.read_text(encoding='utf-8')
        # Find where first ## entry starts
        lines = existing.split('\n')
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith('## '):
                header_end = i
                break
        header = '\n'.join(lines[:header_end])
    else:
        header = """# Published Articles

This index is auto-generated by `tools/archive_article.py` and `tools/update_index.py`.

---

"""

    # Create new entry
    geo_badge = f" (GEO: {metadata['geo_score']}/100)" if metadata['geo_score'] else ""
    entry = f"""## {metadata['published_date']}: {metadata['title']}{geo_badge}

- **Project**: {metadata['project']}
- **Medium**: [{metadata['title']}]({metadata['medium_url']})
- **Source**: [source/{slug}/](source/{slug}/)
- **PDF Archive**: [pdfs/{Path(metadata['pdf_path']).name}](pdfs/{Path(metadata['pdf_path']).name})
{f"- **GitHub Pages**: {metadata['github_pages_url']}" if metadata['github_pages_url'] else ""}

"""

    # Prepend new entry
    if index_path.exists():
        # Insert after header
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(header + '\n' + entry + '\n'.join(lines[header_end:]))
    else:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(header + entry)

    print(f"✅ INDEX.md updated: {index_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Archive a published Medium article'
    )
    parser.add_argument('--source', required=True, help='Path to source markdown file')
    parser.add_argument('--medium-url', required=True, help='Published Medium article URL')
    parser.add_argument('--project', required=True, help='Project name (e.g., "nfl", "ratings")')
    parser.add_argument('--title', required=True, help='Article title')
    parser.add_argument('--geo-score', help='GEO score (e.g., "97")')
    parser.add_argument('--github-pages-url', help='GitHub Pages URL (optional)')

    args = parser.parse_args()

    archive_article(
        source_path=args.source,
        medium_url=args.medium_url,
        project=args.project,
        title=args.title,
        geo_score=args.geo_score,
        github_pages_url=args.github_pages_url
    )


if __name__ == '__main__':
    main()
