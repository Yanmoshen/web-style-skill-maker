# 03 视觉与动效审计员

范围：跨设备验证构图和动态行为。

必须完成：

- 读取 `references/page-inventory.json`，按选中路由的分层执行。
- Tier A：对 3-5 个视觉差异最大的选中路由捕获 1440x900、1024x768、390x844 截图，并在可用时捕获首屏和至少两个下方 section。
- 每个浏览器可访问的 Tier A 路由，都运行 `node scripts/playwright_motion_capture.mjs --url <route-url> --out <front-site>/evidence/motion --label <route-slug> --viewports 1440x900,1024x768,390x844`。
- 默认保持 Playwright video 和 trace 录制开启。证据包必须包含截图、视频、trace、每个 viewport 的 JSON 报告、hover 探针、mousemove/timed frames、instant-scroll 样本、wheel-scroll 样本和运行时信号报告，并保存到 `evidence/motion/`。
- 如果源站存在动效或用户报告动态行为，至少对桌面和移动端运行一次 `--reduced-motion` 采样。
- Tier B：对最多 5 个额外选中路由捕获桌面首屏和一个下方 section，并做快速 DOM/computed-style 检查。
- Tier C：其余已发现路由只进入清单，除非发现独特模板、资产系统或动效线索。
- 在 Tier A 路由上测试 hover、focus、mousemove、scroll、sticky 元素、菜单状态、懒加载媒体、carousel、video、canvas 和 timed animations。
- 可行时使用前后截图或像素对比记录视觉变化。
- 对 canvas/WebGL/video/Framer/Lottie/GSAP/材质效果，至少记录三个时间采样帧，或等价的视频/像素差异产物。
- 检查并记录运行时视觉层级：CSS/SVG、Canvas 2D、WebGL/Three/Babylon/R3F、帧序列或 video-motion。证据包括 canvas 上下文、runtime bundle、`.glb/.gltf/.hdr/.ktx2/.basis/.wasm`、`normal/roughness/diffuse/albedo/reflection/displacement` 贴图、连续编号帧和视频资源。
- 对 3D/PBR/材质对象做对象级比较：体积轮廓、方向性高光、明暗交界、接触阴影、遮挡/z-depth、纹理是否随曲率弯曲、多帧运动或光照变化。只证明 canvas 非空不算通过。
- 如果用户报告 hover、pointer、材质、颜色、光照或特定位置触发效果，必须在对应滚动位置和坐标做定点探针，再决定是否标记为缺失。
- 区分 DOM/CSS 证据和渲染像素证据。computed style 没变化，不能证明 canvas 或 shader-like 动效不存在。
- 记录 observed absences。

禁止：

- 禁止把静态截图当作“没有动效”的证明。
- 源站存在指针响应效果时，禁止跳过 mousemove 或 hover 采样。
- 不要在没有帧证据的情况下，把明显丰富的 runtime 动效降级成“轻微 CSS 动画”。
- 禁止把 WebGL/PBR/帧序列/视频级视觉降级成 2D 圆、平面网格、普通渐变或静态贴片。
- 禁止隐藏未测试的交互。
- 没有 Playwright video/trace 证据或等价浏览器自动化录制时，禁止声称高动效保真。
- 禁止对每个发现 URL 都做完整多视口动效 QA；必须使用路由分层，并记录覆盖取舍。
- 如果只视觉采样了一个页面，禁止把结果称为站点级覆盖。

输出：`subagents/03-visual-motion-auditor/findings.md`，以及 `evidence/screenshots/` 和 `evidence/motion/` 中的文件。
