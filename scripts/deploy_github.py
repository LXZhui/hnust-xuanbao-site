# -*- coding: utf-8 -*-
"""
一键把本站部署到 GitHub Pages。

流程：校验 token → 创建仓库 → 以单个提交上传全部站点文件 → 开启 Pages →
轮询构建状态 → 验证线上地址。

用法:
    python scripts/deploy_github.py --repo hnust-xuanbao-site
    python scripts/deploy_github.py --repo hnust-xuanbao-site --token github_pat_xxx
    python scripts/deploy_github.py --repo hnust-xuanbao-site --dry-run

token 读取顺序: --token 参数 > 环境变量 GITHUB_TOKEN > ~/.dsh/gh_token.txt
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# Windows 控制台默认可能是 GBK，强制用 UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

API = "https://api.github.com"
DEFAULT_TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".dsh", "gh_token.txt")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".vscode", ".idea"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


class ApiError(Exception):
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        msg = payload.get("message") if isinstance(payload, dict) else str(payload)
        super().__init__("HTTP %s: %s" % (status, msg))


class GitHub:
    def __init__(self, token):
        self.token = token

    def request(self, method, path, body=None, ok=(200, 201, 204)):
        url = path if path.startswith("http") else API + path
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hnust-xuanbao-deploy",
            "Authorization": "Bearer " + self.token,
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                self.scopes = resp.headers.get("x-oauth-scopes")
                payload = json.loads(raw.decode("utf-8")) if raw else {}
                if resp.status not in ok:
                    raise ApiError(resp.status, payload)
                return payload
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                payload = json.loads(raw)
            except ValueError:
                payload = {"message": raw[:400]}
            raise ApiError(exc.code, payload) from None

    def get(self, path, ok=(200,)):
        return self.request("GET", path, None, ok)


def read_token(cli_token):
    if cli_token:
        return cli_token.strip()
    env = os.environ.get("GITHUB_TOKEN", "").strip()
    if env:
        return env
    if os.path.exists(DEFAULT_TOKEN_FILE):
        with open(DEFAULT_TOKEN_FILE, "r", encoding="utf-8-sig") as fh:
            token = fh.read().strip()
        if token:
            return token
    return None


def collect_files():
    """收集站点根目录下要上传的所有文件，返回 [(相对路径, 绝对路径)]。"""
    items = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            if name in SKIP_FILES or name.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            items.append((rel, full))
    return items


def human(path):
    return path


def ensure_repo(gh, owner, repo, private):
    try:
        info = gh.get("/repos/%s/%s" % (owner, repo))
        print("  · 仓库已存在：%s" % info["full_name"])
        return info, False
    except ApiError as exc:
        if exc.status != 404:
            raise

    print("  · 正在创建仓库 %s/%s ..." % (owner, repo))
    try:
        info = gh.request(
            "POST",
            "/user/repos",
            {
                "name": repo,
                "private": private,
                "auto_init": True,
                "description": "湖南科技大学建筑与设计学院宣传报道部 · 宣传网站",
                "has_issues": True,
                "has_wiki": False,
            },
        )
    except ApiError as exc:
        if exc.status in (403, 401):
            print()
            print("  ✗ 创建仓库被拒绝（HTTP %s）。" % exc.status)
            print("    原因通常是 token 权限不足。请确认 token 具备：")
            print("      Contents        → Read and write")
            print("      Administration  → Read and write")
            print("      Pages           → Read and write")
            print("    若仍失败，改用 Classic token 并勾选 repo + workflow 两个 scope。")
            print("    另外：账号若是新注册或未验证邮箱，GitHub 也会拒绝创建仓库。")
            print("    GitHub 原始返回：%s" % (exc.payload.get("message") if isinstance(exc.payload, dict) else exc.payload))
        raise
    print("  · 仓库创建成功：%s" % info["html_url"])
    return info, True


def build_commit(gh, owner, repo, files, message):
    """用 Git Data API 生成一个包含全部文件的提交。"""
    entries = []
    total = len(files)
    for index, (rel, full) in enumerate(files, 1):
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode("ascii")
        blob = gh.request(
            "POST", "/repos/%s/%s/git/blobs" % (owner, repo), {"content": content, "encoding": "base64"}
        )
        entries.append({"path": rel, "mode": "100644", "type": "blob", "sha": blob["sha"]})
        if index % 10 == 0 or index == total:
            print("    - 已上传 %d/%d 个文件" % (index, total))

    # 找到现有 main 分支作为父提交（新建的空仓库可能还没有）
    base_tree = None
    parent = None
    try:
        ref = gh.get("/repos/%s/%s/git/ref/heads/main" % (owner, repo))
        parent = ref["object"]["sha"]
        commit = gh.get("/repos/%s/%s/git/commits/%s" % (owner, repo, parent))
        base_tree = commit["tree"]["sha"]
    except ApiError as exc:
        if exc.status not in (404, 409):
            raise
        print("    - 仓库尚无 main 分支，将创建首次提交")

    tree_body = {"tree": entries}
    if base_tree:
        tree_body["base_tree"] = base_tree
    tree = gh.request("POST", "/repos/%s/%s/git/trees" % (owner, repo), tree_body)

    commit_body = {"message": message, "tree": tree["sha"]}
    if parent:
        commit_body["parents"] = [parent]
    new_commit = gh.request("POST", "/repos/%s/%s/git/commits" % (owner, repo), commit_body)

    if parent:
        gh.request(
            "PATCH",
            "/repos/%s/%s/git/refs/heads/main" % (owner, repo),
            {"sha": new_commit["sha"], "force": False},
        )
    else:
        gh.request(
            "POST",
            "/repos/%s/%s/git/refs" % (owner, repo),
            {"ref": "refs/heads/main", "sha": new_commit["sha"]},
        )
    return new_commit["sha"]


def enable_pages(gh, owner, repo):
    body = {"source": {"branch": "main", "path": "/"}}
    try:
        pages = gh.request("POST", "/repos/%s/%s/pages" % (owner, repo), body, ok=(201, 200))
        print("  · GitHub Pages 已开启")
        return pages
    except ApiError as exc:
        if exc.status == 409:
            pages = gh.request("PUT", "/repos/%s/%s/pages" % (owner, repo), body, ok=(204, 200))
            print("  · GitHub Pages 已存在，配置已更新")
            return pages or {}
        if exc.status == 403:
            print("  ! 无法通过 API 开启 Pages（HTTP 403，token 缺少 Pages 权限）。")
            print("    请手动操作：仓库 Settings → Pages → Source 选 'Deploy from a branch'，")
            print("    分支选 main、目录选 / (root)，保存即可。")
            return None
        if exc.status == 422:
            print("  ! Pages 配置被拒绝（HTTP 422）。常见原因：免费账号的仓库为 private。")
            print("    请在 Settings → General 把仓库改为 Public，或升级账号后重试。")
            return None
        raise


def wait_for_build(gh, owner, repo, attempts=30):
    print("  · 等待 Pages 构建 ...")
    for i in range(attempts):
        time.sleep(6)
        try:
            latest = gh.get("/repos/%s/%s/pages/builds/latest" % (owner, repo))
        except ApiError as exc:
            if exc.status == 404:
                continue
            raise
        status = latest.get("status")
        if status == "built":
            print("  · 构建完成（用时约 %d 秒）" % ((i + 1) * 6))
            return True
        if status == "errored":
            print("  ! 构建失败：%s" % latest.get("error", {}).get("message", "未知原因"))
            return False
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    print("  ! 等待超时，构建可能仍在进行，请稍后自行访问站点地址。")
    return False


def verify(url, attempts=10):
    print("  · 验证线上地址 ...")
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": "hnust-xuanbao-deploy"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 200:
                    body = resp.read().decode("utf-8", "replace")
                    ok = "宣传报道部" in body
                    print("  · 站点返回 200%s" % ("，页面内容校验通过" if ok else "（内容可能仍在部署中）"))
                    return True
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                print("  · 返回 HTTP %s，稍后重试 ..." % exc.code)
        except Exception:
            pass
        time.sleep(8)
    print("  ! 暂时无法通过 HTTP 验证，请手动打开站点地址确认。")
    return False


def main():
    parser = argparse.ArgumentParser(description="部署宣传报道部站点到 GitHub Pages")
    parser.add_argument("--repo", default="hnust-xuanbao-site", help="仓库名（默认 hnust-xuanbao-site）")
    parser.add_argument("--token", default=None, help="GitHub token（默认读环境变量或 ~/.dsh/gh_token.txt）")
    parser.add_argument("--private", action="store_true", help="创建为私有仓库（注意：免费账号无法发布 Pages）")
    parser.add_argument("--dry-run", action="store_true", help="只列出将要上传的文件，不做任何网络写操作")
    parser.add_argument("--no-pages", action="store_true", help="只上传文件，不配置 Pages")
    args = parser.parse_args()

    files = collect_files()
    total_bytes = sum(os.path.getsize(f) for _, f in files)

    print("=" * 68)
    print("  宣传报道部站点 · GitHub Pages 部署")
    print("=" * 68)
    print("  站点目录：%s" % ROOT)
    print("  文件数量：%d 个（合计 %.1f KB）" % (len(files), total_bytes / 1024.0))
    print()

    if args.dry_run:
        for rel, full in files:
            print("    %-42s %8.1f KB" % (rel, os.path.getsize(full) / 1024.0))
        print()
        print("  dry-run 结束，未做任何改动。")
        return 0

    token = read_token(args.token)
    if not token:
        print("  ✗ 没有找到 GitHub token。")
        print("    请把 token 写入 %s" % DEFAULT_TOKEN_FILE)
        print("    或设置环境变量 GITHUB_TOKEN，或用 --token 传入。")
        return 2

    gh = GitHub(token)

    print("[1/6] 校验 token ...")
    try:
        user = gh.get("/user")
    except ApiError as exc:
        print("  ✗ token 无效或已过期（HTTP %s）。" % exc.status)
        return 2
    owner = user["login"]
    kind = "Classic token" if gh.scopes else "Fine-grained token"
    print("  已登录：%s（%s%s）" % (owner, kind, "，scopes: " + gh.scopes if gh.scopes else ""))

    print("[2/6] 准备仓库 ...")
    repo_info, created = ensure_repo(gh, owner, args.repo, args.private)

    print("[3/6] 上传站点文件（单个提交）...")
    sha = build_commit(
        gh,
        owner,
        args.repo,
        files,
        "站点上线：湖南科技大学建筑与设计学院宣传报道部宣传网站\n\n"
        "包含首页、部门概况、宣传动态、作品展示、加入我们、联系我们与 404 页面；\n"
        "纯静态实现，无框架无构建步骤。当前为演示内容版本。",
    )
    print("  · 提交完成：%s" % sha[:10])

    pages_url = "https://%s.github.io/%s/" % (owner, args.repo)

    if args.no_pages:
        print("[4/6] 已跳过 Pages 配置（--no-pages）")
        print("[5/6] 已跳过构建等待")
        print("[6/6] 已跳过线上验证")
    else:
        print("[4/6] 配置 GitHub Pages ...")
        enable_pages(gh, owner, args.repo)

        print("[5/6] 等待构建 ...")
        wait_for_build(gh, owner, args.repo)

        print("[6/6] 验证站点 ...")
        verify(pages_url)

    print()
    print("=" * 68)
    print("  完成")
    print("=" * 68)
    print("  仓库地址：%s" % repo_info["html_url"])
    print("  站点地址：%s" % pages_url)
    print()
    print("  后续更新：修改文件后重新运行本脚本即可（会生成新的提交）。")
    print("  安全提醒：部署完成后请立即吊销本次使用的 token。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
