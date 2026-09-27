# Profile assets

Images used by `../README.md` (the organization profile).

| File | What it is |
|---|---|
| `icon.png` | BotBus app icon with rounded (continuous-curvature) corners and transparent background, 256 px |
| `avatar-1024.png` | Same rounded icon at 1024 px, uploaded as the organization avatar |
| `banner.png` | Hero: headline, built-in agents, two iPhones and an Apple Watch |
| `agents.png` | Supported-agents strip: six built-in agents and ACP registry agents |
| `phone-*.png` | Real iPhone screenshots in a CSS device frame (transparent background) |
| `watch-*.png` | Real Apple Watch screenshots in a CSS device frame (transparent background) |

The phone and watch screenshots are the same simulator captures used on [botbus.io](https://botbus.io) (`website/public/shots/en/` in the app repository, showcase fixture data, no real conversations). The rounded icons are cut from `assets/appicon-source-1024.png` in the app repository with a superellipse corner mask (corner radius 30 % of the side, exponent 4). Regenerate the screenshots with [`scripts/render-profile-assets.py`](../../scripts/render-profile-assets.py) after the app UI changes.
