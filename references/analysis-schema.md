# 风格分析 Schema

使用这个结构编写 `references/style-analysis.json`。内容必须基于证据；每个关键判断都要能追溯到源码、DOM、CSS、截图或交互证据。

```json
{
  "source": {
    "url": "https://example.com",
    "site_name": "Example",
    "site_slug": "example",
    "output_folder": "front-example",
    "captured_at": "YYYY-MM-DD",
    "viewports": ["1440x900", "1024x768", "390x844"],
    "limitations": []
  },
  "source_code": {
    "html_files": [],
    "css_files": [],
    "script_files": [],
    "font_files": [],
    "asset_files": [],
    "css_variables": [],
    "media_queries": [],
    "keyframes": [],
    "dom_landmarks": [],
    "evidence_files": [],
    "frontend_runtime_audit": {
      "reports": [],
      "hydrated_dom_reports": [],
      "computed_style_reports": [],
      "network_reports": [],
      "resource_inventory_reports": [],
      "coverage_reports": [],
      "font_reports": [],
      "css_rule_reports": [],
      "accessibility_reports": [],
      "performance_reports": [],
      "layout_audit_reports": [],
      "framework_signal_reports": []
    }
  },
  "site_sampling": {
    "entry_url": "https://example.com/deep/page",
    "canonical_origin": "https://example.com",
    "coverage_level": "site-level | page-level | partial-site",
    "route_budget": {
      "selected_default": "6-10",
      "hard_cap": 12,
      "tier_a_full_visual_routes": "3-5",
      "tier_b_quick_visual_routes": "0-5"
    },
    "discovery_methods": ["seed url", "root page", "nav anchors", "footer anchors", "robots sitemap", "sitemap.xml", "route manifest"],
    "candidate_routes": [
      {
        "url": "https://example.com/pricing",
        "source": "nav anchor",
        "archetype": "pricing",
        "priority": 90,
        "decision": "selected | skipped | blocked | duplicate",
        "reason": "distinct pricing page"
      }
    ],
    "selected_routes": [
      {
        "url": "https://example.com/pricing",
        "archetype": "pricing",
        "tier": "A | B | C",
        "evidence_files": []
      }
    ],
    "skipped_route_classes": [
      {
        "pattern": "/blog/*",
        "reason": "many duplicate article templates; sampled index plus one representative article"
      }
    ],
    "stop_reason": "route budget reached | no new design signals after two archetypes | public routes exhausted | access blocked",
    "coverage_summary": "short statement of what page types were covered and what remains unknown"
  },
  "visual_evidence": {
    "screenshots": [],
    "sections_sampled": [],
    "computed_style_samples": [],
    "pixel_or_screenshot_comparisons": [],
    "playwright_motion_capture": {
      "videos": [],
      "traces": [],
      "reports": [],
      "screenshots": [],
      "hover_probes": [],
      "mousemove_probes": [],
      "scroll_probes": [],
      "reduced_motion_reports": [],
      "runtime_signal_reports": []
    },
    "runtime_visual_system": {
      "tier": "css-static | svg-vector | canvas-2d | webgl-3d | frame-sequence | video-motion | mixed | unknown",
      "source_signals": [
        "canvas count/context",
        "webgl/three/babylon/r3f/lottie/rive/gsap/framer signals",
        "glb/gltf/hdr/ktx2/basis/wasm files",
        "normal/roughness/diffuse/albedo/reflection/displacement texture maps",
        "numbered frame sequence or video files"
      ],
      "minimum_demo_tech": "css/html | svg | canvas-2d | three.js/webgl | frame-sequence | video-like canvas",
      "object_fidelity_checks": [
        "volume silhouette",
        "directional highlight and terminator",
        "cast/contact shadow",
        "texture follows curvature",
        "occlusion/z-depth",
        "multi-frame motion or material change"
      ],
      "downgrade_risks": [],
      "evidence": []
    }
  },
  "interaction_evidence": {
    "hover_states": [],
    "focus_states": [],
    "mousemove_effects": [],
    "scroll_effects": [],
    "timed_animations": [],
    "lazy_loaded_states": [],
    "not_observed": []
  },
  "observed_absences": [
    {
      "trait": "no visible page-level grid background",
      "evidence": "desktop and mobile screenshots plus CSS background audit",
      "do_not_generate": ["technical grid", "paper grid", "blueprint lines"]
    }
  ],
  "identity": {
    "site_type": "saas | ai-product | dashboard | docs | editorial | ecommerce | portfolio | event | learning | other",
    "audience": "primary audience",
    "design_personality": ["precise", "warm", "technical"],
    "summary": "one short paragraph"
  },
  "tokens": {
    "colors": [
      {
        "name": "background",
        "value": "#ffffff",
        "usage": "page background",
        "confidence": "measured | inferred | unknown",
        "evidence": "computed body background"
      }
    ],
    "typography": {
      "font_families": [],
      "scale": [],
      "weights": [],
      "line_heights": [],
      "letter_spacing": [],
      "notes": [],
      "evidence": []
    },
    "spacing": {
      "base_unit": "4px | 8px | inferred",
      "section_gaps": [],
      "component_gaps": [],
      "evidence": []
    },
    "shape": {
      "radii": [],
      "borders": [],
      "shadows": [],
      "evidence": []
    },
    "motion": {
      "durations": [],
      "easing": [],
      "interaction_patterns": [],
      "evidence": []
    }
  },
  "layout_patterns": [
    {
      "name": "pattern name",
      "description": "how it works",
      "responsive_behavior": "desktop/mobile differences",
      "reuse_for": ["page type or component"],
      "evidence": []
    }
  ],
  "component_recipes": [
    {
      "component": "Button",
      "visual_rules": [],
      "states": [],
      "implementation_notes": [],
      "evidence": []
    }
  ],
  "iconography_and_media": {
    "icon_style": "stroke | filled | mixed | custom | none",
    "image_style": "photo | product screenshot | illustration | abstract | video | 3d | none",
    "safe_substitutions": [],
    "evidence": []
  },
  "contamination_checks": {
    "forbidden_without_evidence": [],
    "cross_template_risks": [],
    "source_traits_not_to_copy": []
  },
  "skill_candidate": {
    "suggested_name": "front-example",
    "scope": "what the generated skill should help build",
    "tags": [],
    "avoid": []
  },
  "qa": {
    "minimum_score": 9.8,
    "iteration_stop_rule": {
      "required_score_above": 9.8,
      "max_latest_full_rework_delta": 0.5
    },
    "plateau_escalation": {
      "trigger": "score <= 9.8 and latest_full_rework_delta <= 0.5",
      "allowed_strategies": [
        "asset-fidelity upgrade",
        "runtime visual-system upgrade",
        "typography and lettering upgrade",
        "interaction and scroll-architecture upgrade",
        "component and layout-system upgrade"
      ],
      "forbidden_response": "continuing only small CSS/text/spacing tweaks"
    },
    "blocking_rules": [],
    "required_demo_checks": []
  }
}
```

## 置信标签

- `measured`：直接来自源码、computed styles、DOM、截图或交互轨迹。
- `inferred`：基于部分证据推断，必须明确标记。
- `unknown`：被登录、反爬、懒加载、缺失资源、压缩代码或不可访问状态阻挡。
- `absent`：已经主动检查但没有观察到。

## 最小可用分析

可用分析至少必须包含：

- source URL、site name、site slug、output folder
- site sampling inventory，包含覆盖层级、选中路由、跳过路由类别和停止原因
- 源 HTML/CSS/JS 证据，或明确的源码访问限制
- seed 和 Tier A 路由的 frontend runtime audit 证据：hydration 后 DOM、computed style 样本、CSS rules、字体、network/resources、JS/CSS coverage、accessibility 摘要、performance metrics、布局溢出、controls/forms 和 framework/runtime signals
- 至少 5 条颜色/token 观察，并附证据
- 字体说明，并标记 measured 或 inferred
- 至少 2 个布局模式，包含响应式说明
- 至少 3 个组件配方，包含状态
- 交互证据，或明确的动效缺失记录
- Tier A 路由的 Playwright 动效捕获证据：video、trace、截图、JSON 报告、hover/mousemove/scroll 探针，以及相关时的 reduced-motion fallback
- runtime visual system 层级，尤其是源站存在 canvas/WebGL/video/3D/材质/帧序列时的最低 demo 技术层级
- 至少 3 条 observed absences，用来阻止幻觉式设计特征
- 至少 1 条版权安全替代方案
- demo 必须执行的 QA 检查
