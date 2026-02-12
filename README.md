# Medium Publishing Standards

**Single source of truth** for Medium article publishing across all projects.

## Purpose

This repository centralizes:
- ✅ Medium platform rules (table handling, caching, URLs, etc.)
- ✅ Export workflow and reference implementations
- ✅ Archive of all published articles (PDFs + source)
- ✅ Reviewable index of portfolio

**Why centralized?**
- Prevents rule duplication drift across projects
- Ensures all projects follow proven practices
- Creates browsable archive of published work
- Makes portfolio visible in one place

## Quick Start

### Before Publishing Any Article

1. **Read the standards**: [STANDARDS.md](STANDARDS.md)
2. **Use pre-flight checklist**: 4 mandatory steps before any Medium work
3. **Copy reference implementation**: `templates/export_for_medium.py` if starting fresh

### After Publishing an Article

Archive it for the portfolio:

```bash
python tools/archive_article.py \\
  --source="G:/ai/your-project/article/medium_draft.md" \\
  --medium-url="https://medium.com/@user/article-slug-123" \\
  --project="your_project" \\
  --title="Article Title" \\
  --geo-score="97" \\
  --github-pages-url="https://user.github.io/repo/article/file.html"
```

This creates:
- PDF snapshot in `published/pdfs/`
- Source copy in `published/source/{slug}/`
- Metadata in `published/source/{slug}/metadata.json`
- Updates `published/INDEX.md`

## Repository Structure

```
medium-publishing-standards/
├── STANDARDS.md              # The canonical Medium rules (read this first!)
├── README.md                 # This file
├── templates/
│   ├── export_for_medium.py  # Reference implementation for export script
│   └── (future: render_table_as_png.py, etc.)
├── published/
│   ├── INDEX.md             # Human-readable list of all published articles
│   ├── pdfs/                # PDF snapshots (archival)
│   │   ├── 2026-02-12_rating_inflation.pdf
│   │   └── ...
│   └── source/              # Original markdown + figures
│       ├── rating_inflation/
│       │   ├── medium_draft.md
│       │   ├── figures/
│       │   └── metadata.json
│       └── ...
└── tools/
    ├── archive_article.py   # Archive a published article
    └── update_index.py      # Regenerate INDEX.md from all metadata