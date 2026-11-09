# Edge Node Sync & Subscription Pipeline

Automated high-availability multi-device edge node subscription generator.

### Features
- **Strict Node Separation**:
  - `自动选择`: 42 pure VLESS Anycast nodes across 6 HTTPS ports (443, 8443, 2053, 2083, 2087, 2096).
  - `⚡ WARP-官方专线`: 8 pure Cloudflare WireGuard direct nodes (0 quota consumption).
- **Multi-Device Support**:
  - `sub01.yaml`: PC
  - `sub02.yaml`: Mobile
  - `sub03.yaml`: Tablet
- **Automated Cron**: Every 4 hours via GitHub Actions.
