/**
 * MyGab TV scraper API starter (Cloudflare Workers).
 *
 * This is a browser-friendly backend bridge, NOT a port of every PAhelper
 * site adapter. It fetches public pages server-side and extracts common
 * video/player links. PAhelper adapters require individual porting/testing.
 *
 * Required Worker variable:
 *   ALLOWED_DOMAINS = comma-separated list of adult-only domains you have
 *   personally reviewed, e.g. "example.invalid,another.example"
 *
 * Deploy this Worker separately and set its URL in MyGab TV Admin.
 */
const BLOCKED_HOSTS = new Set(["youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"]);
const BLOCKED = /underage|under-age|\bminor\b|\bchildren?\b|schoolgirl|schoolboy|teen(?:ager)?|barely[\s_-]*legal|young[\s_-]*girl/i;
const MEDIA = /\.(mp4|webm|ogg|m3u8)(?:$|[?#])/i;
const PLAYER_PATH = /\/(embed|player|video|videos|watch)(\/|$)/i;

function allowedDomains(env) {
  return String(env.ALLOWED_DOMAINS || "").split(",").map(x => x.trim().toLowerCase().replace(/^https?:\/\//, "").split("/")[0]).filter(Boolean);
}
function safeUrl(raw, env) {
  try {
    const u = new URL(raw);
    if (!["http:", "https:"].includes(u.protocol)) return null;
    const host = u.hostname.toLowerCase().replace(/^www\./, "");
    if (BLOCKED_HOSTS.has(u.hostname.toLowerCase()) || host.endsWith(".youtube.com") || u.hostname.includes("youtu.be")) return null;
    const approved = allowedDomains(env).some(d => host === d.replace(/^www\./, "") || host.endsWith("." + d.replace(/^www\./, "")));
    return approved ? u : null;
  } catch { return null; }
}
function extract(html, pageUrl, env, keyword) {
  const found = new Map();
  const add = (raw, title = "Video from scanned page", force = false) => {
    if (!raw) return;
    let u;
    try { u = new URL(raw, pageUrl); } catch { return; }
    if (!safeUrl(u.href, env) || BLOCKED.test(title + " " + u.href)) return;
    if (!(MEDIA.test(u.href) || PLAYER_PATH.test(u.pathname) || force)) return;
    if (keyword && !String(title + " " + u.href).toLowerCase().includes(keyword.toLowerCase())) return;
    if (!found.has(u.href)) found.set(u.href, { title: String(title).slice(0, 180), url: u.href, embed: u.href });
  };
  // HTML attributes; intentionally conservative and not a full JS renderer.
  const tags = html.match(/<(?:video|source|iframe|a)\b[^>]*>/gi) || [];
  for (const tag of tags) {
    const attr = n => {
      const re = new RegExp("\\b" + n + "\\s*=\\s*([\"'])(.*?)\\1", "i");
      return tag.match(re)?.[2] || null;
    };
    const title = attr("title") || attr("aria-label") || attr("alt") || "Video from scanned page";
    add(attr("src") || attr("data-src") || attr("href"), title, /<(?:video|source|iframe)\b/i.test(tag));
  }
  for (const m of html.matchAll(/"(?:contentUrl|embedUrl)"\s*:\s*"([^"]+)"/gi)) add(m[1], "Video from page metadata", true);
  for (const m of html.matchAll(/https?:\\?\/\\?\/[^\s"'<>\\]+/gi)) add(m[0].replace(/\\\//g, "/"), "Video link");
  return [...found.values()];
}
export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "*";
    const headers = {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Vary": "Origin",
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    };
    if (request.method === "OPTIONS") return new Response(null, { headers });
    const u = new URL(request.url);
    if (u.pathname === "/health") return Response.json({ ok: true, service: "MyGab TV scraper API", mode: "generic-public-page-scanner" }, { headers });
    if (u.pathname !== "/scan" || request.method !== "GET") return Response.json({ error: "Use GET /scan?url=https%3A%2F%2Fapproved-domain%2Fpage&keyword=optional" }, { status: 404, headers });
    const raw = u.searchParams.get("url");
    if (!raw) return Response.json({ error: "Missing url parameter" }, { status: 400, headers });
    const target = safeUrl(raw, env);
    if (!target) return Response.json({ error: "URL is invalid or its domain is not approved by the server" }, { status: 403, headers });
    try {
      const res = await fetch(target.href, { headers: { "User-Agent": "MyGabTV-Reader/1.0 (+public-page metadata scanner)", "Accept": "text/html,application/xhtml+xml" }, redirect: "follow", signal: AbortSignal.timeout(12000) });
      if (!res.ok) return Response.json({ error: "Source returned HTTP " + res.status }, { status: 502, headers });
      const finalUrl = new URL(res.url);
      if (!safeUrl(finalUrl.href, env)) return Response.json({ error: "Redirect target is not an approved domain" }, { status: 403, headers });
      const type = res.headers.get("content-type") || "";
      if (!type.includes("text/html") && !type.includes("text/plain")) return Response.json({ error: "Source did not return readable HTML/text" }, { status: 415, headers });
      const html = (await res.text()).slice(0, 2_000_000);
      const items = extract(html, finalUrl.href, env, u.searchParams.get("keyword") || "");
      return Response.json({ ok: true, source: finalUrl.hostname, count: items.length, items, note: "Generic extractor only; site-specific players may not be supported. Review results before playback." }, { headers });
    } catch (e) {
      return Response.json({ error: "Could not read public page: " + String(e?.message || e) }, { status: 502, headers });
    }
  }
};
