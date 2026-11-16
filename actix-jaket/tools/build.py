#!/usr/bin/env python3
"""Generate the Actix jacket HyperFrames project from an edit decision list + word transcript.

Usage: python3 -I build.py <words.json> <project_dir>
"""
import json, sys, html, os, re

WORDS = json.load(open(sys.argv[1]))
P = sys.argv[2]
FPS = 30
HOOK = 1.5  # seconds of image hook before the first spoken segment


def fr(t):  # snap to frame grid
    return round(round(t * FPS) / FPS, 4)


# ---------------------------------------------------------------- EDL (source seconds)
# Each tuple: (id, src_in, src_out, cam_scale, note)
EDL = [
    ("s01", 1.60, 3.18, 1.00, "Memang smart, memang style."),
    ("s02", 3.84, 5.98, 1.14, "ni baju hujan yang memang jenis style."),
    ("s03", 6.12, 9.78, 1.00, "Macam ni, jenis camo grey. Ha, ada juga warna lain."),
    ("s04", 9.90, 10.78, 1.12, "Yang best dia ni,"),
    ("s05", 11.16, 13.45, 1.00, "Zip dia pun smooth. Zip jenis waterproof."),
    ("s06", 13.94, 19.62, 1.10, "Lepas tu, dalam dia ni... sesuai untuk hujan, panas, berangin."),
    ("s07", 19.70, 22.46, 1.00, "Lepas tu, dia ada pocket tau kat ni. Ada satu kompartmen."),
    ("s08", 22.76, 24.66, 1.12, "Ha, ni boleh tutup."),
    # cut: "Zip dia memang smooth. Nampak, senang, mudah." (repeat)
    ("s09", 27.28, 28.80, 1.00, "yang best dia lagi kat pocket ni,"),
    # cut: "apa tengok" + 1.7 s dead air
    ("s10", 30.80, 32.42, 1.14, "Ha, pocket dia jenis waterproof tau."),
    ("s11", 32.72, 34.80, 1.00, "Kiri dan kanan, boleh tutup zip dia."),
    # cut: "Nampak, kiri dan kanan. Ha, ada pocket." (repeat)
    ("s12", 38.04, 40.32, 1.12, "So, kalau phone... letak ni, tak jatuh lah."),
    # cut: 1.6 s dead air
    ("s13", 41.84, 44.02, 1.00, "Belakang dia ni, ada jenis hoodie tau. Ni,"),
    ("s14", 44.60, 45.46, 1.10, "boleh pakai sini."),
    ("s15", 45.56, 49.90, 1.00, "Kalau tak nak pakai... boleh buka dan simpan."),
    ("s16", 50.08, 54.10, 1.08, "Ha, memang rare. ...tengah ada promo, tekan ni sekarang."),
]

segs = []
t = HOOK
for sid, a, b, sc, note in EDL:
    a, b = fr(a), fr(b)
    d = fr(b - a)
    segs.append(dict(id=sid, src_in=a, src_out=b, start=fr(t), dur=d, scale=sc, note=note))
    t = fr(t + d)
TOTAL = fr(t)


def out(src):
    """Map a source time to output time (None if the moment was cut)."""
    for s in segs:
        if s["src_in"] - 1e-6 <= src <= s["src_out"] + 1e-6:
            return fr(s["start"] + (src - s["src_in"]))
    return None


def W(src_word_start):  # output time of the first word starting at/after src time
    for w in WORDS:
        if w["start"] >= src_word_start - 0.02:
            o = out(w["start"])
            if o is not None:
                return o
    raise ValueError(src_word_start)


# ---------------------------------------------------------------- caption words
FIX = {"kompakman": "kompartmen", "beranginan.": "berangin.", "-mana": "-mana", "-ala": "-ala"}
HL = {"smart", "style", "camo", "grey", "warna", "smooth", "waterproof", "hujan", "panas",
      "berangin", "pocket", "kompartmen", "kiri", "kanan", "phone", "jatuh", "hoodie",
      "simpan", "rare", "promo", "sekarang", "best"}

kept = []
for w in WORDS:
    txt = w["text"]
    txt = FIX.get(txt, txt)
    for k, v in FIX.items():
        txt = txt.replace(k.strip("."), v.strip(".")) if k.strip(".") in txt else txt
    s_o, e_o = out(w["start"]), out(min(w["end"], w["start"] + 0.9))
    if s_o is None or any(abs(w["start"] - sg["src_out"]) < 0.08 for sg in segs):
        continue
    if e_o is None:
        # word runs past its segment's end: clamp
        seg = next(s for s in segs if s["src_in"] - 1e-6 <= w["start"] <= s["src_out"])
        e_o = fr(seg["start"] + seg["dur"])
    kept.append(dict(text=txt, start=s_o, end=max(e_o, s_o + 0.1)))

# merge hyphen continuations ("mana" + "-mana")
merged = []
for w in kept:
    if w["text"].startswith("-") and merged:
        merged[-1]["text"] += w["text"]
        merged[-1]["end"] = w["end"]
    else:
        merged.append(dict(w))
kept = merged

# group: split into phrases (punctuation / gap >= .15 / take boundary), then chunk each
# phrase into balanced groups of <= 3 words (4 -> 2+2, 5 -> 3+2) so no word is left alone.
seg_starts = {s["start"] for s in segs}
phrases, cur = [], []
for w in kept:
    if cur:
        gap = w["start"] - cur[-1]["end"]
        crossed = any(cur[-1]["start"] < ss <= w["start"] + 1e-3 for ss in seg_starts)
        if gap >= 0.15 or crossed or re.search(r"[.!?]$", cur[-1]["text"]):
            phrases.append(cur); cur = []
    cur.append(w)
if cur:
    phrases.append(cur)
# a lone filler ("Ha," "Ni," "So,") joins the phrase after it when they sit close
merged = []
for ph in phrases:
    if merged and len(merged[-1]) == 1 and merged[-1][0]["text"].lower().strip(",.") in {"ha", "ni", "so"} \
            and ph[0]["start"] - merged[-1][0]["end"] < 0.3:
        merged[-1] = merged[-1] + ph
    else:
        merged.append(ph)
groups = []
for ph in merged:
    n = len(ph)
    k = max(1, -(-n // 3))  # number of chunks
    base, extra = divmod(n, k)
    i = 0
    for c in range(k):
        size = base + (1 if c < extra else 0)
        groups.append(ph[i:i + size]); i += size


def clean_word(t):
    return t.strip(",.").upper()


cap_items, cap_js = [], []
CTA_AT = fr(W(51.12) + 0.25)  # captions stop where the CTA card takes over
groups = [g for g in groups if g[0]["start"] < CTA_AT - 0.05]
for gi, g in enumerate(groups):
    gid = f"cap{gi:02d}"
    g_start = fr(max(g[0]["start"] - 0.04, HOOK + 0.05))
    nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else TOTAL
    g_end = fr(min(max(g[-1]["end"] + 0.12, g_start + 0.45), nxt - 0.02, TOTAL - 0.04, CTA_AT))
    spans = []
    for wi, w in enumerate(g):
        word = clean_word(w["text"])
        hl = " hl" if word.lower() in HL else ""
        spans.append(f'<span id="{gid}w{wi}" class="w{hl}">{html.escape(word)}</span>')
        cap_js.append(f'  pop("#{gid}w{wi}", {w["start"]:.3f});')
    cap_items.append(
        f'    <div id="{gid}" class="cap clip" data-start="{g_start}" data-duration="{fr(g_end - g_start)}" '
        f'data-track-index="0"><div id="{gid}l" class="line">{" ".join(spans)}</div></div>')
    cap_js.append(f'  kill("#{gid}l", {g_end:.3f});')

# ---------------------------------------------------------------- callout timings (output seconds)
T = dict(
    camo=W(6.48), warna=W(8.80), zip=W(12.36), sesuai=W(15.74), hujan=W(16.40), panas=W(17.98),
    angin=W(19.04), pocket=W(20.48), komp=W(21.74), wp_pocket=W(31.46), kirikanan=W(32.76),
    phone=W(38.42), jatuh=W(39.72), hoodie=W(42.74), simpan=W(48.92), rare=W(50.54),
    promo=W(52.74), tekan=W(53.40), dapat=W(51.12),
)
json.dump(dict(segs=segs, total=TOTAL, T=T, groups=[[w["text"] for w in g] for g in groups]),
          open(os.path.join(P, ".edl.json"), "w"), indent=1, ensure_ascii=False)

# ---------------------------------------------------------------- shared styles
FONTS = """
      --accent: #ffd60a;
      --ink: #ffffff;
      --glass: rgba(12, 14, 20, 0.78);
      --promo: #ff3b4e;
      --font-display: "Archivo Black", "Montserrat", sans-serif;
      --font-ui: "Montserrat", sans-serif;
"""

# ---------------------------------------------------------------- index.html
videos, sfx = [], []
for i, s in enumerate(segs):
    videos.append(
        f'        <video id="{s["id"]}" class="clip seg" src="assets/jaket.mp4" data-start="{s["start"]}" '
        f'data-duration="{s["dur"]}" data-media-start="{s["src_in"]}" data-track-index="1" '
        f'data-has-audio="true" data-volume="1" playsinline></video>')

cam_js = []
for s in segs:
    cam_js.append(f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});')
# emphasis punch on "memang rare"
cam_js.append(f'      tl.to("#cam", {{ scale: 1.22, duration: 0.18, ease: "power4.out" }}, {T["rare"]});')
cam_js.append(f'      tl.to("#cam", {{ scale: 1.08, duration: 0.5, ease: "power2.inOut" }}, {fr(T["rare"] + 0.9)});')
# small push during "waterproof" zip line
s05 = next(s for s in segs if s["id"] == "s05")
cam_js.append(f'      tl.to("#cam", {{ scale: 1.12, duration: 0.35, ease: "expo.out" }}, {T["zip"]});')

SFX = [  # (id, file, time, volume)  -- peak lands one frame after the picture
    ("sfx-impact", "impact-bass-1.mp3", 0.0, 0.55),
    ("sfx-whoosh-hook", "whoosh-cinematic.mp3", fr(HOOK - 0.35), 0.45),
    ("sfx-pop-warna", "pop.mp3", fr(T["warna"] + 0.03), 0.5),
    ("sfx-whoosh-zip", "whoosh-short.mp3", fr(T["zip"] - 0.05), 0.4),
    ("sfx-pop-hujan", "pop.mp3", fr(T["hujan"] + 0.03), 0.45),
    ("sfx-pop-panas", "click-soft.mp3", fr(T["panas"] + 0.03), 0.6),
    ("sfx-pop-angin", "pop.mp3", fr(T["angin"] + 0.03), 0.45),
    ("sfx-whoosh-pocket", "whoosh.mp3", fr(T["pocket"] - 0.08), 0.35),
    ("sfx-whoosh-wp", "whoosh-short.mp3", fr(T["wp_pocket"] - 0.05), 0.4),
    ("sfx-pop-jatuh", "pop.mp3", fr(T["jatuh"] + 0.03), 0.45),
    ("sfx-whoosh-hoodie", "whoosh.mp3", fr(T["hoodie"] - 0.08), 0.35),
    ("sfx-sparkle", "sparkle.mp3", fr(T["simpan"]), 0.35),
    ("sfx-impact-rare", "impact-bass-2.mp3", fr(T["rare"] - 0.35), 0.5),
    ("sfx-pop-promo", "pop.mp3", fr(T["rare"] + fr(T["dapat"] - T["rare"] + 0.25) + 0.03), 0.5),
]
import subprocess
def adur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "csv=p=0", os.path.join(P, "assets/sfx", f)]).decode().strip())
lanes = []  # end time per lane
for sid, f, at, vol in SFX:
    d = fr(min(adur(f), TOTAL - at))
    lane = next((i for i, e in enumerate(lanes) if e <= at), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = at + d
    sfx.append(f'      <audio id="{sid}" class="clip" src="assets/sfx/{f}" data-start="{at}" data-duration="{d}" '
               f'data-track-index="{20 + lane}" data-volume="{vol}"></audio>')

flash_at = fr(HOOK - 0.8 * 0.58)

index = f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{{FONTS}      --ground: #000;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--ground); }}
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 32%; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}"
         data-width="1080" data-height="1920">
      <!-- Footage: one clip per kept take (jump cuts). Trim in Studio by dragging clip edges. -->
      <div id="cam">
{chr(10).join(videos)}
      </div>

      <!-- Hook: product proof shot + headline -->
      <div id="hook" data-composition-id="hook" data-composition-src="compositions/hook.html"
           data-start="0" data-duration="{HOOK}" data-track-index="2" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:5"></div>
      <div id="editorial-flash-overlay" data-composition-id="editorial-flash-overlay"
           data-composition-src="compositions/editorial-flash-overlay.html"
           data-start="{flash_at}" data-duration="0.8" data-track-index="3" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:9"></div>

      <!-- Feature callouts, one scene per chapter -->
      <div id="callouts-a" data-composition-id="callouts-a" data-composition-src="compositions/callouts-a.html"
           data-start="0" data-duration="{TOTAL}" data-track-index="4" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:6"></div>
      <div id="callouts-b" data-composition-id="callouts-b" data-composition-src="compositions/callouts-b.html"
           data-start="0" data-duration="{TOTAL}" data-track-index="5" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:6"></div>
      <div id="callouts-c" data-composition-id="callouts-c" data-composition-src="compositions/callouts-c.html"
           data-start="0" data-duration="{TOTAL}" data-track-index="6" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:6"></div>
      <div id="cta" data-composition-id="cta" data-composition-src="compositions/cta.html"
           data-start="0" data-duration="{TOTAL}" data-track-index="7" data-track-kind="graphics"
           data-width="1080" data-height="1920" style="z-index:7"></div>

      <!-- Captions -->
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
           data-start="0" data-duration="{TOTAL}" data-track-index="8" data-track-kind="captions"
           data-width="1080" data-height="1920" style="z-index:8"></div>

      <!-- Sound effects -->
{chr(10).join(sfx)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      // Jump-cut punch-ins: alternate framing on every cut so cuts read as intentional.
{chr(10).join(cam_js)}
      tl.to({{}}, {{ duration: {TOTAL} }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(os.path.join(P, "index.html"), "w").write(index)

# ---------------------------------------------------------------- hook.html
hook = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; background: #050506;
      {FONTS} }}
    #hook-img-wrap {{ position: absolute; inset: 0; transform-origin: 52% 45%; }}
    #hook-img {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; object-position: 58% 50%; }}
    #hook-shade {{ position: absolute; inset: 0;
      background: linear-gradient(180deg, rgba(0,0,0,.72) 0%, rgba(0,0,0,.25) 34%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%); }}
    #hook-copy {{ position: absolute; left: 0; right: 120px; top: 250px; text-align: center; }}
    #hook-kicker {{ font-family: var(--font-ui); font-weight: 800; font-size: 64px; letter-spacing: .04em;
      color: var(--ink); text-transform: uppercase; text-shadow: 0 6px 24px rgba(0,0,0,.6); }}
    #hook-big {{ margin-top: 6px; font-family: var(--font-display); font-size: 132px; line-height: .95;
      color: var(--accent); text-transform: uppercase; letter-spacing: -.01em;
      text-shadow: 0 10px 40px rgba(0,0,0,.65); }}
    #hook-pill {{ display: inline-block; margin-top: 28px; padding: 14px 30px; border-radius: 999px;
      background: var(--glass); color: var(--ink); font-family: var(--font-ui); font-weight: 700; font-size: 38px;
      border: 2px solid rgba(255,255,255,.18); }}
  </style>
  <div id="root" data-composition-id="hook" data-width="1080" data-height="1920">
    <div id="hook-img-wrap">
      <img id="hook-img" class="clip" src="assets/img/hook-pour.jpg" data-start="0" data-duration="{HOOK}" data-track-index="0" />
    </div>
    <div id="hook-shade"></div>
    <div id="hook-copy" class="clip" data-start="0" data-duration="{HOOK}" data-track-index="1">
      <div id="hook-kicker" data-var-text="hookKicker">Kena air pun</div>
      <div id="hook-big"><span id="hook-w1">TAK</span> <span id="hook-w2">MERESAP.</span></div>
    </div>
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
    // frame 0 already carries the headline (thumbnail); the proof shot punches in behind it
    tl.fromTo("#hook-img-wrap", {{ scale: 1.18 }}, {{ scale: 1.04, duration: 0.6, ease: "expo.out" }}, 0);
    tl.fromTo("#hook-img-wrap", {{ scale: 1.04 }}, {{ scale: 1.0, duration: 0.9, ease: "none", immediateRender: false }}, 0.6);
    tl.fromTo("#hook-kicker", {{ opacity: 0.85 }}, {{ opacity: 1, duration: 0.15 }}, 0);
    tl.fromTo("#hook-w1", {{ scale: 1.25, opacity: 0.0 }}, {{ scale: 1, opacity: 1, duration: 0.22, ease: "power4.out" }}, 0.0);
    tl.fromTo("#hook-w2", {{ scale: 1.25, opacity: 0.0, filter: "blur(8px)" }}, {{ scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.22, ease: "power4.out" }}, 0.18);
    window.__timelines["hook"] = tl;
  </script>
</template>
"""
open(os.path.join(P, "compositions/hook.html"), "w").write(hook)

# ---------------------------------------------------------------- callout helpers
CARD_CSS = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {FONTS} }}
    .card {{ position: absolute; left: 60px; top: 880px; display: flex; align-items: center; gap: 22px;
      padding: 22px 34px 22px 24px; border-radius: 28px; background: var(--glass);
      border: 2px solid rgba(255,255,255,.14); box-shadow: 0 18px 50px rgba(0,0,0,.45);
      backdrop-filter: blur(18px); color: var(--ink); font-family: var(--font-ui); }}
    .card .ic {{ width: 78px; height: 78px; border-radius: 20px; background: var(--accent);
      display: flex; align-items: center; justify-content: center; flex: none; }}
    .card .ic svg {{ width: 50px; height: 50px; }}
    .card .k {{ font-size: 28px; font-weight: 600; opacity: .8; letter-spacing: .04em; text-transform: uppercase; }}
    .card .t {{ font-size: 48px; font-weight: 800; line-height: 1.05; text-transform: uppercase; }}
    .card .t b {{ color: var(--accent); font-weight: 800; }}
"""

ICON = {
    "drop": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.7s6 6.6 6 11.1a6 6 0 0 1-12 0C6 9.3 12 2.7 12 2.7z"/></svg>',
    "zip": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round"><path d="M12 2v20"/><path d="M9 5h3M12 8h3M9 11h3M12 14h3"/><rect x="9" y="16" width="6" height="5" rx="1.5"/></svg>',
    "rain": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 15a4 4 0 0 1-.6-8A5.5 5.5 0 0 1 17 7.5a3.8 3.8 0 0 1 0 7.5z"/><path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>',
    "wind": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round"><path d="M3 9h11a3 3 0 1 0-3-3"/><path d="M3 14h15a3 3 0 1 1-3 3"/><path d="M3 19h6"/></svg>',
    "pocket": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linejoin="round"><path d="M5 4h14v9a7 7 0 0 1-14 0z"/><path d="M5 8h14"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round"><rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/></svg>',
    "hood": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 20c0-9 2.5-16 7-16s7 7 7 16"/><path d="M8.5 20c0-5 1.5-9 3.5-9s3.5 4 3.5 9"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12.5l5 5L20 6.5"/></svg>',
}


def card(cid, icon, k, t, start, dur, top=880, var=None):
    vt = f' data-var-text="{var}"' if var else ""
    return (f'    <div id="{cid}" class="card clip" data-start="{start}" data-duration="{dur}" data-track-index="0" '
            f'style="top:{top}px"><div class="ic">{ICON[icon]}</div><div><div class="k">{k}</div>'
            f'<div class="t"{vt}>{t}</div></div></div>')


def card_js(cid, start, dur, frm="x"):
    a = f'"#{cid}", {{ opacity: 0, x: -60, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, {start}'
    b = f'"#{cid}", {{ opacity: 0, x: 40, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(start + dur - 0.24)}'
    return f"    tl.fromTo({a});\n    tl.to({b});"


def scene(cid, css, body, js):
    return f"""<template>
  <style>{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1080" data-height="1920">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""


# ---- callouts-a: camo grey / other colour / waterproof zip
d_camo = fr(T["warna"] - T["camo"] - 0.05)
d_warna = 1.9
d_zip = fr(T["sesuai"] - T["zip"] - 0.2)
css_a = CARD_CSS + """
    #ca-color { position: absolute; right: 56px; top: 520px; width: 300px; padding: 16px; border-radius: 30px;
      background: var(--glass); border: 2px solid rgba(255,255,255,.16); box-shadow: 0 18px 50px rgba(0,0,0,.5); text-align: center; }
    #ca-color img { width: 268px; height: 400px; object-fit: cover; border-radius: 18px; display: block; }
    #ca-color .lbl { margin-top: 14px; font-family: var(--font-ui); font-weight: 800; font-size: 34px; color: var(--ink); text-transform: uppercase; }
    #ca-color .lbl b { color: var(--accent); }
"""
body_a = "\n".join([
    card("ca-camo", "check", "Warna", "Camo <b>Grey</b>", T["camo"], d_camo),
    f'    <div id="ca-color" class="clip" data-start="{T["warna"]}" data-duration="{d_warna}" data-track-index="1">'
    f'<img src="assets/img/green.jpg" alt="" /><div class="lbl">+ <b>Camo Hijau</b></div></div>',
    card("ca-zip", "zip", "Zip", "<b>Waterproof</b><br/>&amp; smooth", T["zip"], d_zip),
])
js_a = "\n".join([
    card_js("ca-camo", T["camo"], d_camo),
    f'    tl.fromTo("#ca-color", {{ opacity: 0, scale: 0.6, rotation: 8 }}, {{ opacity: 1, scale: 1, rotation: 3, duration: 0.5, ease: "back.out(1.4)" }}, {T["warna"]});',
    f'    tl.to("#ca-color", {{ opacity: 0, scale: 0.85, duration: 0.2, ease: "power3.in" }}, {fr(T["warna"] + d_warna - 0.22)});',
    card_js("ca-zip", T["zip"], d_zip),
])
open(os.path.join(P, "compositions/callouts-a.html"), "w").write(scene("callouts-a", css_a, body_a, js_a))

# ---- callouts-b: weather row / pocket + compartment
d_wx = fr(T["pocket"] - T["sesuai"] - 0.15)
d_pk = fr(min(3.0, out(22.42) - T["pocket"] + 0.1))
css_b = CARD_CSS + """
    #cb-wx { position: absolute; left: 0; right: 0; top: 760px; text-align: center; font-family: var(--font-ui); }
    #cb-wx .ttl { display: inline-block; padding: 10px 26px; border-radius: 999px; background: var(--accent); color: #111;
      font-weight: 800; font-size: 34px; letter-spacing: .06em; text-transform: uppercase; }
    #cb-wx .row { margin-top: 22px; display: flex; justify-content: center; gap: 22px; }
    #cb-wx .it { width: 270px; padding: 24px 10px 20px; border-radius: 28px; background: var(--glass);
      border: 2px solid rgba(255,255,255,.14); box-shadow: 0 18px 50px rgba(0,0,0,.45); color: var(--ink); }
    #cb-wx .it .ic { width: 96px; height: 96px; margin: 0 auto; border-radius: 26px; background: var(--accent);
      display: flex; align-items: center; justify-content: center; }
    #cb-wx .it .ic svg { width: 62px; height: 62px; }
    #cb-wx .it .n { margin-top: 14px; font-weight: 800; font-size: 40px; text-transform: uppercase; }
"""
body_b = "\n".join([
    f'    <div id="cb-wx" class="clip" data-start="{T["sesuai"]}" data-duration="{d_wx}" data-track-index="0">'
    f'<div id="cb-ttl" class="ttl">Sesuai untuk</div><div class="row">'
    f'<div id="cb-i1" class="it"><div class="ic">{ICON["rain"]}</div><div class="n">Hujan</div></div>'
    f'<div id="cb-i2" class="it"><div class="ic">{ICON["sun"]}</div><div class="n">Panas</div></div>'
    f'<div id="cb-i3" class="it"><div class="ic">{ICON["wind"]}</div><div class="n">Berangin</div></div>'
    f'</div></div>',
    card("cb-pocket", "pocket", "Simpanan", "Poket +<br/><b>Kompartmen</b>", T["pocket"], d_pk),
])
pop_item = lambda sel, t: f'    tl.fromTo("{sel}", {{ opacity: 0, y: 40, scale: 0.8 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.42, ease: "back.out(1.6)" }}, {t});'
js_b = "\n".join([
    f'    tl.fromTo("#cb-ttl", {{ opacity: 0, y: -16 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, {T["sesuai"]});',
    f'    tl.set(["#cb-i1", "#cb-i2", "#cb-i3"], {{ opacity: 0 }}, {T["sesuai"]});',
    pop_item("#cb-i1", T["hujan"]), pop_item("#cb-i2", T["panas"]), pop_item("#cb-i3", T["angin"]),
    f'    tl.to("#cb-wx", {{ opacity: 0, y: -30, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(T["sesuai"] + d_wx - 0.24)});',
    card_js("cb-pocket", T["pocket"], d_pk),
])
open(os.path.join(P, "compositions/callouts-b.html"), "w").write(scene("callouts-b", css_b, body_b, js_b))

# ---- callouts-c: waterproof pockets / phone safe / hoodie
d_wp = fr(out(34.76) - T["wp_pocket"] + 0.1)
d_ph = fr(out(40.26) - T["phone"] + 0.04)
d_hd = fr(out(49.84) - T["hoodie"] + 0.1)
body_c = "\n".join([
    card("cc-wp", "drop", "Poket", "<b>Waterproof</b><br/>kiri &amp; kanan", T["wp_pocket"], d_wp),
    card("cc-phone", "phone", "Phone", "Selamat,<br/><b>tak jatuh</b>", T["phone"], d_ph),
    card("cc-hood", "hood", "Hoodie", "Boleh <b>simpan</b><br/>dalam kolar", T["hoodie"], d_hd),
])
js_c = "\n".join([card_js("cc-wp", T["wp_pocket"], d_wp), card_js("cc-phone", T["phone"], d_ph),
                  card_js("cc-hood", T["hoodie"], d_hd)])
open(os.path.join(P, "compositions/callouts-c.html"), "w").write(scene("callouts-c", CARD_CSS, body_c, js_c))

# ---- cta: MEMANG RARE stamp, promo badge, tap arrow
d_rare = fr(T["dapat"] - T["rare"] + 0.25)
cta_at = fr(T["rare"] + d_rare)
d_cta = fr(TOTAL - cta_at)
css_cta = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {FONTS} }}
    #ct-rare {{ position: absolute; left: 0; right: 140px; top: 740px; text-align: center; }}
    #ct-rare span {{ display: inline-block; padding: 10px 40px 18px; font-family: var(--font-display); font-size: 140px;
      color: var(--accent); text-transform: uppercase; border: 10px solid var(--accent); border-radius: 26px;
      transform: rotate(-6deg); text-shadow: 0 8px 30px rgba(0,0,0,.5); background: rgba(0,0,0,.28); }}
    #ct-box {{ position: absolute; left: 40px; right: 200px; top: 780px; text-align: center; font-family: var(--font-ui); }}
    #ct-badge {{ display: inline-block; padding: 12px 34px; border-radius: 999px; background: var(--promo); color: #fff;
      font-weight: 900; font-size: 46px; letter-spacing: .06em; text-transform: uppercase; box-shadow: 0 14px 40px rgba(255,59,78,.45); }}
    #ct-main {{ margin-top: 20px; font-family: var(--font-display); font-size: 96px; line-height: .95; color: #fff;
      text-transform: uppercase; text-shadow: 0 10px 34px rgba(0,0,0,.6); }}
    #ct-main b {{ color: var(--accent); font-weight: inherit; }}
    #ct-size {{ display: inline-block; margin-top: 22px; padding: 12px 26px; border-radius: 18px; background: var(--glass);
      color: #fff; font-weight: 700; font-size: 36px; border: 2px solid rgba(255,255,255,.16); }}
    #ct-arrow {{ position: absolute; left: 120px; top: 1160px; width: 150px; height: 150px; }}
"""
body_cta = f"""    <div id="ct-rare" class="clip" data-start="{T['rare']}" data-duration="{d_rare}" data-track-index="0"><span id="ct-rare-s">Memang Rare</span></div>
    <div id="ct-box" class="clip" data-start="{cta_at}" data-duration="{d_cta}" data-track-index="0">
      <div><span id="ct-badge" data-var-text="ctaBadge">Tengah Promo</span></div>
      <div id="ct-main">Tekan<br/><b>Sekarang</b></div>
      <div><span id="ct-size" data-var-text="ctaSize">Saiz M – 5XL tersedia</span></div>
    </div>
    <svg id="ct-arrow" class="clip" data-start="{T['tekan']}" data-duration="{fr(TOTAL - T['tekan'])}" data-track-index="1" viewBox="0 0 100 100" fill="none" stroke="#ffd60a" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"><path id="ct-arrow-p" d="M78 12 C70 50 50 70 22 84 M22 84 L26 58 M22 84 L48 84"/></svg>"""
js_cta = f"""    tl.fromTo("#ct-rare-s", {{ opacity: 0, scale: 2.2 }}, {{ opacity: 1, scale: 1, duration: 0.28, ease: "power4.in" }}, {fr(T['rare'] - 0.2)});
    tl.to("#ct-rare-s", {{ opacity: 0, scale: 0.9, filter: "blur(8px)", duration: 0.2, ease: "power3.in" }}, {fr(T['rare'] + d_rare - 0.22)});
    tl.fromTo("#ct-badge", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.7)" }}, {cta_at});
    tl.fromTo("#ct-main", {{ opacity: 0, y: 30, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {fr(cta_at + 0.12)});
    tl.fromTo("#ct-size", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {fr(cta_at + 0.3)});
    tl.fromTo("#ct-arrow", {{ opacity: 0, x: 30, y: -30 }}, {{ opacity: 1, x: 0, y: 0, duration: 0.3, ease: "expo.out" }}, {T['tekan']});
    tl.to("#ct-arrow", {{ x: -10, y: 10, duration: 0.25, ease: "power2.inOut" }}, {fr(T['tekan'] + 0.3)});"""
open(os.path.join(P, "compositions/cta.html"), "w").write(scene("cta", css_cta, body_cta, js_cta))

# ---------------------------------------------------------------- captions.html
css_cap = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {FONTS} }}
    .cap {{ position: absolute; left: 50px; width: 790px; top: 1150px; text-align: center; overflow: visible; }}
    .cap .line {{ display: inline-block; max-width: 790px; font-family: var(--font-display); font-size: 74px; line-height: 1.04;
      color: var(--ink); text-transform: uppercase; letter-spacing: -.005em;
      -webkit-text-stroke: 3px rgba(0,0,0,.85); paint-order: stroke fill;
      text-shadow: 0 6px 0 rgba(0,0,0,.55), 0 10px 30px rgba(0,0,0,.55); }}
    .cap .w {{ display: inline-block; }}
    .cap .w.hl {{ color: var(--accent); }}
"""
js_cap = """    const pop = (sel, t) => tl.fromTo(sel, { scale: 0.7, opacity: 0, y: 14 }, { scale: 1, opacity: 1, y: 0, duration: 0.16, ease: "back.out(2)" }, t);
    const kill = (sel, end) => { tl.to(sel, { opacity: 0, duration: 0.08, ease: "power2.in" }, end - 0.08); };
""" + "\n".join("  " + l for l in cap_js)
open(os.path.join(P, "compositions/captions.html"), "w").write(
    scene("captions", css_cap, "\n".join(cap_items), js_cap))

print(f"total={TOTAL}s  segments={len(segs)}  caption groups={len(groups)}")
for s in segs:
    print(f'{s["id"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f}  src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}  {s["note"]}')
print(json.dumps(T))
