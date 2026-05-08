提取出的skill做的demo演示
https://front-skills.ballbox.org/


# 网页风格 Skill 生成器

这是一个用于提取网页前端设计语言的 Agent Skill。它会从网站入口 URL 出发，结合源 HTML、CSS、JS、运行时 DOM、computed styles、截图、动效轨迹、响应式状态和人工反馈，生成一个可复用的前端风格模板 Skill 文件夹。

它的目标不是复制网站，而是把网站中的布局节奏、视觉系统、组件模式、交互行为和动效语言抽象成原创、可复用、可安装的前端模板能力。

## 适合做什么

- 从一个网站链接中提取前端设计风格。
- 生成 `front-<site-name>` 形式的前端风格 Skill 文件夹。
- 为新的页面、Web App、落地页、仪表盘或组件库复用某类设计语言。
- 分析网站是否依赖特殊字体、Canvas、WebGL、视频、滚动叙事、hover 材质变化或复杂动效。
- 对生成出来的 demo 做独立评分，并根据评分结果返工。

## 不适合做什么

- 复制原站源码、图片、logo、商标、字体文件、SVG 路径或完整营销文案。
- 把一个页面的提取结果夸大成整个网站的完整风格。
- 只靠截图猜样式。
- 用旧模板污染新网站的提取结果。
- 在没有证据的情况下添加鼠标跟随气泡、装饰网格、额外光圈或多余动效。

## 安装

把这个仓库克隆到全局 Skills 目录：

Windows PowerShell：

```powershell
git clone https://github.com/Yanmoshen/web-style-skill-maker.git "$HOME\.agents\skills\web-style-skill-maker"
```

Linux / macOS：

```bash
git clone https://github.com/Yanmoshen/web-style-skill-maker.git "$HOME/.agents/skills/web-style-skill-maker"
```

安装后，确保你的 Agent 会读取：

```text
~/.agents/skills
```

## 使用方式

在支持 Skills 的 Agent 里直接引用：

```text
使用 $web-style-skill-maker 分析 https://example.com，并生成一个可复用的前端风格 Skill。
```

如果你只给 Agent 一个网址，也可以把它约定成自动执行提取、生成 demo、评分和发布前检查。

## 输出结构

生成出来的前端风格模板必须是完整文件夹，而不是单个 Markdown 文件：

```text
front-<site-slug>/
|-- SKILL.md
|-- agents/
|-- subagents/
|-- references/
|-- evidence/
|-- demo/
|-- qa/
`-- scripts/
```

其中 `demo/` 必须包含可运行的前端 demo；`qa/` 必须包含评分、返工记录和发布判断；`references/` 必须包含风格分析、负证据、页面清单和来源映射。

## 工作流程

1. 把用户给的网址当作入口页，而不是整个网站。
2. 建立有预算的页面清单，默认采样 6 到 10 个代表性页面，硬上限 12 个。
3. 采集源 HTML、CSS、JS、资源列表、DOM 状态、computed styles、截图和动效证据。
4. 将多个 subagent 的结论汇总成设计系统：颜色、字体、间距、形状、组件、布局、媒体、图标、动效和负证据。
5. 生成原创 demo，不复制原站资产，也不制造品牌混淆。
6. 由独立最终仲裁 subagent 对 demo 打分。
7. 如果评分不够高，必须返工；如果进入低增益平台期，要升级实现策略，例如位图/高精 SVG、Canvas/WebGL、自定义字形系统或 scroll theater。

## 评分方向

满分 10 分，至少覆盖：

- 和源站设计语言的相似度。
- 动效与交互灵敏度。
- 运行时视觉系统还原度。
- 响应式与滚动稳定性。
- 可访问性与可用性。
- 性能、安全、隐私和版权安全。
- 生产可维护性。
- 证据完整性和负证据准确性。

命中阻断项时，即使总分高也不能发布。

## 版权边界

这个 Skill 只用于提炼设计语言，不授权复制任何第三方网站。公开 demo 和生成出的模板必须保持原创：

- 可以提炼布局节奏、组件类型、颜色方向、字体层级、动效类别和交互模式。
- 不要复用原站 logo、商标、专有插画、截图、源码、SVG 路径、字体文件、客户名称、完整文案或未授权素材。
- 不要让 demo 看起来像原站镜像，也不要造成品牌归属混淆。
- 本地证据、截图和源码审计结果只用于分析验证；公开发布前必须清理私有路径、凭据和不该公开的材料。

## 仓库内容

- `SKILL.md`：主执行说明。
- `agents/openai.yaml`：Agent UI 元数据。
- `subagents/`：各阶段 subagent 职责说明。
- `references/`：分析结构、评分表、运行时视觉保真和风格生成指南。
- `scripts/`：源码证据采集、运行时审计、动效捕捉、评分和 Skill 生成脚本。
- `qa/`：阻断规则。
- `templates/`：返工报告模板。

友链
https://linux.do/
