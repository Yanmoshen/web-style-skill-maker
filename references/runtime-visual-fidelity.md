# 运行时视觉保真规则

用于判断源站的视觉是否需要 CSS、SVG、Canvas 2D、WebGL/Three.js、帧序列或视频级实现。这个文件是通用规则，不针对某一个网站。

## 先识别运行时层级

把每个核心视觉对象归入一个最低可接受实现层级，并写入 `references/style-analysis.json`：

- `css-static`：主要由颜色、排版、边框、阴影、普通图片和布局构成。CSS/HTML 足够。
- `svg-vector`：核心识别来自矢量字形、路径、图标、描边动画或几何插画。优先 SVG/path/mask/filter。
- `canvas-2d`：核心识别来自 2D 程序纹理、粒子场、像素绘制、平面噪声或非真实光照材质。Canvas 2D 足够。
- `webgl-3d`：核心识别来自真实体积、相机、透视、PBR 材质、法线/粗糙度贴图、环境反射、GLB/GLTF、深度遮挡或交互光照。必须使用 WebGL/Three.js/Babylon/React Three Fiber 等 3D 栈，除非明确选择原创高保真帧序列替代。
- `frame-sequence`：核心识别来自大量连续图片帧、sprite、滚动帧动画或预渲染 3D。可以用原创帧序列、视频-like sprite 或 canvas 图像序列重建。
- `video-motion`：核心识别来自视频、实拍/渲染短片或视频遮罩。可用原创视频、帧序列、canvas 合成或同等复杂度 runtime 替代。

## 源证据触发信号

看到下面任一信号时，必须升级分析深度，不能只看截图或 DOM：

- `<canvas>`、WebGL 上下文、Three/Babylon/R3F/GSAP/Lenis/Lottie/Rive/Framer runtime。
- `.glb`、`.gltf`、`.bin`、`.hdr`、`.exr`、`.ktx2`、`.basis`、`.wasm`。
- asset 名称包含 `normal`、`roughness`、`metalness`、`diffuse`、`albedo`、`ao`、`reflection`、`displacement`、`bump`。
- `/frames/`、`sequence`、`sprite`、连续编号图片、几十到几百张 webp/png/jpg。
- 录屏中可见的体积物体、材质高光、表面纹理随曲率变形、接触阴影、遮挡层级或镜头/滚动驱动的视觉变化。

## 浏览器证据

只要 Tier A 路由可被浏览器打开且可能存在 runtime 视觉，就使用 `scripts/playwright_motion_capture.mjs`。必须保留 video、trace、截图、JSON 报告、hover/mousemove 探针、instant-scroll 样本、wheel-scroll 样本、timed frames、运行时信号报告，以及相关时的 reduced-motion 采样。只有当浏览器捕获和源码资产证据都支持降级时，才能降低运行时层级。

## 技术选型矩阵

- CSS/HTML：适合静态布局、普通卡片、按钮、文字、平面色块和简单过渡。
- SVG：适合标志性线稿、路径字形、图案遮罩、描边动画和可缩放几何图形。
- Canvas 2D：适合织物噪声、平面纹理、粒子、手绘/数据场、非真实 3D 的材质暗示。
- Three.js / Babylon.js / React Three Fiber：适合球体、布料、产品模型、相机透视、PBR、法线贴图、环境反射、投影、遮挡和真实 3D 交互。
- GLSL shader / WebGL material：适合类 shader 表面、折射、流体、反射、扫描线、法线扰动和程序材质。
- 帧序列 / sprite / video-like canvas：适合源站用预渲染图片序列表达高复杂度 3D 或布料动画，但不允许直接复制源站帧，除非用户拥有授权。

## 3D / 材质对象验收

如果源站核心对象读作 3D 或 PBR 材质，demo 至少要满足多数项目：

- 有稳定、可信的体积轮廓，而不是被 clip 的 2D 贴片。
- 有方向性高光、明暗交界、暗部和反射/环境光层次。
- 有接触阴影或投影，能看出对象在空间中的前后关系。
- 纹理随曲率、透视或法线变化弯曲；不能是穿过圆形的均匀平面网格。
- 有遮挡和 z-depth：前景/背景对象互相遮挡，不能像贴纸叠在背景上。
- 多帧采样能看到旋转、漂浮、光照、帧序列或材质变化。
- reduced-motion 下仍保留高保真静态构图。

## QA 封顶

- 源站有 `webgl-3d` / PBR / GLB / 法线贴图 / 真实体积证据，但 demo 只用 Canvas 2D 圆、CSS 圆、平面网格或普通渐变替代：源站风格相似度最高 8.0，动效/材质复杂度最高 6.0。
- 源站有 `frame-sequence` 或 `video-motion` 证据，但 demo 没有多帧或同等 runtime 替代：交互灵敏度最高 7.0，动效/材质复杂度最高 6.5。
- 没有记录运行时层级和技术选型理由：源代码证据覆盖度最高 8.5。
- 动态 Tier A 路由缺少 Playwright video/trace 或等价浏览器自动化录制：交互灵敏度和动效/材质复杂度最高 7.0，源代码证据覆盖度最高 8.5。
- 用户录屏清楚显示 3D/材质效果，而 demo 没有按录屏做定点比较：不能发布。
- 只能通过“非空 canvas”不能证明通过；必须有对象级像素/截图比较，例如体积、阴影、纹理曲率和多帧变化。
