// chartgrab in-page collector (read-only).
// Returns a JSON-serialisable snapshot of every visible <canvas> (RGBA pixels, run-length
// encoded) plus visible text nodes with their page coordinates (for axis labels / titles).
// It never clicks, types, scrolls, mutates the page or performs network requests.
// Usage: evaluate `(${source})(options)` in the page; options are optional.
(function collect(options) {
  const opt = Object.assign({
    minWidth: 120, minHeight: 80,          // ignore tiny canvases (icons, sparklines)
    maxCanvases: 64, maxPixels: 8_000_000, // safety limits
    canvasSelector: 'canvas',
    textSelector: 'body',
    maxTextNodes: 20000,
  }, options || {});

  const dpr = window.devicePixelRatio || 1;
  const visible = (r) => r.width > 0 && r.height > 0 &&
    r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;

  // Run-length encode RGBA as [r,g,b,a,count,...] so flat chart backgrounds compress well.
  function rle(data) {
    const out = [];
    let pr = data[0], pg = data[1], pb = data[2], pa = data[3], n = 0;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2], a = data[i + 3];
      if (r === pr && g === pg && b === pb && a === pa && n < 65535) { n++; continue; }
      out.push(pr, pg, pb, pa, n); pr = r; pg = g; pb = b; pa = a; n = 1;
    }
    out.push(pr, pg, pb, pa, n);
    return out;
  }

  const canvases = [];
  let pixels = 0;
  for (const el of document.querySelectorAll(opt.canvasSelector)) {
    if (canvases.length >= opt.maxCanvases) break;
    const rect = el.getBoundingClientRect();
    if (!visible(rect) || rect.width < opt.minWidth || rect.height < opt.minHeight) continue;
    const entry = {
      index: canvases.length,
      css: {x: rect.left + scrollX, y: rect.top + scrollY, width: rect.width, height: rect.height},
      width: el.width, height: el.height, error: null, rgba_rle: null,
    };
    try {
      if (pixels + el.width * el.height > opt.maxPixels) throw new Error('PIXEL_BUDGET_EXCEEDED');
      const ctx = el.getContext('2d');
      if (!ctx) throw new Error('NOT_2D_CANVAS');          // WebGL canvases are reported, not read
      entry.rgba_rle = rle(ctx.getImageData(0, 0, el.width, el.height).data);
      pixels += el.width * el.height;
    } catch (e) {
      entry.error = String(e && e.message || e);           // e.g. tainted (cross-origin) canvas
    }
    canvases.push(entry);
  }

  const texts = [];
  const walker = document.createTreeWalker(
    document.querySelector(opt.textSelector) || document.body, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  while (walker.nextNode() && texts.length < opt.maxTextNodes) {
    const node = walker.currentNode;
    const text = node.textContent.trim();
    if (!text) continue;
    range.selectNodeContents(node);
    const r = range.getBoundingClientRect();
    if (!visible(r)) continue;
    texts.push({text, x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height});
  }

  return {
    schema: 'CHARTGRAB_SNAPSHOT_V1',
    url: location.href,
    title: document.title,
    captured_at: new Date().toISOString(),
    device_pixel_ratio: dpr,
    canvases, texts,
  };
})
