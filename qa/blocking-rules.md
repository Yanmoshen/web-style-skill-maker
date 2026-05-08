# 阻断规则

命中任意一项时，生成的 Skill 和 demo 直接失败，不看总分：

- 用户明确要求的视觉或交互需求缺失。
- 源站风格被严重误判。
- demo 出现源证据没有支持的视觉特征，例如凭空出现网格、渐变、深色壳、bento 布局或 3D 场景。
- 浏览器可访问的 seed/Tier A 路由缺少 frontend runtime audit 报告，包括 hydration 后 DOM、computed styles、CSS/font/network/resource 证据、accessibility 摘要、performance metrics、布局溢出和 framework/runtime signals。
- demo 添加源码/录屏没有的网站级鼠标跟随泡泡、光圈、磁吸指针或 pointer overlay，尤其是用户已经明确否定该效果时。
- demo 使用 CSS/canvas 伪光圈、径向 hover glow 或大面积 pointer spotlight，在视觉上表现得像自定义鼠标效果，但没有源站证据。
- 移动端或桌面端核心路径不可用。
- 文本、控件或媒体明显重叠、溢出或被裁切。
- 正常滚动时重要卡片、tablet、控件或文本互相碰撞。
- sticky 或长滚动面板因为没有实现/测试滚动轨道而裁切、过早退出或露出异常状态。
- 用普通字体拉伸替代源站自定义字形。
- 源站关键 hover、mousemove、scroll 或 timed motion 没有测试。
- Tier A 动态路由缺少 Playwright video/trace 捕获，或缺少等价的 hover、mousemove、instant-scroll、wheel-scroll、timed-frame 浏览器自动化录制证据。
- 源站有明显 canvas/WebGL/video/材质/滚动动效，但 demo 只有静态面板或很轻的 CSS 漂移。
- 源站有真实 3D/PBR/GLB/法线贴图/粗糙度贴图/反射贴图/帧序列证据，但 demo 用 2D 圆形、普通渐变、平面网格、静态贴片或只证明 canvas 非空来冒充。
- 缺少运行时视觉层级记录，导致 WebGL/帧序列/视频级视觉被降级成 CSS 或 Canvas 2D。
- 用户报告的 hover、pointer、材质、颜色、光照或特定位置触发效果没有经过定点复测就被否定。
- `demo/` 下缺少可运行 demo 文件。
- 缺少 QA 证据。
- 暴露本地路径、凭据、私有 URL 或用户专属部署数据。
- 使用未授权 logo、截图、插画、付费字体或原文案。
- 生成 Skill 是单个 `SKILL.md`，而不是 `front-<site-slug>` 文件夹。
- 分数小于等于 9.8 就当成完成，或跳过迭代收益收敛规则。
- 分数小于等于 9.8 且最近一次完整返工提分 `<= 0.5` 时，被当作收敛，而不是触发策略升级。
- 平台期返工仍然只做小幅 CSS/文字/间距微调，而失败证据实际需要更强的资产、运行时视觉、字形排版、交互/滚动或组件/布局策略。
- 忽略用户给出的低分或明确否定意见，继续把最终分数校准到接近满分。
