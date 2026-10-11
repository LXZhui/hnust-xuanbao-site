# 湖南科技大学 建筑与设计学院 宣传报道部 · 宣传网站

一个纯静态、零依赖、零构建步骤的部门宣传站点。上传到任意静态托管（GitHub Pages、Gitee Pages、Cloudflare Pages、校内服务器）即可直接访问。

> **当前状态：演示版本。** 站点结构、版式与交互均已就绪，但除部门名称外，**所有数据、栏目名、动态条目、作品信息与联系方式都是示例占位内容**。正式对外发布前请按 [待替换清单.md](待替换清单.md) 逐项替换。

---

## 一、站点结构

```
hnust-xuanbao-site/
├── index.html                首页（Hero / 简介 / 职能 / 栏目 / 矩阵 / 动态 / 招新）
├── about.html                部门概况（定位 / 架构 / 流程 / 原则）
├── news.html                 宣传动态（示例列表）
├── works.html                作品展示（带分类筛选）
├── join.html                 加入我们（岗位表 / 流程 / FAQ / 报名表单）
├── contact.html              联系我们（联系方式 / 投稿指南 / 合作转载）
├── 404.html                  404 页面（GitHub Pages 会自动使用）
├── .nojekyll                 关闭 Jekyll 处理，避免构建异常
├── assets/
│   ├── css/style.css         全部样式（含深色主题与响应式）
│   ├── js/main.js            全部交互（导航 / 主题 / 动画 / 筛选 / 计数）
│   └── img/                  自动生成的抽象示意图与图标
└── scripts/
    ├── gen_assets.py         重新生成 assets/img 下的 SVG 素材
    └── deploy_github.py      一键创建仓库、上传站点并开启 GitHub Pages
```

**技术说明**：没有框架、没有 npm、没有打包。所有页面都是可以直接用浏览器打开的静态 HTML，样式集中在 `style.css`，交互集中在 `main.js`。改文字只需要编辑 HTML，不需要重新构建。

---

## 二、本地预览

直接双击 `index.html` 即可。若希望更接近线上环境（相对路径、404 行为一致），可启动一个本地静态服务器：

```powershell
# 用 Python（推荐，无需安装任何东西）
python -m http.server 8080 --directory .

# 或用 Node
npx serve .
```

然后访问 <http://localhost:8080>。

---

## 三、部署到 GitHub Pages

### 方式 A：自动部署（一条命令）

1. 在 GitHub 上创建一个 **Fine-grained personal access token**：
   - 头像 → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token
   - **Repository access**：`All repositories`（首次创建仓库时选它更省事）
   - **Permissions** 至少需要：
     - `Contents` → Read and write（上传站点文件）
     - `Administration` → Read and write（创建仓库、开启 Pages）
     - `Pages` → Read and write（配置 Pages）
   - 有效期建议 7 天，用完立即吊销
2. 把 token 写入一个**仓库目录之外**的文件（避免被上传）：

   ```powershell
   Set-Content -Path "$env:USERPROFILE\.dsh\gh_token.txt" -Value "github_pat_你的token" -NoNewline -Encoding ascii
   ```

3. 运行部署脚本：

   ```powershell
   python scripts/deploy_github.py --repo hnust-xuanbao-site
   # 或显式传入 token
   python scripts/deploy_github.py --repo hnust-xuanbao-site --token github_pat_xxx
   ```

脚本会依次完成：校验 token → 创建仓库 → 以**一个干净的提交**上传全部站点文件 → 开启 GitHub Pages → 轮询构建状态 → 验证线上地址可访问，最后打印站点 URL。

> **如果创建仓库时报 403**：多半是 token 权限不足。Fine-grained token 创建个人仓库需要 `Administration: write`；若仍失败，改用 **Classic token** 并勾选 `repo` 与 `workflow` 两个 scope，兼容性最好。

### 方式 B：手动部署

```bash
git init
git add .
git commit -m "站点初始化：湖南科技大学建筑与设计学院宣传报道部"
git branch -M main
git remote add origin https://github.com/<你的用户名>/hnust-xuanbao-site.git
git push -u origin main
```

推送后在仓库页面进入 **Settings → Pages**，`Source` 选择 `Deploy from a branch`，分支选 `main`、目录选 `/ (root)`，保存。约 1 分钟后站点上线。

### 上线地址

```
https://<你的用户名>.github.io/hnust-xuanbao-site/
```

---

## 四、换成自己的域名（可选）

1. 在域名服务商处添加一条 `CNAME` 记录，指向 `<你的用户名>.github.io`。
2. 在本仓库添加一个名为 `CNAME` 的文件，内容只写域名，例如：

   ```
   xuanbao.example.edu.cn
   ```

3. 回到 **Settings → Pages**，填入自定义域名并勾选 `Enforce HTTPS`。

---

## 五、日常维护

### 修改文字内容
直接用编辑器改对应 HTML 文件，然后 `git commit && git push`，GitHub Pages 会自动重新构建。

### 替换配图
把 `assets/img/` 下的示例图替换为真实图片即可，建议：

- 首页配图：4:3，建议 1600×1200 以上
- 动态缩略图：16:10，建议 1200×750
- 作品封面：4:3，建议 1200×900
- 文件命名用小写英文与连字符，例如 `work-graduation-exhibition.jpg`

若要修改图片路径，记得同步修改 HTML 中的 `src`。

### 重新生成抽象示意图
```powershell
python scripts/gen_assets.py
```

### 扩展指引

| 想做的事 | 怎么做 |
| --- | --- |
| 给每条动态加独立详情页 | 复制 `news.html` 为 `news-001.html`，把列表项标题包上 `<a href="news-001.html">`，并把列表页的摘要替换为详情内容 |
| 给作品加外链 | 在 `.work-card__body` 内加 `<a class="btn btn--ghost btn--sm" href="https://...">阅读原文</a>` |
| 增加导航页面 | 复制 `contact.html` 作为模板，改标题与内容，然后在**所有页面**的 `.nav` 与页脚中同步添加 `<a class="nav-link" href="新页面.html">名称</a>` |
| 让报名表真正提交到服务器 | `join.html` 目前用 `mailto:` 方案（无需后端）。若要收集数据，可接入表单服务（如 Formspree / 金数据 / 腾讯问卷），把 `<form>` 改为对应 `action` 与字段名，并删除页尾的 mailto 脚本 |
| 去掉演示提示条 | 删除每个页面 `<body>` 开头的 `<div class="demo-banner">…</div>` 整段 |
| 关闭深色主题 | 删除 `main.js` 中 `initTheme()` 的调用，并删除 `style.css` 里 `html[data-theme="dark"]` 规则块 |

### 内容合规提醒

站点是**对外公开发布**的，请务必注意：

- 不使用未获授权的图片、字体、音乐与视频素材；
- 涉及人物肖像的图片，发布前取得当事人同意；
- 不公开成员与师生的身份证号、住址、私人手机号等敏感信息；
- 涉及学院重大事项的表述，以学院官方审定的口径为准。

---

## 六、许可

站点代码（HTML / CSS / JS）可自由修改使用。页面中的文字与图片内容请以部门与学院的授权为准。
