#!/usr/bin/env python3
"""
EZ_THEME src/config/index.js 渲染器.

策略: 不替换整个 config 文件 (上游升级会失效),
而是 surgical 替换具体字段, 上游加新字段自动继承.

支持的 18 卡 → 字段映射:
    Card 1  基础信息       → SITE_CONFIG.{siteName, siteDescription}
    Card 2  面板 & API     → PANEL_TYPE, API_CONFIG.staticBaseUrl, API_MIDDLEWARE_*
    Card 3  域名授权       → AUTHORIZED_DOMAINS, SECURITY_CONFIG
    Card 4  主题外观       → DEFAULT_CONFIG.{primaryColor, defaultTheme, defaultLanguage, enableLandingPage}
    Card 5  登录页布局     → AUTH_LAYOUT_CONFIG.layoutType
    Card 6  Landing 文案   → SITE_CONFIG.landingText
    Card 7  支付外观       → PAYMENT_CONFIG
    Card 8  客户端下载     → CLIENT_CONFIG.clientLinks + showXxx
    Card 9  邀请           → INVITE_CONFIG
    Card 10 工单           → TICKET_CONFIG
    Card 11 节点 & 流量    → NODES_CONFIG / TRAFFICLOG_CONFIG
    Card 12 客服           → CUSTOMER_SERVICE_CONFIG
    Card 13 导航           → NAVIGATION_CONFIG
    Card 14 More 卡片      → MORE_PAGE_CONFIG
    Card 15 验证码         → CAPTCHA_CONFIG
    Card 16 浏览器限制     → BROWSER_RESTRICT_CONFIG / CUSTOM_HEADERS
    Card 17 钱包           → WALLET_CONFIG
    Card 18 构建保护       → (这个写到 .env.production, 不在 config 里)

用法:
    python3 render-config.py <payload.json> <input.js> <output.js>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


def load_payload(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def js_string(s: str) -> str:
    """转义成 JS 字符串字面量"""
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def js_array(items: list[Any]) -> str:
    """转 JS 字面量数组"""
    return json.dumps(items, ensure_ascii=False)


def js_bool(b: bool) -> str:
    return "true" if b else "false"


# ──────────────────────────────────────────────────────────────────────
# Patch 函数 - 每个修改一个 config 字段
# ──────────────────────────────────────────────────────────────────────


def patch_panel_type(content: str, value: str) -> str:
    """改 PANEL_TYPE: 'V2board' → 'Xiao-V2board' 等"""
    return re.sub(
        r"(PANEL_TYPE\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
    )


def patch_api_static_base_url(content: str, urls: list[str]) -> str:
    """API_CONFIG.staticBaseUrl 数组"""
    pretty = js_array(urls)
    return re.sub(
        r"(staticBaseUrl\s*:\s*)\[[^\]]*\]",
        lambda m: f"{m.group(1)}{pretty}",
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_authorized_domains(content: str, domains: list[str]) -> str:
    """AUTHORIZED_DOMAINS: 顶层数组 (在 config 对象里)"""
    pretty = js_array(domains)
    return re.sub(
        r"(AUTHORIZED_DOMAINS\s*:\s*)\[[^\]]*\]",
        lambda m: f"{m.group(1)}{pretty}",
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_site_name(content: str, value: str) -> str:
    return re.sub(
        r"(SITE_CONFIG\s*:\s*\{[^}]*?siteName\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_site_description(content: str, value: str) -> str:
    return re.sub(
        r"(SITE_CONFIG\s*:\s*\{[^}]*?siteDescription\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_primary_color(content: str, value: str) -> str:
    return re.sub(
        r"(primaryColor\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
    )


def patch_default_language(content: str, value: str) -> str:
    return re.sub(
        r"(defaultLanguage\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
    )


def patch_default_theme(content: str, value: str) -> str:
    return re.sub(
        r"(defaultTheme\s*:\s*)'[^']*'",
        rf"\1{js_string(value)}",
        content,
        count=1,
    )


def patch_enable_landing(content: str, value: bool) -> str:
    return re.sub(
        r"(enableLandingPage\s*:\s*)(true|false)",
        rf"\1{js_bool(value)}",
        content,
        count=1,
    )


def patch_auth_layout(content: str, layout_type: str) -> str:
    """AUTH_LAYOUT_CONFIG.layoutType: 'center' | 'split'"""
    return re.sub(
        r"(AUTH_LAYOUT_CONFIG\s*:\s*\{[^}]*?layoutType\s*:\s*)'[^']*'",
        rf"\1{js_string(layout_type)}",
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_security(content: str, sec: dict) -> str:
    """SECURITY_CONFIG 的 3 个布尔字段"""
    for key in (
        "enableFrontendDomainCheck",
        "enableApiDomainCheck",
        "enableAntiDebugging",
    ):
        if key in sec:
            content = re.sub(
                rf"({key}\s*:\s*)(true|false)",
                rf"\1{js_bool(sec[key])}",
                content,
                count=1,
            )
    return content


def patch_client_links(content: str, links: dict) -> str:
    """
    CLIENT_CONFIG.clientLinks 是个嵌套 dict.
    最简单: 替换整段 clientLinks: { ... }
    """
    keys = ["ios", "android", "macos", "windows", "linux", "openwrt"]
    items = []
    for k in keys:
        v = links.get(k, "")
        items.append(f"            {k}: {js_string(v)}")
    new_block = "clientLinks: {\n" + ",\n".join(items) + "\n        }"

    return re.sub(
        r"clientLinks\s*:\s*\{[^}]*\}",
        new_block,
        content,
        count=1,
        flags=re.DOTALL,
    )


def patch_customer_service(content: str, cs: dict) -> str:
    """CUSTOMER_SERVICE_CONFIG 关键 3 个字段"""
    if "enabled" in cs:
        content = re.sub(
            r"(CUSTOMER_SERVICE_CONFIG\s*:\s*\{[^}]*?enabled\s*:\s*)(true|false)",
            rf"\1{js_bool(cs['enabled'])}",
            content,
            count=1,
            flags=re.DOTALL,
        )
    if "type" in cs:
        content = re.sub(
            r"(CUSTOMER_SERVICE_CONFIG\s*:\s*\{[^}]*?type\s*:\s*)'[^']*'",
            rf"\1{js_string(cs['type'])}",
            content,
            count=1,
            flags=re.DOTALL,
        )
    if "customHtml" in cs:
        escaped = cs["customHtml"].replace("\\", "\\\\").replace("'", "\\'")
        content = re.sub(
            r"(CUSTOMER_SERVICE_CONFIG\s*:\s*\{[^}]*?customHtml\s*:\s*)'[^']*'",
            rf"\1'{escaped}'",
            content,
            count=1,
            flags=re.DOTALL,
        )
    return content


def patch_navigation(content: str, nav: dict) -> str:
    """NAVIGATION_CONFIG 2 个字段"""
    if "thirdNavItem" in nav:
        content = re.sub(
            r"(thirdNavItem\s*:\s*)'[^']*'",
            rf"\1{js_string(nav['thirdNavItem'])}",
            content,
            count=1,
        )
    if "fourthNavItem" in nav:
        content = re.sub(
            r"(fourthNavItem\s*:\s*)'[^']*'",
            rf"\1{js_string(nav['fourthNavItem'])}",
            content,
            count=1,
        )
    return content


# ──────────────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────────────


def render(payload: dict, input_path: str, output_path: str) -> None:
    content = Path(input_path).read_text(encoding="utf-8")
    original_len = len(content)

    # Card 1: 基础信息
    site = payload.get("site", {})
    if site.get("name"):
        content = patch_site_name(content, site["name"])
    if site.get("description"):
        content = patch_site_description(content, site["description"])

    # Card 2: 面板 & API
    panel = payload.get("panel", {})
    if panel.get("type"):
        content = patch_panel_type(content, panel["type"])
    if panel.get("api_urls"):
        content = patch_api_static_base_url(content, panel["api_urls"])

    # Card 3: 域名授权
    security = payload.get("security", {})
    if security.get("authorized_domains"):
        content = patch_authorized_domains(content, security["authorized_domains"])
    sec_flags = {}
    for src, dst in [
        ("frontend_check", "enableFrontendDomainCheck"),
        ("api_check", "enableApiDomainCheck"),
        ("anti_debug", "enableAntiDebugging"),
    ]:
        if src in security:
            sec_flags[dst] = security[src]
    if sec_flags:
        content = patch_security(content, sec_flags)

    # Card 4: 主题外观
    defaults = payload.get("defaults", {})
    if defaults.get("primary_color"):
        content = patch_primary_color(content, defaults["primary_color"])
    if defaults.get("language"):
        content = patch_default_language(content, defaults["language"])
    if defaults.get("theme"):
        content = patch_default_theme(content, defaults["theme"])
    if "enable_landing" in defaults:
        content = patch_enable_landing(content, defaults["enable_landing"])

    # Card 5: 登录页
    auth = payload.get("auth", {})
    if auth.get("layout"):
        content = patch_auth_layout(content, auth["layout"])

    # Card 8: 客户端下载
    client = payload.get("client", {})
    if client.get("links"):
        content = patch_client_links(content, client["links"])

    # Card 12: 客服
    cs = payload.get("customer_service", {})
    if cs:
        content = patch_customer_service(content, cs)

    # Card 13: 导航
    nav = payload.get("navigation", {})
    if nav:
        content = patch_navigation(content, nav)

    # 写出
    Path(output_path).write_text(content, encoding="utf-8")
    print(f"✅ config 渲染完成: {output_path}")
    print(f"   原文件 {original_len} → 新文件 {len(content)} 字符")


def main() -> None:
    if len(sys.argv) != 4:
        print(
            f"用法: {sys.argv[0]} <payload.json> <input config.js> <output config.js>",
            file=sys.stderr,
        )
        sys.exit(1)

    payload = load_payload(sys.argv[1])
    render(payload, sys.argv[2], sys.argv[3])


if __name__ == "__main__":
    main()
