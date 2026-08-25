# AI 代理 Worker 部署指南

本 Worker 用于转发前端的 AI 视觉识别请求到通义千问或 OpenAI，解决浏览器跨域限制。Worker 本身不存储任何密钥，纯透传。

---

## 1. 注册 Cloudflare 账号

前往 https://dash.cloudflare.com/sign-up 注册，**无需绑卡**，免费额度（每天 10 万次请求）完全够用。

---

## 2. 部署方式

### 方式 A：网页粘贴（最简单，推荐）

1. 登录 Cloudflare Dashboard
2. 左侧菜单进入 **Workers & Pages** → 点击 **Create** → **Create Worker**
3. 将默认名称改为 `spanish-vocab-ai-proxy`
4. 把 `index.js` 的全部内容粘贴到编辑器中，替换掉默认代码
5. 点击 **Deploy**
6. 部署成功后记下 URL，格式类似：
   ```
   https://spanish-vocab-ai-proxy.你的子域名.workers.dev
   ```

### 方式 B：CLI 部署

```bash
# 安装 Wrangler CLI
npm install -g wrangler

# 进入 worker 目录，登录并部署
cd worker
wrangler login
wrangler deploy
```

部署成功后终端会输出 Worker URL。

---

## 3. 使用

部署完成后，将 Worker URL 填入背单词应用的「设置」页面中的「AI 代理地址」字段即可。

前端调用示例：

```javascript
fetch('https://spanish-vocab-ai-proxy.xxx.workers.dev', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': '你的API密钥',
    'x-provider': 'qwen',  // 或 'openai'
  },
  body: JSON.stringify({
    model: 'qwen-vl-plus',
    messages: [{ role: 'user', content: [...] }],
  }),
});
```

---

## 4. 注意事项

- Cloudflare Workers 免费版每天 10 万次请求，CPU 时间 10ms/请求（fetch 等待时间不算），完全够用
- Worker 不存储任何密钥，API Key 由前端每次请求时通过 header 传入
- 支持的 provider：`qwen`（通义千问）、`openai`（OpenAI）
