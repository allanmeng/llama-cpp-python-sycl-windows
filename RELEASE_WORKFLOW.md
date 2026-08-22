# 发布流程 SOP：打包 whl 之后的步骤（Step 1–5）

> 适用范围：whl 已用 `pack_sycl_whl.py` 生成在 `whl/` 后，到远端 Release + 文档推送完成。
> 历史教训：0.3.48 发版在发布环节连续出错（tag 用 `+`、Release 标题格式错、wheel `+` 被吞成 `.`）。
> 本 SOP 把每个坑固化为 **⚠️ 检查点**，严格执行。

---

## 命名铁律（最关键，本次全错在这里）

| 位置 | 正确写法 | 错误写法 |
|------|----------|----------|
| git tag | `v0.3.48-sycl`（`-sycl`） | `v0.3.48+sycl` ❌ |
| Release tag_name | `v0.3.48-sycl` | `v0.3.48+sycl` ❌ |
| Release 标题 (name) | `v0.3.48-sycl`（= tag 名，极简） | `llama-cpp-python 0.3.48+sycl (...)` ❌ |
| 本地 wheel 文件名 | `llama_cpp_python-0.3.48+sycl-cp313-cp313-win_amd64.whl`（`+sycl`，与 CHANGELOG 内部标题一致） | 用 `-sycl` 反而不一致 ❌ |
| CHANGELOG 内部小标题 | `## [0.3.48+sycl] - 2026-08-22`（`+sycl`） | `-sycl` ❌（与历史 0.3.47 的 `[0.3.47+sycl]` 不一致） |

**核心区分**：
- **对外发布标识（git tag / Release）用 `-sycl`** —— 这是 GitHub 地址、用户引用的稳定标识，历来所有版本都是 `-sycl`。
- **文档内部 + wheel 文件名用 `+sycl`** —— 这是 CHANGELOG 既定风格，且 GitHub asset 上传时 `+` 需编码才能保留（见 Step 3 坑③）。
- 两者不冲突：Release body 直接贴 CHANGELOG 段，正文里自然出现 `[0.3.48+sycl]` 小标题，但 Release 的 tag/title 是 `-sycl`。

---

## Step 1 — 精简打包（pack_sycl_whl.py）

- 确认本机 site-packages 已装目标版本：`python -c "import importlib.metadata as m; print(m.version('llama_cpp_python'))"`
- 改 `pack_sycl_whl.py` 的 `out` 路径版本号（0.3.47→0.3.48），**保留 `+sycl` 写法**
- 运行：`python pack_sycl_whl.py`
- ⚠️ 校验：wheel 内 5 个 oneAPI DLL（dnnl/mkl_core.3/mkl_sycl_blas.6/mkl_tbb_thread.3/tbb12）已删、libomp140 保留、ggml/llama/mtmd 齐全
- 产物：`whl/llama_cpp_python-0.3.48+sycl-cp313-cp313-win_amd64.whl`

## Step 2 — 更新 CHANGELOG

- 在 `[0.3.47+sycl]` 之前插入 `[0.3.48+sycl]` 段
- 结构对齐 0.3.47 骨架：`### Changed from JamePeng` / `### Changed (this build)` / `### Performance (measured, B580)` / `### Environment`
- ⚠️ 不要加 `### Notes` 段（0.3.47 没有，两版结构须同构）；⚠️ 提醒放进 `Changed (this build)`
- ⚠️ wheel 文件名引用用 `+sycl`（与本地一致）

## Step 3 — 创建 GitHub Release + 上传 whl（⚠️ 本次重灾区）

**前置**：需用户明确授权（"授权上传 Release"）。

### 3.1 创建 Release
- ⚠️ **tag 必须用 `-sycl`**：`tag_name: "v0.3.48-sycl"`
- ⚠️ **标题必须 = tag 名**：`name: "v0.3.48-sycl"`（不要写长描述）
- body 先用占位，随后用 API 补完整 CHANGELOG 段

### 3.2 补 Release body
- 抽取 CHANGELOG 的 `[0.3.48+sycl]` 段为 `release_notes_0348.md`（纯文本，含 `[0.3.48+sycl]` 小标题）
- API PATCH body

### 3.3 上传 wheel（⚠️ 坑③：文件名 `+` 会被吞）
- ⚠️ **curl 上传时 `+` 必须 URL 编码为 `%2B`**，否则 GitHub 把 `+` 当 query-string 空格、规范化成 `.`，导致 asset 名变成 `llama_cpp_python-0.3.48.sycl-...whl`（与 0.3.47 的 `+sycl` 不一致）
- 正确做法：
  ```
  ENC_NAME="llama_cpp_python-0.3.48%2Bsycl-cp313-cp313-win_amd64.whl"
  curl -X POST ".../assets?name=${ENC_NAME}" --data-binary "@本地whl"
  ```
- ❌ 不要用 `gh release create --latest "whl/..."` 之后又手改（混用 gh 和 curl 易乱）；要么全 gh，要么全 curl+%2B
- 验证上传后 asset 名确实带 `+`

### 3.4 如果传错了（如 `.sycl` 或错误 tag）
- 删错 asset：`DELETE .../releases/assets/{id}`
- 删错 Release：`DELETE .../releases/{id}`（删 tag 会级联删 Release）
- 删错远端 tag：`git push origin --delete "v0.3.48+sycl"`
- 重建用正确 `-sycl` tag，重传用 `%2B` 编码

## Step 4 — 更新 README / README_EN

- 版本号段：`## 最新版本说明（v0.3.48+sycl · 2026-08-22）`（用 `+sycl`，与 CHANGELOG 一致）
- ⚠️ 两条提醒：BREAKING `GenericMTMDChatHandler` 签名变更 + `ctx_checkpoints=0` 崩溃（含 comfyui-sg-llama-cpp 已修复链接）
- ⚠️ 性能段：只留 0.3.48 实测（不要 0.3.45/0.3.47 对比表，Allan 要求去掉）
- ⚠️ wheel 安装命令里的文件名用 `+sycl`（与本地一致）
- 中英文同步

## Step 5 — git commit + push（临时 PAT 后重置 URL）

- 暂存文档：`git add CHANGELOG.md README.md README_EN.md ...`
- ⚠️ `pack_sycl_whl.py` 被 .gitignore 忽略（本地构建脚本不进 git），不强行 `-f`
- commit → push `origin main`
- ⚠️ **push 前用临时 PAT 设 remote URL，push 完立即重置为无 token 形式**：
  ```
  git remote set-url origin "https://${PAT}@github.com/allanmeng/llama-cpp-python-sycl-windows.git"
  git push origin main
  git remote set-url origin "https://github.com/allanmeng/llama-cpp-python-sycl-windows.git"
  ```
- ⚠️ 验证重置：`git remote get-url origin | grep -q "ghp_" && echo WARN || echo OK`

---

## 发布后自检清单（每次发版末尾必跑）

- [ ] git tag 本地 + 远端都是 `v0.3.XX-sycl`（`-` 非 `+`）
- [ ] Release tag_name = `v0.3.XX-sycl`，title = `v0.3.XX-sycl`
- [ ] Release asset 文件名带 `+sycl`（不是 `.sycl`）
- [ ] Release body = CHANGELOG `[0.3.XX+sycl]` 段原文
- [ ] CHANGELOG / README / README_EN 三处版本号、wheel 文件名均为 `+sycl`
- [ ] remote URL 无 token
- [ ] commit 已 push，五个步骤每步都有完成回报

## 本次（0.3.48）踩坑复盘

1. **tag 用 `+sycl`** → 应为 `-sycl`。修复：删 `v0.3.48+sycl` tag（级联删 Release），建 `v0.3.48-sycl` 重建。
2. **Release 标题写长格式 `llama-cpp-python 0.3.48+sycl (...)`** → 应为 `v0.3.48-sycl`。修复：重建 Release 时 title 直接 = tag。
3. **wheel 上传 `+` 被吞成 `.`** → curl URL 中 `+` 未编码。修复：删错 asset，用 `%2B` 重传，asset 名恢复 `llama_cpp_python-0.3.48+sycl-...whl`（与 0.3.47 一致）。
4. **README 多了 0.3.45/0.3.47 对比表** → Allan 要求只留 0.3.48 实测。删表。
5. **ctx_checkpoints 段缺插件链接** → 补 comfyui-sg-llama-cpp 已修复说明。
