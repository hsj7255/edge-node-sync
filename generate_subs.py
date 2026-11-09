import urllib.request
import json
import ssl
import os
import re

# Cloudflare & Domain constants
UUID = "0e12affd-6afa-48bf-bb85-5272fcc0504e"
DOMAIN_BASE = "websiteformewhohsj.cc.cd"

# WARP accounts per device
WARP_CONFIGS = {
    "sub01": {
        "private_key": "sHDsqTnJPvRWZZUGFrOsM8gbTjU8yb7pCn/Ke0aazX0=",
        "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
        "reserved": [173, 52, 233],
        "v4": "172.16.0.2",
        "v6": "2606:4700:110:8ab3:2f83:58be:4385:fd05"
    },
    "sub02": {
        "private_key": "sHDsqTnJPvRWZZUGFrOsM8gbTjU8yb7pCn/Ke0aazX0=",
        "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
        "reserved": [95, 91, 32],
        "v4": "172.16.0.2",
        "v6": "2606:4700:110:8ab3:2f83:58be:4385:fd05"
    },
    "sub03": {
        "private_key": "sHDsqTnJPvRWZZUGFrOsM8gbTjU8yb7pCn/Ke0aazX0=",
        "public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
        "reserved": [53, 235, 23],
        "v4": "172.16.0.2",
        "v6": "2606:4700:110:8ab3:2f83:58be:4385:fd05"
    }
}

WARP_ENDPOINTS = [
    {"name": "⚡ WARP-官方专线-01", "server": "engage.cloudflareclient.com", "port": 2408},
    {"name": "⚡ WARP-官方专线-02", "server": "162.159.193.10", "port": 2408},
    {"name": "⚡ WARP-官方专线-03", "server": "162.159.192.1", "port": 894},
    {"name": "⚡ WARP-官方专线-04", "server": "162.159.195.1", "port": 8884},
    {"name": "⚡ WARP-官方专线-05", "server": "188.114.96.1", "port": 2408},
    {"name": "⚡ WARP-官方专线-06", "server": "188.114.97.1", "port": 890},
    {"name": "⚡ WARP-官方专线-07", "server": "188.114.98.1", "port": 1074},
    {"name": "⚡ WARP-官方专线-08", "server": "188.114.99.1", "port": 8984}
]

# Fallback clean Anycast IPs (China Telecom optimized)
FALLBACK_IPS = [
    "104.16.125.127", "104.16.94.155", "104.18.7.34", "104.20.227.120",
    "104.22.11.214", "104.23.195.172", "104.23.214.15", "104.24.0.32",
    "104.24.120.219", "104.24.141.113", "104.24.222.245", "104.26.83.77",
    "104.26.253.237", "104.27.24.43", "104.27.72.191", "104.27.238.208",
    "108.162.192.131", "108.162.196.66", "108.162.204.242", "108.162.225.118",
    "108.162.234.40", "108.162.244.237", "141.101.69.73", "141.101.84.234",
    "141.101.106.124", "141.101.108.92", "141.101.108.247", "141.101.118.98",
    "141.101.120.226", "141.101.122.151", "141.101.123.136", "162.158.6.178",
    "162.158.33.72", "162.158.45.221", "162.158.211.13", "162.159.18.244",
    "162.159.65.63", "162.159.112.37", "172.65.162.1", "172.70.18.42",
    "172.70.90.230", "172.70.163.15"
]

PORTS = [443, 8443, 2053, 2083, 2087, 2096]

def fetch_best_ips():
    ips = []
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            "https://bestcf.pages.dev/vps789/top20.txt",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            text = resp.read().decode('utf-8', errors='ignore')
            for line in text.splitlines():
                line = line.strip()
                match = re.match(r"^(\d+\.\d+\.\d+\.\d+)", line)
                if match:
                    ips.append(match.group(1))
    except Exception as e:
        print("BestCF fetch fallback:", e)
    
    # Merge with fallback to ensure at least 42 unique IPs
    for ip in FALLBACK_IPS:
        if ip not in ips:
            ips.append(ip)
    return ips[:42]

def generate_yaml(sub_name, clean_ips):
    warp_conf = WARP_CONFIGS[sub_name]
    sub_domain = f"{sub_name}.{DOMAIN_BASE}"
    
    proxies = []
    auto_nodes = []
    warp_nodes = []
    ai_nodes = []
    
    # 1. Generate 8 WARP WireGuard nodes
    for ep in WARP_ENDPOINTS:
        node_name = ep["name"]
        warp_nodes.append(node_name)
        ai_nodes.append(node_name)
        proxies.append(f"""  - name: "{node_name}"
    type: wireguard
    server: {ep['server']}
    port: {ep['port']}
    ip: {warp_conf['v4']}
    ipv6: "{warp_conf['v6']}"
    private-key: "{warp_conf['private_key']}"
    public-key: "{warp_conf['public_key']}"
    reserved: {warp_conf['reserved']}
    udp: true
    mtu: 1280
    remote-dns-resolve: true
    dns: [1.1.1.1]""")

    # 2. Generate 42 VLESS nodes across 6 HTTPS ports
    for i, ip in enumerate(clean_ips):
        port = PORTS[i % len(PORTS)]
        node_name = f"优选节点-{i+1:02d} ({port})"
        auto_nodes.append(node_name)
        ai_nodes.append(node_name)
        proxies.append(f"""  - name: "{node_name}"
    type: vless
    server: {ip}
    port: {port}
    uuid: {UUID}
    network: ws
    udp: true
    tls: true
    skip-cert-verify: true
    alpn: [http/1.1]
    servername: {sub_domain}
    client-fingerprint: chrome
    ws-opts:
      path: "/{UUID}?ed=2048"
      headers:
        Host: {sub_domain}""")

    # Strategy group proxies strings
    auto_list = ", ".join([f'"{n}"' for n in auto_nodes])
    warp_list = ", ".join([f'"{n}"' for n in warp_nodes])
    ai_list = ", ".join([f'"{n}"' for n in ai_nodes])
    all_list = ", ".join([f'"{n}"' for n in (auto_nodes + warp_nodes)])

    yaml_content = f"""# EdgeNodeSync 订阅 · 设备: {sub_name} · 节点总数: {len(proxies)} (42 VLESS + 8 WARP)
# 生成时间: {os.environ.get('GITHUB_RUN_ID', 'Local')}
port: 7890
socks-port: 7891
allow-lan: false
mode: rule
log-level: info
ipv6: false
external-controller: 127.0.0.1:9090

dns:
  enable: true
  listen: 0.0.0.0:1053
  ipv6: false
  default-nameserver:
    - 223.5.5.5
    - 119.29.29.29
  enhanced-mode: fake-ip
  fake-ip-range: 198.18.0.1/16
  nameserver:
    - https://doh.pub/dns-query
    - https://dns.alidns.com/dns-query

proxies:
{chr(10).join(proxies)}

proxy-groups:
  - {{name: 🚀 节点选择, type: select, proxies: [自动选择, ⚡ WARP-官方专线, 🤖 人工智能, 🎬 国际流媒体, 全部节点, DIRECT]}}
  - {{name: 一键连接, type: select, proxies: [🚀 节点选择]}}
  # 自动优选池：物理隔离，仅包含 42 个纯 VLESS 优选节点（0 WARP，彻底避免 CN GeoIP）
  - {{name: 自动选择, type: url-test, proxies: [{auto_list}], url: 'https://www.gstatic.com/generate_204', interval: 600, tolerance: 50, lazy: true}}
  # ⚡ WARP 官方专线：WireGuard UDP 直连 Cloudflare 骨干网 (0 额度消耗，独立稳定)
  - {{name: ⚡ WARP-官方专线, type: fallback, proxies: [{warp_list}], url: 'https://www.gstatic.com/generate_204', interval: 600}}
  # 人工智能专属组：优选节点 + WARP
  - {{name: 🤖 人工智能, type: url-test, proxies: [{ai_list}], url: 'https://www.gstatic.com/generate_204', interval: 600, tolerance: 50, lazy: true}}
  # 国际流媒体
  - {{name: 🎬 国际流媒体, type: url-test, proxies: [{all_list}], url: 'https://www.gstatic.com/generate_204', interval: 600, tolerance: 50, lazy: true}}
  - {{name: 全部节点, type: select, proxies: [{all_list}]}}

rules:
  # 国内直连
  - DOMAIN-SUFFIX,cn,DIRECT
  - DOMAIN-KEYWORD,-cn,DIRECT
  - GEOIP,CN,DIRECT
  # AI 服务走人工智能组
  - DOMAIN-SUFFIX,openai.com,🤖 人工智能
  - DOMAIN-SUFFIX,chatgpt.com,🤖 人工智能
  - DOMAIN-SUFFIX,anthropic.com,🤖 人工智能
  - DOMAIN-SUFFIX,claude.ai,🤖 人工智能
  - DOMAIN-SUFFIX,gemini.google.com,🤖 人工智能
  - DOMAIN-SUFFIX,cursor.com,🤖 人工智能
  - DOMAIN-SUFFIX,cursor.sh,🤖 人工智能
  # 流媒体
  - DOMAIN-SUFFIX,youtube.com,🎬 国际流媒体
  - DOMAIN-SUFFIX,googlevideo.com,🎬 国际流媒体
  - DOMAIN-SUFFIX,netflix.com,🎬 国际流媒体
  # 默认走节点选择
  - MATCH,🚀 节点选择
"""
    return yaml_content

def main():
    print("Fetching best IPs...")
    ips = fetch_best_ips()
    print(f"Acquired {len(ips)} IPs.")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for sub in ["sub01", "sub02", "sub03"]:
        content = generate_yaml(sub, ips)
        out_path = os.path.join(script_dir, f"{sub}.yaml")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {sub}.yaml ({len(content)} bytes)")

if __name__ == "__main__":
    main()
