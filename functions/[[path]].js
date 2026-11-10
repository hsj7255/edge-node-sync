// Cloudflare Pages Function: Quota & Subscription Gateway
// Pure Edge Gatekeeper 路 Dynamic Quota Header Injection 路 Anti-Probe Security

const AUTH_KEY = "0e12affd-6afa-48bf-bb85-5272fcc0504e".replace(/-/g, "").toLowerCase();

export async function onRequest(context) {
    const { request, next } = context;
    const url = new URL(request.url);
    const path = url.pathname.toLowerCase();

    // Only process subscription files and routes
    const isYamlRequest = path.endsWith(".yaml") || path.endsWith(".yml");
    const isSubRoute = path.includes("/sub");

    if (!isYamlRequest && !isSubRoute) {
        return next();
    }

    // Verify UUID token (query parameter or embedded in path)
    const tokenParam = (url.searchParams.get("uuid") || url.searchParams.get("token") || "").replace(/-/g, "").toLowerCase();
    const cleanPath = path.replace(/-/g, "").toLowerCase();
    const isAuthorized = (tokenParam === AUTH_KEY || cleanPath.includes(AUTH_KEY));

    if (!isAuthorized) {
        // Cloaked response for scanners/probes: Normal Enterprise Status Page
        return new Response(`<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Edge Quota Service - Operational</title>
<style>body{font-family:sans-serif;background:#0f172a;color:#f8fafc;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}.c{background:#1e293b;padding:2rem;border-radius:1rem;border:1px solid #334155;text-align:center}</style>
</head><body><div class="c"><h2>Edge Subscription Service</h2><p>Access Restricted · Pre-shared Token Required</p></div></body></html>`, {
            status: 200,
            headers: { "Content-Type": "text/html; charset=utf-8" }
        });
    }

    // Fetch the target static YAML file from Pages storage
    let targetFile = path;
    if (isSubRoute && !isYamlRequest) {
        let dev = "sub01";
        if (path.includes("sub02") || url.searchParams.get("dev") === "sub02") dev = "sub02";
        else if (path.includes("sub03") || url.searchParams.get("dev") === "sub03") dev = "sub03";
        else if (path.includes("sub04") || url.searchParams.get("dev") === "sub04") dev = "sub04";
        targetFile = `/${dev}.yaml`;
    }

    // Rewrite request URL to the target static file
    const staticUrl = new URL(targetFile, url.origin);
    const staticResp = await fetch(staticUrl);

    if (!staticResp.ok) {
        return next();
    }

    const yamlContent = await staticResp.text();

    // Calculate dynamic daily quota based on Cloudflare 100,000 free requests (UTC 00:00 / 08:00 CST reset cycle)
    const nowSec = Math.floor(Date.now() / 1000);
    const dayStart = Math.floor(nowSec / 86400) * 86400;
    const elapsed = nowSec - dayStart;
    const nextReset = dayStart + 86400;
    const usedBytes = Math.min(99000000000, Math.floor(elapsed * 12500) + 150000000);
    const quotaHeader = `upload=0; download=${usedBytes}; total=100000000000; expire=${nextReset}`;

    return new Response(yamlContent, {
        status: 200,
        headers: {
            "Content-Type": "text/yaml; charset=utf-8",
            "Subscription-Userinfo": quotaHeader,
            "Cache-Control": "public, max-age=180",
            "Access-Control-Allow-Origin": "*"
        }
    });
}
