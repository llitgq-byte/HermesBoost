## GitHub Profile README 模板

> 复制到 `username/username` 仓库的 `README.md` 即可显示在 Profile 顶部。
> 替换 `{USERNAME}`、`{EMAIL}`、`{SOCIAL_LINKS}` 等占位符。

```markdown
## Hi there 👋, I'm **{YOUR_NAME}**

<img align="right" src="https://komarev.com/ghpvc/?username={USERNAME}&color=blueviolet&style=flat-square&label=PROFILE+VIEWS" />

{ONE_LINE_TAGLINE}

{ONE_LINE_STATUS}

{CALL_TO_ACTION}

---

### 🔥 About Me

- 🔭 I'm currently exploring **{CURRENT_FOCUS}**
- 🌱 Currently learning **{LEARNING}**
- 💬 Ask me about **{TOPIC_1}**, **{TOPIC_2}**, or **{TOPIC_3}**
- ⚡ Fun fact: {FUN_FACT}
- 🎯 **Open to opportunities** — [Email me](mailto:{EMAIL}) if you have something interesting

---

### 🛠️ Tech Stack

#### Languages
![Java](https://img.shields.io/badge/Java-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

#### Frontend
![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![Node.js](https://img.shields.io/badge/Node.js-5FA04E?style=for-the-badge&logo=nodedotjs&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)

#### Tools & Infra
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Git](https://img.shields.io/badge/Git-F05032?style=for-the-badge&logo=git&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

---

### 📊 GitHub Stats

<p>
  <img height="170" src="https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=58A6FF&icon_color=C792EA&text_color=8B949E" />
  <img height="170" src="https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&theme=tokyonight&hide_border=true&bg_color=0D1117&title_color=58A6FF&text_color=8B949E" />
</p>

<p>
  <img height="170" src="https://github-readme-streak-stats.herokuapp.com/?user={USERNAME}&theme=tokyonight&hide_border=true&background=0D1117&stroke=30363D&ring=58A6FF&fire=C792EA&currStreakLabel=58A6FF&sideLabels=8B949E&currStreakNum=FFFFFF&sideNums=FFFFFF&dates=555555" />
  <img height="170" src="https://github-profile-trophy.vercel.app/?username={USERNAME}&theme=onestar&no-bg=true&no-frame=true&column=7&margin-w=5" />
</p>

---

### 📫 Find Me Online

[![Email](https://img.shields.io/badge/Email-{EMAIL}-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:{EMAIL})
{SOCIAL_LINKS}

---

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=80&section=footer&width=100%" />

<p align="center">
  <em>Built with ❤️ and way too much ☕ by <strong>{YOUR_NAME}</strong></em>
</p>
```

### 卡片服务

| 卡片 | URL |
|------|-----|
| GitHub Stats | `github-readme-stats.vercel.app/api` |
| Top Languages | 同上 `?url=/api/top-langs` |
| Streak Stats | `github-readme-streak-stats.herokuapp.com` |
| Trophy | `github-profile-trophy.vercel.app` |
| Profile Views | `komarev.com/ghpvc` |
| Shields.io 徽章 | `shields.io` |
| 波浪分隔线 | `capsule-render.vercel.app` |

### 主题配色参考 (Tokyo Night)

| 参数 | 值 |
|------|-----|
| `bg_color` | `0D1117` |
| `title_color` | `58A6FF` |
| `icon_color` | `C792EA` |
| `text_color` | `8B949E` |
| `ring` / `fire` | `58A6FF` / `C792EA` |

### 写入 GitHub 的方法

1. **剪贴板粘贴**（推荐用于含 emoji 的内容）：`clipboard.writeText` + `Meta+a` + `Meta+v`，emoji 在 writeText 中正常传递。
2. **execCommand insertText**：通过 `browser_console` 用 `document.execCommand('insertText')` 单步写入，emoji **必须**用 JSON 代理对（`\ud83d\udc4b`），`\u{XXXX}` 语法不工作。见 SKILL.md §3.8 代理对照表。
3. **GitHub API**：需要 Personal Access Token，浏览器内 fetch 被 CORS 拦截。
