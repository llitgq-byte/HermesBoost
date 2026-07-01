# 文件上传替代方案

当 `browser_cdp` 的 `DOM.setFileInputFiles` 不可用时（CDP 端点为 HTTP 而非 WebSocket），记录以下方案。

## 方案 A：DataTransfer + File 对象

适用于页面已有 `<input type="file">` 的场景。

### 从 base64 data URL 创建 File

```javascript
(async () => {
  const input = document.querySelector('#avatar_upload');
  if (!input) return 'not found';
  
  // base64 data URL → File
  const dataUrl = 'data:image/png;base64,...';
  const [header, base64] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)[1];
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const file = new File([bytes], 'avatar.png', { type: mime });
  
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
  return 'ok';
})()
```

### 从 Blob 创建 File

```javascript
(async () => {
  const input = document.querySelector('input[type="file"]');
  const blob = new Blob([/* ArrayBuffer */], { type: 'image/png' });
  const file = new File([blob], 'image.png', { type: 'image/png' });
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
})()
```

## 方案 B：本地 HTTP 服务器（⚠️ 通常不可行）

**限制：** HTTPS 页面无法 fetch HTTP localhost（混合内容策略）。

```python
# 启动带 CORS 头的本地服务器
from http.server import HTTPServer, SimpleHTTPRequestHandler
class CORSHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
HTTPServer(('127.0.0.1', 18888), CORSHandler).serve_forever()
```

```javascript
// 浏览器端 — 仅对 HTTP 页面有效
(async () => {
  const resp = await fetch('http://127.0.0.1:18888/file.png');
  const blob = await resp.blob();
  // ... 同方案 A
})()
```

## 方案 C：手动上传

当自动化方案都不可行时，直接告知用户手动操作。

## 决策流程

```
需要上传文件？
├── 有 data URL / base64？
│   └── 是 → 方案 A（DataTransfer + File）
├── 只有本地文件路径？
│   ├── 页面是 HTTP？→ 方案 B（本地服务器）
│   └── 页面是 HTTPS？→ 方案 C（手动上传）
└── 没有 file input 元素？
    └── 方案 C（手动上传）
```

## 相关经验

- 2026-06-30：GitHub 头像上传，CDP 端点 HTTP 限制 + HTTPS 混合内容限制，最终用户手动上传成功
