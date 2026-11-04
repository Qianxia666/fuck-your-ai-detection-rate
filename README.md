# FYADR

**F**uck **Y**our **A**I **D**etection **R**ate —— 本地运行的长文档改写工作台。

它把 DOCX / TXT 拆成彼此独立的段落与段内分块，交给**你自己配置**的模型逐轮改写，再用原文对照、差异标记和逐段审阅完成回填导出。全程只在本机启动一个服务，文档、密钥和结果都留在本地磁盘。

![FYADR 工作区](docs/images/workbench.png)

[查看完整界面截图](docs/SCREENSHOTS.md)

---

## 项目简介

**它是什么**

- 一个跑在本机的 Web 工具：Python（Flask）提供接口与页面托管，React 负责界面，不依赖任何云端账号或中转服务。
- 一条「导入 → 分段 → 多轮改写 → 逐段审阅 → 原位导出」的完整流水线，DOCX 只替换选中正文的文字节点，不改字体、字号、行距和页面设置。
- 一个把模型调用权完全交给用户的客户端：内置 DeepSeek 官方入口，也能接任意 OpenAI 兼容渠道，密钥只存在本机配置里。

**它不是什么**

- 不是 AI 内容检测服务，也不承诺任何平台的通过率。改写质量取决于你选的模型和提示词。
- 不做学校 / 单位格式模板的自动重排，也不接管排版。
- 不提供账号体系、云同步和多人协作。

**适合谁**：需要批量改写论文、报告、稿件，又要求原文排版和术语不被破坏，且不希望文档离开本机的人。

---

## 功能特性

**两种入口**

- 上传 `.docx` / `.txt`（最大 40 MB，可拖拽）。
- **直接粘贴正文**：不用先存成文件，粘进来就能改写，上限 30 万字，可通过 `FYADR_MAX_TEXT_CHARS` 调整；粘贴的文本默认整篇即改写范围，仍可再调。

**改写流程**

- **段落隔离 + 段内分块**：不同段落不会混在同一次请求里；超长段落沿句号、问号、分号等语义边界继续拆分，三档分块（细致 / 标准 / 长段）。
- **逐轮提示词**：1–3 轮改写，每轮独立选提示词，上一轮的完整输出就是下一轮的输入。
- **1–16 路块并发**：并发处理不同分块，结果仍按原文顺序回填。
- **实时返回与断点继续**：模型一开始输出就刷新进度；中止后只继续未完成的分块。
- **逐段审阅**：原文对照、差异标记、采用改写、保留原文、手动编辑、单独重跑。
- **提醒不干预**：数字、引用、URL、技术标识符和保护词的变化只做提醒，不覆盖模型结果，也不阻断导出。
- **继续改写**：以当前审阅结果作为下一轮输入，可重新选模型、提示词、分块、并发和保护词。

**导出与格式**

- DOCX 原位回填：复制原文件包，只在 `word/document.xml` 定点替换选中正文的既有文字节点，保留段落、样式、编号、超链接、页眉页脚、图片、表格和分节信息。
- TXT 直接按段落顺序输出。
- 导出前检查包结构、未选区域和可读性，发现问题时列出具体段落，由你决定返回修改还是继续导出。

**工程特性**

- 单文件 exe：`FYADR.exe` 自带 Python 运行时与前端产物，双击即用，配置和数据跟 exe 同目录（便携模式）。
- 本地数据：只监听 `127.0.0.1`，接口不回传明文密钥（前端只拿到掩码占位符与末四位预览）。
- 深浅色主题、桌面 / 平板 / 手机自适应。

---

## 安装与使用

### 环境要求

| 方式 | 需要 |
|---|---|
| 免安装 exe | Windows 10/11，无需 Python / Node |
| 源码运行 | Python 3.10+、Node.js 18+ |

### 方式一：免安装 exe（推荐给普通用户）

1. 下载 `FYADR.exe`（自行打包见[打包](#打包为单文件-exe)）。
2. 双击运行，浏览器会自动打开 `http://127.0.0.1:8765`。
3. 首次启动会在 exe 同级目录生成 `FYADR-data/`，配置、上传的文档、导出结果都在里面。整个文件夹可以随 exe 一起拷走。

命令行参数：

```text
FYADR.exe                 启动并打开浏览器
FYADR.exe --no-browser    只启动服务
FYADR.exe --appdata       数据改存到系统用户目录（%APPDATA%\FYADR）
```

### 方式二：一键脚本（源码运行）

```powershell
git clone https://github.com/Qianxia666/fuck-your-ai-detection-rate.git
cd fuck-your-ai-detection-rate
.\start_web.bat
```

脚本会检查 Python / Node、安装缺失依赖、启动后端（8765）与前端开发服务器（1420），然后打开 <http://127.0.0.1:1420>。

```powershell
# 不自动打开浏览器
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\start_web.ps1 -NoBrowser
```

### 方式三：手动分步

```powershell
python -m pip install -r requirements.txt
npm --prefix app ci
npm --prefix app run build

# 构建后由后端一并托管前后端
python scripts/web_app.py           # http://127.0.0.1:8765
```

前后端分离调试：

```powershell
python scripts/web_app.py           # 终端 1：接口
npm --prefix app run dev:web        # 终端 2：Vite + /api 代理 → 1420
```

### 使用流程

1. **配置模型**：进入「模型连接」，填写 API 地址与密钥，拉取或手填模型名，测试连接。
2. **选入口**：上传 DOCX / TXT，或直接在首页右侧粘贴正文。
3. **确认正文范围**（仅 DOCX）：自动锁定标题、表格、目录域、修订痕迹等不该动的部分，可手动勾选。
4. **改写设置**：选模型、轮数、每轮提示词、分块档位与并发数。
5. **开始改写**：进度实时刷新；随时可以停止，之后只继续未完成的分块。
6. **逐段审阅**：对照原文、查看差异和提醒，逐段决定采用改写 / 保留原文 / 手动编辑 / 重跑。
7. **导出**：下载 Word（原格式回填）或 TXT；也可以「继续改写」再跑一轮。

![正文范围](docs/images/document-scope.png)

---

## 环境变量

全部可选，都有合理默认值。`.env.example` 是占位符模板，真实取值不要提交。

| 变量 | 默认 | 说明 |
|---|---|---|
| `FYADR_PORT` | `8765` | 后端监听端口（仅 `127.0.0.1`） |
| `FYADR_CONFIG_DIR` | 便携目录或系统用户目录 | 配置文件所在目录 |
| `FYADR_DATA_DIR` | 配置目录下的 `data` | 文档、任务快照、导出文件 |
| `FYADR_MAX_UPLOAD_BYTES` | `41943040` | 单次上传大小上限（约 40 MB） |
| `FYADR_MAX_TEXT_CHARS` | `300000` | 粘贴文本的字符上限，前端同步读取 |
| `FYADR_BACKEND_URL` | `http://127.0.0.1:8765` | 仅开发模式：Vite 代理的后端地址 |
| `PYTHON` | `python` | 仅回归脚本：指定解释器 |

**模型密钥**不走环境变量：在界面里填写后保存到本机 `config.json`，安全性依赖该目录的文件权限。接口只返回 `__FYADR_SAVED_SECRET__` 占位符与末四位预览，因此密钥不会出现在页面源码、日志或仓库中。

---

## 目录结构

```text
fuck-your-ai-detection-rate/
├─ app/                        前端：React 18 + Vite + Tailwind + shadcn/ui
│  ├─ src/
│  │  ├─ components/core/      改写页、审阅区、模型连接、提示词、保护区地图、最近文档
│  │  ├─ components/ui/        shadcn/ui 基础组件（按钮、抽屉、标签页等）
│  │  ├─ hooks/ lib/ types/    useThemeMode、接口封装、差异计算、类型定义
│  │  ├─ styles/global.css     设计变量（颜色、圆角、动效）
│  │  └─ CoreApp.tsx           应用外壳、侧边栏与页面切换
│  ├─ public/                  品牌图标
│  └─ vite.config.ts           开发服务器与 /api 代理
├─ scripts/                    后端：Flask 服务与测试
│  ├─ web_app.py               HTTP 接口、静态托管、SSE 事件流
│  ├─ core_documents.py        文档导入、分段、正文范围、DOCX/TXT 导出
│  ├─ core_runs.py             任务编排：分块、并发、审阅、续跑、导出校验
│  ├─ core_llm.py              模型请求：Chat Completions / Responses 流式解析
│  ├─ core_config.py           配置读写、密钥掩码、提示词管理
│  ├─ core_warnings.py         数字 / 引用 / URL / 术语 / 保护词提醒检查
│  ├─ core_*_regression.py     核心回归用例（文档、配置、模型、任务、提醒、接口）
│  ├─ browser_e2e_smoke.mjs    浏览器端到端冒烟
│  └─ run_regressions.py       回归总入口
├─ prompts/defaults/           内置改写提示词（打包进 exe）
├─ packaging/                  exe 打包：launcher.py、fyadr.spec、build_exe.py
├─ docs/                       截图、开发与发布说明、操作指南
├─ .github/workflows/ci.yml    CI：回归 + 前端检查
├─ start_web.bat / .ps1        一键启动（源码运行）
├─ build_exe.bat               一键打包 exe
├─ requirements.txt            Flask / httpx / lxml
└─ .env.example                环境变量占位符
```

---

## 数据与隐私

- 服务只监听 `127.0.0.1`，不对外暴露端口。
- API Key、文档原文、任务快照、断点和导出文件都保存在本机。
- 只有**被选中的正文分块**会随请求发送给你配置的模型服务；表格、目录域、公式、修订、页眉页脚不会进入请求。
- 请求头不包含 `max_tokens` / `max_output_tokens`，不会替你压缩输出长度。
- 最近文档最多保留 20 条，删除前需确认。
- 客户端读取系统与环境代理，本机地址自动绕过代理。

> 便携模式的 `FYADR-data/` 里有你的文档和密钥，分享 exe 时务必排除这个目录。

---

## 打包为单文件 exe

```powershell
.\build_exe.bat
# 等价于 python packaging/build_exe.py
```

流程：构建前端静态产物 → 准备构建虚拟环境（`.venv-build`）→ PyInstaller onefile 打包。产物在 `dist-exe/FYADR.exe`（约 15 MB），内置 Python 运行时、依赖、`app/dist` 与 `prompts/`。

注意：

- 未签名的 PyInstaller 产物可能被 Windows Defender / SmartScreen 误报，添加信任即可。
- 打包机需要 Python 3.10+ 与 Node 18+；目标机器什么都不需要。

---

## 开发与测试

```powershell
python -m unittest discover -s scripts -p "core_*_regression.py" -v   # 核心回归
python scripts/run_regressions.py --fail-fast                         # 回归 + 编译 + 前端检查 + 构建
python scripts/run_regressions.py --include-browser-e2e --fail-fast   # 追加浏览器端到端
npm --prefix app run check:text                                       # 前端文案检查
```

回归覆盖两种流式协议、任意字节分片、超时与取消、代理、重试边界、1–16 路并发顺序、段内分块、多轮衔接、提醒不回退、逐段审阅、DOCX 原位回填和响应式界面。

浏览器回归需要本机 Chrome；它用 `scripts/e2e_mock_provider.py` 起一个假模型，不会调用真实接口。可用 `PYTHON=<解释器路径>` 指定运行后端的 Python。

---

## 贡献指南

欢迎 Issue 与 PR。提之前请先读 [CONTRIBUTING.md](CONTRIBUTING.md)，核心几条：

- **只服务两条主链路**：DOCX 原位回填、分块流式改写。不重新引入评分门禁、学校规则、每轮模型路由。
- **原 DOCX 是唯一格式真相源**，不二次排版；失败的分块明确暂停，不用原文冒充成功。
- **UI 沿用现有 shadcn 工作台与语义色**，不另起一套组件风格。
- **绝不提交**真实文档、API Key、私有接口地址、个人路径或本地运行产物；新配置优先走环境变量并在 `.env.example` 里补占位符。
- 提交前跑一遍核心回归；涉及界面改动的附截图。

PR 流程：fork → 新建分支（`feat/…`、`fix/…`、`docs/…`）→ 提交（参照现有 `feat:` / `fix:` / `chore:` 前缀）→ 开 PR 说明动机、改法和验证方式。

安全相关问题请按 [SECURITY.md](SECURITY.md) 的方式私下报告，不要直接开公开 Issue。

---

## 常见问题

**端口被占用？** 设置 `FYADR_PORT` 换一个端口；exe 会在启动时提示。

**页面打不开 / 一直转圈？** 确认后端控制台没有报错，或访问 `/api/ping` 看是否返回 `{"ok": true}`。

**本地代理导致 502？** 客户端会自动绕过 `127.0.0.1`；用 curl 自查时记得加 `--noproxy '*'`。

**导出的 Word 排版变了？** 文字变长变短会让 Word 重新换行分页，这不属于格式丢失；导出前的检查会标出可能的风险段落。

---

## 项目来源与致谢

本项目是 [multi-zhangyang/fuck-your-ai-detection-rate](https://github.com/multi-zhangyang/fuck-your-ai-detection-rate) 的衍生版本，在其基础上增加了纯文字入口、单文件 exe 打包与界面优化。

早期基础设施与使用思路参考了 [baibaiAIGC](https://github.com/poleHansen/baibaiAIGC)；部分中文改写提示词的设计参考了 [Linux.do](https://linux.do/) 社区的公开讨论与经验整理。继续分发或二次开发时，请尊重原社区内容贡献者与平台规则。

感谢所有提交 Issue、提供文档样例、验证模型兼容性的人。

---

## 免责声明

本项目不提供 AI 内容检测服务，也不承诺通过任何平台的检测。请确认你有权处理所上传的文档，并对模型调用、审阅结果和最终导出内容负责。使用本项目产生的任何后果由使用者自行承担。

## 许可

[AGPL-3.0](LICENSE)
