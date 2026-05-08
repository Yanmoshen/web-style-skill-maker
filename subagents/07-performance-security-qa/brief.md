# 07 性能与安全 QA

范围：检查运行成本、隐私、安全和版权。

必须完成：

- 审查资源体积、图片/视频使用、字体加载、动画成本、layout thrash 风险和异常状态。
- 使用 frontend runtime audit 报告检查 network/resource summary、performance metrics、JS/CSS coverage、失败请求、第三方域名、字体/视频/图片体积、framework signals、storage key names 和布局溢出证据。
- 检查第三方资源、外链、用户输入、注入 HTML、telemetry、密钥、私有数据和许可证敏感资产。
- 标记专有截图、logo、原文案或付费字体，除非用户明确拥有授权。

禁止：

- 禁止为了相似度批准未授权源站资产。
- audit 报告显示 JS/CSS coverage 差、请求失败或 runtime 资源过大时，禁止忽略。
- 禁止忽略外部脚本或隐藏追踪。

输出：`subagents/07-performance-security-qa/findings.md`。
