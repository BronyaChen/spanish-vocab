# 部署指南（Render 云部署）

把「西语单词」App 部署到公网，手机浏览器即可访问并「添加到主屏幕」获得类原生 App 体验。

> 为什么要云部署？本地 `localhost` 只有本机能访问，手机连不上。部署到 Render 后会得到一个公网 URL，手机随时随地都能打开。

---

## 一、注册 Render 账号

1. 打开 [https://render.com](https://render.com)
2. 用 GitHub / GitLab / 邮箱注册并登录（免费套餐即可）

## 二、把代码推到 Git 仓库

Render 通过连接 Git 仓库来部署。先把本项目推到 GitHub（或 GitLab）：

```bash
git init
git add .
git commit -m "spanish vocab app"
git branch -M main
git remote add origin https://github.com/<你的用户名>/spanish-vocab.git
git push -u origin main
```

## 三、创建 PostgreSQL 数据库（免费版）

1. Render 控制台 → 右上角 **New +** → **PostgreSQL**
2. Name 填 `spanish-vocab-db`，Database 填 `spanish_vocab`，Plan 选 **Free**
3. 点击 **Create Database**
4. 创建完成后，在数据库详情页找到 **Connection → Internal Database URL**（形如 `postgresql://user:pass@host/spanish_vocab`），复制备用

## 四、创建 Web Service 并连接仓库

**方式 A：用蓝图（推荐，一键搞定）**

1. **New +** → **Blueprint**
2. 选择刚推上去的仓库，Render 会自动读取根目录的 `render.yaml`
3. 它会同时创建 Web Service 和 PostgreSQL 数据库，并自动把 `DATABASE_URL` 注入到 Web Service
4. 点击 **Apply** 开始部署

**方式 B：手动创建 Web Service**

1. **New +** → **Web Service** → 连接你的仓库
2. 配置：
   - Runtime：`Python`
   - Build Command：`pip install -r requirements-cloud.txt`
   - Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment** 里新增环境变量：
   - `DATABASE_URL` = 第三步复制的 Connection String
   - `PYTHON_VERSION` = `3.11`
4. 点击 **Create Web Service**

## 五、首次部署自动建表

应用启动时会自动执行 `init_db()` 创建所需数据表，无需手动操作。第一次部署可能需要几分钟安装依赖。

## 六、手机打开并添加到主屏幕

1. 部署成功后，Render 会给出一个 URL，形如：
   `https://spanish-vocab-xxxx.onrender.com`
2. 手机浏览器打开该 URL
3. 添加到主屏幕：
   - **iOS Safari**：点底部「分享」→「添加到主屏幕」
   - **Android Chrome**：点右上角「⋮」→「添加到主屏幕 / 安装应用」
4. 之后从桌面图标打开即为全屏 App 体验（Service Worker 已启用，弱网/离线也可访问已缓存内容）

## 七、本地数据迁移到云端

若本地已录入过单词，可迁移到云端数据库：

1. **本地**：打开本地 App → 设置 → 点「导出备份」，下载 `words_backup.json`
2. 把该文件传到手机（微信 / AirDrop / 邮件均可）
3. **云端**：手机打开云端 App → 设置 → 点「导入备份」→ 选择该 JSON 文件
4. 导入完成会提示「新增 N，跳过 M」（同名单词自动跳过，不会重复）

---

## 备选：使用 Docker 部署

项目根目录已提供 `Dockerfile`，可部署到任意支持容器的平台：

```bash
docker build -t spanish-vocab .
docker run -d -p 8000:8000 -e DATABASE_URL="postgresql://user:pass@host/spanish_vocab" spanish-vocab
```

不传 `DATABASE_URL` 时默认使用容器内 SQLite（重启容器数据会丢失，仅适合临时试用），生产环境请务必接入 PostgreSQL。

## 常见问题

- **免费实例休眠**：Render 免费 Web Service 长时间无访问会休眠，首次访问需等待约 30 秒冷启动，属正常现象。
- **免费数据库有效期**：Render 免费 PostgreSQL 有使用期限，到期前记得用「导出备份」保存数据。
- **改动如何生效**：向仓库 `main` 分支 `git push` 后，Render 会自动重新部署。
