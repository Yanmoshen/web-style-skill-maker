#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const DEFAULT_VIEWPORTS = "1440x900,1024x768,390x844";

function usage() {
  return `
Usage:
  node scripts/frontend_runtime_audit.mjs --url <url> --out <dir> [options]

Options:
  --url <url>              Target URL to audit.
  --out <dir>              Output directory, usually evidence/frontend.
  --label <slug>           Label prefix for files.
  --viewports <list>       Comma list, e.g. 1440x900,1024x768,390x844.
  --wait-ms <number>       Wait after load before auditing. Default 1500.
  --max-elements <number>  Max DOM elements to include in snapshots. Default 600.
  --headed                 Run a visible browser.
  --no-coverage            Disable JS/CSS coverage collection.
  --no-probe-scroll        Disable lazy-load scroll probing.
`.trim();
}

function parseArgs(argv) {
  const args = {
    viewports: DEFAULT_VIEWPORTS,
    waitMs: 1500,
    maxElements: 600,
    headed: false,
    coverage: true,
    probeScroll: true
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--url") args.url = next();
    else if (arg === "--out") args.out = next();
    else if (arg === "--label") args.label = next();
    else if (arg === "--viewports") args.viewports = next();
    else if (arg === "--wait-ms") args.waitMs = Number(next());
    else if (arg === "--max-elements") args.maxElements = Number(next());
    else if (arg === "--headed") args.headed = true;
    else if (arg === "--no-coverage") args.coverage = false;
    else if (arg === "--no-probe-scroll") args.probeScroll = false;
    else throw new Error(`Unknown argument: ${arg}`);
  }

  if (!args.help && (!args.url || !args.out)) {
    throw new Error("--url and --out are required");
  }
  return args;
}

function slugify(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-+/g, "-")
    .slice(0, 72) || "audit";
}

function labelFromUrl(url) {
  try {
    const parsed = new URL(url);
    return slugify(`${parsed.hostname.replace(/^www\./, "")}-${parsed.pathname || "home"}`);
  } catch {
    return "audit";
  }
}

function parseViewports(value) {
  return String(value || DEFAULT_VIEWPORTS)
    .split(",")
    .map(item => item.trim())
    .filter(Boolean)
    .map(item => {
      const match = item.match(/^(\d+)x(\d+)$/i);
      if (!match) throw new Error(`Invalid viewport: ${item}`);
      return {
        label: `${match[1]}x${match[2]}`,
        width: Number(match[1]),
        height: Number(match[2])
      };
    });
}

async function loadPlaywright() {
  const normalize = module => module.chromium ? module : module.default;
  try {
    return normalize(await import("playwright"));
  } catch (firstError) {
    try {
      const requireFromCwd = createRequire(path.join(process.cwd(), "package.json"));
      const resolved = requireFromCwd.resolve("playwright");
      return normalize(await import(pathToFileURL(resolved).href));
    } catch {
      throw new Error(`Playwright is required. Install it in the workspace with npm i -D playwright. Original error: ${firstError.message}`);
    }
  }
}

async function ensureDirs(root) {
  const dirs = {
    root,
    reports: path.join(root, "reports")
  };
  await Promise.all(Object.values(dirs).map(dir => fs.mkdir(dir, { recursive: true })));
  return dirs;
}

function mergeRanges(ranges) {
  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  const merged = [];
  for (const range of sorted) {
    const last = merged[merged.length - 1];
    if (!last || range.start > last.end) {
      merged.push({ start: range.start, end: range.end });
    } else {
      last.end = Math.max(last.end, range.end);
    }
  }
  return merged;
}

function summarizeCoverage(entries) {
  return entries.map(entry => {
    const ranges = mergeRanges(entry.ranges || []);
    const usedBytes = ranges.reduce((sum, range) => sum + Math.max(0, range.end - range.start), 0);
    const totalBytes = entry.text ? entry.text.length : 0;
    return {
      url: entry.url || "inline",
      totalBytes,
      usedBytes,
      usedPercent: totalBytes ? Number(((usedBytes / totalBytes) * 100).toFixed(2)) : 0,
      rangeCount: ranges.length
    };
  }).sort((a, b) => b.totalBytes - a.totalBytes).slice(0, 200);
}

function summarizeAxTree(nodes) {
  const roleCounts = {};
  const namedNodes = [];
  for (const node of nodes || []) {
    const role = node.role?.value || "unknown";
    roleCounts[role] = (roleCounts[role] || 0) + 1;
    const name = node.name?.value || "";
    if (name && namedNodes.length < 200) {
      namedNodes.push({
        role,
        name: String(name).slice(0, 120),
        ignored: Boolean(node.ignored)
      });
    }
  }
  return {
    nodeCount: nodes?.length || 0,
    roleCounts,
    namedNodes
  };
}

function summarizePerformanceMetrics(metrics) {
  const output = {};
  for (const item of metrics || []) {
    output[item.name] = item.value;
  }
  return output;
}

async function collectFrontendSnapshot(page, { viewport, maxElements, networkRecords, coverageSummary, axSummary, performanceMetrics }) {
  const browserSnapshot = await page.evaluate(({ maxElements, viewport }) => {
    const textOf = element => (element?.textContent || "").replace(/\s+/g, " ").trim().slice(0, 140);
    const attr = (element, name) => element.getAttribute(name) || "";
    const rectOf = element => {
      const rect = element.getBoundingClientRect();
      return {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom),
        left: Math.round(rect.left)
      };
    };
    const visible = element => {
      const rect = element.getBoundingClientRect();
      const styles = getComputedStyle(element);
      return rect.width > 1 && rect.height > 1 && styles.visibility !== "hidden" && styles.display !== "none" && Number(styles.opacity || 1) > 0.01;
    };
    const dataAttrs = element => Array.from(element.attributes || [])
      .filter(attribute => attribute.name.startsWith("data-"))
      .slice(0, 12)
      .map(attribute => ({ name: attribute.name, value: attribute.value.slice(0, 120) }));
    const pickStyle = styles => {
      const properties = [
        "display", "position", "zIndex", "boxSizing", "width", "height",
        "marginTop", "marginRight", "marginBottom", "marginLeft",
        "paddingTop", "paddingRight", "paddingBottom", "paddingLeft",
        "fontFamily", "fontSize", "fontWeight", "lineHeight", "letterSpacing", "textTransform",
        "color", "backgroundColor", "backgroundImage",
        "borderTopWidth", "borderTopColor", "borderRadius", "boxShadow",
        "opacity", "transform", "filter", "backdropFilter",
        "animationName", "animationDuration", "animationTimingFunction",
        "transitionProperty", "transitionDuration", "transitionTimingFunction",
        "overflow", "overflowX", "overflowY"
      ];
      return Object.fromEntries(properties.map(property => [property, styles[property] || ""]));
    };
    const describeElement = (element, index = 0) => {
      const styles = getComputedStyle(element);
      return {
        index,
        tag: element.tagName.toLowerCase(),
        id: element.id || "",
        className: typeof element.className === "string" ? element.className.slice(0, 180) : "",
        role: attr(element, "role"),
        ariaLabel: attr(element, "aria-label"),
        title: attr(element, "title"),
        href: attr(element, "href"),
        src: attr(element, "src"),
        alt: attr(element, "alt"),
        text: textOf(element),
        rect: rectOf(element),
        dataAttrs: dataAttrs(element),
        styles: pickStyle(styles)
      };
    };
    const resourceExtension = url => {
      try {
        return new URL(url, location.href).pathname.split(".").pop().toLowerCase().slice(0, 12);
      } catch {
        return "";
      }
    };
    const classifyResource = url => {
      const ext = resourceExtension(url);
      if (["css"].includes(ext)) return "css";
      if (["js", "mjs"].includes(ext)) return "script";
      if (["woff", "woff2", "ttf", "otf"].includes(ext)) return "font";
      if (["png", "jpg", "jpeg", "webp", "gif", "svg", "avif"].includes(ext)) return "image";
      if (["mp4", "webm", "mov"].includes(ext)) return "video";
      if (["glb", "gltf", "bin", "hdr", "exr", "ktx2", "basis", "wasm"].includes(ext)) return "runtime-asset";
      return ext || "other";
    };

    const meta = {
      url: location.href,
      title: document.title,
      lang: document.documentElement.lang || "",
      charset: document.characterSet || "",
      viewportMeta: document.querySelector("meta[name='viewport']")?.content || "",
      canonical: document.querySelector("link[rel='canonical']")?.href || "",
      robots: document.querySelector("meta[name='robots']")?.content || "",
      description: document.querySelector("meta[name='description']")?.content || "",
      openGraph: Array.from(document.querySelectorAll("meta[property^='og:']")).map(item => ({ property: item.getAttribute("property"), content: item.content })).slice(0, 40),
      twitter: Array.from(document.querySelectorAll("meta[name^='twitter:']")).map(item => ({ name: item.getAttribute("name"), content: item.content })).slice(0, 40)
    };

    const cssCustomProperties = {};
    for (const [scope, element] of [["root", document.documentElement], ["body", document.body]]) {
      if (!element) continue;
      const styles = getComputedStyle(element);
      cssCustomProperties[scope] = Array.from(styles)
        .filter(property => property.startsWith("--"))
        .slice(0, 400)
        .map(property => ({ property, value: styles.getPropertyValue(property).trim() }));
    }

    const stylesheets = Array.from(document.styleSheets).map((sheet, index) => ({
      index,
      href: sheet.href || "inline",
      disabled: sheet.disabled,
      media: sheet.media ? Array.from(sheet.media).join(", ") : "",
      ownerTag: sheet.ownerNode?.tagName?.toLowerCase() || ""
    }));

    const cssRuleInventory = {
      inaccessibleStyleSheets: [],
      mediaQueries: [],
      keyframes: [],
      fontFaces: [],
      selectorSamples: []
    };
    for (const sheet of Array.from(document.styleSheets)) {
      let rules = [];
      try {
        rules = Array.from(sheet.cssRules || []);
      } catch (error) {
        cssRuleInventory.inaccessibleStyleSheets.push({ href: sheet.href || "inline", reason: error.name || "inaccessible" });
        continue;
      }
      for (const rule of rules) {
        if (rule.type === CSSRule.STYLE_RULE && cssRuleInventory.selectorSamples.length < 300) {
          cssRuleInventory.selectorSamples.push({
            selector: rule.selectorText,
            propertyCount: rule.style?.length || 0,
            customProperties: Array.from(rule.style || []).filter(property => property.startsWith("--")).slice(0, 20)
          });
        } else if (rule.type === CSSRule.MEDIA_RULE && cssRuleInventory.mediaQueries.length < 120) {
          cssRuleInventory.mediaQueries.push(rule.conditionText);
        } else if (rule.type === CSSRule.KEYFRAMES_RULE && cssRuleInventory.keyframes.length < 120) {
          cssRuleInventory.keyframes.push({
            name: rule.name,
            frameCount: rule.cssRules?.length || 0
          });
        } else if (rule.type === CSSRule.FONT_FACE_RULE && cssRuleInventory.fontFaces.length < 120) {
          cssRuleInventory.fontFaces.push({
            fontFamily: rule.style.getPropertyValue("font-family"),
            fontWeight: rule.style.getPropertyValue("font-weight"),
            fontStyle: rule.style.getPropertyValue("font-style"),
            src: rule.style.getPropertyValue("src").slice(0, 240)
          });
        }
      }
    }

    const fontFaces = document.fonts ? Array.from(document.fonts).map(font => ({
      family: font.family,
      style: font.style,
      weight: font.weight,
      stretch: font.stretch,
      status: font.status,
      variationSettings: font.variationSettings || ""
    })).slice(0, 120) : [];

    const sampleSelectors = [
      "body", "header", "nav", "main", "footer", "section", "article", "aside",
      "h1", "h2", "h3", "p", "a", "button", "input", "textarea", "select",
      "img", "svg", "canvas", "video",
      "[class*='hero' i]", "[class*='card' i]", "[class*='grid' i]", "[class*='menu' i]", "[class*='button' i]"
    ];
    const computedStyleSamples = [];
    for (const selector of sampleSelectors) {
      for (const element of Array.from(document.querySelectorAll(selector)).filter(visible).slice(0, 5)) {
        computedStyleSamples.push({ selector, ...describeElement(element, computedStyleSamples.length) });
      }
    }

    const elements = Array.from(document.querySelectorAll("body *")).slice(0, maxElements).map((element, index) => describeElement(element, index));

    const performanceResources = performance.getEntriesByType("resource").map(entry => ({
      name: entry.name,
      initiatorType: entry.initiatorType,
      duration: Number(entry.duration.toFixed(2)),
      transferSize: entry.transferSize || 0,
      encodedBodySize: entry.encodedBodySize || 0,
      decodedBodySize: entry.decodedBodySize || 0,
      classification: classifyResource(entry.name)
    })).slice(0, 800);
    const resourceSummary = performanceResources.reduce((summary, resource) => {
      const key = resource.classification || resource.initiatorType || "other";
      if (!summary[key]) summary[key] = { count: 0, transferSize: 0, encodedBodySize: 0, decodedBodySize: 0 };
      summary[key].count += 1;
      summary[key].transferSize += resource.transferSize || 0;
      summary[key].encodedBodySize += resource.encodedBodySize || 0;
      summary[key].decodedBodySize += resource.decodedBodySize || 0;
      return summary;
    }, {});

    const images = Array.from(document.images).map((image, index) => ({
      index,
      src: image.currentSrc || image.src || "",
      alt: image.alt || "",
      loading: image.loading || "",
      naturalWidth: image.naturalWidth,
      naturalHeight: image.naturalHeight,
      rect: rectOf(image),
      className: image.className || ""
    })).slice(0, 200);
    const backgroundImages = Array.from(document.querySelectorAll("body *"))
      .map((element, index) => {
        const styles = getComputedStyle(element);
        const backgroundImage = styles.backgroundImage;
        if (!backgroundImage || backgroundImage === "none") return null;
        return {
          index,
          tag: element.tagName.toLowerCase(),
          className: typeof element.className === "string" ? element.className.slice(0, 140) : "",
          backgroundImage: backgroundImage.slice(0, 300),
          rect: rectOf(element)
        };
      })
      .filter(Boolean)
      .slice(0, 120);

    const scripts = Array.from(document.scripts).map((script, index) => ({
      index,
      src: script.src || "",
      type: script.type || "",
      async: script.async,
      defer: script.defer,
      module: script.type === "module",
      inlineLength: script.src ? 0 : (script.textContent || "").length
    })).slice(0, 200);
    const links = Array.from(document.querySelectorAll("link")).map((link, index) => ({
      index,
      rel: link.rel || "",
      href: link.href || "",
      as: link.as || "",
      type: link.type || "",
      media: link.media || "",
      crossOrigin: link.crossOrigin || ""
    })).slice(0, 200);

    const canvasVideo = {
      canvases: Array.from(document.querySelectorAll("canvas")).map((canvas, index) => {
        let webgl = false;
        let webgl2 = false;
        try {
          webgl = Boolean(canvas.getContext("webgl"));
          webgl2 = Boolean(canvas.getContext("webgl2"));
        } catch {
          webgl = false;
          webgl2 = false;
        }
        return {
          index,
          width: canvas.width,
          height: canvas.height,
          rect: rectOf(canvas),
          id: canvas.id || "",
          className: canvas.className || "",
          webgl,
          webgl2
        };
      }),
      videos: Array.from(document.querySelectorAll("video")).map((video, index) => ({
        index,
        src: video.currentSrc || video.src || "",
        poster: video.poster || "",
        autoplay: video.autoplay,
        muted: video.muted,
        loop: video.loop,
        controls: video.controls,
        videoWidth: video.videoWidth,
        videoHeight: video.videoHeight,
        rect: rectOf(video)
      }))
    };

    const animationInventory = {
      computed: Array.from(document.querySelectorAll("body *"))
        .map((element, index) => {
          const styles = getComputedStyle(element);
          const hasAnimation = styles.animationName && styles.animationName !== "none";
          const hasTransition = styles.transitionProperty && styles.transitionProperty !== "all 0s ease 0s" && Number.parseFloat(styles.transitionDuration) > 0;
          if (!hasAnimation && !hasTransition) return null;
          return {
            index,
            tag: element.tagName.toLowerCase(),
            className: typeof element.className === "string" ? element.className.slice(0, 160) : "",
            text: textOf(element),
            rect: rectOf(element),
            animationName: styles.animationName,
            animationDuration: styles.animationDuration,
            animationTimingFunction: styles.animationTimingFunction,
            transitionProperty: styles.transitionProperty,
            transitionDuration: styles.transitionDuration,
            transitionTimingFunction: styles.transitionTimingFunction
          };
        })
        .filter(Boolean)
        .slice(0, 180),
      webAnimations: document.getAnimations ? document.getAnimations().map((animation, index) => ({
        index,
        playState: animation.playState,
        currentTime: animation.currentTime,
        playbackRate: animation.playbackRate,
        effectTarget: animation.effect?.target ? describeElement(animation.effect.target, index) : null
      })).slice(0, 120) : []
    };

    const interactiveSelectors = "a, button, input, select, textarea, details, summary, [role='button'], [role='link'], [aria-haspopup], [tabindex], [contenteditable='true']";
    const interactiveCandidates = Array.from(document.querySelectorAll(interactiveSelectors)).map((element, index) => ({
      index,
      tag: element.tagName.toLowerCase(),
      role: attr(element, "role"),
      type: attr(element, "type"),
      name: attr(element, "name"),
      ariaLabel: attr(element, "aria-label"),
      text: textOf(element),
      href: attr(element, "href"),
      disabled: Boolean(element.disabled || attr(element, "aria-disabled") === "true"),
      tabIndex: element.tabIndex,
      rect: rectOf(element),
      visible: visible(element)
    })).slice(0, 300);

    const forms = Array.from(document.forms).map((form, index) => ({
      index,
      id: form.id || "",
      name: form.name || "",
      method: form.method || "",
      action: form.action || "",
      fields: Array.from(form.elements).map(field => ({
        tag: field.tagName?.toLowerCase() || "",
        type: field.type || "",
        name: field.name || "",
        id: field.id || "",
        placeholder: field.getAttribute?.("placeholder") || "",
        ariaLabel: field.getAttribute?.("aria-label") || ""
      })).slice(0, 80)
    })).slice(0, 40);

    const eventAttributes = ["onclick", "onmouseenter", "onmouseleave", "onmousemove", "onscroll", "onchange", "oninput", "onsubmit"];
    const eventAttributeCounts = Object.fromEntries(eventAttributes.map(name => [name, document.querySelectorAll(`[${name}]`).length]));

    const landmarks = Array.from(document.querySelectorAll("header, nav, main, footer, aside, section, article, [role]")).map((element, index) => ({
      index,
      tag: element.tagName.toLowerCase(),
      role: attr(element, "role"),
      ariaLabel: attr(element, "aria-label"),
      text: textOf(element),
      rect: rectOf(element)
    })).slice(0, 160);
    const unnamedControls = interactiveCandidates.filter(item => item.visible && ["button", "a"].includes(item.tag) && !item.text && !item.ariaLabel && !item.name).slice(0, 120);

    const documentWidth = Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth || 0);
    const horizontalOverflow = documentWidth > window.innerWidth + 2;
    const overflowingElements = Array.from(document.querySelectorAll("body *"))
      .map((element, index) => {
        const rect = element.getBoundingClientRect();
        if (!visible(element)) return null;
        if (rect.right <= window.innerWidth + 2 && rect.left >= -2) return null;
        const styles = getComputedStyle(element);
        return {
          index,
          tag: element.tagName.toLowerCase(),
          className: typeof element.className === "string" ? element.className.slice(0, 160) : "",
          text: textOf(element),
          rect: rectOf(element),
          position: styles.position,
          overflowX: styles.overflowX
        };
      })
      .filter(Boolean)
      .slice(0, 120);
    const clippedText = Array.from(document.querySelectorAll("body *"))
      .map((element, index) => {
        const styles = getComputedStyle(element);
        const clips = element.scrollWidth > element.clientWidth + 2 || element.scrollHeight > element.clientHeight + 2;
        if (!clips || !visible(element)) return null;
        if (!["hidden", "clip", "auto", "scroll"].includes(styles.overflow) && !["hidden", "clip", "auto", "scroll"].includes(styles.overflowX) && !["hidden", "clip", "auto", "scroll"].includes(styles.overflowY)) return null;
        return {
          index,
          tag: element.tagName.toLowerCase(),
          className: typeof element.className === "string" ? element.className.slice(0, 160) : "",
          text: textOf(element),
          rect: rectOf(element),
          clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth,
          clientHeight: element.clientHeight,
          scrollHeight: element.scrollHeight,
          overflow: styles.overflow,
          overflowX: styles.overflowX,
          overflowY: styles.overflowY
        };
      })
      .filter(Boolean)
      .slice(0, 120);
    const positionedLayers = Array.from(document.querySelectorAll("body *"))
      .map((element, index) => {
        const styles = getComputedStyle(element);
        if (!["fixed", "sticky", "absolute"].includes(styles.position) && styles.zIndex === "auto") return null;
        return {
          index,
          tag: element.tagName.toLowerCase(),
          className: typeof element.className === "string" ? element.className.slice(0, 160) : "",
          text: textOf(element),
          rect: rectOf(element),
          position: styles.position,
          zIndex: styles.zIndex
        };
      })
      .filter(Boolean)
      .slice(0, 160);
    const sections = Array.from(document.querySelectorAll("main > *, body > main, section, article")).map((element, index) => ({
      index,
      tag: element.tagName.toLowerCase(),
      className: typeof element.className === "string" ? element.className.slice(0, 180) : "",
      text: textOf(element),
      rect: rectOf(element)
    })).slice(0, 120);

    const scriptText = scripts.map(script => script.src).join(" ").toLowerCase();
    const htmlText = document.documentElement.outerHTML.slice(0, 500000).toLowerCase();
    const frameworkSignals = {
      next: Boolean(window.__NEXT_DATA__ || document.querySelector("#__next") || scriptText.includes("_next/")),
      nuxt: Boolean(window.__NUXT__ || document.querySelector("#__nuxt") || scriptText.includes("_nuxt/")),
      gatsby: Boolean(window.___gatsby || scriptText.includes("gatsby")),
      astro: Boolean(document.querySelector("[data-astro-cid]") || scriptText.includes("astro")),
      vite: Boolean(scriptText.includes("/@vite/") || scriptText.includes("vite")),
      remix: Boolean(scriptText.includes("@remix-run") || htmlText.includes("__remixcontext")),
      svelte: Boolean(scriptText.includes("svelte") || htmlText.includes("svelte-")),
      angular: Boolean(document.querySelector("[ng-version]") || scriptText.includes("angular")),
      react: Boolean(window.__REACT_DEVTOOLS_GLOBAL_HOOK__ || scriptText.includes("react") || document.querySelector("#root, [data-reactroot]")),
      vue: Boolean(window.__VUE__ || scriptText.includes("vue") || document.querySelector("[data-v-]")),
      framer: Boolean(window.Framer || document.querySelector("[data-framer-name], [data-framer-component-type]") || scriptText.includes("framer")),
      webflow: Boolean(window.Webflow || document.documentElement.hasAttribute("data-wf-page") || scriptText.includes("webflow")),
      gsap: Boolean(window.gsap || window.ScrollTrigger || scriptText.includes("gsap")),
      lottie: Boolean(window.lottie || scriptText.includes("lottie")),
      rive: Boolean(window.Rive || scriptText.includes("rive")),
      three: Boolean(window.THREE || scriptText.includes("three")),
      babylon: Boolean(window.BABYLON || scriptText.includes("babylon"))
    };

    let storageKeys = { localStorage: [], sessionStorage: [] };
    try {
      storageKeys = {
        localStorage: Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index)).filter(Boolean).slice(0, 80),
        sessionStorage: Array.from({ length: sessionStorage.length }, (_, index) => sessionStorage.key(index)).filter(Boolean).slice(0, 80)
      };
    } catch {
      storageKeys = { localStorage: ["inaccessible"], sessionStorage: ["inaccessible"] };
    }

    return {
      capturedAt: new Date().toISOString(),
      viewport,
      meta,
      stylesheets,
      cssRuleInventory,
      cssCustomProperties,
      fontFaces,
      computedStyleSamples,
      elementInventory: elements,
      scripts,
      links,
      images,
      backgroundImages,
      canvasVideo,
      animationInventory,
      interactiveCandidates,
      forms,
      eventAttributeCounts,
      accessibilityDomSummary: {
        landmarks,
        unnamedControls,
        imageCount: images.length,
        imagesMissingAlt: images.filter(image => !image.alt).length
      },
      layoutAudit: {
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight,
        documentWidth,
        scrollHeight: document.documentElement.scrollHeight,
        horizontalOverflow,
        overflowingElements,
        clippedText,
        positionedLayers,
        sections
      },
      performanceResources,
      resourceSummary,
      frameworkSignals,
      storageKeysOnly: storageKeys
    };
  }, { maxElements, viewport });

  return {
    ...browserSnapshot,
    networkRecords: networkRecords.slice(0, 800),
    networkSummary: summarizeNetwork(networkRecords),
    coverageSummary,
    accessibilityTreeSummary: axSummary,
    performanceMetrics
  };
}

function summarizeNetwork(records) {
  const summary = {};
  for (const record of records) {
    const key = record.resourceType || record.classification || "other";
    if (!summary[key]) summary[key] = { count: 0, ok: 0, failed: 0, bytes: 0 };
    summary[key].count += 1;
    if (record.failure) summary[key].failed += 1;
    else if (record.status && record.status < 400) summary[key].ok += 1;
    summary[key].bytes += record.contentLength || 0;
  }
  return summary;
}

function classifyRequestUrl(url) {
  try {
    const ext = new URL(url).pathname.split(".").pop().toLowerCase();
    if (["css"].includes(ext)) return "css";
    if (["js", "mjs"].includes(ext)) return "script";
    if (["woff", "woff2", "ttf", "otf"].includes(ext)) return "font";
    if (["png", "jpg", "jpeg", "webp", "gif", "svg", "avif"].includes(ext)) return "image";
    if (["mp4", "webm", "mov"].includes(ext)) return "video";
    if (["glb", "gltf", "bin", "hdr", "exr", "ktx2", "basis", "wasm"].includes(ext)) return "runtime-asset";
    return ext || "other";
  } catch {
    return "other";
  }
}

async function probeScroll(page) {
  const metrics = await page.evaluate(() => ({
    height: document.documentElement.scrollHeight,
    viewport: window.innerHeight
  }));
  const maxScroll = Math.max(0, metrics.height - metrics.viewport);
  for (const y of [...new Set([0, 0.33, 0.66, 1].map(ratio => Math.round(maxScroll * ratio)))]) {
    await page.evaluate(scrollY => window.scrollTo({ top: scrollY, behavior: "instant" }), y);
    await page.waitForTimeout(300);
  }
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.waitForTimeout(300);
}

async function runViewport({ chromium, args, dirs, viewport }) {
  const label = `${args.label || labelFromUrl(args.url)}-${viewport.label}`;
  const browser = await chromium.launch({ headless: !args.headed });
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1
  });
  const page = await context.newPage();
  const client = await context.newCDPSession(page);
  await client.send("Performance.enable").catch(() => {});

  const networkRecords = [];
  const requestRecords = new Map();
  page.on("request", request => {
    const record = {
      url: request.url(),
      method: request.method(),
      resourceType: request.resourceType(),
      classification: classifyRequestUrl(request.url()),
      status: null,
      mimeType: "",
      contentLength: 0,
      failure: "",
      timing: typeof request.timing === "function" ? request.timing() : null
    };
    requestRecords.set(request, record);
    networkRecords.push(record);
  });
  page.on("response", response => {
    const request = response.request();
    const record = requestRecords.get(request);
    if (!record) return;
    const headers = response.headers();
    record.status = response.status();
    record.mimeType = headers["content-type"] || "";
    record.contentLength = Number(headers["content-length"] || 0);
    record.fromServiceWorker = response.fromServiceWorker();
  });
  page.on("requestfailed", request => {
    const record = requestRecords.get(request);
    if (record) record.failure = request.failure()?.errorText || "request failed";
  });

  let coverageStarted = false;
  if (args.coverage && page.coverage) {
    await page.coverage.startJSCoverage({ resetOnNavigation: false }).then(() => { coverageStarted = true; }).catch(() => {});
    await page.coverage.startCSSCoverage({ resetOnNavigation: false }).catch(() => {});
  }

  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(args.waitMs);
  if (args.probeScroll) {
    await probeScroll(page);
  }

  const coverageSummary = { js: [], css: [], unavailable: !coverageStarted };
  if (coverageStarted) {
    const [jsCoverage, cssCoverage] = await Promise.all([
      page.coverage.stopJSCoverage().catch(() => []),
      page.coverage.stopCSSCoverage().catch(() => [])
    ]);
    coverageSummary.js = summarizeCoverage(jsCoverage);
    coverageSummary.css = summarizeCoverage(cssCoverage);
  }

  const axTree = await client.send("Accessibility.getFullAXTree").catch(() => ({ nodes: [] }));
  const performanceResult = await client.send("Performance.getMetrics").catch(() => ({ metrics: [] }));
  const report = await collectFrontendSnapshot(page, {
    viewport,
    maxElements: args.maxElements,
    networkRecords,
    coverageSummary,
    axSummary: summarizeAxTree(axTree.nodes),
    performanceMetrics: summarizePerformanceMetrics(performanceResult.metrics)
  });

  const reportPath = path.join(dirs.reports, `${label}-frontend-runtime-audit.json`);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + "\n", "utf8");
  await context.close();
  await browser.close();
  return {
    label,
    viewport,
    report: reportPath,
    networkSummary: report.networkSummary,
    resourceSummary: report.resourceSummary,
    frameworkSignals: report.frameworkSignals,
    layoutAudit: {
      horizontalOverflow: report.layoutAudit.horizontalOverflow,
      overflowingCount: report.layoutAudit.overflowingElements.length,
      clippedTextCount: report.layoutAudit.clippedText.length
    },
    coverage: {
      jsFiles: report.coverageSummary.js.length,
      cssFiles: report.coverageSummary.css.length,
      unavailable: report.coverageSummary.unavailable
    },
    accessibility: {
      axNodeCount: report.accessibilityTreeSummary.nodeCount,
      unnamedControlCount: report.accessibilityDomSummary.unnamedControls.length,
      imagesMissingAlt: report.accessibilityDomSummary.imagesMissingAlt
    }
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    return;
  }

  const { chromium } = await loadPlaywright();
  const outRoot = path.resolve(args.out);
  const dirs = await ensureDirs(outRoot);
  const viewports = parseViewports(args.viewports);
  const results = [];

  for (const viewport of viewports) {
    results.push(await runViewport({ chromium, args, dirs, viewport }));
  }

  const summary = {
    url: args.url,
    capturedAt: new Date().toISOString(),
    output: outRoot,
    viewports,
    results
  };
  const summaryPath = path.join(dirs.reports, `${args.label || labelFromUrl(args.url)}-frontend-runtime-summary.json`);
  await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({ ok: true, summary: summaryPath, results }, null, 2));
}

main().catch(error => {
  console.error(error.stack || error.message);
  console.error("\n" + usage());
  process.exit(1);
});
