# QA 评分表

在根据生成风格 Skill 构建 demo 后，使用此评分表做发布门禁。评分必须由独立最终仲裁 agent/subagent 完成，不能由实现 agent 自评，也不能由评分脚本替代。

`scripts/score_extraction.py` 只是计算器和 Markdown 格式化器。只有当独立仲裁员已经审查证据、填写 `qa/scorecard.json` 并记录评分审查元数据后，才能运行它。

## 独立仲裁要求

- 仲裁员必须独立于负责风格提取、Skill 综合、demo 实现或 demo review 的 agent。
- 仲裁员必须检查源码证据、DOM/CSS 证据、动效证据、截图、demo notes 和所有 subagent findings。
- 仲裁员必须检查 seed 和 Tier A 路由的 frontend runtime audit 报告：hydration 后 DOM 清单、computed style 样本、CSS custom properties/rules、字体、scripts、network/resource inventory、JS/CSS coverage、accessibility tree 摘要、performance metrics、framework signals、forms/controls、布局溢出、文本裁切和 sticky/fixed 层。
- 对 Tier A 路由和任何存在动态行为的源站，仲裁员必须检查 Playwright 动效捕获产物：浏览器 video、trace zip、截图、JSON 报告、hover/mousemove/scroll 探针、运行时信号报告，以及相关时的 reduced-motion 捕获。
- 仲裁员必须检查 `references/page-inventory.json`，确认提取结果属于站点级、部分站点还是页面级。
- 仲裁员必须打开或运行实际的 `demo/index.html` 文件，并在桌面、平板和移动尺寸下检查 demo。
- 当源站包含 canvas/WebGL/video/材质/滚动动效时，仲裁员必须检查多帧、视频帧或像素差异证据。只看 DOM computed style 不足以批准动效。
- 当源站包含真实 3D、PBR、GLB/GLTF、法线/粗糙度/反射贴图、帧序列或视频级视觉时，仲裁员必须检查 `runtime_visual_system` 和 `references/runtime-visual-fidelity.md`，确认 demo 技术栈达到最低层级。
- 3D/材质对象必须做对象级比较：体积轮廓、方向性高光、明暗交界、接触阴影、遮挡/z-depth、纹理曲率和多帧变化。非空 canvas 或像素有变化不能单独证明通过。
- 如果用户提供录屏，仲裁员必须检查从录屏抽取的代表帧，并明确比较 demo 与用户可见行为是否一致。
- 仲裁员必须检查是否越界添加：源码证据没有的网站级鼠标跟随泡泡、光圈、装饰覆盖层或字体替代。
- 即使 DOM 里没有 cursor 元素，也必须检查视觉越界：大面积径向光晕、伪元素 spotlight、canvas halo 只要跟随鼠标，就按鼠标效果处理。
- 仲裁员必须检查多个滚动位置，重要卡片、tablet、控件或文本发生碰撞时必须判失败。
- 仲裁员必须在 QA 时强制 instant scroll，记录实际 `scrollY`，并检查 sticky/scroll track 是否会造成裁切或过早退出。
- 仲裁员必须纳入用户校准。如果用户手动给上一版 demo 约 8 分或明确否定某些缺陷，在这些缺陷修复并复测前，不能给出高于 9.8 的发布分。
- 仲裁员必须为每个维度填写数字分数、责任 subagent、证据和必要修复动作。
- scorecard 必须包含 `scoring_review.arbiter_role`、`scoring_review.independent_from`、`scoring_review.evidence_reviewed`、`scoring_review.demo_reviewed` 和 `scoring_review.judgment_notes`。
- 没有独立审查就运行脚本，属于无效 QA。

## 加权维度

| 维度 | 权重 | 通过标准 |
|---|---:|---|
| 源站风格相似度 | 1.5 | 布局节奏、层级、配色、字体、组件语言和气质与证据一致，但不克隆。 |
| 交互灵敏度与动效还原 | 1.0 | hover、focus、mousemove、scroll、timing、easing 和动态变化与已观察源站行为一致。 |
| 动效/材质复杂度与滚动保真度 | 1.0 | canvas/WebGL/video-like 视觉、材质/高光行为、持续动效、sticky/scroll 叙事和多帧节奏要匹配源站感知复杂度。 |
| 源代码证据覆盖度 | 1.1 | 判断由源 HTML/CSS/JS、DOM、computed styles、截图或明确推断支撑。 |
| 生产可维护性 | 1.1 | 组件、tokens、命名、状态和响应式规则足够清晰，可进入真实前端工作流。 |
| 响应式视觉稳定性 | 1.1 | 桌面、平板和移动端没有重叠、不可读文本、坏控件或横向溢出。 |
| 可访问性 | 1.0 | 语义、键盘、焦点、对比度、动效偏好和文本可读性达标。 |
| 内容与品牌语气匹配 | 0.9 | 文案风格和信息密度符合源站类别，不暴露内部流程说明。 |
| 性能与运行稳定性 | 0.9 | 动画成本、媒体体积、加载行为和异常状态合理。 |
| 安全、隐私和版权安全 | 0.8 | 无危险脚本、私有数据、未授权资产、复制 logo 或隐藏追踪。 |
| 可复现性与产物完整度 | 0.6 | 工作目录、证据、QA 文件和源码限制记录完整且可复现。 |

## 发布门禁

- `score > 9.8`、无阻断项，且最近一次完整返工提分 `<= 0.5`：停止并发布。
- `score > 9.8`、无阻断项，且最近一次完整返工提分 `> 0.5`：再做一轮收敛验证，然后重评。
- `9.0 <= score <= 9.8` 且最近一次完整返工提分 `> 0.5`：继续定向返工；修复失败维度和受影响维度。
- `9.0 <= score <= 9.8` 且最近一次完整返工提分 `<= 0.5`：视为策略平台期，不是收敛。升级实现策略后再重评。
- `8.0 <= score < 9.0`：失败；修复失败维度和受影响维度。
- `score < 8.0`：失败；回到源证据阶段重新生成。
- 任意阻断项：失败，不看总分。

策略平台期升级：

- 分数小于等于 9.8 且最近一轮提分很小，不是停止理由，而是说明当前方案已经不再有效。
- 下一轮返工不能继续把小幅 CSS、文字、间距微调当作主要修复方案。
- 必须根据失败维度选择至少一种更强策略：
  - 为复杂图片、图表、产品视觉、插画/图标系统、纹理场、媒体主导 hero 或视觉隐喻做资产保真升级
  - 为 Canvas/WebGL/video、类 shader 表面、交互式光照、粒子/数据视觉、3D 或 pointer/scroll 驱动视觉响应做运行时视觉系统升级
  - 为自定义展示字体、特殊字形、数字系统、可变字体或文字即视觉的处理方式做字形与排版升级
  - 为多步骤交互、sticky/pinned 区块、阶段式 reveal、carousel、timeline、模式切换或滚动联动叙事做交互与滚动架构升级
  - 为跨页面组件缺失、信息密度、响应式行为、布局原语或状态覆盖不足做组件与布局系统升级
- 在 `qa/redo-report.md` 记录选择的升级策略、被放弃的弱策略、预期提分和验证计划。

硬性封顶规则：

- 如果缺少 `demo/index.html`、`demo/styles.css` 或 `demo/script.js`，可复现性最高 5.0，并且发布失败。
- 如果 Skill 声称做了全站提取，但只采样了一个公开路由，源代码证据覆盖度最高 7.0，内容与品牌语气匹配最高 8.0，直到缩小声明或扩大路由采样。
- 如果缺少 `references/page-inventory.json`，源代码证据覆盖度最高 8.0，因为无法审计页面覆盖。
- 如果浏览器可访问的 seed/Tier A 路由缺少 frontend runtime audit 报告，源代码证据覆盖度最高 8.0，性能与运行稳定性最高 8.0。
- 如果在浏览器可访问情况下缺少 computed style 样本、CSS custom properties/rules、字体清单或 network/resource inventory，源代码证据覆盖度最高 8.5。
- 如果在浏览器可访问情况下缺少布局溢出/文本裁切/control inventory 或 accessibility tree 摘要，响应式稳定性和可访问性最高 8.5。
- 如果 JS/CSS coverage 不可用且没有写明被阻挡，源代码证据覆盖度最高 8.8，性能与运行稳定性最高 8.5。
- 如果源站明显使用 canvas/WebGL/video/材质动效，而 demo 只有静态卡片或很轻的 CSS 漂移，相似度最高 8.0，动效/材质复杂度最高 6.0。
- 如果源站有真实 3D/PBR/GLB/法线贴图/帧序列证据，但 demo 用 2D 圆形、普通渐变、平面网格、静态贴片或只证明 canvas 非空来替代，相似度最高 8.0，动效/材质复杂度最高 6.0。
- 如果没有记录运行时视觉层级和技术选型理由，源代码证据覆盖度最高 8.5。
- 如果动效证据没有至少三个时间采样或等价的视频/像素差异记录，交互灵敏度和动效/材质复杂度最高 7.0。
- 如果 Tier A 路由证据或用户报告的动态行为缺少 Playwright video/trace，或缺少等价的 hover、mousemove、instant-scroll、timed-frame 浏览器自动化录制证据，交互灵敏度和动效/材质复杂度最高 7.0，源代码证据覆盖度最高 8.5。
- 如果 reduced-motion 行为相关但没有 reduced-motion 浏览器捕获或 fallback 验证，可访问性最高 8.0，动效/材质复杂度最高 8.0。
- 如果用户报告的交互没有被复现，仲裁员必须要求定点复测，不能直接当作缺失。
- 如果 demo 添加源码证据没有的网站级鼠标跟随物、泡泡、光圈或 pointer overlay，交互灵敏度最高 7.5；当用户明确否定该效果时，这是阻断项。
- 如果 demo 通过 CSS、canvas、SVG 或伪元素添加视觉上跟随鼠标的 halo/spotlight，即使 DOM 里没有 cursor 元素，也按鼠标跟随物同样封顶。
- 如果正常滚动时独立卡片、tablet、控件或文本重叠，响应式视觉稳定性最高 7.0，且这是阻断项。
- 如果 sticky/scroll 面板因为滚动轨道太短或未测试导致重要内容被裁切或过早退出，响应式视觉稳定性最高 8.0，滚动保真度最高 8.0。
- 如果用普通字体拉伸替代源站自定义字形，相似度最高 8.0。
- 如果用户给过上一轮较低人工分，最终分数只能通过和该反馈绑定的修复证据逐步提高；不能从被否定的约 8 分 demo 直接跳到发布级满分附近。

## 迭代停止规则

每一轮评分必须写入 `qa/iteration-history.json`。

只有同时满足下面条件时才能停止：

- 最新分数高于 9.8
- 没有阻断项
- 最近一次完整返工提分不超过 0.5

如果分数已经高于 9.8，但最近一次返工提分超过 0.5，必须再做一轮迭代来证明结果已经收敛。

如果分数小于等于 9.8，且最近一次完整返工提分不超过 0.5，说明还没有收敛。必须标记当前方案平台期，并要求策略升级。

## 失败说明要求

每个失败维度必须包含：

- 责任 subagent
- 失败的产物或流程环节
- 证明失败的证据
- 精确修复动作
- 必须复查的范围
- 当 score 小于等于 9.8 且 delta `<= 0.5` 时，必须写明选择的通用升级策略，以及为什么继续小幅 CSS 微调不够
