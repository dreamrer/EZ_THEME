#!/usr/bin/env python3
"""
渲染 EZ_THEME 的 .env.production.

Card 18 (构建保护) 的 4 个开关全部映射到 .env.production:
    VUE_APP_TITLE         ← payload.site.name (用 site 名当 title)
    VUE_APP_CONFIGJS      ← payload.build.config_separate
    VUE_APP_OBFUSCATION   ← payload.build.obfuscation
    VUE_APP_DEBUGGING     ← payload.build.anti_debug
    VUE_APP_ENV           ← 'production' (固定)

用法:
    python3 render-env.py <payload.json> <output .env.production>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 3:
        print(f"用法: {sys.argv[0]} <payload.json> <output>", file=sys.stderr)
        sys.exit(1)

    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])

    # 默认值: 全部安全保护开启
    build = payload.get("build", {})
    title = payload.get("site", {}).get("name", "EZ Theme")
    config_separate = build.get("config_separate", True)
    obfuscation = build.get("obfuscation", True)
    anti_debug = build.get("anti_debug", True)

    def yn(b: bool) -> str:
        return "true" if b else "false"

    content = f"""# 由 ez-theme-builder CI 自动生成
# 订单: {payload.get('order_id', 'N/A')}
# 时间: build-time

VUE_APP_TITLE={title}
VUE_APP_CONFIGJS={yn(config_separate)}
VUE_APP_OBFUSCATION={yn(obfuscation)}
VUE_APP_DEBUGGING={yn(anti_debug)}
VUE_APP_ENV=production
"""

    output.write_text(content, encoding="utf-8")
    print(f"✅ .env.production 渲染完成: {output}")
    print(f"   VUE_APP_TITLE={title}")
    print(f"   VUE_APP_CONFIGJS={yn(config_separate)}")
    print(f"   VUE_APP_OBFUSCATION={yn(obfuscation)}")
    print(f"   VUE_APP_DEBUGGING={yn(anti_debug)}")


if __name__ == "__main__":
    main()
