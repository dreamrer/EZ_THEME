#!/usr/bin/env python3
"""
渲染 "部署说明.txt" - zip 包里给机场主看的纯文本说明.

用法:
    python3 render-readme.py <payload.json> <order_id>
    (输出到 stdout)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <payload.json> <order_id>", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    order_id = sys.argv[2]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    site = payload.get("site", {})
    panel = payload.get("panel", {})
    security = payload.get("security", {})

    api_urls = panel.get("api_urls", [])
    domains = security.get("authorized_domains", [])

    text = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  EZ_THEME 主题部署说明
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

订单号:    {order_id}
打包时间:  {now}
站点名称:  {site.get('name', 'N/A')}
站点描述:  {site.get('description', 'N/A')}
面板类型:  {panel.get('type', 'N/A')}

API 后端 ({len(api_urls)} 个):
"""
    for i, url in enumerate(api_urls, 1):
        text += f"   {i}. {url}\n"

    text += f"\n授权前端域名 ({len(domains)} 个):\n"
    for i, d in enumerate(domains, 1):
        text += f"   {i}. {d}\n"

    text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  部署步骤
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 解压 zip 到本地任意目录
   (里面就是你的前端静态文件)

2. 把整个文件夹内容上传到你的 nginx 静态服务器
   例如: /www/wwwroot/your-frontend/

3. 配置 nginx (重点是 try_files 兜底 SPA 路由):

   server {
       listen 80;
       server_name """ + (domains[0] if domains else 'your-domain.com') + """;

       root /www/wwwroot/your-frontend;
       index index.html;

       # SPA 路由兜底
       location / {
           try_files $uri $uri/ /index.html;
       }

       # gzip 静态资源
       gzip on;
       gzip_types text/css application/javascript image/svg+xml;

       # 缓存策略 (vite 出的文件名带 hash, 长缓存安全)
       location ~* \\.(?:css|js|woff2?|ttf|otf|eot)$ {
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }

4. 给 nginx 加 https (推荐, EZ_THEME 部分功能需要 https):
   - certbot 自动签 Let's Encrypt
   - 或用 CDN (Cloudflare) 反代

5. 浏览器访问 https://your-domain.com
   ✅ 出现 Landing 落地页 = 部署成功
   ❌ 白屏: 看浏览器控制台报错
       - "Network Error": API 域名配错
       - "Unauthorized domain": 域名不在白名单 (在 src/config 改)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  改配置 (不重新打包)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

zip 里有个独立的 config 文件 (形如 042.xxxxxx.js, 100KB)
这是混淆压缩后的配置. 大多数运营改动不需要重新打包:

  - 改 Logo: 直接替换 logo.png
  - 改 favicon: 直接替换 favicon.ico
  - 改主题色 / API URL / 客户端下载链接:
      → 找 TG bot, /repackage 重新打包 (会扣点数)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  支持
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

部署遇到问题 → TG bot 发 /support
源码升级 → /repackage
意见反馈 → /feedback

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
