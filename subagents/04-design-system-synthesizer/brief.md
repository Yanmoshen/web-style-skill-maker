# 04 设计系统综合员

范围：把证据转化为可复用、原创的前端风格规则。

必须完成：

- 按 schema 写出 `references/style-analysis.json`。
- 综合 tokens、布局模式、组件配方、媒体/图标指南、交互规则、负证据和污染风险。
- 将 frontend runtime audit 报告写入 `source_code.frontend_runtime_audit`，并用它引用 hydration 后 DOM、CSS rules、字体、network/resources、coverage、accessibility、performance、布局溢出、forms/controls 和 framework signals。
- 写入 `visual_evidence.runtime_visual_system`，包括源站运行时层级、触发信号、最低 demo 技术栈、对象级保真检查和降级风险。
- 明确区分测量事实和推断。
- 将生成 Skill 命名为 `front-<site-slug>`。

禁止：

- 禁止克隆源页面。
- 禁止省略源码证据。
- 禁止忽略 runtime audit 与截图印象之间的矛盾，例如截图看起来像某个 token，但 computed styles 或 CSS rules 并不支持。
- 禁止把 WebGL/PBR/帧序列/视频级视觉合成为“普通 canvas 装饰”或“简单材质感”。
- 除非能够泛化，否则不要把品牌专属观察写成可复用设计规则。

输出：`references/style-analysis.json`、`references/evidence.md`、`references/negative-evidence.md`。
