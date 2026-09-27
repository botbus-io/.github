#!/usr/bin/env python3
"""Render the images used by profile/README.md with headless Google Chrome (macOS).

Inputs are copied from the BotBus app repository next to this script before running:

    fonts/        <- website/public/fonts/*.woff2 (Geist, SIL OFL 1.1)
    shots/        <- website/public/shots/en/*.webp converted to PNG (real simulator captures)
    agents/       <- website/public/agents/*.svg
    icon-512.png  <- website/public/icon-512.png

The device frames, colors and typography follow website/public/styles.css so the
profile page matches botbus.io. Output goes to out/ as 2x PNGs; transparent assets are
trimmed to their content box. Copy out/*.png to profile/assets/ afterwards.

    python3 render-profile-assets.py            # everything
    python3 render-profile-assets.py banner     # one target
"""Render the GitHub org profile assets for botbus-io with headless Chrome.

Reuses the website's fonts, real device screenshots, device-frame CSS and agent icons.
Outputs 2x PNGs into out/ and trims transparent assets to their content box.
"""
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

BASE_CSS = """
@font-face { font-family: 'Geist'; src: url('fonts/Geist-Variable.woff2') format('woff2'); font-weight: 100 900; }
@font-face { font-family: 'Geist Mono'; src: url('fonts/GeistMono-Variable.woff2') format('woff2'); font-weight: 100 900; }
:root {
  --bg: #0f0f10; --surface: #18181b; --surface-raised: #202024;
  --line: rgba(255,255,255,.08); --line-strong: rgba(255,255,255,.14);
  --text: #ededee; --text-soft: #c8c8cc; --muted: #a1a1a8; --faint: #8a8a92;
  --amber: #F8C04A; --wait: #f08a3c; --ok: #4cc38a; --run: #7eb0ff;
  --font: 'Geist', -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
  --mono: 'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: transparent; }
body { font-family: var(--font); color: var(--text); -webkit-font-smoothing: antialiased; }

/* Device frames: same construction as website/public/styles.css */
.device-phone { --dw: 300px; position: relative; display: block; width: var(--dw); margin: 0; padding: calc(var(--dw) * .032); border-radius: calc(var(--dw) * .16); background: #0a0a0b; box-shadow: inset 0 0 0 1.5px #3b3b41, inset 0 0 0 5px #151517, 0 0 0 1px rgba(255, 255, 255, .05), 0 30px 60px -30px rgba(0, 0, 0, .6); }
.device-phone img { display: block; width: 100%; height: auto; border-radius: calc(var(--dw) * .125); }
.device-phone::after { content: ''; position: absolute; left: calc(var(--dw) * .367); top: calc(var(--dw) * .062); width: calc(var(--dw) * .267); height: calc(var(--dw) * .069); border-radius: 999px; background: #000; }
.device-watch { --dw: 190px; --case: calc(var(--dw) * .07); position: relative; isolation: isolate; display: block; width: var(--dw); margin: 0; padding: var(--case); }
.device-watch img { position: relative; display: block; width: 100%; height: auto; border-radius: calc(var(--dw) * .19); box-shadow: 0 0 0 1px #000, 0 0 0 calc(var(--case) - 2px) #1b1b1e, 0 0 0 calc(var(--case) - .5px) #45454c, 0 0 0 var(--case) #0c0c0d, 0 20px 40px -20px rgba(0, 0, 0, .6); }
.device-watch::before { content: ''; position: absolute; z-index: -1; left: 18%; right: 18%; top: -22%; bottom: -22%; border-radius: calc(var(--dw) * .1); background: #151517; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .06); }
.device-watch::after { content: ''; position: absolute; z-index: -1; right: -3.5%; top: 27%; width: 6%; height: 17%; border-radius: calc(var(--dw) * .02); background: #2c2c31; box-shadow: inset 0 0 0 1px rgba(255, 255, 255, .1); }

.chip { display: inline-flex; align-items: center; gap: 8px; padding: 7px 12px 7px 10px; border-radius: 999px; background: var(--surface); box-shadow: inset 0 0 0 1px var(--line-strong); font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; }
.chip img { width: 16px; height: 16px; filter: invert(1); opacity: .85; }
.chip.small { padding: 5px 10px 5px 8px; font-size: 12px; font-weight: 500; color: var(--text-soft); }
.chip.small img { width: 13px; height: 13px; }
"""

BUILTIN = [
    ("codex", "Codex"),
    ("claude", "Claude Code"),
    ("hermes", "Hermes"),
    ("pi", "Pi"),
    ("openclaw", "OpenClaw"),
    ("deepseek", "DeepSeek Harness"),
]
REGISTRY = [
    ("gemini", "Gemini CLI"),
    ("goose", "goose"),
    ("opencode", "OpenCode"),
    ("qwen-code", "Qwen Code"),
    ("kimi", "Kimi CLI"),
    ("cursor", "Cursor"),
    ("github-copilot-cli", "GitHub Copilot"),
    ("cline", "Cline"),
    ("mistral-vibe", "Mistral Vibe"),
    ("kilo", "Kilo"),
    ("acp-default", "any ACP agent"),
]


def chips(items, small=False):
    cls = "chip small" if small else "chip"
    return "".join(
        f'<span class="{cls}"><img src="agents/{f}.svg" alt="">{n}</span>' for f, n in items
    )


def page(body, css, width, height):
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{BASE_CSS}
body {{ width: {width}px; height: {height}px; overflow: hidden; }}
{css}</style></head><body>{body}</body></html>"""


def phone(name, dw=330):
    css = "body { display: flex; align-items: flex-start; justify-content: center; padding-top: 30px; }"
    body = f'<figure class="device-phone" style="--dw:{dw}px"><img src="shots/phone-{name}.png" alt="" decoding="sync"></figure>'
    return page(body, css, 460, 830)


def watch(name, dw=190):
    css = "body { display: flex; align-items: flex-start; justify-content: center; padding-top: 70px; }"
    body = f'<figure class="device-watch" style="--dw:{dw}px"><img src="shots/watch-{name}.png" alt="" decoding="sync"></figure>'
    return page(body, css, 320, 400)


def agents_strip():
    css = """
    body { padding: 8px 10px; }
    .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .row + .row { margin-top: 12px; }
    .label { font: 500 11px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--faint); margin-right: 4px; }
    """
    body = f"""
    <div class="row"><span class="label">Built in</span>{chips(BUILTIN)}</div>
    <div class="row"><span class="label">Via ACP</span>{chips(REGISTRY, small=True)}</div>
    """
    return page(body, css, 940, 200)


def banner():
    css = """
    body { background: var(--bg); position: relative; }
    body::before { content: ''; position: absolute; inset: 0; background: radial-gradient(rgba(255,255,255,.07) 1px, transparent 1.3px) 0 0 / 26px 26px; -webkit-mask-image: radial-gradient(ellipse 60% 70% at 72% 50%, #000, transparent 75%); mask-image: radial-gradient(ellipse 60% 70% at 72% 50%, #000, transparent 75%); }
    .copy { position: absolute; left: 72px; top: 0; bottom: 0; width: 600px; display: flex; flex-direction: column; justify-content: center; }
    .kicker { display: inline-flex; align-items: center; gap: 12px; font-size: 17px; font-weight: 600; color: var(--muted); letter-spacing: .01em; }
    .kicker img { width: 40px; height: 40px; border-radius: 10px; }
    h1 { margin: 22px 0 0; font-size: 46px; line-height: 1.1; font-weight: 700; letter-spacing: -.035em; }
    h1 em { font-style: normal; color: var(--amber); }
    .sub { margin: 20px 0 0; max-width: 470px; color: var(--muted); font-size: 16.5px; line-height: 1.65; }
    .works { margin-top: 26px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; max-width: 600px; }
    .works .label { flex-basis: 100%; font: 500 11px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; color: var(--faint); margin-bottom: 2px; }
    .works .chip { font-size: 12px; padding: 6px 11px 6px 9px; }
    .works .chip img { width: 14px; height: 14px; }
    .devices { position: absolute; right: 64px; top: 0; bottom: 0; width: 470px; }
    .devices > * { position: absolute; }
    .phone-back { --dw: 190px; left: 0; top: 70px; filter: brightness(.72) saturate(.85); z-index: 1; }
    .phone-front { --dw: 225px; left: 150px; top: 26px; z-index: 2; }
    .watch { --dw: 142px; right: 0; bottom: 100px; z-index: 3; }
    .hero-chip { z-index: 4; display: inline-flex; align-items: center; gap: 8px; padding: 8px 13px 8px 11px; border-radius: 12px; background: rgba(28,28,31,.96); box-shadow: inset 0 0 0 1px var(--line-strong), 0 20px 40px -20px rgba(0,0,0,.9); font-size: 12px; font-weight: 600; white-space: nowrap; }
    .hero-chip i { width: 8px; height: 8px; border-radius: 50%; }
    .chip-wait { left: -26px; top: 340px; }
    .chip-wait i { background: var(--wait); }
    .chip-ok { right: -6px; bottom: 46px; }
    .chip-ok i { background: var(--ok); }
    """
    body = f"""
    <div class="copy">
      <div class="kicker"><img src="icon-512.png" alt="">BotBus</div>
      <h1>Your AI agents,<br><em>anywhere you go.</em></h1>
      <p class="sub">Follow the coding agents running on your computer from your phone and watch: approve requests, reply, start new tasks and open what they built.</p>
      <div class="works"><span class="label">Works with</span>{chips(BUILTIN)}</div>
    </div>
    <div class="devices">
      <figure class="device-phone phone-back"><img src="shots/phone-machines.png" alt="" decoding="sync" loading="eager"></figure>
      <figure class="device-phone phone-front"><img src="shots/phone-machine.png" alt="" decoding="sync" loading="eager"></figure>
      <figure class="device-watch watch"><img src="shots/watch-approval.png" alt="" decoding="sync" loading="eager"></figure>
      <span class="hero-chip chip-wait"><i></i>Awaiting approval · npm test</span>
      <span class="hero-chip chip-ok"><i></i>Approved on your watch</span>
    </div>
    """
    return page(body, css, 1200, 560)


TARGETS = {
    "banner": (banner(), 1200, 560, False),
    "agents": (agents_strip(), 940, 200, True),
}
for n in ["machines", "machine", "approval", "artifacts", "preview", "newtask"]:
    TARGETS[f"phone-{n}"] = (phone(n), 460, 830, True)
for n in ["machines", "machine", "approval", "input"]:
    TARGETS[f"watch-{n}"] = (watch(n), 320, 400, True)


def render(name, html, width, height, trim):
    html_path = HERE / f"{name}.html"
    html_path.write_text(html, encoding="utf-8")
    out_path = OUT / f"{name}.png"
    cmd = [
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--allow-file-access-from-files", "--default-background-color=00000000",
        "--force-device-scale-factor=2", "--virtual-time-budget=4000",
        "--run-all-compositor-stages-before-draw", f"--window-size={width},{height}",
        f"--screenshot={out_path}", f"file://{html_path}",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    img = Image.open(out_path).convert("RGBA")
    if trim:
        bbox = img.getchannel("A").getbbox()
        pad = 8
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(img.width, bbox[2] + pad), min(img.height, bbox[3] + pad))
        img = img.crop(bbox)
    else:
        img = img.convert("RGB")
    img.save(out_path, optimize=True)
    print(f"{name}: {img.width}x{img.height} {out_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for name, (html, w, h, trim) in TARGETS.items():
        if only and name not in only:
            continue
        render(name, html, w, h, trim)
