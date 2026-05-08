# 01 源码审计员

范围：在视觉综合之前，先采集源码层面的证据。

必须完成：

- 把用户提供的 URL 当作 seed route。从 anchors、导航/页脚链接、canonical/alternate links、`robots.txt` sitemap 声明、`/sitemap.xml` 和可见 route manifest 中发现同站候选路由。
- 建立 `references/page-inventory.json`，记录候选路由、发现来源、页面 archetype、优先级、是否选中、跳过原因和访问限制。
- 选择有边界的代表集合：默认 6-10 个公开路由，硬上限 12 个。优先选择不同页面 archetype，而不是很多相似 URL。
- 抓取 seed route 和选中代表路由的主 HTML 和可访问同源 CSS。
- 记录 stylesheet URL、inline style、CSS variables、keyframes、media queries、font declarations、SVG/icon 用法、asset 引用、共享 bundle 和路由专属 bundle。
- 在浏览器中检查 seed route 和最高优先级页面 archetype 的 hydration 后 DOM，并保存关键结构片段。
- 对 seed route 和每个浏览器可访问的 Tier A 路由，运行 `node scripts/frontend_runtime_audit.mjs --url <route-url> --out <front-site>/evidence/frontend --label <route-slug> --viewports 1440x900,1024x768,390x844`。
- 保留 runtime audit JSON 报告，覆盖 hydration 后 DOM 清单、computed style 样本、CSS rules/custom properties、media queries、keyframes、font faces、scripts/links、图片/背景图、canvas/video 清单、network/resources、JS/CSS coverage、accessibility tree 摘要、performance metrics、framework/runtime signals、forms/controls、布局溢出、文本裁切、定位层和 section boxes。
- 记录被阻止的源码文件、压缩 bundle、反爬、登录墙或缺失 source map。

禁止：

- 禁止从截图推断视觉特征。
- 禁止把压缩 class name 当作设计 token。
- 禁止省略负面发现。
- 当网站会 hydration 或 lazy-load UI 时，禁止用静态 HTML 替代浏览器 runtime 证据。
- 禁止只采样一个页面就声称覆盖了整个网站。
- 除非用户明确授权且安全，禁止跟进 private、account、checkout、admin、auth、query-heavy、search-result 或可能产生副作用的路由。
- 禁止盲目爬取所有发现 URL；必须聚类，并在达到路由预算或“无新增设计信号”停止条件时收手。

输出：`subagents/01-source-code-auditor/findings.md`、`references/page-inventory.json`，以及 `evidence/source/`、`evidence/css/`、`evidence/dom/`、`evidence/routes/` 和 `evidence/frontend/` 中的证据文件。
