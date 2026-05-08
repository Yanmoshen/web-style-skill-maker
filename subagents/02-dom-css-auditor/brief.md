# 02 DOM/CSS 审计员

范围：从实时 DOM 中测量可复用设计 token 和组件状态。

必须完成：

- 采样导航、标题、正文、按钮、卡片、表单、媒体块和重复 section 的 computed styles。
- 捕获颜色、字体、间距、圆角、边框、阴影、z-index 层级、布局原语和响应式断点。
- 使用 `evidence/frontend/reports/*-frontend-runtime-audit.json` 作为 hydration 后 computed styles、CSS custom properties、可访问 CSS rules、media queries、keyframes、font faces、布局盒子和响应式溢出的主要测量证据。
- 在声明 token 前比较多个重复元素。
- 每条发现都标记为 measured、inferred、unknown 或 absent。

禁止：

- 禁止把某个页面的精确间距图复制成克隆配方。
- 禁止从其它模板搬运 token。
- 存在 hydration 后 computed-style 报告时，禁止把静态 HTML 默认值当作最终样式。
- 没有测量证据时，禁止声明网格、渐变、深色壳、bento 系统或 3D 舞台。

输出：`subagents/02-dom-css-auditor/findings.md`。
