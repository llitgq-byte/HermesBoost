# Bilingual README on GitHub — Approaches

Reference for creating bilingual (or multilingual) README files on GitHub via browser or local git.

---

## Two Approaches

### Approach A: Single File with Anchor Links

One README.md file containing both languages, toggled by anchor links.

```markdown
[🇬🇧 English](#english) · [🇨🇳 中文](#中文)

<a name="english"></a>
## English Content
(...)

<a name="中文"></a>
## 中文内容
(...)
```

**Pros:** One file, both languages visible on page, no scrolling.
**Cons:** Long file, harder to diff, both languages render in search.

**When to use:** Short READMEs, or when the two versions are direct translations of the same structure.

### Approach B: Split Files with Cross-Links (Recommended for Long Content)

Separate files per language, with navigation links at the top of each:

- `README.md` — English default → top link: `[🇨🇳 中文](README.zh.md)`
- `README.zh.md` — Chinese → top link: `[English](README.md)`

**Pros:** Clean separation, each language gets its own rendering and search, easier to maintain significantly different content per language.
**Cons:** Two files to keep in sync, GitHub only shows README.md as default landing.

**When to use:** Content differs significantly between languages, or when the user explicitly prefers separation.

### When to Use Which

```
Bilingual README needed?
├── Content is mostly the same across languages?
│   └── Single file with anchor links (Approach A)
├── Content differs significantly (different structure, different depth)?
│   └── Split files (Approach B)
└── User preference?
    └── Follow explicit preference
```

---

## Committing Split-File Bilingual README

When creating both files via GitHub web editor:

1. Create repo with initial `README.md` (via `https://github.com/new` → check "Add README")
2. Edit/commit `README.md` via `https://github.com/OWNER/REPO/edit/main/README.md` — should include Chinese link at top
3. Create `README.zh.md` via `https://github.com/OWNER/REPO/new/main` — should include English link at top
4. Commit with appropriate message

---

## Real-World Session (2026-07-01 — HermesBoost)

1. Created repo `llitgq-byte/HermesBoost` via web UI (with empty README created by GitHub)
2. Edited `README.md` with single-file anchor-based bilingual content — committed
3. User feedback: split into separate files
4. Created `README.zh.md` via `/new/main`, updated `README.md` to add cross-link
5. Both files committed successfully

**Lesson:** When user says "split into separate files," don't default to single-file anchor switching. Honor the explicit preference.
