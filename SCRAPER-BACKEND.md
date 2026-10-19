# MyGab TV hosted scraper bridge

This Worker provides a same-origin-independent HTTP API that the Fire Stick browser can call. It is a generic public-page scanner, **not a complete port of PAhelper**. PAhelper is a Plex metadata agent with site-specific Python adapters; those adapters need to be ported and tested individually.

## Deploy (one-time setup)

1. Create a Cloudflare account and open Workers & Pages.
2. Create a Worker named `mygab-tv-scraper`.
3. Paste the contents of `worker.js` into its editor and deploy.
4. In Worker settings, add a variable named `ALLOWED_DOMAINS` containing only domains you have verified are adults-only, comma-separated. Do not include YouTube.
5. Test `https://YOUR-WORKER.workers.dev/health`; it should return `{"ok":true,...}`.
6. Test `/scan?url=` with a URL-encoded public page from an approved domain.

Example:
```
https://YOUR-WORKER.workers.dev/scan?url=https%3A%2F%2Fexample.invalid%2Fvideos
```

## Security and limitations

- The server-side domain allowlist is mandatory. It prevents the Worker from becoming an unrestricted URL fetcher and blocks YouTube.
- Do not use it to bypass authentication, paywalls, access controls, DRM, or website restrictions.
- This extracts common public HTML media/player links only. It cannot render JavaScript, execute the PAhelper plugin, or guarantee a playable stream.
- The site's age/content cannot be reliably determined from titles or URLs alone; use only domains you have independently verified and review results.
- The worker must be deployed separately; GitHub Pages cannot run server-side code. No live endpoint is configured until you deploy it and enter its URL in MyGab TV.
