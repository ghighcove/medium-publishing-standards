# Medium Publishing Standards

**Version**: 1.0
**Last Updated**: 2026-02-12

This document is the **single source of truth** for all Medium article publishing across all projects. All project-level CLAUDE.md files should reference this document, not duplicate these rules.

---

## Pre-Flight Checklist (MANDATORY)

Before any Medium publishing work, complete these 4 steps:

1. ✅ **Read this document** (G:\ai\medium-publishing-standards\STANDARDS.md)
2. ✅ **Check project lessons**: Read your project's `tasks/lessons.md` for publishing-related entries
3. ✅ **Verify requirements**: Tables are PNG images (not HTML), images use GitHub Pages URLs, filenames are unique/timestamped
4. ✅ **Use reference implementation**: Copy `templates/export_for_medium.py` if starting fresh

---

## Critical Platform Rules

### Table Handling (CRITICAL)

**Medium does NOT render HTML `<table>` tags properly.** Columns run together, formatting breaks.

**✅ Correct approach**: Render tables as PNG images using matplotlib
- Use `matplotlib.pyplot.table()` to generate styled table
- Save to `figures/table_*.png` in your project
- Reference in markdown: `![Table description](../figures/table_name.png)`
- Export script will convert to GitHub Pages absolute URL

**❌ Wrong approach**: HTML `<table>` tags (even valid HTML5)
- These will import to Medium but render as garbled text
- Do not rely on markdown library's table conversion for final output

**When to render tables as PNG**:
- Always, for any table going to Medium
- Before running your export script (replace markdown table syntax with image reference)

**Example workflow**:
```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 3))
ax.axis('off')

data = [['Row 1', 'Value 1'], ['Row 2', 'Value 2']]
columns = ['Header 1', 'Header 2']

table = ax.table(cellText=data, colLabels=columns, loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)

plt.savefig('figures/table_name.png', dpi=200, bbox_inches='tight')
```

Then in markdown:
```markdown
![Table showing analysis results with 2 rows and 2 columns](../figures/table_name.png)
```

### Image URLs

**✅ Use GitHub Pages URLs**: `https://<username>.github.io/<repo>/figures/image.png`
- These serve with `content-type: image/png`
- Medium accepts them for article import
- Medium accepts them for images within articles

**❌ Never use raw.githubusercontent.com for article import URLs**:
- Format: `https://raw.githubusercontent.com/<user>/<repo>/master/article/file.html`
- These serve with `content-type: text/plain`
- Medium **rejects** them for article import (returns "Import failed" error)
- However, raw.githubusercontent.com **works fine** for images within article content

**Summary**:
- Article import URL: GitHub Pages only
- Images in article: GitHub Pages preferred, raw.githubusercontent.com works

### Filename Caching (CRITICAL)

**Medium caches imported articles aggressively by URL path.** Updating file content does NOT bust the cache — Medium serves old cached version even after you push new content.

**✅ Solution**: Always use unique timestamped filenames

**Required format**: `{article_name}_{YYYYMMDD}_{HHMM}_{hash}.html`

**Example**: `rating_inflation_20260212_1130_991e9cf8.html`
- Date: 2026-02-12
- Time: 11:30
- Hash: MD5 of content (first 8 chars)

**Why this works**:
- Every export gets a completely new URL
- Medium has never seen this URL before → no cache hit
- Enables immediate re-imports after fixes

**Reference implementation**: See `templates/export_for_medium.py` → `generate_unique_filename()`

### Document Structure

Medium requires full HTML5 document structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Article Title</title>
</head>
<body>
<!-- Your article content here -->
</body>
</html>
```

**Do NOT** just export the `<body>` content — include DOCTYPE, html, head, charset meta tag.

### Markdown to HTML Conversion

**✅ Use Python `markdown` library** (v3.4.3+):
```python
import markdown

html_body = markdown.markdown(
    markdown_text,
    extensions=['tables', 'fenced_code'],
    output_format='html5'
)
```

**Benefits**:
- Handles lists correctly (`<ul>`, `<li>`)
- Handles headings, links, bold, italic correctly
- Handles fenced code blocks
- Handles markdown table syntax (but remember: convert tables to PNG images before this step)

**❌ Do NOT use regex-based conversion**:
- Misses edge cases (nested lists, complex formatting)
- Harder to maintain
- Prone to breaking on special characters

**Note**: Even though `markdown` library handles table syntax, you should **intercept tables before conversion** and replace with image references in the markdown source. This way the library converts the image reference, not the table itself.

### Image Wrapping

Wrap all images in `<p>` tags (Medium requirement):

```html
<p><img src="https://username.github.io/repo/figures/chart.png" alt="Chart description"></p>
```

The `markdown` library does this automatically for standalone images. If you insert images via HTML (e.g., for tables), make sure they're wrapped.

---

## Export Workflow (Step-by-Step)

### 1. Prepare Article Content

- Write article in markdown (`article/medium_draft.md`)
- Generate all visualizations (charts, figures) as PNG files
- **If article has tables**: Render them as PNG images, replace markdown table syntax with image references

### 2. Run Export Script

```bash
python scripts/export_for_medium.py article/medium_draft.md
```

This should:
- Read markdown source
- Convert image paths from relative (`../figures/chart.png`) to GitHub Pages absolute URLs
- Use `markdown` library to convert markdown → HTML
- Wrap HTML body in full document structure (DOCTYPE, html, head, body)
- Generate unique timestamped filename
- Save to `article/{unique_filename}.html`
- Output GitHub Pages URL for Medium import

**Reference implementation**: `G:\ai\medium-publishing-standards\templates\export_for_medium.py`

### 3. Commit and Push to GitHub

```bash
git add article/{unique_filename}.html figures/ scripts/
git commit -m "Add Medium export: {article_name}"
git push origin main
```

**Verify GitHub Pages enabled**:
- Go to repo Settings → Pages
- Source: Deploy from branch `main` (or `master`), root `/`
- Custom domain: optional

### 4. Wait for GitHub Pages Rebuild

GitHub Pages typically rebuilds in **30-60 seconds** after push.

**Verify deployment**:
```bash
curl -I https://<username>.github.io/<repo>/article/{unique_filename}.html
# Should return: HTTP/2 200
```

### 5. Import to Medium

**Manual method** (always works):
1. Navigate to: `https://medium.com/p/import`
2. Paste GitHub Pages URL
3. Click "Import"
4. Wait for import to complete
5. Add tags (5 max)
6. Set publication schedule (if desired)
7. Add SEO description in Settings → More settings → SEO description

**Browser automation method** (optional):
- Use `claude-in-chrome` MCP server
- Navigate to `https://medium.com/p/import`
- Automate: URL input, Import click, tag addition
- Manual: Schedule date (date picker automation unreliable), SEO description

### 6. Archive Published Article

After article is live on Medium:

```bash
python G:/ai/medium-publishing-standards/tools/archive_article.py \
  --source="<project>/article/medium_draft.md" \
  --medium-url="https://medium.com/@username/article-slug-12345" \
  --project="<project_name>" \
  --title="Article Title" \
  --geo-score="97"
```

This creates:
- PDF snapshot in `published/pdfs/`
- Source copy in `published/source/{article_slug}/`
- Metadata entry in `published/source/{article_slug}/metadata.json`
- Updates `published/INDEX.md`

---

## Troubleshooting

### Import fails with "Import failed" error

**Most likely**: Using raw.githubusercontent.com URL for article import
- **Fix**: Use GitHub Pages URL instead
- **Verify**: GitHub Pages enabled, file deployed, `curl -I` returns 200

### Article imported but tables are garbled

**Root cause**: HTML `<table>` tags in source
- **Fix**: Render tables as PNG images, replace table syntax with image references
- **Verify**: Open exported HTML in browser, confirm tables are `<img>` tags not `<table>`

### Article imported but images don't load

**Most likely**: Image URLs are relative paths or incorrect absolute URLs
- **Fix**: Verify all image URLs are GitHub Pages absolute URLs
- **Test**: Open each image URL in browser, should load PNG directly
- **Check**: Export script converted relative paths (`../figures/`) to absolute

### Medium shows old version after re-import

**Root cause**: Medium's aggressive URL caching
- **Fix**: Generate new unique filename with current timestamp
- **Verify**: New filename is actually different from previous (date/time/hash all changed)
- **Never**: Reuse a filename after updating content

### Lists or bullets not rendering

**Most likely**: Regex-based markdown conversion or malformed HTML
- **Fix**: Use Python `markdown` library with `extensions=['tables', 'fenced_code']`
- **Verify**: Open exported HTML in browser, inspect source for `<ul>` and `<li>` tags

---

## Quality Standards

### GEO Score Requirement

All published articles should achieve **GEO score ≥ 95/100** before publication.

Run GEO audit:
```bash
/seo-for-llms article/medium_draft.md
```

Apply HIGH and MEDIUM priority recommendations before publishing.

### Attribution Requirement

All research articles must include attribution preface (per global CLAUDE.md):

```markdown
*This article's content and analytical perspective were crafted by [model name]. The project genesis and direction came from Glenn Highcove. For more information and feedback, connect with Glenn on [LinkedIn](https://www.linkedin.com/in/glennhighcove/).*
```

Place between subtitle and first `---` separator.

Insert actual current model name dynamically (e.g., "Claude Opus 4.6", "Claude Sonnet 4.5").

---

## Testing Protocol

### Before Declaring "Fixed" or "Done"

**MANDATORY**: Verify feature works in actual Medium editor, not just deployed to GitHub.

**"Done" means**:
1. ✅ File deployed to GitHub Pages (HTTP 200)
2. ✅ Import to Medium succeeds (no "Import failed" error)
3. ✅ Article appears in Medium editor with correct formatting
4. ✅ Tables render as images (not garbled text)
5. ✅ All images load correctly
6. ✅ Lists render as bullets
7. ✅ Headings render with proper hierarchy

**"Code deployed to GitHub" ≠ "Feature works in Medium"**

Take screenshot of Medium editor showing correct rendering before claiming success.

### Cache Busting Verification

When testing filename generation:

1. Generate first export: `article_20260212_1000_abc123.html`
2. Make trivial content change (add period to sentence)
3. Generate second export: `article_20260212_1001_def456.html`
4. Verify filenames are different (time and/or hash changed)
5. Import both to Medium (should work, no cache hit)

---

## Reference Implementations

### Export Script

See `templates/export_for_medium.py` for complete working implementation.

Key functions:
- `generate_unique_filename(article_name, html_content)` → unique filename with timestamp + hash
- `markdown_to_html(markdown_content, github_pages_base, repo_name)` → converts markdown to HTML with image URL rewriting
- `export_article_for_medium(markdown_path, output_dir)` → main workflow

### Table Rendering

See `templates/render_table_as_png.py` for matplotlib table generation examples.

---

## Failed Approaches (Do Not Repeat)

### ❌ HTML Table Tags

**What was tried**: Convert markdown tables to HTML `<table>` tags using markdown library
**Why it failed**: Medium doesn't render `<table>` tags — columns run together as plain text
**Lesson**: Always render tables as PNG images before export

### ❌ Base64 Data URI Images

**What was tried**: Embed images as base64 data URIs in HTML
**Why it failed**: Unnecessary complexity, file size bloat, same result as PNG URLs
**Lesson**: Use simple `<img src="https://...">` with GitHub Pages URLs

### ❌ Regex-Based Markdown Conversion

**What was tried**: Use regex patterns to convert markdown → HTML (headers, lists, bold, italic)
**Why it failed**: Missed lists, complex formatting, special characters
**Lesson**: Use Python `markdown` library with proper extensions

### ❌ Reusing Filenames

**What was tried**: Update content in `article_medium_ready.html`, push, re-import
**Why it failed**: Medium caches by URL path — serves old cached version
**Lesson**: Always generate unique timestamped filename

### ❌ Committing "Fixes" Without Medium Editor Verification

**What was tried**: Make change, commit with "Fix Medium import" message, assume it works
**Why it failed**: "Deployed to GitHub" ≠ "Works in Medium editor"
**Lesson**: Mandatory end-to-end verification in actual Medium editor before declaring success

---

## Updates to This Document

When you discover a new Medium publishing rule or pitfall:

1. Update this document (STANDARDS.md)
2. Commit with clear message: "Add Medium rule: [brief description]"
3. Notify all projects using Medium publishing (update their CLAUDE.md to reference latest version)
4. Consider adding to export script template if automatable

**This document evolves** — treat it as living documentation, not static reference.

---

**Questions?** Check `published/INDEX.md` for examples of successfully published articles, or review reference implementations in `templates/`.
