# Career Agent — 当前最小运行包

一个 Hermes Agent、九个按需组合的业务 Skills、四个 Career 工具。只包含当前运行和首次配置需要的文件；不包含旧代码、历史资料、测试档案、个人经历或登录信息。

## 使用范围

- 真实简历 PDF/文本/图片 → 待确认 Evidence 候选。
- 新 JD + 一份已有个人 Evidence → 原文提取、要求分析、能力及行业/场景匹配、风险/职业价值、简历建议、HTML/Markdown 报告。
- 补充材料 → Evidence 或案例维护提案；按明确要求生成简历文本草稿并审核。
- 事实和正式 ID 不自动批准，维护不自动应用。公司调查延后，PDF/Word 简历视觉排版审核不在本版范围。
- 长期职业偏好保存、未确认表达候选采集尚未实施。当前只消费调用方确认并配置的条件，不声称具有自动偏好 memory。

## 文件职责

| 位置 | 责任 |
|---|---|
| `AGENTS.md` | 当前运行入口与事实/权限边界，不依赖旧背景 |
| `.agents/skills/` | 九个 Skill，实际引用的规则/schema，以及 Evidence 校验脚本 |
| `plugins/career-decision/` | Hermes 注册、工具适配和图像传输 |
| `harness/worker.py` + `CONTRACT.md` | 输入快照、上下文、产物依赖、校验、状态与失败保留 |
| `harness/report.py` + `report.template.html` | 验证后生成网页及 Markdown |
| `harness/install_profile.py` | 首次配置已有的空专用 profile |
| `requirements.txt` | 当前依赖版本；PDF 还需要系统 `pdftoppm` |

## 首次配置

需要已有 Hermes 安装、可用的 `openai-codex` 登录和 `gpt-6.1-sol` 访问权限。本包不复制登录信息、不改 Hermes core。当前已配置的 profile 不要重复执行 installer：它会拒绝覆盖。

在包根目录准备 Python 环境和本地数据位置：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p data/private
```

系统需要 Poppler 的 `pdftoppm`。先按 Hermes 当前 profile 命令创建尚未配置插件的 `career-decision` 专用 profile，再执行：

```bash
.venv/bin/python harness/install_profile.py \
  --profile-dir "$HOME/.hermes/profiles/career-decision" \
  --project-dir "$PWD" \
  --pdf-python "$PWD/.venv/bin/python" \
  --pdf-renderer "$(command -v pdftoppm)" \
  --input-root "$HOME/Downloads"
```

installer 生成忽略的 `data/private/hermes-config.local.json`，以及 profile 配置、SOUL 和插件源码链接。输入位置、Evidence 路径、输出位置、PDF 工具和已确认条件属于本机配置，不写入 Skill。

JD 分析需要一份符合 `resume-intake/schemas/evidence.schema.json` 的个人 Evidence；默认本地位置是 `data/private/career-master.local.yaml`。可以在生成的 runtime config 中把 `evidence_path` 指向你已保存的那份资料，保持单一权威来源，无需复制旧记录。首次 intake 可以在没有当前 Evidence 的情况下生成 pending 候选，但本版不会自动把候选升级为正式资料。

新包重新开始任务；旧项目运行的 rules hash 不同，不导入或继续旧 run。

## 启动与输入

在包根目录运行：

```bash
hermes -p career-decision --in "$PWD"
```

在对话里给出实际文件的完整路径，并说明任务。JD 可使用 JPG/PNG/WebP、PDF 或 TXT；简历审核输入是实际 TXT，PDF 简历可用于 intake。多份输入时明确哪些是 JD，哪些是简历。当前每文件上限 20 MB、PDF 上限 10 页，上下文超限会明确失败。

请求新 JD 分析时说明：使用当前 Evidence，逐项判断重要性/支持程度、行业及业务场景、工作性质、风险和简历建议，按现有模板生成 HTML，返回实际文件路径。

输出保存到配置的本地 `runs_dir`。`validated_pending_review` 表示确定性检查通过；事实确认、语义审核和本人验收仍需分别完成。

## 上传 Git

提交本包代码文件即可。`.gitignore` 排除个人资料、配置、输出、凭据和环境。运行时数据不在此包中；本包没有样例个人事实、历史报告或自动创建的偏好。完整验证记录由整理任务单独保存，不作为 Agent 运行依赖。
