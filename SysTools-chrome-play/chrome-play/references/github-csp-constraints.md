# GitHub CSP Constraints & Browser-Only Workarounds

Reference for GitHub web rendering quirks encountered when editing or creating content via browser automation.

---

## 1. README.md CSP Limitation: `<style>` Tags Stripped

### The Problem

GitHub's Content Security Policy **strips `<style>` tags** from rendered markdown files (README.md, wiki pages, etc.). Any CSS you write inside a `<style>` block in markdown will be silently removed — the content renders as if it never existed.

### What Breaks

| Approach | Status | Why |
|----------|--------|-----|
| `<style>` block in markdown | ❌ Stripped | GitHub CSP |
| `:target` CSS tab toggle | ❌ Stripped | Same reason |
| `style=""` inline attributes | ✅ Works | Allowed by CSP |
| `<script>` | ❌ Stripped | Same CSP |

### Working Alternative: Anchor Link Switching

For bilingual README content (or any toggle-like behavior), use **anchor links** instead of CSS:

```markdown
<!-- Toggle links at top -->
[🇬🇧 English](#english) · [🇨🇳 中文](#中文)

<!-- English section (default — appears first in source) -->
<a name="english"></a>
## English Content
(... English text ...)

<!-- Chinese section -->
<a name="中文"></a>
## 中文内容
(... 中文内容 ...)
```

**How it works:**
- English section is placed first in the file → renders as default when none of the anchor hashes are in the URL.
- Clicking `[🇬🇧 English](#english)` navigates to `#english`, jumping to the English anchor.
- Clicking `[🇨🇳 中文](#中文)` jumps to the Chinese anchor.
- No JS, no CSS — pure HTML anchors that survive GitHub's CSP.

### Verification Checklist

After pushing a bilingual README:

- [ ] Top of rendered README shows the toggle links (both should be clickable)
- [ ] Default section renders correctly (the one placed first in source)
- [ ] Clicking the second language link scrolls/jumps to the correct section
- [ ] No `<style>` or `<script>` blocks appear in the rendered HTML (View Page Source to verify)

### Real-World Trial

**2026-07-01 — HermesBoost repo creation:**
1. Attempted CSS tab-toggle (`:target` + `<style>` in README.md)
2. Committed via GitHub web editor → pushed live
3. Checked rendered README → `<style>` block silently missing, toggle non-functional
4. Rewrote with anchor-link switching → committed again → worked perfectly

**Lesson: Always assume `<style>` will be stripped from GitHub-rendered markdown.**

### Alternative: Split Files (README.md + README.zh.md)

When content differs significantly between languages, or when the user explicitly prefers separation, use two files instead of one:

- `README.md` (default, English or primary language) — top link: `[🇨🇳 中文](README.zh.md)`
- `README.zh.md` (secondary language) — top link: `[English](README.md)`

GitHub renders `README.md` as the default landing page; `README.zh.md` is accessed only by clicking the link (no GitHub UI auto-discovery for localized READMEs unless `?locale=` is used).

Decision criteria:
- Single file: short content, parallel structure, user hasn't expressed format preference
- Split files: long content, different structure per language, or user explicitly requests separation

Detailed comparison: `references/github-bilingual-readme.md`

---

## 2. When `gh` CLI Is Not Installed

Some agent machines don't have GitHub CLI (`gh`) installed. Here's the checklist to detect and fall back:

### Detection

```bash
command -v gh &>/dev/null && echo "gh available" || echo "gh NOT available"
```

### Fallback: GitHub Web UI

When `gh` is absent, use browser automation to:

| Task | Web UI URL | Key Steps |
|------|-----------|-----------|
| Create empty repo | `https://github.com/new` | Fill repo name, uncheck "Add README", click Create |
| Create repo with README | `https://github.com/new` | Fill repo name, **check** "Add README", click Create |
| Edit existing file | `https://github.com/OWNER/REPO/edit/main/FILE.md` | Modify in CodeMirror editor, click Commit |
| Commit changes | Editor page → "Commit changes..." button | Fill commit message, click Commit |

### CodeMirror Editor Writing (Reminder)

GitHub uses CodeMirror 6 in its web editor. Always use `document.execCommand('insertText', ...)`:

```javascript
(() => {
  const cmContent = document.querySelector('.cm-content');
  if (!cmContent) return 'no editor';
  cmContent.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, 'YOUR_CONTENT_HERE');
  return 'done, len: ' + cmContent.textContent.length;
})()
```

See §3.8 of `tools-chrome-play` SKILL.md for full details, emoji encoding rules, and verification steps.

---

## 3. Browser API Calls to api.github.com — Blocked

Calling `fetch('https://api.github.com/...')` from browser console on a GitHub page **fails** due to CORS/CSRF. Don't attempt this at all.

The ONLY browser-based approaches on GitHub pages are:
- Direct DOM manipulation (clicks, form fills, CodeMirror writes)
- Navigation to specific URLs (new repo page, edit file page)

---

## 4. Decision Tree: Creating a New GitHub Repo from Scratch

```
Need to create a new GitHub repo?
├── gh CLI available?
│   ├── YES → `gh repo create NAME --public --description "..."`
│   └── NO → GitHub Web UI
│       ├── 1. browser_navigate('https://github.com/new')
│       ├── 2. Fill repo name
│       ├── 3. (Un)check "Add README" based on needs
│       │   ├── CHECKED → GitHub creates empty README, commit via web editor
│       │   └── UNCHECKED → repo fully empty; use CodeMirror or push locally
│       ├── 4. Click "Create repository" button
│       └── 5. If editing content: navigate to /edit/main/FILENAME
│
├── Need to add/edit files?
│   ├── Empty repo (no local clone needed)?
│   │   └── Edit via CodeMirror on /new/main or /edit/main paths
│   ├── Have local content to push?
│   │   └── git remote add origin URL → git push origin main
│   └── Both? → prefer local push (preserves full markdown fidelity)
```
Bilingual README needed?
├── Single-file (same structure, short)?
│   └── Use anchor links (see §1)
├── Split-file (different structure, or user preference)?
│   └── README.md + README.zh.md with cross-links
│       └── See references/github-bilingual-readme.md
└── Verify after render: toggle links work, no <style> in output
```
