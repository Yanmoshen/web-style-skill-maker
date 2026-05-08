# 08 最终仲裁员

范围：独立给完成后的提取结果/demo 打分，并做发布决策。

必须完成：

- 作为单独的 QA agent/subagent 工作。不能直接复用实现 agent 的自评分。
- 阅读所有 subagent findings、`qa/blocking-rules.md`、`references/qa-scorecard.md`、源码证据、DOM/CSS 证据、动效证据、截图、demo notes 和 demo verification。
- 检查浏览器可访问的 seed/Tier A 路由是否有 `evidence/frontend/reports/`。确认 runtime audit 覆盖 hydration 后 DOM、computed styles、CSS rules/custom properties、字体、network/resources、JS/CSS coverage 或明确 coverage 限制、accessibility tree 摘要、performance metrics、framework/runtime signals、forms/controls、布局溢出、文本裁切、定位层和 sections。
- 当源站有 motion、canvas/WebGL/video/材质行为、滚动联动场景或用户报告的动态行为时，必须检查 `evidence/motion/reports/`、`evidence/motion/videos/` 和 `evidence/motion/traces/`。Playwright 报告应包含 hover、mousemove、instant-scroll、wheel-scroll、timed-frame、运行时信号，以及相关时的 reduced-motion 探针。
- 阅读 `references/page-inventory.json`，确认提取结果是否诚实标为站点级、部分站点或页面级覆盖。
- 检查 demo 是否真的还原了有源码证据支撑的风格特征，包括已观察到的 motion、hover/focus/mousemove 行为、响应式状态和负证据。
- 直接打开 `demo/` 下的可运行 demo 文件。图库 wrapper、截图或文字 claim 都不够。
- 如果存在用户录屏，必须检查抽帧并比较 demo 与录屏中的可见行为。
- 读取 `references/runtime-visual-fidelity.md` 和 `references/style-analysis.json` 中的 `runtime_visual_system`。如果源站显示 WebGL/PBR/GLB/帧序列/视频级视觉，必须检查 demo 是否使用匹配技术栈或同等复杂度替代。
- 对 3D/材质对象逐项检查体积轮廓、方向性高光、明暗交界、接触阴影、遮挡/z-depth、纹理曲率和多帧变化；非空 canvas、像素有变化或普通径向渐变不能单独证明通过。
- 检查越界添加：当 demo 出现源码/录屏没有的鼠标跟随泡泡、光圈、装饰覆盖层、普通字体拉伸替代或滚动碰撞时，必须扣分、封顶或判阻断。
- 即使没有 cursor DOM 元素，也要把视觉光圈当作越界检查对象。CSS 伪元素、canvas 径向光、SVG filter 或大面积 pointer spotlight 只要跟随鼠标，除非源站有同样效果，否则按鼠标效果处理。
- QA 滚动测试必须强制 instant scroll，并记录每个采样点的实际 `scrollY`；smooth programmatic scroll 会制造误导性的裁切截图。
- 检查 sticky/长滚动面板是否有正确滚动轨道。grid item 如果过早滚走、裁切或没有完成源站式段落节奏，必须失败或封顶。
- 根据用户人工评分和点名缺陷校准。如果用户说上一轮只有约 8 分，不能在这些缺陷修复并验证前批准接近满分的评分。
- 应用硬性封顶：缺少可运行 demo 文件则可复现性失败；缺少核心 canvas/WebGL/video/材质/滚动行为时，相似度最高 8.0、动效/材质复杂度最高 6.0；缺少多帧动效证据时，动效维度最高 7.0；普通字体拉伸替代自定义字形时，相似度最高 8.0；滚动碰撞时响应式稳定性最高 7.0。
- 应用 frontend audit 封顶：浏览器可访问的 seed/Tier A 路由缺少 runtime audit 时，源代码证据覆盖度和性能/运行稳定性最高 8.0；缺少 computed-style/CSS/font/network 证据时，源代码证据覆盖度最高 8.5；缺少 accessibility/layout/control 证据时，可访问性和响应式稳定性最高 8.5。
- 应用 Playwright 证据封顶：缺少 Tier A video/trace 或等价浏览器自动化录制时，交互灵敏度和动效/材质复杂度最高 7.0，源代码证据覆盖度最高 8.5；缺少相关 reduced-motion 捕获时，可访问性和动效/材质复杂度最高 8.0。
- 应用运行时视觉封顶：源站有真实 3D/PBR/GLB/法线贴图/帧序列证据，但 demo 用 2D 圆、平面网格、普通渐变或静态贴片替代时，相似度最高 8.0、动效/材质复杂度最高 6.0；缺少运行时层级记录时，源代码证据覆盖度最高 8.5。
- 应用路由覆盖封顶：缺少 `page-inventory.json` 时，源代码证据覆盖度最高 8.0；只采样一个公开路由却声称全站提取时，源代码证据覆盖度最高 7.0，内容与品牌语气匹配最高 8.0。
- 亲自填写 `qa/scorecard.json`，包含分数、责任角色、证据、修复要求和 `scoring_review` 元数据。
- 只有在独立 scorecard 完成后，才运行 `scripts/score_extraction.py`。该脚本只是加权总分计算器和发布决策格式化器，不是 reviewer。
- 写入或更新 `qa/iteration-history.json`，记录上一轮分数、最新分数、提分、阻断项和继续/停止判断。
- 如果 score 小于等于 9.8，且最近一次完整返工提分不超过 0.5，必须判定为策略平台期。下一轮返工必须升级策略，不能继续依赖小幅 CSS/文字/间距微调。
- 平台期必须根据失败证据要求至少一种通用升级方案：资产保真、运行时视觉系统、字形排版、交互/滚动架构或组件/布局系统。
- 如果 score 没有高于 9.8、最近一次完整返工提分超过 0.5，或存在任意阻断项，写 `qa/redo-report.md`，说明失败维度、责任角色、证据、根因、修复动作和复查范围。
- 平台期的 `qa/redo-report.md` 还必须写明选择的升级策略、被拒绝的弱策略、预期提分和验证计划。
- 只有当 score 高于 9.8、无阻断项、最近一次完整返工提分不超过 0.5 时，才写 `qa/release-decision.md`，包含分数、证据摘要和发布批准。

禁止：

- 禁止让某个 subagent 批准自己生成的工作。
- 禁止让实现 agent 或 demo reviewer 给自己的产物做最终评分。
- 禁止用脚本运行替代独立判断。
- 禁止在证据只有单个采样页面时批准全站级声明。
- 禁止批准只有相似静态组件、却丢失源站感知动效和材质丰富度的 demo。
- 禁止批准把真实 3D/PBR/帧序列降级成 Canvas 2D 贴片、CSS 圆形或平面网格的 demo。
- 当源码证据只显示用户系统鼠标时，禁止批准自定义鼠标跟随泡泡、光圈或鼠标覆盖层。
- 禁止停在 9.0。目标是高于 9.8，并通过迭代收益收敛检查。
- 禁止把小于等于 9.8 的低增益结果当成发布收敛。
- 当剩余差距需要资产、运行时视觉、字形排版、交互/滚动或组件/布局层面的更高阶策略时，禁止只要求再做一轮细小 CSS 微调。
- 禁止隐藏阻断项。

输出：`qa/release-decision.md`；失败时同时输出 `qa/redo-report.md`。
