#!/usr/bin/env python3
"""
Medium Article Tracker - Cross-project visibility into published and pending articles.

Scans:
- Published: <this-repo>/published/source/*/metadata.json
- Pending: <projects-root>/**/MEDIUM_PUBLISH_INFO_*.md

Usage:
    python medium_tracker.py --list                    # All articles
    python medium_tracker.py --list --status published  # Published only
    python medium_tracker.py --list --project nfl       # Filter by project
    python medium_tracker.py --html                     # Generate dashboard
    python medium_tracker.py --json                     # JSON export
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    try:
        print("⚠️  Install 'rich' for better CLI formatting: pip install rich")
    except UnicodeEncodeError:
        print("[WARNING] Install 'rich' for better CLI formatting: pip install rich")


@dataclass
class Article:
    """Article metadata."""
    title: str
    project: str
    status: str  # 'published' or 'pending'
    medium_url: Optional[str] = None
    github_pages_url: Optional[str] = None
    published_date: Optional[str] = None
    geo_score: Optional[int] = None
    source_path: Optional[str] = None
    metadata_path: Optional[str] = None


def scan_published_articles() -> List[Article]:
    """Scan published/source/*/metadata.json for published articles."""
    articles = []
    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / 'published' / 'source'

    if not source_dir.exists():
        return articles

    for metadata_file in source_dir.glob('*/metadata.json'):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Parse GEO score (handle both string and int)
            geo_score = None
            if data.get('geo_score'):
                try:
                    geo_score = int(str(data['geo_score']).split('/')[0])
                except (ValueError, IndexError):
                    pass

            articles.append(Article(
                title=data.get('title', 'Unknown'),
                project=data.get('project', 'Unknown'),
                status='published',
                medium_url=data.get('medium_url'),
                github_pages_url=data.get('github_pages_url'),
                published_date=data.get('published_date'),
                geo_score=geo_score,
                source_path=data.get('source_file'),
                metadata_path=str(metadata_file)
            ))
        except (json.JSONDecodeError, KeyError) as e:
            try:
                print(f"⚠️  Skipping invalid metadata: {metadata_file} ({e})", file=sys.stderr)
            except UnicodeEncodeError:
                print(f"[WARNING] Skipping invalid metadata: {metadata_file} ({e})", file=sys.stderr)

    return articles


def scan_pending_articles(projects_root: Optional[str] = None) -> List[Article]:
    """Scan for MEDIUM_PUBLISH_INFO_*.md pending articles across projects.

    Args:
        projects_root: Root directory to scan. Defaults to parent of this repo.
    """
    articles = []
    base_dir = Path(projects_root) if projects_root else Path(__file__).parent.parent.parent

    if not base_dir.exists():
        return articles

    for info_file in base_dir.glob('**/MEDIUM_PUBLISH_INFO_*.md'):
        # Skip template file
        if 'template' in info_file.name.lower():
            continue

        try:
            content = info_file.read_text(encoding='utf-8')

            # Extract title from first heading
            title_match = re.search(r'^#\s+Medium Publishing Info:\s*(.+?)$', content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else 'Unknown'

            # Extract project from path (parent directory name)
            project = info_file.parent.parent.name

            # Extract GEO score
            geo_match = re.search(r'\*\*GEO Score:\*\*\s*(\d+)', content)
            geo_score = int(geo_match.group(1)) if geo_match else None

            # Extract GitHub Pages URL
            github_url_match = re.search(
                r'https://ghighcove\.github\.io/[^\s\)]+',
                content
            )
            github_pages_url = github_url_match.group(0) if github_url_match else None

            # Extract article filename
            article_match = re.search(r'\*\*Article:\*\*\s*(.+?)$', content, re.MULTILINE)
            article_filename = article_match.group(1).strip() if article_match else None

            # Construct source path
            source_path = None
            if article_filename:
                source_path = str(info_file.parent / article_filename)

            articles.append(Article(
                title=title,
                project=project,
                status='pending',
                github_pages_url=github_pages_url,
                geo_score=geo_score,
                source_path=source_path,
                metadata_path=str(info_file)
            ))
        except Exception as e:
            try:
                print(f"⚠️  Skipping invalid info file: {info_file} ({e})", file=sys.stderr)
            except UnicodeEncodeError:
                print(f"[WARNING] Skipping invalid info file: {info_file} ({e})", file=sys.stderr)

    return articles


def get_all_articles(status_filter: Optional[str] = None, project_filter: Optional[str] = None) -> List[Article]:
    """Get all articles with optional filters."""
    published = scan_published_articles()
    pending = scan_pending_articles()
    all_articles = published + pending

    # Apply filters
    if status_filter:
        all_articles = [a for a in all_articles if a.status == status_filter]

    if project_filter:
        all_articles = [a for a in all_articles if a.project.lower() == project_filter.lower()]

    # Sort by date (published first, then pending, then by date desc)
    def sort_key(article):
        status_order = {'published': 0, 'pending': 1}
        date_str = article.published_date or '9999-99-99'
        return (status_order.get(article.status, 2), date_str)

    all_articles.sort(key=sort_key, reverse=True)

    return all_articles


def print_table(articles: List[Article]):
    """Print articles as a formatted table."""
    if not articles:
        print("No articles found.")
        return

    if RICH_AVAILABLE:
        console = Console()
        table = Table(title="Medium Articles", show_header=True, header_style="bold magenta")

        table.add_column("Status", style="cyan", width=10)
        table.add_column("Project", style="green", width=15)
        table.add_column("Title", style="white", width=40)
        table.add_column("GEO", justify="right", width=5)
        table.add_column("Date", width=12)

        for article in articles:
            status_color = "green" if article.status == 'published' else "yellow"
            table.add_row(
                f"[{status_color}]{article.status}[/{status_color}]",
                article.project,
                article.title[:40],
                str(article.geo_score) if article.geo_score else "—",
                article.published_date or "—"
            )

        console.print(table)
    else:
        # Fallback to simple table
        print(f"{'Status':<12} {'Project':<15} {'Title':<40} {'GEO':<5} {'Date':<12}")
        print("-" * 90)
        for article in articles:
            print(f"{article.status:<12} {article.project:<15} {article.title[:40]:<40} "
                  f"{str(article.geo_score) if article.geo_score else '—':<5} "
                  f"{article.published_date or '—':<12}")

    # Print summary
    published_count = sum(1 for a in articles if a.status == 'published')
    pending_count = sum(1 for a in articles if a.status == 'pending')
    avg_geo = sum(a.geo_score for a in articles if a.geo_score) / len([a for a in articles if a.geo_score]) if any(a.geo_score for a in articles) else 0

    print(f"\nSummary: {len(articles)} total | {published_count} published | {pending_count} pending | Avg GEO: {avg_geo:.1f}")


def export_json(articles: List[Article], output_path: Optional[str] = None):
    """Export articles to JSON."""
    data = {
        'generated': datetime.now().isoformat(),
        'total': len(articles),
        'published': sum(1 for a in articles if a.status == 'published'),
        'pending': sum(1 for a in articles if a.status == 'pending'),
        'articles': [asdict(a) for a in articles]
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        try:
            print(f"✅ JSON exported to: {output_path}")
        except UnicodeEncodeError:
            print(f"[OK] JSON exported to: {output_path}")
    else:
        print(json.dumps(data, indent=2))


def generate_html_dashboard(articles: List[Article], output_path: Optional[str] = None):
    """Generate HTML dashboard."""
    template_path = Path(__file__).parent.parent / 'templates' / 'dashboard_template.html'

    if not template_path.exists():
        try:
            print(f"❌ Template not found: {template_path}")
        except UnicodeEncodeError:
            print(f"[ERROR] Template not found: {template_path}")
        print("   Run this script with --html after creating templates/dashboard_template.html")
        return

    template = template_path.read_text(encoding='utf-8')

    # Calculate summary stats
    published_count = sum(1 for a in articles if a.status == 'published')
    pending_count = sum(1 for a in articles if a.status == 'pending')
    avg_geo = sum(a.geo_score for a in articles if a.geo_score) / len([a for a in articles if a.geo_score]) if any(a.geo_score for a in articles) else 0

    # Generate table rows
    rows_html = []
    for article in articles:
        status_class = 'status-published' if article.status == 'published' else 'status-pending'
        medium_link = f'<a href="{article.medium_url}" target="_blank">View</a>' if article.medium_url else '—'
        github_link = f'<a href="{article.github_pages_url}" target="_blank">View</a>' if article.github_pages_url else '—'

        rows_html.append(f'''
            <tr class="{status_class}">
                <td data-status="{article.status}">{article.status}</td>
                <td data-project="{article.project}">{article.project}</td>
                <td data-title="{article.title}">{article.title}</td>
                <td data-geo="{article.geo_score or 0}">{article.geo_score or '—'}</td>
                <td data-date="{article.published_date or ''}">{article.published_date or '—'}</td>
                <td>{medium_link}</td>
                <td>{github_link}</td>
            </tr>
        ''')

    # Replace placeholders
    html = template.replace('{{TOTAL_COUNT}}', str(len(articles)))
    html = html.replace('{{PUBLISHED_COUNT}}', str(published_count))
    html = html.replace('{{PENDING_COUNT}}', str(pending_count))
    html = html.replace('{{AVG_GEO}}', f"{avg_geo:.1f}")
    html = html.replace('{{TABLE_ROWS}}', '\n'.join(rows_html))
    html = html.replace('{{GENERATED_DATE}}', datetime.now().strftime('%Y-%m-%d %H:%M'))

    # Write output
    if output_path is None:
        output_path = Path(__file__).parent.parent / 'published' / 'index.html'

    Path(output_path).write_text(html, encoding='utf-8')
    try:
        print(f"✅ HTML dashboard generated: {output_path}")
    except UnicodeEncodeError:
        print(f"[OK] HTML dashboard generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Medium Article Tracker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--list', action='store_true', help='List all articles')
    parser.add_argument('--status', choices=['published', 'pending'], help='Filter by status')
    parser.add_argument('--project', help='Filter by project name')
    parser.add_argument('--html', action='store_true', help='Generate HTML dashboard')
    parser.add_argument('--json', nargs='?', const=True, help='Export JSON (optional output path)')

    args = parser.parse_args()

    # Default to --list if no action specified
    if not any([args.list, args.html, args.json]):
        args.list = True

    # Get articles
    articles = get_all_articles(status_filter=args.status, project_filter=args.project)

    # Execute actions
    if args.list:
        print_table(articles)

    if args.html:
        generate_html_dashboard(articles)

    if args.json:
        output_path = args.json if isinstance(args.json, str) else None
        export_json(articles, output_path)


if __name__ == '__main__':
    main()
