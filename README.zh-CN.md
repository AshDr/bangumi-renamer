<div align="center">
  <img src="desktop/src-tauri/icons/icon.png" alt="Bangumi Renamer 图标" width="160">
  <h1>Bangumi Renamer</h1>
  <p>简体中文 | <a href="README.md">English</a></p>
</div>

一款类似 FileBot 的动画和电视剧剧集文件重命名工具，通过
[TheTVDB](https://thetvdb.com/) 或
[The Movie Database (TMDB)](https://www.themoviedb.org/) 获取元数据。项目同时提供 Typer
命令行工具和带有 React 18 前端的 Tauri 2 桌面应用。

桌面应用支持两种元数据源，并默认使用 TheTVDB。命令行工具目前仅使用 TMDB。

## 功能特性

- 使用 [`anitopy`](https://github.com/igorcmoura/anitopy) 解析动画文件名，并兼容常见的中、日、
  英文季度和集数标记
- 递归扫描 MKV、MP4、AVI、M4V 和 MOV 视频
- 支持 ASS、SSA、SRT、VTT、SUB、IDX、SUP 和 MKS 外挂字幕
- 保留字幕语言和用途后缀，例如 `.chs.ass`、`.cht.ass` 和 `.zh-Hans.forced.srt`
- 桌面应用支持 TheTVDB v4 和 TMDB v3 元数据查询，并使用有效期为 7 天的本地缓存
- 使用 [`rapidfuzz`](https://github.com/rapidfuzz/RapidFuzz) 进行标题模糊匹配
- 自动匹配错误时可手动修正：命令行使用 `--tmdb-id <N>`，桌面应用使用当前元数据源的候选项选择器
- 目标文件已存在时，可选择跳过、添加数字后缀或覆盖
- 默认安全：命令行默认仅预览；桌面应用只有在明确执行应用操作后才会修改文件
- 桌面界面支持简体中文、繁体中文、英语和日语
- 桌面应用支持浅色、深色和跟随系统主题，并可为当前文件夹选择元数据语言

## 安装

命令行工具需要 Python 3.11+ 和 [`uv`](https://docs.astral.sh/uv/)。开发桌面应用还需要
Node.js 20+、Rust 工具链以及 Tauri 2 对应平台的系统依赖。

```bash
git clone https://github.com/AshDr/bangumi-renamer.git
cd bangumi-renamer
uv sync                    # 命令行和 Python 核心
uv sync --extra dev        # Python 开发依赖
cd desktop && npm install  # React 和 Tauri 依赖
```

## 元数据凭据

命令行工具目前需要 TMDB v3 API 密钥：

```bash
export TMDB_API_KEY=your_key_here
```

可前往 <https://www.themoviedb.org/settings/api> 获取密钥。如果希望使用本地 `.env` 文件，复制
`.env.example` 后需要明确让 `uv` 加载它：

```bash
cp .env.example .env
uv run --env-file .env bangumi-renamer /path/to/videos
```

桌面应用支持以下元数据源：

| 元数据源 | 桌面应用凭据 | 说明 |
|----------|--------------|------|
| TheTVDB | `THETVDB_API_KEY`，可选 `THETVDB_PIN` | 默认元数据源，使用 v4 API。subscriber-supported 密钥可能需要 PIN。 |
| TMDB | `TMDB_API_KEY` | 可选元数据源，使用 v3 API。 |

可以在桌面应用的设置对话框中填写凭据，也可以使用上表中的环境变量。元数据源的访问条款和申请方式请参阅
[TheTVDB API 说明](https://thetvdb.com/api-information) 和
[TMDB API 设置](https://www.themoviedb.org/settings/api)。

## 使用方法 - 命令行

预览重命名结果（默认行为，不修改文件）：

```bash
uv run bangumi-renamer /path/to/videos
```

实际重命名文件：

```bash
uv run bangumi-renamer /path/to/videos --apply
```

自动匹配错误时，强制使用指定的 TMDB 电视剧 ID：

```bash
uv run bangumi-renamer /path/to/videos --tmdb-id 209867
```

参数：

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `--version` | 关闭 | 显示命令行工具版本并退出。 |
| `--apply` | 关闭 | 执行重命名。未指定时只输出预览。 |
| `--tmdb-id N` | 自动 | 跳过搜索和匹配，为所有文件使用指定的 TMDB 电视剧 ID。 |
| `--lang` | `en-US` | TMDB 元数据语言。 |
| `--yes` / `-y` | 关闭 | 使用 `--apply` 时跳过交互式 y/N 确认。 |
| `--plain` | 关闭 | 输出适合脚本处理的稳定制表符分隔格式。 |
| `--json` | 关闭 | 输出结构化 JSON。 |
| `--no-color` | 关闭 | 禁用终端 ANSI 颜色。 |
| `--no-input` | 关闭 | 禁用交互提示，在需要确认时直接失败。 |
| `--debug` | 关闭 | 遇到意外错误时显示回溯信息。 |
| `--on-conflict` | `suffix` | 使用 `skip`、`suffix` 或 `overwrite` 处理已有目标文件。 |
| `--verbose` / `-v` | 关闭 | 包含额外的解析详情。 |

路径可以是单个受支持的媒体文件，也可以是目录。目录扫描会递归进行，并跳过隐藏文件和隐藏目录。
当标准输出不是 TTY 时，命令行工具会自动切换为纯文本逐行输出。

## 使用方法 - 桌面应用

```bash
cd desktop
npm run tauri dev
```

1. 首次启动时，如果默认的 TheTVDB 元数据源没有 API 密钥，应用会自动打开设置。选择 TheTVDB 或
   TMDB，并填写对应凭据。
2. 将文件夹拖放到窗口，或点击**选择文件夹**。应用会递归扫描文件并生成预览，此时不会修改任何文件。
3. 检查解析出的季度和集数、元数据匹配、置信度、目标名称和状态。可以更改当前文件夹的元数据语言，
   也可以使用搜索操作选择其他匹配项。
4. 在设置中选择目标文件冲突策略，默认为添加数字后缀。
5. 点击**应用**并确认。操作记录会写入所选根目录下的
   `.bangumi-renamer/history/<timestamp>.json`。

React 前端本身不会重命名文件。Tauri 将白名单中的命令转发给
`bangumi_renamer.desktop_bridge`，再由它调用与命令行工具相同的 `build_plan()` 和
`apply_plan()` 函数。

构建可安装的桌面应用包：

```bash
cd desktop
npm run tauri:build
```

构建脚本会先使用 PyInstaller 创建单文件 Python sidecar，然后将其与 Tauri 应用一起打包。

## 输出格式

```text
{SeriesName}-S{season:02}E{episode:02}.{ext}
```

示例：

```text
[SubsPlease] Frieren - 01 (1080p).mkv
-> Frieren-S01E01.mkv
```

外挂字幕使用相同的紧凑文件名，同时保留能够识别的字幕后缀：

```text
[SubsPlease] Frieren - 01 (1080p).zh-Hans.forced.srt
-> Frieren-S01E01.zh-hans.forced.srt
```

## 项目结构

```text
src/bangumi_renamer/
  cli.py             # Typer 命令行入口
  core.py            # 共享 build_plan / apply_plan 流程
  scanner.py         # 递归发现媒体文件
  parser.py          # anitopy 封装和字幕后缀解析
  metadata.py        # 共享元数据源协议
  thetvdb.py         # TheTVDB v4 客户端
  tmdb.py            # TMDB v3 客户端
  cache.py           # 本地 JSON TTL 缓存
  matcher.py         # rapidfuzz 评分和手动匹配
  renamer.py         # 文件名生成、清理和冲突处理
  display.py         # Rich 和纯文本命令行输出
  history.py         # .bangumi-renamer/history/ 下的操作记录
  desktop_bridge.py  # 连接桌面应用与 Python 共享流程的 JSON 边界
desktop/
  src/               # React 18 和 TypeScript 前端
  src-tauri/         # Tauri 2 和 Rust 桌面外壳
scripts/
  build_desktop_bridge.py  # 构建捆绑的 Python sidecar
tests/
  test_*.py          # Python 单元测试和集成测试
  scenario/          # 跨组件回归测试
```

## 开发

```bash
uv sync --extra dev --extra desktop
uv run pytest -v
uv run ruff check src tests
cd desktop
npm install
npm run test
npm run build
```

## 许可证

MIT

元数据由 [TheTVDB](https://thetvdb.com/) 提供。欢迎补充缺失信息或订阅支持。
