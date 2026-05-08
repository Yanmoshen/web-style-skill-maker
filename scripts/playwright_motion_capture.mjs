#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const DEFAULT_VIEWPORTS = "1440x900,1024x768,390x844";

function usage() {
  return `
Usage:
  node scripts/playwright_motion_capture.mjs --url <url> --out <dir> [options]

Options:
  --url <url>              Target URL to capture.
  --out <dir>              Output directory, usually evidence/motion.
  --label <slug>           Label prefix for files.
  --viewports <list>       Comma list, e.g. 1440x900,1024x768,390x844.
  --duration-ms <number>   Approximate capture duration per viewport. Default 12000.
  --wait-ms <number>       Wait after load before probing. Default 1500.
  --headed                 Run a visible browser.
  --no-video               Disable Playwright video recording.
  --no-trace               Disable Playwright trace.
  --no-hover               Disable hover probes.
  --no-scroll              Disable scroll probes.
  --reduced-motion         Capture with prefers-reduced-motion: reduce.
`.trim();
}

function parseArgs(argv) {
  const args = {
    viewports: DEFAULT_VIEWPORTS,
    durationMs: 12000,
    waitMs: 1500,
    headed: false,
    video: true,
    trace: true,
    hover: true,
    scroll: true,
    reducedMotion: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const next = () => argv[++index];
    if (arg === "--help" || arg === "-h") args.help = true;
    else if (arg === "--url") args.url = next();
    else if (arg === "--out") args.out = next();
    else if (arg === "--label") args.label = next();
    else if (arg === "--viewports") args.viewports = next();
    else if (arg === "--duration-ms") args.durationMs = Number(next());
    else if (arg === "--wait-ms") args.waitMs = Number(next());
    else if (arg === "--headed") args.headed = true;
    else if (arg === "--no-video") args.video = false;
    else if (arg === "--no-trace") args.trace = false;
    else if (arg === "--no-hover") args.hover = false;
    else if (arg === "--no-scroll") args.scroll = false;
    else if (arg === "--reduced-motion") args.reducedMotion = true;
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
    .slice(0, 72) || "capture";
}

function labelFromUrl(url) {
  try {
    const parsed = new URL(url);
    return slugify(`${parsed.hostname.replace(/^www\./, "")}-${parsed.pathname || "home"}`);
  } catch {
    return "capture";
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
    screenshots: path.join(root, "screenshots"),
    videos: path.join(root, "videos"),
    traces: path.join(root, "traces"),
    reports: path.join(root, "reports")
  };
  await Promise.all(Object.values(dirs).map(dir => fs.mkdir(dir, { recursive: true })));
  return dirs;
}

async function getRuntimeSignals(page) {
  return await page.evaluate(() => {
    const resources = performance.getEntriesByType("resource").map(entry => entry.name);
    const assetPatterns = /\.(glb|gltf|bin|hdr|exr|ktx2|basis|wasm|mp4|webm|mov)(\?|$)|normal|roughness|metalness|diffuse|albedo|reflection|displacement|\/frames\/|sequence|sprite/i;
    const assets = resources.filter(url => assetPatterns.test(url)).slice(0, 200);
    const globals = ["THREE", "BABYLON", "gsap", "ScrollTrigger", "lottie", "Rive", "Lenis", "Webflow", "Framer", "__NEXT_DATA__", "___gatsby"]
      .filter(key => Boolean(window[key]));
    const canvases = [...document.querySelectorAll("canvas")].map((canvas, index) => {
      let webgl = false;
      try {
        webgl = Boolean(canvas.getContext("webgl") || canvas.getContext("webgl2"));
      } catch {
        webgl = false;
      }
      const rect = canvas.getBoundingClientRect();
      return {
        index,
        width: canvas.width,
        height: canvas.height,
        clientWidth: Math.round(rect.width),
        clientHeight: Math.round(rect.height),
        className: canvas.className || "",
        id: canvas.id || "",
        webgl
      };
    });
    const videos = [...document.querySelectorAll("video")].map((video, index) => ({
      index,
      src: video.currentSrc || video.src || "",
      poster: video.poster || "",
      videoWidth: video.videoWidth,
      videoHeight: video.videoHeight,
      className: video.className || ""
    }));
    const animatedElements = [...document.querySelectorAll("*")]
      .map((element, index) => {
        const styles = getComputedStyle(element);
        const animation = styles.animationName && styles.animationName !== "none";
        const transition = Number.parseFloat(styles.transitionDuration) > 0;
        if (!animation && !transition) return null;
        const rect = element.getBoundingClientRect();
        return {
          index,
          tag: element.tagName.toLowerCase(),
          text: (element.textContent || "").trim().slice(0, 80),
          className: element.className ? String(element.className).slice(0, 120) : "",
          animationName: styles.animationName,
          transitionDuration: styles.transitionDuration,
          rect: {
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height)
          }
        };
      })
      .filter(Boolean)
      .slice(0, 100);
    return {
      url: location.href,
      title: document.title,
      bodyClass: document.body?.className ? String(document.body.className) : "",
      scrollHeight: document.documentElement.scrollHeight,
      viewportHeight: window.innerHeight,
      resources: assets,
      globals,
      canvases,
      videos,
      animatedElements
    };
  });
}

async function visibleHoverCandidates(page) {
  return await page.evaluate(() => {
    const selectors = "a, button, [role='button'], [data-menu-trigger], [aria-haspopup], input, select, textarea, canvas, video";
    return [...document.querySelectorAll(selectors)]
      .map((element, index) => {
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        const visible = rect.width >= 8 && rect.height >= 8 && style.visibility !== "hidden" && style.display !== "none" && rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth;
        if (!visible) return null;
        return {
          index,
          tag: element.tagName.toLowerCase(),
          text: (element.textContent || element.getAttribute("aria-label") || element.getAttribute("title") || "").trim().slice(0, 80),
          x: Math.round(rect.left + rect.width / 2),
          y: Math.round(rect.top + rect.height / 2),
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        };
      })
      .filter(Boolean)
      .slice(0, 12);
  });
}

async function captureScreenshot(page, file, fullPage = false) {
  await page.screenshot({ path: file, fullPage });
  return file;
}

async function runViewport({ chromium, args, dirs, viewport }) {
  const label = `${args.label || labelFromUrl(args.url)}-${viewport.label}${args.reducedMotion ? "-reduced-motion" : ""}`;
  const browser = await chromium.launch({
    headless: !args.headed,
  });
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    reducedMotion: args.reducedMotion ? "reduce" : "no-preference",
    recordVideo: args.video ? {
      dir: dirs.videos,
      size: { width: viewport.width, height: viewport.height }
    } : undefined
  });

  if (args.trace) {
    await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
  }

  const page = await context.newPage();
  const consoleMessages = [];
  const requestFailures = [];
  page.on("console", message => {
    if (["error", "warning"].includes(message.type())) {
      consoleMessages.push({ type: message.type(), text: message.text().slice(0, 500) });
    }
  });
  page.on("requestfailed", request => {
    requestFailures.push({ url: request.url(), failure: request.failure()?.errorText || "request failed" });
  });

  await page.goto(args.url, { waitUntil: "domcontentloaded", timeout: 45000 });
  await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(args.waitMs);

  const screenshots = [];
  screenshots.push(await captureScreenshot(page, path.join(dirs.screenshots, `${label}-initial.png`)));
  const runtimeSignals = await getRuntimeSignals(page);

  const hoverSamples = [];
  if (args.hover) {
    const candidates = await visibleHoverCandidates(page);
    for (const candidate of candidates.slice(0, 8)) {
      await page.mouse.move(candidate.x, candidate.y, { steps: 8 });
      await page.waitForTimeout(350);
      const file = path.join(dirs.screenshots, `${label}-hover-${candidate.index}.png`);
      screenshots.push(await captureScreenshot(page, file));
      hoverSamples.push({ ...candidate, screenshot: file });
    }
  }

  const scrollSamples = [];
  if (args.scroll) {
    const pageMetrics = await page.evaluate(() => ({
      height: document.documentElement.scrollHeight,
      viewport: window.innerHeight
    }));
    const maxScroll = Math.max(0, pageMetrics.height - pageMetrics.viewport);
    const positions = [...new Set([0, 0.18, 0.35, 0.55, 0.75, 1].map(ratio => Math.round(maxScroll * ratio)))];
    for (const y of positions) {
      await page.evaluate(scrollY => window.scrollTo({ top: scrollY, behavior: "instant" }), y);
      await page.waitForTimeout(450);
      const actualY = await page.evaluate(() => Math.round(window.scrollY));
      const file = path.join(dirs.screenshots, `${label}-scroll-${String(actualY).padStart(5, "0")}.png`);
      screenshots.push(await captureScreenshot(page, file));
      scrollSamples.push({ requestedY: y, actualY, screenshot: file });
      await page.mouse.wheel(0, Math.max(120, Math.round(pageMetrics.viewport * 0.35)));
      await page.waitForTimeout(250);
    }
  }

  const endTime = Date.now() + Math.max(1000, args.durationMs - args.waitMs);
  let motionFrame = 0;
  while (Date.now() < endTime && motionFrame < 8) {
    const x = Math.round((0.15 + (motionFrame % 4) * 0.23) * viewport.width);
    const y = Math.round((0.24 + (motionFrame % 3) * 0.22) * viewport.height);
    await page.mouse.move(x, y, { steps: 12 });
    await page.waitForTimeout(500);
    const file = path.join(dirs.screenshots, `${label}-timed-${motionFrame}.png`);
    screenshots.push(await captureScreenshot(page, file));
    motionFrame += 1;
  }

  const finalSignals = await getRuntimeSignals(page);
  let tracePath = "";
  if (args.trace) {
    tracePath = path.join(dirs.traces, `${label}.zip`);
    await context.tracing.stop({ path: tracePath });
  }

  const video = page.video();
  await page.close();
  await context.close();
  let videoPath = "";
  if (video) {
    videoPath = path.join(dirs.videos, `${label}.webm`);
    await video.saveAs(videoPath).catch(async () => {
      videoPath = await video.path().catch(() => "");
    });
  }
  await browser.close();

  const report = {
    label,
    url: args.url,
    viewport,
    reducedMotion: args.reducedMotion,
    screenshots,
    video: videoPath,
    trace: tracePath,
    hoverSamples,
    scrollSamples,
    runtimeSignals,
    finalSignals,
    consoleMessages,
    requestFailures: requestFailures.slice(0, 80)
  };
  const reportPath = path.join(dirs.reports, `${label}-motion-report.json`);
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + "\n", "utf8");
  return { ...report, report: reportPath };
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
    viewports,
    output: outRoot,
    results: results.map(result => ({
      label: result.label,
      viewport: result.viewport,
      report: result.report,
      video: result.video,
      trace: result.trace,
      screenshotCount: result.screenshots.length,
      hoverCount: result.hoverSamples.length,
      scrollCount: result.scrollSamples.length,
      runtimeSignals: {
        canvases: result.runtimeSignals.canvases,
        videos: result.runtimeSignals.videos,
        globals: result.runtimeSignals.globals,
        resources: result.runtimeSignals.resources
      }
    }))
  };
  const summaryPath = path.join(dirs.reports, `${args.label || labelFromUrl(args.url)}-playwright-motion-summary.json`);
  await fs.writeFile(summaryPath, JSON.stringify(summary, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({ ok: true, summary: summaryPath, results: summary.results }, null, 2));
}

main().catch(error => {
  console.error(error.stack || error.message);
  console.error("\n" + usage());
  process.exit(1);
});
