#!/usr/bin/env python3
"""Create a production-style `front-<site>` skill folder from style-analysis.json."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse


ROLE_BRIEFS = [
    ("01-source-code-auditor", "Treat the input URL as a seed route; discover same-site candidates, create references/page-inventory.json, select 6-10 representative public routes with a hard cap of 12, then collect HTML, CSS, JS, asset, font, hydrated DOM, and frontend runtime audit evidence before visual synthesis. Run scripts/frontend_runtime_audit.mjs for browser-reachable seed/Tier A routes."),
    ("02-dom-css-auditor", "Measure computed styles, repeated components, breakpoints, tokens, and layout primitives from hydrated DOM and frontend runtime audit reports."),
    ("03-visual-motion-auditor", "Use references/page-inventory.json tiers: full multi-viewport motion probes for 3-5 distinct routes, lighter screenshots for up to 5 additional routes, and inventory-only treatment for the rest unless unique visual/motion evidence appears. Run scripts/playwright_motion_capture.mjs for browser-reachable Tier A routes so evidence includes video, trace, screenshots, hover/mousemove/scroll probes, timed frames, runtime signals, and reduced-motion fallback when relevant. Classify runtime visual tier: CSS/SVG, Canvas 2D, WebGL/Three/Babylon/R3F, frame sequence, or video-motion; record 3D/PBR/normal-map/frame-sequence evidence."),
    ("04-design-system-synthesizer", "Convert evidence into reusable tokens, layout patterns, components, interaction rules, negative evidence, frontend_runtime_audit references, and runtime_visual_system guidance with minimum demo technology."),
    ("05-demo-implementation-reviewer", "Review the generated demo for fidelity, maintainability, state coverage, cross-template contamination, and whether runtime/canvas/WebGL/3D/frame-sequence visuals use an adequate technology tier."),
    ("06-accessibility-responsive-qa", "Check keyboard access, focus, contrast, semantics, reduced motion, viewport stability, text fit, overflow, and instant-scroll samples; use Playwright reduced-motion capture when source/demo motion is relevant."),
    ("07-performance-security-qa", "Check animation cost, resource weight, third-party resources, private data, unsafe scripts, licensing risk, JS/CSS coverage, performance metrics, failed requests, storage key names, and large runtime assets from frontend runtime audit reports."),
    ("08-final-arbiter", "Independently review all evidence and the demo, including frontend runtime audit reports and Playwright videos/traces/reports for dynamic Tier A routes, fill the scorecard, then apply blocking rules. Approve only above 9.8 with no blockers and delta <= 0.5; at or below 9.8 with delta <= 0.5, require strategy escalation instead of more small CSS tweaks. The score script only aggregates the arbiter-filled scorecard."),
]

SCORE_DIMENSIONS = [
    ("similarity", "Similarity to source style", 1.5),
    ("sensitivity", "Interaction sensitivity and motion fidelity", 1.0),
    ("motion_material_scroll", "Motion/material complexity and scroll fidelity", 1.0),
    ("source_evidence", "Source-code evidence coverage", 1.1),
    ("maintainability", "Production maintainability", 1.1),
    ("responsive", "Responsive visual stability", 1.1),
    ("accessibility", "Accessibility", 1.0),
    ("content_brand", "Content and brand-tone fit", 0.9),
    ("performance", "Performance and runtime stability", 0.9),
    ("security_licensing", "Security, privacy, and licensing safety", 0.8),
    ("reproducibility", "Reproducibility and artifact completeness", 0.6),
]


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    if not value:
        return ""
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:56].strip("-")


def as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    return str(value)


def md_list(values, fallback: str = "No specific guidance captured.") -> str:
    cleaned = [text(item) for item in as_list(values) if text(item)]
    if not cleaned:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in cleaned)


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def infer_host_slug(url: str) -> str:
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        host = ""
    host = re.sub(r"^www\.", "", host)
    return slugify(host.split(".")[0] or host) or "site"


def infer_front_name(analysis: dict, override: str | None = None) -> str:
    source = analysis.get("source", {}) if isinstance(analysis.get("source"), dict) else {}
    candidate = analysis.get("skill_candidate", {}) if isinstance(analysis.get("skill_candidate"), dict) else {}
    choices = [
        override,
        source.get("output_folder"),
        candidate.get("output_folder"),
        candidate.get("project_slug"),
        source.get("site_slug"),
        source.get("site_name"),
        infer_host_slug(text(source.get("url"))),
        candidate.get("suggested_name"),
    ]
    for choice in choices:
        slug = slugify(text(choice))
        if slug:
            if slug.startswith("front-"):
                return slug[:63].strip("-")
            return f"front-{slug}"[:63].strip("-")
    return "front-site"


def compact_color(item) -> str:
    if isinstance(item, dict):
        name = text(item.get("name"), "color")
        value = text(item.get("value"), "unknown")
        usage = text(item.get("usage"))
        confidence = text(item.get("confidence"))
        evidence = text(item.get("evidence"))
        tail = f" for {usage}" if usage else ""
        conf = f" ({confidence})" if confidence else ""
        ev = f"; evidence: {evidence}" if evidence else ""
        return f"`{name}`: `{value}`{tail}{conf}{ev}"
    return text(item)


def compact_layout(item) -> str:
    if not isinstance(item, dict):
        return f"- {text(item)}"
    name = text(item.get("name"), "Layout pattern")
    desc = text(item.get("description"), "Reusable layout pattern.")
    responsive = text(item.get("responsive_behavior"))
    evidence = ", ".join(text(x) for x in as_list(item.get("evidence")) if text(x))
    reuse_for = ", ".join(text(x) for x in as_list(item.get("reuse_for")) if text(x))
    suffix = []
    if responsive:
        suffix.append(f"Responsive: {responsive}")
    if reuse_for:
        suffix.append(f"Reuse for: {reuse_for}")
    if evidence:
        suffix.append(f"Evidence: {evidence}")
    tail = f" {' '.join(suffix)}" if suffix else ""
    return f"- **{name}**: {desc}{tail}"


def compact_component(item) -> str:
    if not isinstance(item, dict):
        return f"### {text(item, 'Component')}\n\n- Recreate as a reusable component pattern."
    name = text(item.get("component"), "Component")
    visual_rules = md_list(item.get("visual_rules"), "No visual rules captured.")
    states = md_list(item.get("states"), "Include default, hover, focus, disabled, loading, and active states when relevant.")
    notes = md_list(item.get("implementation_notes"), "Keep implementation idiomatic to the target stack.")
    evidence = md_list(item.get("evidence"), "Evidence not recorded; treat as inference until verified.")
    return f"### {name}\n\n**Visual Rules**\n{visual_rules}\n\n**States**\n{states}\n\n**Implementation Notes**\n{notes}\n\n**Evidence**\n{evidence}"


def evidence_summary(analysis: dict) -> list[str]:
    source_code = analysis.get("source_code", {}) if isinstance(analysis.get("source_code"), dict) else {}
    visual = analysis.get("visual_evidence", {}) if isinstance(analysis.get("visual_evidence"), dict) else {}
    interaction = analysis.get("interaction_evidence", {}) if isinstance(analysis.get("interaction_evidence"), dict) else {}
    lines = []
    for key in ["html_files", "css_files", "script_files", "font_files", "asset_files", "media_queries", "keyframes"]:
        values = as_list(source_code.get(key))
        if values:
            lines.append(f"{key.replace('_', ' ').title()}: {', '.join(text(v) for v in values if text(v))}")
    frontend_audit = source_code.get("frontend_runtime_audit")
    if isinstance(frontend_audit, dict):
        audit_bits = []
        for key in ["reports", "hydrated_dom_reports", "computed_style_reports", "network_reports", "resource_inventory_reports", "coverage_reports", "font_reports", "css_rule_reports", "accessibility_reports", "performance_reports", "layout_audit_reports", "framework_signal_reports"]:
            values = [text(x) for x in as_list(frontend_audit.get(key)) if text(x)]
            if values:
                audit_bits.append(f"{key.replace('_', ' ')}: {', '.join(values[:8])}")
        if audit_bits:
            lines.append("Frontend Runtime Audit: " + "; ".join(audit_bits))
    for key in ["screenshots", "sections_sampled", "computed_style_samples"]:
        values = as_list(visual.get(key))
        if values:
            lines.append(f"{key.replace('_', ' ').title()}: {', '.join(text(v) for v in values if text(v))}")
    playwright_capture = visual.get("playwright_motion_capture")
    if isinstance(playwright_capture, dict):
        capture_bits = []
        for key in ["videos", "traces", "reports", "screenshots", "hover_probes", "mousemove_probes", "scroll_probes", "reduced_motion_reports", "runtime_signal_reports"]:
            values = [text(x) for x in as_list(playwright_capture.get(key)) if text(x)]
            if values:
                capture_bits.append(f"{key.replace('_', ' ')}: {', '.join(values[:8])}")
        if capture_bits:
            lines.append("Playwright Motion Capture: " + "; ".join(capture_bits))
    runtime = visual.get("runtime_visual_system")
    if isinstance(runtime, dict):
        runtime_bits = []
        for key in ["tier", "minimum_demo_tech"]:
            value = text(runtime.get(key))
            if value:
                runtime_bits.append(f"{key.replace('_', ' ')}: {value}")
        signals = [text(x) for x in as_list(runtime.get("source_signals")) if text(x)]
        if signals:
            runtime_bits.append("signals: " + ", ".join(signals[:12]))
        checks = [text(x) for x in as_list(runtime.get("object_fidelity_checks")) if text(x)]
        if checks:
            runtime_bits.append("object checks: " + ", ".join(checks[:12]))
        if runtime_bits:
            lines.append("Runtime Visual System: " + "; ".join(runtime_bits))
    for key in ["hover_states", "focus_states", "mousemove_effects", "scroll_effects", "timed_animations"]:
        values = as_list(interaction.get(key))
        if values:
            lines.append(f"{key.replace('_', ' ').title()}: {', '.join(text(v) for v in values if text(v))}")
    return lines


def site_coverage_lines(analysis: dict) -> list[str]:
    sampling = analysis.get("site_sampling", {}) if isinstance(analysis.get("site_sampling"), dict) else {}
    lines = []
    coverage_level = text(sampling.get("coverage_level"))
    if coverage_level:
        lines.append(f"Coverage level: {coverage_level}")
    entry_url = text(sampling.get("entry_url"))
    if entry_url:
        lines.append(f"Entry URL: {entry_url}")
    selected = as_list(sampling.get("selected_routes"))
    if selected:
        route_bits = []
        for route in selected[:12]:
            if isinstance(route, dict):
                url = text(route.get("url"))
                archetype = text(route.get("archetype"), "route")
                tier = text(route.get("tier"))
                label = f"{archetype}: {url}" if url else archetype
                if tier:
                    label = f"{label} ({tier})"
                route_bits.append(label)
            else:
                route_bits.append(text(route))
        lines.append("Selected routes: " + "; ".join(item for item in route_bits if item))
    skipped = as_list(sampling.get("skipped_route_classes"))
    if skipped:
        skipped_bits = []
        for item in skipped[:6]:
            if isinstance(item, dict):
                pattern = text(item.get("pattern"), "route class")
                reason = text(item.get("reason"))
                skipped_bits.append(f"{pattern}: {reason}" if reason else pattern)
            else:
                skipped_bits.append(text(item))
        lines.append("Skipped route classes: " + "; ".join(item for item in skipped_bits if item))
    stop_reason = text(sampling.get("stop_reason"))
    if stop_reason:
        lines.append(f"Stop reason: {stop_reason}")
    coverage_summary = text(sampling.get("coverage_summary"))
    if coverage_summary:
        lines.append(f"Coverage summary: {coverage_summary}")
    if not lines:
        lines.append("No multi-page route inventory was recorded; treat this as page-level or partial-site evidence until more routes are sampled.")
    return lines


def absence_lines(analysis: dict) -> list[str]:
    lines = []
    for item in as_list(analysis.get("observed_absences")):
        if isinstance(item, dict):
            trait = text(item.get("trait"), "absence")
            evidence = text(item.get("evidence"))
            do_not = ", ".join(text(x) for x in as_list(item.get("do_not_generate")) if text(x))
            tail = []
            if evidence:
                tail.append(f"evidence: {evidence}")
            if do_not:
                tail.append(f"do not generate: {do_not}")
            lines.append(f"{trait}" + (f" ({'; '.join(tail)})" if tail else ""))
        elif text(item):
            lines.append(text(item))
    return lines


def build_skill_markdown(analysis: dict, skill_name: str) -> str:
    source = analysis.get("source", {}) if isinstance(analysis.get("source"), dict) else {}
    identity = analysis.get("identity", {}) if isinstance(analysis.get("identity"), dict) else {}
    tokens = analysis.get("tokens", {}) if isinstance(analysis.get("tokens"), dict) else {}
    skill_candidate = analysis.get("skill_candidate", {}) if isinstance(analysis.get("skill_candidate"), dict) else {}
    icon_media = analysis.get("iconography_and_media", {}) if isinstance(analysis.get("iconography_and_media"), dict) else {}

    site_type = text(identity.get("site_type"), "frontend")
    summary = text(identity.get("summary"), "A reusable frontend style derived from analyzed source and visual evidence.")
    scope = text(skill_candidate.get("scope"), f"Build original {site_type} interfaces with this design language.")
    personality = ", ".join(text(x) for x in as_list(identity.get("design_personality")) if text(x))
    url = text(source.get("url"))
    description = (
        f"Build original {site_type} interfaces using this evidence-backed frontend style folder. "
        f"Use when the user asks for UI, web app, landing page, dashboard, docs, or component styling that should feel {personality or 'cohesive, polished, and product-ready'}."
    )

    colors = md_list([compact_color(c) for c in as_list(tokens.get("colors"))], "Choose a restrained palette with accessible contrast.")
    typography = tokens.get("typography", {}) if isinstance(tokens.get("typography"), dict) else {}
    spacing = tokens.get("spacing", {}) if isinstance(tokens.get("spacing"), dict) else {}
    shape = tokens.get("shape", {}) if isinstance(tokens.get("shape"), dict) else {}
    motion = tokens.get("motion", {}) if isinstance(tokens.get("motion"), dict) else {}

    type_notes = []
    for label, key in [
        ("Font families", "font_families"),
        ("Scale", "scale"),
        ("Weights", "weights"),
        ("Line heights", "line_heights"),
        ("Letter spacing", "letter_spacing"),
    ]:
        values = [text(x) for x in as_list(typography.get(key)) if text(x)]
        if values:
            type_notes.append(f"{label}: {', '.join(values)}")
    type_notes.extend(text(x) for x in as_list(typography.get("notes")) if text(x))
    type_notes.extend(f"Evidence: {text(x)}" for x in as_list(typography.get("evidence")) if text(x))

    spacing_notes = []
    if spacing.get("base_unit"):
        spacing_notes.append(f"Base unit: {text(spacing.get('base_unit'))}")
    for label, key in [("Section gaps", "section_gaps"), ("Component gaps", "component_gaps")]:
        values = [text(x) for x in as_list(spacing.get(key)) if text(x)]
        if values:
            spacing_notes.append(f"{label}: {', '.join(values)}")
    spacing_notes.extend(f"Evidence: {text(x)}" for x in as_list(spacing.get("evidence")) if text(x))

    shape_notes = []
    for label, key in [("Radii", "radii"), ("Borders", "borders"), ("Shadows", "shadows")]:
        values = [text(x) for x in as_list(shape.get(key)) if text(x)]
        if values:
            shape_notes.append(f"{label}: {', '.join(values)}")
    shape_notes.extend(f"Evidence: {text(x)}" for x in as_list(shape.get("evidence")) if text(x))

    motion_notes = []
    for label, key in [("Durations", "durations"), ("Easing", "easing"), ("Patterns", "interaction_patterns")]:
        values = [text(x) for x in as_list(motion.get(key)) if text(x)]
        if values:
            motion_notes.append(f"{label}: {', '.join(values)}")
    motion_notes.extend(f"Evidence: {text(x)}" for x in as_list(motion.get("evidence")) if text(x))

    layouts = "\n".join(compact_layout(x) for x in as_list(analysis.get("layout_patterns"))) or "- Use simple, responsive layouts that preserve the analyzed density and hierarchy."
    components = "\n\n".join(compact_component(x) for x in as_list(analysis.get("component_recipes"))) or "### Core Components\n\n- Define buttons, cards, navigation, forms, and content sections before composing pages."
    avoid = md_list(skill_candidate.get("avoid"), "Do not clone the source site, reuse protected assets, or copy exact text/layout.")

    icon_lines = []
    if icon_media.get("icon_style"):
        icon_lines.append(f"Icon style: {text(icon_media.get('icon_style'))}")
    if icon_media.get("image_style"):
        icon_lines.append(f"Image style: {text(icon_media.get('image_style'))}")
    icon_lines.extend(text(x) for x in as_list(icon_media.get("safe_substitutions")) if text(x))
    icon_lines.extend(f"Evidence: {text(x)}" for x in as_list(icon_media.get("evidence")) if text(x))

    evidence_lines = evidence_summary(analysis)
    coverage_lines = site_coverage_lines(analysis)
    absent = absence_lines(analysis)
    source_note = f"\n\nSource inspiration: {url}" if url else ""

    return f"""---
name: {skill_name}
description: {yaml_string(description)}
---

# {skill_name.replace("-", " ").title()}

## Overview

{summary} {scope}{source_note}

## Evidence Boundary

Use this skill with the bundled evidence folder. Treat source-backed items as stable, inferred items as hypotheses, unknown items as risks, and absent items as hard guards.

**Source And Visual Evidence**
{md_list(evidence_lines, "No evidence summary was recorded; inspect references/style-analysis.json before use.")}

**Site Coverage**
{md_list(coverage_lines, "No route inventory was recorded; treat this as page-level evidence.")}

**Observed Absences**
{md_list(absent, "No negative evidence was recorded; verify before adding grid, gradient, 3D, video, bento, terminal, or dark-shell patterns.")}

## Design Principles

- Translate the source inspiration into original UI work instead of recreating one page exactly.
- Preserve the observed personality: {personality or "polished, coherent, and usable"}.
- Make hierarchy obvious through spacing, contrast, and type scale before adding decoration.
- Use source-backed motion and interaction patterns; do not invent dynamic effects, but do not downgrade runtime/canvas/material motion into trivial CSS drift.
- Match the source runtime visual tier. If evidence shows WebGL/PBR/GLB/normal maps/frame sequences/video-level material motion, use Three.js/WebGL/Babylon/R3F, GLSL, original frame sequences, or an equivalent runtime system; do not substitute 2D circles, flat grids, generic gradients, or merely nonblank canvas.
- Keep components reusable across pages, states, and responsive breakpoints.
- Use accessible contrast, keyboard states, and clear interaction feedback.

## Tokens

### Colors

{colors}

### Typography

{md_list(type_notes, "Use a clean type scale with distinct display, heading, body, caption, and utility roles.")}

### Spacing

{md_list(spacing_notes, "Use consistent spacing tokens and larger section rhythm than component rhythm.")}

### Shape And Elevation

{md_list(shape_notes, "Use radius, border, and shadow sparingly to support hierarchy.")}

### Motion

{md_list(motion_notes, "Use short, purposeful transitions for hover, focus, entrance, and navigation changes.")}

## Layout Patterns

{layouts}

## Component Recipes

{components}

## Iconography And Media

{md_list(icon_lines, "Use open-license icons and original or user-owned media.")}

## Implementation Guidance

- Start by defining design tokens, then primitives, then page patterns.
- Use framework-native conventions and existing project styling utilities where available.
- Include desktop, tablet, and mobile states.
- Use `scripts/frontend_runtime_audit.mjs` to collect source/demo frontend evidence when implementation fidelity matters: hydrated DOM, computed styles, CSS rules/custom properties, fonts, scripts/links, network/resource inventory, JS/CSS coverage, accessibility tree summary, performance metrics, framework signals, forms/controls, layout overflow, clipped text, positioned layers, and section boxes.
- Use `scripts/playwright_motion_capture.mjs` to collect demo/source comparison evidence when runtime motion matters: video, trace, screenshots, hover/mousemove probes, instant-scroll samples, wheel-scroll samples, timed frames, runtime signals, and reduced-motion fallback.
- Choose the demo technology from evidence: CSS/HTML for static UI, SVG for vector/path systems, Canvas 2D for flat procedural textures, Three.js/WebGL/Babylon/R3F for lit 3D/PBR objects, and original frame sequences or video-like canvas for pre-rendered motion.
- For 3D/material objects, verify volume silhouette, directional highlight, terminator, cast/contact shadow, occlusion/z-depth, texture curvature, and multi-frame motion or material change.
- Verify no cross-template artifacts appear in the demo.
- If Site Coverage is page-level or partial-site, do not claim unvisited sections of the source site are represented.
- Prefer lucide or another open icon set when the target stack supports it.

## Demo QA Checklist

- Similarity to source style is treated as a near-final target and should be pushed toward 9.8+/10 after comparing source evidence, user recordings when provided, and demo screenshots.
- Interaction sensitivity is tested for hover, focus, mousemove, scroll, material changes, canvas/video/WebGL regions, and timed motion where relevant.
- The demo does not add cursor followers, bubbles, halos, stretched generic typography, or other interaction/visual layers absent from source evidence.
- Cards, tablets, controls, and text do not collide at sampled scroll offsets.
- Source-visible motion/material/scroll complexity is represented in the runnable `demo/` files with multi-frame verification.
- Playwright video/trace or equivalent browser-automation recordings exist for dynamic Tier A routes and user-reported behavior, including hover, mousemove, instant-scroll, wheel-scroll, timed-frame, runtime-signal, and reduced-motion probes where relevant.
- Runtime visual-system tier is documented and met. Source 3D/PBR/GLB/normal-map/frame-sequence evidence cannot be approved when represented only by 2D circles, flat grids, generic gradients, static stickers, or nonblank canvas checks.
- Source-code evidence supports the visual claims.
- Frontend runtime audit reports exist for browser-reachable seed/Tier A routes and support the hydrated DOM, computed style, CSS/font/network/resource, coverage, accessibility, performance, framework, layout, and control claims.
- Responsive layouts do not overlap, overflow, or hide core content.
- Accessibility, performance, security, and licensing checks pass.
- `qa/scorecard.json` was completed by an independent final arbiter agent/subagent; the weighted total is above 9.8, no blocking issue exists, and the latest full rework improved the score by no more than 0.5.
- If the weighted total is at or below 9.8 and the latest full rework delta is no more than 0.5, treat the result as a strategy plateau. Escalate to a stronger generic strategy such as asset fidelity, runtime visual systems, typography/lettering, interaction/scroll architecture, or component/layout systems instead of continuing tiny CSS/text/spacing tweaks.

## Avoid

{avoid}
- Do not use traits listed in Observed Absences.
- Do not describe a single sampled page as the whole source website.
- Do not add a technical grid, paper grid, blueprint background, gradient wash, dark shell, 3D scene, bento card system, or terminal UI unless it is source-backed.
- Do not downgrade source-backed WebGL/PBR/frame-sequence/video visuals into Canvas 2D or CSS-only approximations without recording the downgrade risk and applying the QA caps.
- Do not use the original site's logos, trademarks, proprietary screenshots, illustrations, paid fonts, private data, or marketing copy unless the user confirms they own or license them.
"""


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value) -> None:
    write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def copy_score_script(skill_dir: Path) -> None:
    source = Path(__file__).with_name("score_extraction.py")
    target = skill_dir / "scripts" / "score_extraction.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copyfile(source, target)
    else:
        write_text(target, "#!/usr/bin/env python3\nprint('score_extraction.py missing from source skill')\n")


def copy_playwright_motion_script(skill_dir: Path) -> None:
    source = Path(__file__).with_name("playwright_motion_capture.mjs")
    target = skill_dir / "scripts" / "playwright_motion_capture.mjs"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copyfile(source, target)
    else:
        write_text(target, "#!/usr/bin/env node\nconsole.error('playwright_motion_capture.mjs missing from source skill');\nprocess.exit(1);\n")


def copy_frontend_runtime_audit_script(skill_dir: Path) -> None:
    source = Path(__file__).with_name("frontend_runtime_audit.mjs")
    target = skill_dir / "scripts" / "frontend_runtime_audit.mjs"
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copyfile(source, target)
    else:
        write_text(target, "#!/usr/bin/env node\nconsole.error('frontend_runtime_audit.mjs missing from source skill');\nprocess.exit(1);\n")


def make_placeholder_dirs(skill_dir: Path) -> None:
    for rel in [
        "evidence/source",
        "evidence/dom",
        "evidence/css",
        "evidence/routes",
        "evidence/frontend",
        "evidence/frontend/reports",
        "evidence/screenshots",
        "evidence/motion",
        "evidence/motion/screenshots",
        "evidence/motion/videos",
        "evidence/motion/traces",
        "evidence/motion/reports",
        "demo",
        "demo/screenshots",
        "qa",
        "references",
        "subagents",
        "scripts",
    ]:
        path = skill_dir / rel
        path.mkdir(parents=True, exist_ok=True)
        if rel.startswith("evidence/"):
            write_text(path / ".gitkeep", "")


def build_scorecard() -> dict:
    return {
        "minimum_score": 9.8,
        "scoring_review": {
            "arbiter_role": "",
            "independent_from": [],
            "evidence_reviewed": [],
            "demo_reviewed": False,
            "judgment_notes": ""
        },
        "iteration_review": {
            "previous_score": None,
            "latest_score": None,
            "latest_full_rework_delta": None,
            "escalation_strategy": "",
            "stop_rule_satisfied": False,
            "decision": "continue"
        },
        "blocking_issues": [],
        "dimensions": [
            {
                "id": key,
                "name": name,
                "weight": weight,
                "score": None,
                "responsible_subagent": "",
                "evidence": "",
                "required_fix": ""
            }
            for key, name, weight in SCORE_DIMENSIONS
        ]
    }


def write_role_files(skill_dir: Path) -> None:
    for role, brief in ROLE_BRIEFS:
        role_dir = skill_dir / "subagents" / role
        write_text(role_dir / "brief.md", f"# {role}\n\n{brief}\n\nWrite findings in `findings.md` with evidence, risks, and required fixes.\n")
        write_text(role_dir / "findings.md", "# Findings\n\nStatus: pending\n")


def write_support_files(skill_dir: Path, analysis: dict) -> None:
    source = analysis.get("source", {}) if isinstance(analysis.get("source"), dict) else {}
    source_code = analysis.get("source_code", {}) if isinstance(analysis.get("source_code"), dict) else {}
    site_sampling = analysis.get("site_sampling", {}) if isinstance(analysis.get("site_sampling"), dict) else {}
    evidence = evidence_summary(analysis)
    absences = absence_lines(analysis)

    write_json(skill_dir / "references" / "style-analysis.json", analysis)
    write_text(skill_dir / "references" / "evidence.md", "# Evidence Summary\n\n" + md_list(evidence, "Evidence not yet summarized.") + "\n")
    write_json(skill_dir / "references" / "page-inventory.json", site_sampling or {
        "coverage_level": "page-level",
        "selected_routes": [{"url": source.get("url", ""), "archetype": "seed", "tier": "A"}],
        "stop_reason": "no multi-page route inventory was recorded",
        "coverage_summary": "Treat this generated skill as page-level or partial-site until representative routes are sampled."
    })
    write_text(skill_dir / "references" / "negative-evidence.md", "# Negative Evidence\n\n" + md_list(absences, "No negative evidence recorded yet.") + "\n")
    write_text(skill_dir / "references" / "runtime-visual-fidelity.md", "# Runtime Visual Fidelity\n\nClassify each core visual object before choosing demo technology.\n\n## Runtime Tiers\n\n- `css-static`: colors, type, layout, borders, shadows, ordinary images, and simple transitions.\n- `svg-vector`: vector paths, lettering, masks, icon systems, stroke animation, and geometric illustration.\n- `canvas-2d`: 2D procedural texture, particles, pixel drawing, flat noise fields, and non-PBR material hints.\n- `webgl-3d`: real volume, camera, perspective, PBR materials, normal/roughness/reflection maps, GLB/GLTF, shadows, occlusion, and interactive lighting. Use Three.js, Babylon.js, React Three Fiber, or equivalent WebGL.\n- `frame-sequence`: numbered image sequences, sprite animation, or pre-rendered 3D/scroll frames. Use original frame sequences, sprite sheets, or video-like canvas.\n- `video-motion`: video, rendered clips, video masks, or live-action/CG motion. Use original video, generated frames, canvas composition, or equivalent runtime.\n\n## Source Signals\n\nUpgrade analysis when source evidence includes canvas/WebGL contexts; Three/Babylon/R3F/Lottie/Rive/GSAP/Framer runtime; `.glb`, `.gltf`, `.bin`, `.hdr`, `.exr`, `.ktx2`, `.basis`, or `.wasm`; asset names containing `normal`, `roughness`, `metalness`, `diffuse`, `albedo`, `ao`, `reflection`, `displacement`, or `bump`; `/frames/`, `sequence`, `sprite`, or many numbered images; or user recordings showing volume, highlights, texture curvature, shadows, occlusion, camera motion, or scroll-driven material changes.\n\n## Browser Evidence\n\nUse `scripts/playwright_motion_capture.mjs` for browser-reachable Tier A routes whenever runtime visuals are possible. Preserve the video, trace, screenshots, JSON reports, hover/mousemove probes, instant-scroll samples, wheel-scroll samples, timed frames, runtime-signal report, and reduced-motion pass when relevant. Downgrade a runtime tier only when browser capture and source assets both support the downgrade.\n\n## Demo Technology Matrix\n\n- Use CSS/HTML for static UI.\n- Use SVG for vector/path/lettering systems.\n- Use Canvas 2D for flat procedural textures and 2D generated visuals.\n- Use Three.js/WebGL/Babylon/R3F for spheres, cloth, product models, PBR, normal maps, environment lighting, shadows, occlusion, and true 3D interaction.\n- Use GLSL/shader materials for refraction, reflection, normal perturbation, procedural surfaces, and post-processing.\n- Use original frame sequences, sprite sheets, or video-like canvas when the source relies on pre-rendered frame motion.\n\n## Object-Level Checks\n\nFor source 3D/PBR/material objects, verify volume silhouette, directional highlights, terminator, cast/contact shadows, occlusion/z-depth, texture following curvature, multi-frame motion/material change, and reduced-motion fallback. A nonblank canvas or generic pixel variance is not enough.\n\n## QA Caps\n\n- Source `webgl-3d`/PBR/GLB/normal-map evidence represented by 2D circles, flat grids, generic gradients, static stickers, or only nonblank canvas checks: similarity max 8.0 and motion/material max 6.0.\n- Source `frame-sequence` or `video-motion` represented without multi-frame or equivalent runtime replacement: interaction max 7.0 and motion/material max 6.5.\n- Missing runtime tier and technology rationale when runtime evidence exists: source evidence max 8.5.\n- Missing Playwright video/trace or equivalent browser-automation recording for dynamic Tier A routes: interaction and motion/material max 7.0, source evidence max 8.5.\n- User recordings showing 3D/material behavior without targeted demo comparison: no release.\n")
    write_json(skill_dir / "references" / "source-map.json", {
        "url": source.get("url", ""),
        "page_inventory": "references/page-inventory.json",
        "selected_routes": as_list(site_sampling.get("selected_routes")) if site_sampling else [],
        "html_files": as_list(source_code.get("html_files")),
        "css_files": as_list(source_code.get("css_files")),
        "script_files": as_list(source_code.get("script_files")),
        "font_files": as_list(source_code.get("font_files")),
        "asset_files": as_list(source_code.get("asset_files")),
        "evidence_files": as_list(source_code.get("evidence_files")),
        "frontend_runtime_audit": source_code.get("frontend_runtime_audit", {}),
    })
    write_text(skill_dir / "references" / "qa-scorecard.md", "# QA Scorecard\n\nScoring must be performed by an independent `08-final-arbiter` agent/subagent after reviewing `references/page-inventory.json`, source evidence, DOM/CSS evidence, frontend runtime audit reports, motion evidence, Playwright video/trace/reports, screenshots, user recording frames when provided, subagent findings, and the runnable demo under `demo/`. The implementation or demo-review agent must not score its own work.\n\nFill `qa/scorecard.json`, including `scoring_review`, before running `scripts/score_extraction.py --scorecard qa/scorecard.json --out qa/release-decision.md`. The script is only a weighted-total calculator and Markdown formatter; it is not the reviewer. Completion requires a score above 9.8/10, no blocking issues, and a latest full-rework score delta no greater than 0.5. If score is at or below 9.8 and the latest full-rework delta is no greater than 0.5, treat the result as a strategy plateau and escalate beyond small CSS/text/spacing tweaks. The next redo must use a generic higher-leverage strategy matched to the failed evidence: asset fidelity, runtime visual systems, typography/lettering, interaction/scroll architecture, or component/layout systems. If browser-reachable seed/Tier A routes lack frontend runtime audit reports, cap source evidence and performance/runtime stability at 8.0. If computed-style/CSS/font/network evidence is missing despite browser access, cap source evidence at 8.5. If accessibility/layout/control evidence is missing despite browser access, cap accessibility and responsive stability at 8.5. If source-visible canvas/WebGL/video/material/scroll motion is missing from the demo, cap similarity at 8.0 and motion/material complexity at 6.0. If dynamic Tier A routes or user-reported dynamic behavior lack Playwright video/trace or equivalent browser-automation recordings with hover, mousemove, instant-scroll, wheel-scroll, timed-frame, and runtime-signal probes, cap interaction sensitivity and motion/material complexity at 7.0 and source evidence at 8.5. If relevant reduced-motion behavior was not captured or verified, cap accessibility and motion/material complexity at 8.0. If source-visible WebGL/PBR/GLB/normal-map/frame-sequence/video-level visuals are represented only by 2D circles, flat grids, generic gradients, static stickers, or nonblank canvas checks, cap similarity at 8.0 and motion/material complexity at 6.0. If runtime_visual_system is not documented when such evidence exists, cap source evidence at 8.5. If the demo claims whole-site extraction from one sampled public route or lacks page inventory, cap source evidence and content fit. If the demo invents cursor followers/bubbles or scroll collisions, fail or apply the relevant hard cap.\n")
    write_json(skill_dir / "qa" / "scorecard.json", build_scorecard())
    write_text(skill_dir / "qa" / "blocking-rules.md", "# Blocking Rules\n\n- Missing user requirement.\n- Serious style mismatch.\n- Invented trait without source evidence, including cursor followers, bubbles, halos, stretched generic typography, decorative grids, dark shells, bento layouts, or 3D scenes not present in source evidence.\n- Browser-reachable seed/Tier A routes lack frontend runtime audit reports for hydrated DOM, computed styles, CSS/font/network/resource evidence, accessibility summary, performance metrics, layout overflow, and framework/runtime signals.\n- Unusable mobile or desktop core path.\n- Text/control/media overlap, overflow, clipping, or scroll-offset collision.\n- Dynamic Tier A routes lack Playwright video/trace capture or an equivalent browser-automation recording with hover, mousemove, instant-scroll, wheel-scroll, timed-frame, and runtime-signal probes.\n- Source has visible canvas/WebGL/video/material/scroll motion, but the demo only implements static panels or tiny CSS drift.\n- Source has visible WebGL/PBR/GLB/normal-map/frame-sequence/video-level visuals, but the demo represents them with 2D circles, flat grids, generic gradients, static stickers, or only a nonblank canvas check.\n- Runtime visual tier is missing or downgraded, causing WebGL/frame-sequence/video evidence to be treated as CSS or Canvas 2D.\n- User-reported hover, pointer, material, color, lighting, or location-specific effects are dismissed without targeted retesting.\n- Runnable demo files under `demo/` are missing.\n- Missing QA evidence.\n- Unauthorized assets, private data, unsafe scripts, or copied brand material.\n- Score at or below 9.8 treated as complete, or iteration plateau rule skipped.\n- Score at or below 9.8 with delta <= 0.5 is accepted as convergence instead of triggering a stronger asset, runtime visual, typography, interaction/scroll, or component/layout strategy.\n- A plateau redo continues only tiny CSS/text/spacing tweaks when the failed evidence requires a stronger strategy.\n")
    write_text(skill_dir / "qa" / "redo-report.md", "# Redo Report\n\nStatus: pending\n\nFill this when the score is at or below 9.8, the latest full rework improves by more than 0.5, or a blocking issue exists.\n\nWhen score is at or below 9.8 and latest full-rework delta is no more than 0.5, record the selected generic upgrade strategy, rejected weaker strategy, why small CSS/text/spacing tweaks are insufficient, expected score impact, and verification plan.\n")
    write_text(skill_dir / "qa" / "release-decision.md", "# Release Decision\n\nStatus: pending\n")
    write_text(skill_dir / "demo" / "index.html", "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>Generated Style Demo</title>\n  <link rel=\"stylesheet\" href=\"./styles.css\">\n</head>\n<body>\n  <main class=\"demo-root\">\n    <h1>Replace this placeholder with the source-backed demo.</h1>\n  </main>\n  <script src=\"./script.js\" defer></script>\n</body>\n</html>\n")
    write_text(skill_dir / "demo" / "styles.css", ":root { color-scheme: light; }\nbody { margin: 0; font-family: system-ui, sans-serif; }\n.demo-root { min-height: 100vh; display: grid; place-items: center; padding: 24px; }\n")
    write_text(skill_dir / "demo" / "script.js", "document.documentElement.dataset.demoReady = 'true';\n")
    write_text(skill_dir / "demo" / "motion-report.json", json.dumps({"status": "pending", "required": ["frontend runtime audit reports for hydrated DOM/computed styles/CSS/font/network/resource evidence", "desktop/tablet/mobile screenshots", "Playwright video recordings", "Playwright trace zip files", "hover/focus/mousemove probes", "instant-scroll samples", "wheel-scroll samples", "timed-frame samples", "runtime visual signal reports", "reduced-motion fallback capture when relevant", "multi-frame motion or pixel-diff evidence"]}, indent=2) + "\n")
    write_text(skill_dir / "demo" / "implementation-notes.md", "# Demo Implementation Notes\n\nDocument how the runnable demo maps to source-backed style rules, motion/material behavior, scroll states, and where it intentionally differs for originality.\n")
    write_text(skill_dir / "demo" / "verification.md", "# Demo Verification\n\nRecord viewport screenshots, interaction tests, motion/frame checks, accessibility checks, and score summary.\n")


def write_openai_yaml(skill_dir: Path, skill_name: str) -> None:
    display_name = skill_name.replace("-", " ").title()
    default_prompt = f"Use ${skill_name} to style this frontend with the evidence-backed design language."
    write_text(
        skill_dir / "agents" / "openai.yaml",
        "interface:\n"
        f"  display_name: {yaml_string(display_name)}\n"
        f"  short_description: {yaml_string('Evidence-backed frontend style folder')}\n"
        f"  default_prompt: {yaml_string(default_prompt)}\n",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a production frontend style skill folder from style-analysis.json.")
    parser.add_argument("--analysis", required=True, help="Path to style-analysis.json")
    parser.add_argument("--out", required=True, help="Output directory that will contain the generated front-<site> folder")
    parser.add_argument("--name", help="Override site slug or front-<site> folder name")
    parser.add_argument("--force", action="store_true", help="Overwrite the generated folder if it already exists")
    args = parser.parse_args()

    analysis_path = Path(args.analysis).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    if not analysis_path.exists():
        print(f"analysis file not found: {analysis_path}", file=sys.stderr)
        return 2

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if not isinstance(analysis, dict):
        print("analysis root must be a JSON object", file=sys.stderr)
        return 2

    skill_name = infer_front_name(analysis, args.name)
    skill_dir = out_dir / skill_name
    if skill_dir.exists():
        if not args.force:
            print(f"skill folder already exists: {skill_dir}", file=sys.stderr)
            print("rerun with --force to overwrite generated files", file=sys.stderr)
            return 3
        shutil.rmtree(skill_dir)

    make_placeholder_dirs(skill_dir)
    write_text(skill_dir / "SKILL.md", build_skill_markdown(analysis, skill_name))
    write_openai_yaml(skill_dir, skill_name)
    write_role_files(skill_dir)
    write_support_files(skill_dir, analysis)
    copy_score_script(skill_dir)
    copy_frontend_runtime_audit_script(skill_dir)
    copy_playwright_motion_script(skill_dir)

    print(skill_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
