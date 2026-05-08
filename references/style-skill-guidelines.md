# 风格 Skill 编写规范

生成出的风格 Skill 应该帮助 Codex 创作原创前端界面，而不是克隆某个具体网站。

## 命名

使用小写 hyphen-case，并且生成文件夹必须以 `front-` 开头。

- 好的文件夹名：`front-vercel`、`front-stripe`、`front-linear`、`front-athens-week`
- 好的 Skill 内部风格名：`Minimal Developer Cloud`、`Gradient Fintech Platform`
- 避免：只用品牌名、包含 `clone`、或没有 `front-` 前缀

文件夹名和 frontmatter 的 `name` 应保持一致。

## 生成项目目录

每个生成 Skill 都必须是文件夹，不是单文件：

```text
front-<site-slug>/
|-- SKILL.md
|-- agents/openai.yaml
|-- subagents/<role>/brief.md
|-- references/style-analysis.json
|-- references/evidence.md
|-- references/negative-evidence.md
|-- references/page-inventory.json
|-- references/source-map.json
|-- evidence/source/
|-- evidence/dom/
|-- evidence/css/
|-- evidence/routes/
|-- evidence/frontend/
|   `-- reports/
|-- evidence/screenshots/
|-- evidence/motion/
|   |-- screenshots/
|   |-- videos/
|   |-- traces/
|   `-- reports/
|-- demo/index.html
|-- demo/styles.css
|-- demo/script.js
|-- demo/implementation-notes.md
|-- demo/verification.md
|-- demo/screenshots/
|-- demo/motion-report.json
|-- qa/scorecard.json
|-- qa/blocking-rules.md
|-- qa/redo-report.md
|-- qa/release-decision.md
|-- scripts/frontend_runtime_audit.mjs
|-- scripts/playwright_motion_capture.mjs
`-- scripts/score_extraction.py
```

## `SKILL.md` 必需章节

1. frontmatter，包含 `name` 和触发信息充足的 `description`。
2. Overview：描述可复用设计语言和灵感来源。
3. Evidence Boundary：说明哪些是 measured、inferred、unknown、absent。
4. Site Coverage：说明采样路由、页面 archetype、跳过的路由类别，以及结果是站点级、部分站点还是页面级。
5. Design Principles：5-8 条可复用设计规则。
6. Tokens：颜色、字体、间距、形状、层级、动效。
7. Layout Patterns：页面级布局模式。
8. Component Recipes：常见 UI 组件和状态。
9. Interaction And Motion：触发方式、时间、灵敏度规则，以及 canvas/WebGL/video/材质/滚动效果的多帧证据。
10. Implementation Guidance：面向目标技术栈或通用前端实现。
11. Demo QA Checklist：独立最终仲裁评分、评分门禁、平台期升级规则和阻断项。
12. Avoid：克隆、污染、可访问性和滥用警告。

## 证据规则

- 优先使用源码、DOM、computed styles 和交互轨迹，而不是截图印象。
- 把用户提供的 URL 当作入口页。声称站点级风格前，必须建立有边界的多页面清单。
- 默认选择 6-10 个代表路由，硬上限 12 个。存在时优先覆盖 home/root、feature/product、pricing、docs/blog/article、case/customer、about/contact 以及视觉明显不同的 campaign/event 页面。
- 按 URL pattern、导航标签、DOM 骨架和组件签名聚类重复路由。大型 docs/blog 集合只采样索引页加一个代表详情页。
- 如果只采样了一个路由，生成 Skill 必须标为页面级或部分站点，不能说是全站级。
- 截图用于验证构图，不能替代源码检查。
- 对 seed route 和浏览器可访问的 Tier A 路由运行 frontend runtime audit。必须保留报告，覆盖 hydration 后 DOM、computed styles、CSS custom properties/rules、media queries、keyframes、字体、scripts/links、图片/背景图、canvas/video、network/resources、JS/CSS coverage、accessibility tree、performance metrics、framework/runtime signals、forms/controls、只含 key 不含 value 的 storage keys、布局溢出、文本裁切、定位层和 section boxes。
- 对 Tier A 路由，如果页面可被浏览器打开，必须保留 Playwright 动效捕获证据：video、trace、截图、JSON 报告、hover/mousemove 探针、instant-scroll 样本、wheel-scroll 样本、timed frames、运行时信号，以及相关时的 reduced-motion fallback。
- 对 canvas、WebGL、video、Framer、Lottie、GSAP 或材质效果，必须捕获多帧证据和像素/视频差异。DOM computed style 不能单独证明或否定这些效果。
- 对真实 3D、PBR、GLB/GLTF、法线/粗糙度/反射贴图、预渲染帧序列或视频级视觉，必须记录运行时视觉层级和最低可接受 demo 技术栈。CSS/Canvas 2D 不是 WebGL/PBR 的自动替代品。
- 当源站物体的识别来自体积、光照、遮挡、投影和表面纹理曲率时，生成 Skill 必须写清对象级保真规则：轮廓、明暗交界、高光、接触阴影、纹理随曲率弯曲、多帧变化和 reduced-motion 静态 fallback。
- 用户观察到的交互必须定点复测后，才能标记为缺失。
- 每个主要视觉特征都必须有证据，或者明确标为推断。
- 必须记录负证据。如果源站没有网格背景、卡片堆叠、渐变光晕、3D 舞台或终端 UI，要明确写下。
- 禁止把其它生成模板的视觉特征带进来。

## 安全规则

- 除非用户拥有品牌，否则使用调整后的近似色，而不是直接使用品牌色。
- 使用 lucide、phosphor、radix icons 或框架原生图标等通用开源图标。
- 使用系统字体或开放授权字体。
- 禁止包含复制的营销文案、专有插画、截图、logo、客户名、参会者数据、私有 URL 或源站资产。
- 如果精确间距会导致页面变成克隆，不要保留精确间距图。

## 质量标准

好的风格 Skill 应该让 Codex 在不打开原网站的情况下，也能创作多个同类新页面。它描述的是规则、取舍、证据边界、交互行为和可复用模式，而不是一次性的页面观察。

demo 必须是 `demo/` 目录下可运行的小型前端工程，并包含截图与 Playwright/video/trace 动效验证产物。分数小于等于 9.8/10、迭代收益收敛规则未满足、存在阻断项、scorecard 不是由独立最终仲裁 agent/subagent 填写，或源站核心 motion/材质/滚动行为没有进入 demo 时，不允许发布。

如果源站核心视觉层级是 `webgl-3d`、`frame-sequence` 或 `video-motion`，demo 技术选型必须匹配该层级：Three.js/Babylon/R3F/GLSL、原创帧序列、video-like canvas 或同等复杂度的生成资产。只用 2D 圆、普通渐变、平面网格、非空 canvas 或静态截图，不得获得发布级相似度。

当 demo 分数小于等于 9.8，且最近一次完整返工提分不超过 0.5 时，生成出的 skill 必须把结果视为策略平台期。下一轮必须根据失败证据升级到通用的更高杠杆策略：资产保真、运行时视觉系统、字形排版、交互/滚动架构或组件/布局系统，不能继续只靠小幅 CSS/文字/间距微调补分。
