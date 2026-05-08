---
name: web-style-skill-maker-zh
description: 中文版网页前端风格提取 Skill。分析网站 URL、源 HTML/CSS/JS、DOM 状态、截图、动效和响应式行为，提取可复用的前端设计语言，并生成生产级 front-site-name 风格 Skill 文件夹。Use when the user asks in Chinese to analyze a website frontend style, UI design, visual language, source code, layout, typography, icons, motion, demo fidelity, or turn a web reference into a reusable frontend template/style skill with QA scoring.
---

# 网页风格 Skill 生成器中文版

## 执行标准

用这个 Skill 把现有网站转化为可复用、原创的前端风格 Skill。源网站是证据，不是要照抄的模板。产物必须是完整文件夹 `front-<site-slug>`，不能只是一个 Markdown 文件。

这个 Skill 专门避免一种失败：只看截图、沿用旧模板、受上下文污染，然后凭感觉发明源站没有的设计特征。任何设计特征如果没有在源 HTML/CSS/JS、计算后的 DOM、交互轨迹或截图证据中出现，就必须标记为“推断”或“未观察到”，不能当作源站事实发布。

## 不可妥协项

- 先检查源 HTML、CSS、JS bundle、DOM 结构、computed styles、加载资源和交互行为，再做视觉判断。
- 截图只能用来验证构图和视觉结果，不能作为唯一依据。
- 把用户给的网址当作入口页，不要自动当成整个网站。必须先建立有预算的页面清单，再声称提取的是站点级风格。
- 如果最终只访问或采样了一个页面，产物只能称为页面级提取，并明确写出覆盖限制，不能说代表整个网站。
- 必须生成完整的 `front-<site-slug>/` Skill 文件夹，包含 subagent 文件夹、references、evidence、demo notes 和 QA 记录。
- 必须记录负证据，例如“没有可见页面网格”“没有渐变背景”“不是卡片堆叠布局”“未观察到 hover 动效”。
- 把动态行为作为一级源特征处理。如果源站包含 canvas、WebGL、Framer/GSAP/Lottie、视频、滚动联动面板、指针敏感材质变化或持续动画，必须用多帧证据提取并复现动效语言。静态截图不能获得高动态分或高相似度分。
- 必须识别运行时视觉层级。如果源站有真实 3D 体积、WebGL、GLB/GLTF、PBR 贴图、法线/粗糙度/反射贴图、预渲染帧序列或视频级材质动画，demo 不能用 2D 圆、CSS 渐变、平面网格或非空 canvas 冒充；必须选择 WebGL/Three.js/Babylon/React Three Fiber、原创帧序列、shader 或同等复杂度的 runtime 替代。
- 将用户观察到的交互先记录为待复测假设。如果自动探针没有复现用户指出的 hover、pointer、scroll、材质、颜色、光照或特定位置触发变化，不要直接宣判缺失；必须做第二轮定点测试并写明是否仍未复现。
- 生成的 demo 必须是 `demo/` 目录下可运行、可复现的小型前端工程，不能只是截图，不能只写说明并指向图库源码。
- 产物必须原创：除非用户明确拥有授权，否则不能复用 logo、商标、专有插画、原文案、精确布局、私有数据或付费字体。
- 如果用户提供录屏，必须把录屏作为一等行为证据处理。抽取关键帧，并用录屏校验 demo 的动效、材质、滚动布局和误加交互，而不是只看静态截图。
- 禁止凭空添加自定义鼠标跟随物、泡泡、光圈、磁吸指针、装饰网格或额外动效层，除非源码/录屏证明这是网站自身 UI。录屏里看到系统鼠标指针，不等于网站有鼠标跟随效果。
- 也要禁止“视觉上像鼠标跟随物”的替代实现：CSS 伪元素、径向高光、canvas 光晕、大面积聚光灯渐变，只要看起来像跟着鼠标的 halo/bubble，就必须有源站证据才能做。
- 必须做滚动过程重叠检查。正常滚动时，如果卡片、蓝色 tablet、按钮或文本块互相碰撞，即使首屏截图可用也判失败。
- 对 sticky 或长滚动面板，必须验证滚动轨道高度足够，并用 instant scroll 多点采样。grid 里的 sticky 元素如果没有显式轨道，可能会悄悄滚走或被裁切。
- 禁止把源站自定义字形替换成普通字体拉伸效果。如果原字形受保护或无法使用，只能做非同一的原创形状系统来表达相近重量/节奏，或者直接省略，不得用 transform-stretched text 假冒。
- demo 完成后必须交给独立的最终仲裁 agent/subagent 做 QA 评分。目标不是勉强通过；必须持续迭代，直到评分高于 9.8/10，且最近一次完整返工带来的提分不超过 0.5 分。
- 低于或等于 9.8 的低增益迭代不是停止理由，而是说明当前实现策略已经进入平台期。此时必须升级策略，不能继续只靠小幅 CSS 微调。
- 如果用户给出人工分数或质量判断，必须把它当作评分校准证据。用户认为只有 8 分左右的 demo，在点名问题修复并复测前，不能被独立仲裁打成接近发布满分。
- 任意阻断项命中都直接失败，即使总分高于 9.8 也不能发布。

## 必需输出目录

每个生成出的风格 Skill 都必须使用这个结构：

```text
front-<site-slug>/
|-- SKILL.md
|-- agents/
|   `-- openai.yaml
|-- subagents/
|   |-- 01-source-code-auditor/
|   |-- 02-dom-css-auditor/
|   |-- 03-visual-motion-auditor/
|   |-- 04-design-system-synthesizer/
|   |-- 05-demo-implementation-reviewer/
|   |-- 06-accessibility-responsive-qa/
|   |-- 07-performance-security-qa/
|   `-- 08-final-arbiter/
|-- references/
|   |-- style-analysis.json
|   |-- evidence.md
|   |-- negative-evidence.md
|   |-- page-inventory.json
|   |-- source-map.json
|   `-- qa-scorecard.md
|-- evidence/
|   |-- source/
|   |-- dom/
|   |-- css/
|   |-- routes/
|   |-- frontend/
|   |   `-- reports/
|   |-- screenshots/
|   `-- motion/
|       |-- screenshots/
|       |-- videos/
|       |-- traces/
|       `-- reports/
|-- demo/
|   |-- index.html
|   |-- styles.css
|   |-- script.js
|   |-- implementation-notes.md
|   |-- verification.md
|   |-- screenshots/
|   `-- motion-report.json
|-- qa/
|   |-- scorecard.json
|   |-- blocking-rules.md
|   |-- redo-report.md
|   `-- release-decision.md
`-- scripts/
    |-- frontend_runtime_audit.mjs
    |-- playwright_motion_capture.mjs
    `-- score_extraction.py
```

根目录的 `SKILL.md` 是可被 agent 调用的 Skill。其它文件夹用于保存证据、角色工作记录和 QA 决策，让另一个 agent 能追溯每条风格规则为什么存在。

## Subagent 配置

当系统允许 subagent 且用户要求多 agent / 并行工作时，按下面角色分派，且每个角色使用独立写入范围。若不能启动 subagent，就按相同角色顺序手动执行，并写出同样的文件。

- `01-source-code-auditor`：采集 HTML、stylesheet 链接、inline style、script bundle、asset 引用、source map、页面变体，以及 hydration 后前端证据的浏览器 runtime audit 报告。输出 `subagents/01-source-code-auditor/findings.md`。
- `02-dom-css-auditor`：从 hydration 后 DOM/runtime audit 报告中采样重复元素的 computed styles、字体、颜色 token、间距、圆角、阴影、布局原语、CSS rules、字体和响应式溢出。输出 `subagents/02-dom-css-auditor/findings.md`。
- `03-visual-motion-auditor`：捕获桌面/移动截图、滚动段落、hover/focus/mousemove 状态、动画时间、canvas/video/WebGL 帧、前后像素证据和交互缺失。输出 `subagents/03-visual-motion-auditor/findings.md`。
- `04-design-system-synthesizer`：把证据合成为可复用的设计原则、tokens、组件配方、布局模式、媒体/图标规则和负证据。输出 `references/style-analysis.json`。
- `05-demo-implementation-reviewer`：审查 demo 的组件完整度、状态覆盖、是否混入其它模板、以及生产可维护性。输出 `subagents/05-demo-implementation-reviewer/findings.md`。
- `06-accessibility-responsive-qa`：检查键盘、焦点、对比度、语义结构、移动/平板/桌面布局稳定性、溢出和文本适配。输出 `subagents/06-accessibility-responsive-qa/findings.md`。
- `07-performance-security-qa`：检查资源体积、动画成本、第三方资源、隐私、不安全脚本、版权风险、异常状态、coverage、network/resource inventory 和 performance metrics。输出 `subagents/07-performance-security-qa/findings.md`。
- `08-final-arbiter`：独立审查全部证据，包括 frontend runtime audit 和 motion capture 报告，然后填写评分表，应用阻断规则，检查 9.8 分和迭代收益停止条件，批准发布或写返工报告。输出 `qa/release-decision.md`。

每个角色的正式任务说明在 `subagents/*/brief.md` 中。

## 工作流程

1. **初始化干净工作目录**
   - 根据网站名称或域名生成稳定 ASCII slug。
   - 默认使用 `front-<site-slug>` 作为文件夹名和 Skill 名，除非用户给出更明确的名称。
   - 不要把旧风格文件夹当作新视觉基底，除非用户明确说明两个网站属于同一设计家族。

2. **用固定预算发现站点路由**
   - 把用户 URL 当作 seed route。推导 canonical origin；安全时同时检查根页面和用户给出的具体页面。
   - 当可以直接 HTTP 访问时，先运行 `scripts/capture_source_evidence.py --url <url> --out <front-site>/evidence`，用于初始 HTML/CSS 抓取，并从 anchors、canonical links、`robots.txt` sitemap 声明和可访问的 `/sitemap.xml` 生成首轮页面清单。
   - 视觉综合前必须建立 `references/page-inventory.json`，包含候选路由、发现来源、页面 archetype、优先级、是否选中、跳过原因和访问限制。
   - 默认路由预算：选择 6-10 个公开页面，硬上限 12 个。网站很小或大量受阻时可以更少。
   - 优先覆盖页面类型，而不是追求数量：home/root、product/feature、pricing/plans、docs/blog/article、case study/customer、about/company/contact，以及明显不同的 campaign/event 页面。
   - 按 URL pattern、导航标签、DOM 骨架、页面类型和重复组件签名聚类去重。大型 docs/blog 站只采样索引页加 1 个代表详情页，不要采样一堆近似文章。
   - 到达预算、公开候选耗尽、访问受阻，或连续两个新页面类型没有带来新的 token、组件、布局模式或动效行为时停止扩展。
   - 除非用户明确要求且访问安全，否则不要跟进 private、account、checkout、admin、auth、search-result、query-heavy 或可能产生副作用的路由。

3. **采集源代码证据**
   - 对 seed route 和选中的代表页面抓取 HTML 与同源 CSS。
   - 用浏览器检查 seed route 以及最高优先级页面 archetype 的 hydration 后 DOM。
   - 记录 stylesheet URL、inline style、CSS custom properties、font declarations、media queries、animation/keyframe 名称、SVG/icon 用法、asset URL、路由专属脚本、共享 bundle 和 JS 驱动交互。
   - 对 seed route 和每个浏览器可访问的 Tier A 路由，运行前端 runtime 审计：
     `node scripts/frontend_runtime_audit.mjs --url <route-url> --out <front-site>/evidence/frontend --label <route-slug> --viewports 1440x900,1024x768,390x844`
   - runtime 审计必须采集 hydration 后 DOM 清单、computed style 样本、CSS custom properties、可访问 CSS rules、media queries、keyframes、font faces、scripts、links、图片/背景图、canvas/video 清单、framework/runtime signals、network request/response 摘要、performance resource entries、JS/CSS coverage、accessibility tree 摘要、form/control 清单、event attributes、只含 key 不含 value 的 storage keys、布局溢出/文本裁切、定位层、sticky/fixed 元素和 section boxes。
   - 如果 JS/CSS coverage 或 accessibility tree 采集受阻，必须记录限制，但保留其它浏览器采集到的前端报告。
   - 把相关片段保存到 `evidence/source/`、`evidence/css/`、`evidence/dom/` 和 `evidence/routes/`。
   - 如果源码访问受阻，必须明确写出限制，并用 computed styles 和浏览器 DOM 检查补充。
   - 如果路由采样最终只有一个页面，必须在 `references/style-analysis.json` 中明确标记为页面级提取。

4. **采集视觉与动效证据**
   - 使用分层采样，避免多页面覆盖导致时间爆炸：
     - Tier A：3-5 个视觉差异最大的选中路由，采集 1440x900、1024x768、390x844，首屏加至少两个下方 section，并做交互探针。
     - Tier B：最多 5 个额外选中路由，只采集桌面首屏和一个下方 section，再做快速 DOM/computed-style 检查。
     - Tier C：其余已发现路由只进入清单，除非它暴露出独特模板、资产系统或动效线索。
   - 每个可用浏览器打开的 Tier A 路由，都必须运行 Playwright 动效捕获：
     `node scripts/playwright_motion_capture.mjs --url <route-url> --out <front-site>/evidence/motion --label <route-slug> --viewports 1440x900,1024x768,390x844`
   - Playwright 捕获必须模拟可见 hover 目标、mousemove、instant scroll 多点、mouse wheel 和 timed frames。默认开启 video 与 trace 录制，并把截图和 JSON 报告保存到 `evidence/motion/{screenshots,videos,traces,reports}/`。
   - 如果源站有动效、canvas/WebGL/video、滚动联动场景或用户报告的动态行为，还要运行 reduced-motion 兜底采样，例如：
     `node scripts/playwright_motion_capture.mjs --url <route-url> --out <front-site>/evidence/motion --label <route-slug>-reduced --viewports 1440x900,390x844 --reduced-motion`
   - 如果 Playwright 无法运行，必须记录失败原因，使用等价浏览器自动化方式补采；没有 video/trace 或等价多帧证据时，不得声称高动效保真。
   - 在 Tier A 路由上测试 hover、focus、mousemove、scroll、sticky nav、carousel、modal、menu、video/canvas/3D 区域、材质/高光变化和 lazy-loaded media。
   - 对动态效果记录触发方式、影响元素、时间、easing、视觉变化，并至少保存三个时间采样帧或截图。
    - 对 canvas/WebGL/video 区域使用像素差异或视频帧证据。不要只看 DOM computed style，因为 canvas 材质和类 shader 变化通常不会出现在 CSS 里。
    - 检查运行时视觉信号：`canvas` 上下文、WebGL bundle、`.glb/.gltf/.hdr/.ktx2/.basis/.wasm`、`normal/roughness/diffuse/albedo/reflection/displacement` 贴图、`/frames/` 连续编号图片、Lottie/Rive/GSAP/Framer runtime。把结果写入 `runtime_visual_system`，并标记最低可接受 demo 技术层级。
    - 对 3D 或 PBR 物体做对象级截图比较：体积轮廓、明暗交界、方向性高光、接触阴影、遮挡/z-depth、纹理是否随曲率弯曲，以及多帧变化。非空 canvas 或像素有变化不能单独算通过。
    - 如果用户提供录屏，必须抽取代表帧，并记录录屏中可见的用户主张。用录屏检查布局时序、hover/材质行为和误加的交互，比如不该存在的鼠标跟随泡泡。
    - 禁止只用 DOM 证明“没有 cursor”。还必须看像素/截图，确认没有大面积跟随鼠标的 halo、bubble 或聚光灯。
    - 如果目标是 Framer 或其它 runtime 很重的建站器，必须检查 hydration 后 DOM 和 runtime bundle/source map，并在 hydration 后、滚动后采样。静态 HTML 不够。
   - 只靠截图是不合格的。

5. **提取并写入分析**
   - 先读 `references/analysis-schema.md`。
   - 填写 `references/style-analysis.json`，明确 measured、inferred、unknown、absent。
   - 每个主要 token、布局模式、组件或动效规则都必须指向源码证据、frontend runtime audit/computed-style 证据、截图证据、动效证据或明确的推断说明。
   - 填写 `site_sampling`，包含选中路由、跳过的路由类别、页面 archetype 覆盖、停止原因，以及输出属于站点级还是页面级。

6. **生成 Skill 文件夹**
   - 运行 `scripts/style_skill_from_analysis.py --analysis <style-analysis.json> --out <skills-root>`。
   - 脚本会创建带 subagent、references、evidence、QA 文件和根 `SKILL.md` 的 `front-<site-slug>/`。
   - 编辑生成的 `SKILL.md`，增强具体性，删除弱推断，补充源站负证据。
   - 最终面向用户的说明和报告优先使用中文。

7. **构建或审查 demo**
   - demo 必须展示源站风格的布局、组件密度、动效词汇和响应式行为，同时不能复制受保护资产。
   - demo 必须以 `demo/index.html`、`demo/styles.css`、`demo/script.js` 形式落盘，并包含 `demo/motion-report.json`，说明测得的原站动效和 demo 中的对应实现。
    - 如果源站依赖 canvas/WebGL/video/材质效果，demo 应包含原创 canvas/WebGL/video-like 替代或同等复杂度的生成视觉系统。只放静态卡片和很轻的 CSS 漂移动效不够。
    - 如果源站核心视觉是 3D/PBR/法线贴图/GLB/帧序列，demo 必须使用匹配层级的技术：Three.js/WebGL/Babylon/R3F、GLSL shader、原创帧序列或高保真生成资产。Canvas 2D 只能用于平面程序纹理；不能用圆形 clip、平面网格或普通径向渐变冒充真实球体、布料或产品模型。
    - 如果源站使用长滚动或 sticky 面板，demo 必须包含可滚动/sticky 状态，并保存首屏和至少两个下方分区截图。
    - 匹配交互边界。只实现已观察到的 hover/材质目标和响应；如果录屏没有显示网站级全局鼠标跟随物、泡泡、光圈或替换光标，就禁止添加。
    - 保持 section 分离。滚动/sticky 可以存在，但不能与前后 section 的卡片、tablet、CTA 或重要文案发生碰撞。
    - sticky 面板如果位于 CSS grid 或复杂布局容器中，必须做显式滚动 track/wrapper，并用多个 instant scroll 点验证内容不会裁切、碰撞或过早退出。
    - 检查污染：没有证据时，不得出现网格、渐变、卡片 bento、深色 app shell、3D 物体、终端 UI 等其它模板特征。
   - 在 `demo/implementation-notes.md` 记录实现说明。

7A. **当 9.8 以下评分进入平台期时升级实现策略**
   - 如果独立评分小于等于 9.8，且最近一次完整返工提分 `<= 0.5`，不要继续做小幅 CSS、文字、间距微调。必须把它视为当前方案平台期。
   - 下一轮返工必须根据失败维度选择至少一种更高杠杆、通用化的实现策略：
     - **资产保真升级**：当源站依赖复杂图片、图表、产品视觉、插画/图标系统、纹理场、媒体主导 hero 或视觉隐喻时，生成原创位图、SVG、矢量或 canvas 资产，不要用普通盒子粗略代替。
     - **运行时视觉系统升级**：当源站依赖 Canvas/WebGL/video、类 shader 表面、交互式光照、粒子/数据视觉、3D、PBR 贴图、GLB/GLTF、帧序列或 pointer/scroll 驱动的视觉响应时，构建合适的运行时渲染替代，并用多帧和对象级像素差异验证。可选技术包括 Three.js、Babylon.js、React Three Fiber、GLSL shader、原创 sprite/帧序列、CanvasTexture/程序 normal map、postprocessing 和轻量视频-like canvas。
     - **字形与排版升级**：当源站识别度依赖自定义展示字体、特殊字形、数字系统、可变字体或文字即视觉的处理方式时，用授权字体、SVG path、生成式字形节奏或 CSS 文本系统重建；不要用普通字体拉伸冒充。
     - **交互与滚动架构升级**：当源站依赖多步骤交互、sticky/pinned 区块、阶段式 reveal、carousel、timeline、模式切换或滚动联动叙事时，重建交互架构，包含明确状态轨道、进入/停留/退出状态和分阶段截图。
     - **组件与布局系统升级**：当差距来自跨页面组件缺失、信息密度、响应式行为、布局原语或状态覆盖不足时，重建可复用组件/布局系统，而不是只修一个截图。
   - 在 `qa/redo-report.md` 和 `demo/implementation-notes.md` 记录选择的升级策略、被放弃的弱策略、预期提分和验证计划。
   - 升级后重新跑完整证据、截图、交互、响应式、低动效偏好和独立仲裁流程。

8. **评分与门禁**
   - 把评分交给独立的 `08-final-arbiter` agent/subagent；它不能是生成分析或 demo 的同一个角色。
   - 最终仲裁员必须读取 `references/qa-scorecard.md`、`qa/blocking-rules.md`、所有 subagent findings、源码证据、交互证据和 demo verification。
   - 最终仲裁员亲自填写 `qa/scorecard.json`，包含分数、责任角色、证据、修复要求和 `scoring_review` 元数据。
   - 独立判断完成后，才运行 `scripts/score_extraction.py --scorecard qa/scorecard.json --out qa/release-decision.md`，用于计算加权总分并格式化发布决策。
   - 脚本只是计算器和格式化器，不能当成评分 reviewer，也不能替代独立 agent 判断。
   - 如果总分小于等于 9.8、最近一次完整返工提分大于 0.5，或存在任意阻断项，都不能视为完成。必须在 `qa/redo-report.md` 写明失败维度、失败角色、原因和精确修改要求。
   - 在 `qa/iteration-history.json` 记录每轮分数、相对上一轮的提分、阻断项和仲裁员的继续/停止判断。

## QA 评分维度

总分 10.0，除非用户给出更严格的 rubric，否则使用下面权重：

- 源站风格相似度：1.5
- 交互灵敏度与动效还原：1.0
- 动效/材质复杂度与滚动保真度：1.0
- 源代码证据覆盖度：1.1
- 生产可维护性：1.1
- 响应式视觉稳定性：1.1
- 可访问性：1.0
- 内容与品牌语气匹配：0.9
- 性能与运行稳定性：0.9
- 安全、隐私和版权安全：0.8
- 可复现性与产物完整度：0.6

发布规则：

- `score > 9.8`、无阻断项，且最近一次完整返工提分 `<= 0.5`：停止并发布。
- `score > 9.8`、无阻断项，且最近一次完整返工提分 `> 0.5`：再做一轮收敛验证，然后重评。
- `9.0 <= score <= 9.8` 且最近一次完整返工提分 `> 0.5`：继续定向返工，重评失败维度和受影响维度。
- `9.0 <= score <= 9.8` 且最近一次完整返工提分 `<= 0.5`：当前策略已进入平台期；必须升级到更强的资产、运行时视觉、字形排版、交互/滚动或组件/布局策略后再评分。
- `8.0 <= score < 9.0`：失败，定向返工后重评失败维度和受影响维度。
- `score < 8.0`：从源证据阶段整体重做。
- 任意阻断项：直接失败。

## 禁止行为

- 没有源/DOM/CSS/截图证据时，禁止推断技术网格、纸张网格、蓝图背景、bento grid、渐变光晕、深色 app shell 或 3D 场景。
- 禁止因为复用代码、fallback CSS、旧上下文或方便实现，把其它模板的视觉元素带进来。
- 禁止添加源码/录屏没有的网站级鼠标泡泡、全局 pointer follower、鼠标光圈、磁吸指针或指针跟随装饰层。录屏里的系统光标不算证据。
- 禁止添加大面积径向 hover glow 或伪元素 spotlight，让页面视觉上像存在 cursor bubble；即使 DOM 里没有 cursor 元素也不行。
- 禁止让 sticky/scroll section 与前一屏卡片、tablet、CTA 或重要文案重叠；必须测试多个滚动位置，不能只测顶部和最终 section。
- QA 中禁止信任 smooth-scroll 采样。测试时要强制 instant scroll 并记录实际 `scrollY`，因为平滑滚动会制造误导性的裁切截图。
- 禁止用普通字体拉伸或 transform-stretched text 代替源站自定义字形。
- 禁止用单个桌面截图证明完整风格系统。
- 禁止把单个采样页面描述成整个网站。必须写明路由覆盖范围和限制。
- 禁止盲目爬取所有 URL。必须使用页面类型采样、硬路由预算、去重和停止条件。
- 源站存在动效时，禁止跳过 hover、focus、mousemove、scroll、sticky、lazy-load、video、canvas 或 animation 测试。
- 没有多帧证据和对应 demo 实现时，动效分不得超过 7.0。
- 浏览器可访问的 seed/Tier A 路由缺少 frontend runtime audit 报告时，源代码证据覆盖度不得超过 8.0。
- 在浏览器可访问情况下缺少 computed-style、CSS rule、字体、network/resource、accessibility、performance 或 layout audit 证据时，源代码证据覆盖度不得超过 8.5。
- 当源站的核心 canvas/WebGL/video/材质/滚动行为缺失，或被轻微 CSS 漂移替代时，相似度不得超过 8.0。
- 当源站有真实 3D/PBR/GLB/法线贴图/帧序列证据，而 demo 用 2D 圆、平面网格、普通 CSS 渐变或只证明 canvas 非空来替代时，相似度不得超过 8.0，动效/材质复杂度不得超过 6.0。
- 没有记录运行时视觉层级和技术选型理由时，源代码证据覆盖度不得超过 8.5。
- 不要发布 `demo/` 目录里没有可运行 demo 文件的生成 skill。
- 禁止停在 9.0。目标是高于 9.8，并通过迭代收益收敛检查。
- 禁止因为最近一次提分很小，就在 score 小于等于 9.8 时停止或发布。低于 9.8 的低增益代表必须升级策略，不代表已经收敛。
- 当剩余差距需要资产、运行时视觉、字形排版、交互/滚动或组件/布局层面的更高阶策略时，禁止继续只做小幅 CSS 微调。
- 禁止同一个角色既生成 demo 又最终批准自己的结果。
- 禁止让实现、综合或 demo-review 角色给自己的工作打最终分；最终评分必须由独立最终仲裁 agent/subagent 完成。
- 禁止把运行 `score_extraction.py` 当作评分流程；它只能汇总独立仲裁员已经填写好的 scorecard。
- 禁止用“需要优化”这类空话掩盖失败原因。
- 禁止在公开 Skill 中暴露本地路径、私有截图、私有 token、凭据或用户专属部署信息。
- 禁止把生成 Skill 做成单个 `SKILL.md`；必须是完整文件夹。

## 资源文件

- 写 `style-analysis.json` 前先读 `references/analysis-schema.md`。
- 草拟生成 Skill 前先读 `references/style-skill-guidelines.md`。
- 给 demo 评分前先读 `references/qa-scorecard.md`。
- 评估 runtime/canvas/WebGL/3D/材质对象前先读 `references/runtime-visual-fidelity.md`。
- 在 seed 和 Tier A 路由上用 `scripts/frontend_runtime_audit.mjs` 采集 hydration 后前端 runtime 证据：DOM、computed styles、CSS rules、字体、network/resources、coverage、accessibility、performance、framework signals、布局溢出和控件清单。
- 可抓取目标 URL 时，用 `scripts/capture_source_evidence.py` 做初始源码采集。
- 分析完成后用 `scripts/style_skill_from_analysis.py` 生成完整 Skill 文件夹。
- 在 Tier A 视觉路由上用 `scripts/playwright_motion_capture.mjs` 录制浏览器 video、trace、截图、hover/mousemove/scroll 探针、reduced-motion 兜底证据和运行时视觉信号。
- 独立仲裁员完成评分后，才用 `scripts/score_extraction.py` 做最终加权计算和发布决策格式化。
