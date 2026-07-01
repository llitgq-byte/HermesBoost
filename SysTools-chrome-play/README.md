# SysTools-chrome-play

[🇨🇳 中文](README.zh.md) · **English**

---

<p align="center">
  <strong>⚡ Copy this to your Agent → Agent will auto-configure everything:</strong>
</p>

<p align="center">
  <code>Download all files from https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-chrome-play/chrome-play, place them under $HERMES_HOME/skills/Always/tools-chrome-play/, add <code>browser</code> to the enabled toolsets list, set <code>browser.cdp_url: http://127.0.0.1:9222</code> in config.yaml, then restart the gateway. This is the Chrome Play skill — control a local Chrome browser via CDP (Chrome DevTools Protocol) for web automation, data extraction, and page interaction.</code>
</p>

---

A comprehensive **local Chrome browser automation skill** for Hermes Agent. Connect to a locally running Chrome instance via Chrome DevTools Protocol (CDP) to navigate, click, type, extract data, and interact with any website — including complex SPAs like GitHub.

## Why Does This Exist?

Browser automation is one of the most powerful capabilities an AI agent can have, but it comes with a maze of gotchas: SPA navigation silently failing, CodeMirror editors appending instead of replacing, file uploads blocked by CDP HTTP endpoints, GitHub sudo mode wiping form state on page switch... This skill documents 13+ pitfalls with proven workarounds so the agent doesn't waste turns discovering them.

## Core Features

- **Chrome startup guide** — complete instructions for macOS, Linux, and Windows (terminal, login items, systemd, LaunchAgent)
- **Hermes configuration** — CDP URL setup, browser toolset enablement
- **10 browser tools documented** — navigate, snapshot, click, type, scroll, press, console, vision, CDP, back
- **SPA navigation patterns** — JS click templates, wait strategies, cross-section navigation, Vue/React input handling
- **CodeMirror 6 deep-dive** — execCommand insertText, surrogate pair emoji encoding, clipboard paste fallback, delete-and-recreate recovery
- **File upload workarounds** — DataTransfer objects, mixed content limitations, decision tree
- **GitHub Web UI reference** — profile editing, directory deletion, sudo mode, CSP constraints
- **13 documented pitfalls** with solutions

## How It Works

1. Launch Chrome with `--remote-debugging-port=9222 --user-data-dir=~/chrome-hermes-profile`
2. Configure Hermes: `browser.cdp_url: http://127.0.0.1:9222`
3. Agent uses `browser_navigate()` to connect, then interacts via snapshot/click/type/console
4. SPA pages use JavaScript click (IIFE-wrapped) instead of `browser_click`
5. Complex editors (CodeMirror 6) use `execCommand('insertText')` with surrogate pair encoding

## Installation

### Step 1: Launch Chrome with CDP

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/chrome-hermes-profile" &

# Verify
curl http://127.0.0.1:9222/json/version
```

### Step 2: Configure Hermes

```yaml
# config.yaml
browser:
  cdp_url: http://127.0.0.1:9222
```

Enable the browser toolset: `hermes tools enable browser`

### Step 3: Install Skill

1. Download all files from the [`chrome-play/`](https://github.com/llitgq-byte/HermesBoost/tree/main/SysTools-chrome-play/chrome-play) directory
2. Place them under `$HERMES_HOME/skills/Always/tools-chrome-play/`
3. Restart the gateway

## File Structure

```
SysTools-chrome-play/
├── README.md                         ← This file
├── README.zh.md                      ← 中文文档
└── chrome-play/
    ├── SKILL.md                      ← Agent instructions (full guide + 13 pitfalls)
    ├── references/
    │   ├── file-upload-workarounds.md       ← File upload techniques and limitations
    │   ├── github-browser-edit-pitfalls.md   ← CodeMirror / editor pitfalls
    │   ├── github-bilingual-readme.md        ← Bilingual README strategies
    │   ├── github-csp-constraints.md         ← GitHub CSP + Web UI decision trees
    │   └── github-profile-editing.md         ← GitHub profile optimization
    └── templates/
        └── github-profile-readme.md          ← Profile README template (Tokyo Night)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `browser_navigate` fails to connect | Check Chrome is running with `--remote-debugging-port=9222` |
| Port already in use | `lsof -i :9222` — kill existing Chrome or use different port |
| Profile lock conflict | Ensure `--user-data-dir` differs from your main Chrome profile |
| SPA click silently fails | Use JS click with IIFE wrapper (see §3.2 in SKILL.md) |
| File upload doesn't work | CDP HTTP endpoint limitation — use DataTransfer or manual upload |

## License

MIT
