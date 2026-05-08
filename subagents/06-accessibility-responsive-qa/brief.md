# 06 可访问性与响应式 QA

范围：验证多设备和辅助路径下的可用性。

必须完成：

- 检查桌面、平板、移动端是否有重叠、溢出、文本裁切、不可达控件和布局跳动。
- 检查键盘导航、焦点状态、语义 landmark、button/link 角色、文本对比度、减少动效兼容和可读字号。
- 当源站或 demo 动效相关时，使用 Playwright 动效证据，或重新运行 `scripts/playwright_motion_capture.mjs --reduced-motion`；滚动检查必须使用多个 instant-scroll 位置，而不是依赖 smooth scroll。
- 记录截图和失败位置。

禁止：

- 禁止用单一 viewport 代表所有 viewport 通过。
- 禁止批准隐藏溢出或只在某一个宽度下能放得下的文本。

输出：`subagents/06-accessibility-responsive-qa/findings.md`。
