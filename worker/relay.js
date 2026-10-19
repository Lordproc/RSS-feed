// Relay for RSS-feed: fetches a Substack feed from Cloudflare's network, because Substack
// refuses requests from GitHub's servers. Only Substack feed addresses are relayed.
// Paste this into a Cloudflare Worker and deploy. Use: https://<worker>.workers.dev/?url=<feed>

export default {
  async fetch(request) {
    let target;
    try {
      target = new URL(new URL(request.url).searchParams.get("url"));
    } catch {
      return new Response("Add ?url= with a Substack feed address.", { status: 400 });
    }
    const host = target.hostname;
    const isSubstack = host === "substack.com" || host.endsWith(".substack.com");
    if (target.protocol !== "https:" || !isSubstack || !target.pathname.startsWith("/feed")) {
      return new Response("Only Substack feeds are relayed.", { status: 403 });
    }
    const upstream = await fetch(target, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
      },
      cf: { cacheTtl: 900, cacheEverything: true },  // keep a copy for 15 minutes
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("Content-Type") || "application/xml" },
    });
  },
};
