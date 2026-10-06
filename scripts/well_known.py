"""Generate /.well-known files for iOS Universal Links and Android App Links.

Run after changing a constant below:  python3 scripts/well_known.py
scripts/check_site.py fails if the committed files differ from what this script generates.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUNDLE_ID = "ai.tibyaan.app"
ANDROID_PACKAGE = "ai.tibyaan.app"

# Apple team IDs allowed to open tibyaan.ai/k/* and /join links.
# U7PZ665QGN = the current (personal/dev) signing identity.
# TODO(owner): add the Tibyaan LLC team ID once Apple approves the enrollment, and remove the dev
#              one when release builds are signed by the LLC team.
APPLE_TEAM_IDS = ["U7PZ665QGN"]

# SHA-256 signing-certificate fingerprints ("AB:CD:...") allowed to open the links on Android.
# TODO(owner): add the Play Console "App signing key certificate" SHA-256 (Setup -> App signing),
#              plus the upload/debug key fingerprints for sideloaded builds if wanted. Until then
#              Android shows the web page (or a chooser) instead of opening the app directly.
ANDROID_SHA256_FINGERPRINTS = []

# Paths the app handles.
APP_PATHS = ["/k/*", "/join"]


def apple_app_site_association():
    app_ids = [f"{team}.{BUNDLE_ID}" for team in APPLE_TEAM_IDS]
    return {
        "applinks": {
            "details": [
                {
                    "appIDs": app_ids,
                    "components": [{"/": path, "comment": "Khatm Circle and school invite links"} for path in APP_PATHS],
                    # Pre-iOS 13 format, same meaning.
                    "appID": app_ids[0],
                    "paths": APP_PATHS,
                }
            ]
        }
    }


def assetlinks():
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": ANDROID_PACKAGE,
                "sha256_cert_fingerprints": ANDROID_SHA256_FINGERPRINTS,
            },
        }
    ]


def rendered():
    """Published path -> exact file content."""
    dump = lambda value: json.dumps(value, indent=2) + "\n"
    return {
        ".well-known/apple-app-site-association": dump(apple_app_site_association()),
        ".well-known/assetlinks.json": dump(assetlinks()),
    }


def main():
    for path, content in rendered().items():
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
