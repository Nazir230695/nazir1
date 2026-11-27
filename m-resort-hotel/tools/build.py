"""Builds index.html + compositions/overlay.html for the M Resort hotel review.

Edit the SEGS / LABELS / LINES tables below and re-run:  python3 tools/build.py
Clips live in assets/clips/<id>.mp4 (1080x1920 proxies of the Drive originals).
"""
import json, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (clip id, src_in, src_out, volume)
SEGS = [
    # HOOK
    ("214006", 2.4, 4.0, 0.25),   # lobby lights
    ("182348", 7.4, 9.0, 0.25),   # pool + umbrellas
    # NAME CARD
    ("190426", 14.6, 17.6, 0.3),  # facade with M logo
    # POOL
    ("182348", 2.6, 4.6, 0.4),
    ("181645", 22.6, 25.0, 0.4),
    ("182450", 0.0, 2.6, 0.7),    # dad lifts kid
    ("182728", 0.0, 2.0, 0.5),    # slide stairs
    ("183804", 6.0, 8.0, 0.5),    # jacuzzi
    ("182958", 2.0, 4.4, 0.5),    # rain shower
    # NIGHT
    ("190329", 20.4, 22.8, 0.35),
    ("190630", 6.8, 9.2, 0.35),
    # KIDS
    ("204248", 11.0, 13.4, 0.45),
    ("204553", 0.0, 1.6, 0.4),
    # GYM
    ("100014", 14.4, 16.4, 0.35),
    ("101330", 6.4, 8.6, 0.4),
    # BREAKFAST
    ("080709", 15.0, 17.0, 0.35),
    ("081052", 0.0, 1.5, 0.3),
    ("081405", 0.4, 1.9, 0.3),
    ("081914", 6.8, 8.4, 0.3),
    ("081754", 20.8, 22.4, 0.3),
    ("082458", 8.0, 10.0, 0.35),
    # ROOM
    ("121042", 0.6, 3.0, 0.5),
    ("121139", 3.2, 6.0, 1.0),    # "Terbaik!"
    ("121042", 16.4, 18.6, 0.6),  # thumbs up
    # OUTRO / CTA
    ("190329", 24.0, 28.6, 0.35),
]

# build the cut list
cuts, t = [], 0.0
for i, (cid, a, b, vol) in enumerate(SEGS):
    d = round(b - a, 4)
    cuts.append(dict(id=f"s{i:02d}", clip=cid, src_in=a, dur=d, start=round(t, 4), vol=vol))
    t += d
TOTAL = round(t, 4)
start = {c["id"]: c["start"] for c in cuts}
def at(i):
    return cuts[i]["start"]
def end(i):
    return round(cuts[i]["start"] + cuts[i]["dur"], 4)

HOOK_END = end(1)
NAME = (at(2), end(2))
CTA = (at(24), TOTAL)

# section labels (top pill): (text, icon, from-seg, to-seg)
LABELS = [
    ("Kolam ala resort", "wave", 3, 6),
    ("Jacuzzi", "bubble", 7, 7),
    ("Rain shower", "drop", 8, 8),
    ("Waktu malam", "moon", 9, 10),
    ("Kids club", "star", 11, 12),
    ("Gym 24 jam", "dumbbell", 13, 14),
    ("Breakfast buffet", "fork", 15, 20),
    ("Dalam bilik", "bed", 21, 23),
]

# review lines (lower third): (text, from-seg, to-seg)
LINES = [
    ("Lantai kolam dia<br><b>macam pasir</b>", 3, 4),
    ("Anak-anak memang <b>tak nak naik</b> 😂", 5, 6),
    ("Berendam dalam <b>jacuzzi</b>, lega habis", 7, 7),
    ("Mandi bawah <b>rain shower</b> tepi kolam", 8, 8),
    ("Malam-malam lagi <b>cantik</b> ✨", 9, 10),
    ("Ada <b>ball pit</b> &amp; <b>wall climbing</b>", 11, 12),
    ("Gym buka <b>24 jam</b>, view taman", 13, 14),
    ("Western, Melayu, Jepun — <b>semua ada</b>", 15, 17),
    ("Nasi lemak, sambal dia <b>padu</b> 🔥", 18, 19),
    ("Pinggan penuh, perut kenyang 😋", 20, 20),
    ("Ada <b>coffee set</b> &amp; <b>minibar</b>", 21, 21),
    ("Overall? <b>Terbaik!</b> 👍", 22, 23),
]

GRADE = {
    "preset": None, "intensity": 0.8,
    "adjust": {"exposure": 0.02, "contrast": 0.1, "highlights": -0.14, "shadows": 0.06, "whites": 0,
               "blacks": -0.04, "temperature": 0.02, "tint": 0, "vibrance": 0.14, "saturation": 0.04},
    "details": {"vignette": 0.1, "vignetteMidpoint": 0.5, "vignetteRoundness": 0, "vignetteFeather": 0.65,
                "grain": 0, "grainSize": 0.25, "grainRoughness": 0.5},
}
grade_attr = html.escape(json.dumps(GRADE, separators=(",", ":")), quote=True)

ICONS = {
    "check": '<svg viewBox="0 0 24 24"><path d="M12 1.8l2.6 1.9 3.2-.1 1 3.1 2.6 1.9-1 3.1 1 3.1-2.6 1.9-1 3.1-3.2-.1L12 22.2l-2.6-1.9-3.2.1-1-3.1-2.6-1.9 1-3.1-1-3.1 2.6-1.9 1-3.1 3.2.1z" fill="#20d5ec"/><path d="M7.6 12.3l3 3 5.8-6" stroke="#0b0b0f" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "wave": '<svg viewBox="0 0 24 24" fill="none" stroke="#0aa5ff" stroke-width="2.4" stroke-linecap="round"><path d="M2 9c2.5-2 4.5-2 7 0s4.5 2 7 0 4.5-2 6 0"/><path d="M2 15c2.5-2 4.5-2 7 0s4.5 2 7 0 4.5-2 6 0"/></svg>',
    "bubble": '<svg viewBox="0 0 24 24" fill="none" stroke="#0aa5ff" stroke-width="2.2"><circle cx="8" cy="14" r="5"/><circle cx="17" cy="8" r="3.4"/><circle cx="17.5" cy="17.5" r="2"/></svg>',
    "drop": '<svg viewBox="0 0 24 24" fill="#0aa5ff"><path d="M12 2.5s7 7.6 7 12.6a7 7 0 0 1-14 0c0-5 7-12.6 7-12.6z"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="#ff4d8d"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>',
    "dumbbell": '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round"><path d="M6 7v10M3 9.5v5M18 7v10M21 9.5v5M6 12h12"/></svg>',
    "fork": '<svg viewBox="0 0 24 24" fill="none" stroke="#e8590c" stroke-width="2.4" stroke-linecap="round"><path d="M7 3v8M4.5 3v5a2.5 2.5 0 0 0 5 0V3M7 11v10M17 3c-2 1.5-3 4-3 7h3v11"/></svg>',
    "bed": '<svg viewBox="0 0 24 24" fill="none" stroke="#7048e8" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18V6M3 13h18v5M21 13a3 3 0 0 0-3-3h-7v3"/><circle cx="7" cy="10.5" r="1.6"/></svg>',
    "pin_g": '<svg viewBox="0 0 24 24"><path d="M12 1.8a7.6 7.6 0 0 0-7.6 7.6c0 5.6 7.6 12.8 7.6 12.8s7.6-7.2 7.6-12.8A7.6 7.6 0 0 0 12 1.8z" fill="#22c55e"/><circle cx="12" cy="9.4" r="2.9" fill="#fff"/></svg>',
    "pin_w": '<svg viewBox="0 0 24 24"><path d="M12 1.8a7.6 7.6 0 0 0-7.6 7.6c0 5.6 7.6 12.8 7.6 12.8s7.6-7.2 7.6-12.8A7.6 7.6 0 0 0 12 1.8z" fill="#fff"/><circle cx="12" cy="9.4" r="2.9" fill="#22c55e"/></svg>',
    "pin": '<svg viewBox="0 0 24 24"><path d="M12 1.8a7.6 7.6 0 0 0-7.6 7.6c0 5.6 7.6 12.8 7.6 12.8s7.6-7.2 7.6-12.8A7.6 7.6 0 0 0 12 1.8z" fill="#fe2c55"/><circle cx="12" cy="9.4" r="2.9" fill="#fff"/></svg>',
}
STARS = "".join('<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>' for _ in range(5))

# ---------------------------------------------------------------- index.html
vids = []
for c in cuts:
    vids.append(
        f'        <video data-color-grading="{grade_attr}" id="{c["id"]}" class="clip seg" src="assets/clips/{c["clip"]}.mp4" '
        f'data-start="{c["start"]}" data-duration="{c["dur"]}" data-media-start="{c["src_in"]}" data-track-index="1" '
        f'data-has-audio="true" data-volume="{c["vol"]}" playsinline></video>')

sfx = []
def fx(name, t0, dur, vol):
    sfx.append(f'      <audio id="sx{len(sfx):02d}" class="clip" src="assets/sfx/{name}.mp3" data-start="{round(t0,4)}" data-duration="{dur}" data-track-index="{20 + len(sfx) % 3}" data-volume="{vol}"></audio>')
fx("impact-bass-1", 0.0, 1.0, 0.55)
fx("impact-bass-2", 0.75, 1.0, 0.5)
fx("pop", 1.55, 0.7, 0.4)
fx("whoosh-cinematic", HOOK_END - 0.25, 1.4, 0.4)
fx("sparkle", NAME[0] + 0.5, 1.1, 0.3)
for (_, _, a, _) in LABELS:
    fx("whoosh-short", at(a) - 0.05, 0.55, 0.3)
fx("pop", at(22) + 0.05, 0.7, 0.35)
fx("riser", CTA[0] - 1.2, 1.6, 0.3)
fx("impact-bass-1", CTA[0] + 0.1, 1.0, 0.45)
fx("click", CTA[0] + 1.3, 0.4, 0.5)
fx("sparkle", CTA[0] + 1.4, 1.1, 0.3)

zooms = []
for i, c in enumerate(cuts):
    s0, s1 = (1.0, 1.07) if i % 2 == 0 else (1.07, 1.0)
    zooms.append(f'      tl.fromTo("#{c["id"]}", {{ scale: {s0} }}, {{ scale: {s1}, duration: {c["dur"]}, ease: "none", immediateRender: false }}, {c["start"]});')

index = f'''<!DOCTYPE html>
<html lang="ms">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=1080, height=1920">
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }}
      #cam {{ position: absolute; inset: 0; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; transform-origin: 50% 45%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: one clip per kept shot. Built by tools/build.py -->
      <div id="cam">
{chr(10).join(vids)}
      </div>
      <div id="overlay" data-composition-id="overlay" data-composition-src="compositions/overlay.html" data-start="0" data-duration="{TOTAL}" data-track-index="2" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:10"></div>
{chr(10).join(sfx)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(zooms)}
      tl.to({{}}, {{ duration: {TOTAL} }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
open(os.path.join(ROOT, "index.html"), "w").write(index)

# ---------------------------------------------------------------- overlay.html
els, anim = [], []
def show(sel, t0, t1, kind="pop"):
    if kind == "pop":
        anim.append(f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.7)" }}, {round(t0,4)});')
    elif kind == "rise":
        anim.append(f'    tl.fromTo("{sel}", {{ opacity: 0, y: 30, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {round(t0,4)});')
    elif kind == "slam":
        anim.append(f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 1.8, filter: "blur(14px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.32, ease: "expo.out" }}, {round(t0,4)});')
    if t1 is not None:
        anim.append(f'    tl.to("{sel}", {{ opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }}, {round(t1 - 0.18,4)});')

# persistent header
els.append(f'    <div id="hdr" class="clip" data-start="0" data-duration="{TOTAL}" data-track-index="0" style="position:absolute;left:60px;width:960px;top:214px" data-layout-allow-safe-zone>'
           f'<div id="hdr-i" class="hdr"><div class="hdr-l"><div class="hdr-tr">{ICONS["check"]}<span>TRUSTED REVIEW</span></div><div class="hdr-u">@rezeki.nazir</div></div>'
           f'<div class="hdr-sep"></div><div class="hdr-r"><div class="hdr-h">M Resort &amp; Hotel</div><div class="hdr-c">Kuala Lumpur <span class="hdr-st">★</span> 4.9</div></div></div></div>')
show("#hdr-i", 0.15, None, "pop")

# hook
hd = HOOK_END
els.append(f'    <div id="hk" class="clip" data-start="0" data-duration="{hd}" data-track-index="0" style="position:absolute;left:0;width:1080px;top:560px;text-align:center">'
           f'<div id="hk1" class="hk-a">HOTEL <span class="t20">T20</span></div>'
           f'<div id="hk2" class="hk-b">HARGA <span class="b40">B40</span> 😱</div>'
           f'<div style="margin-top:34px"><span id="hk3" class="tt-pill"><span class="tt-dot"></span>booking di TikTok</span></div></div>')
show("#hk1", 0.0, None, "slam")
show("#hk2", 0.75, None, "slam")
show("#hk3", 1.55, None, "pop")
anim.append(f'    tl.to("#hk", {{ opacity: 0, y: -40, filter: "blur(10px)", duration: 0.22, ease: "power2.in" }}, {round(hd-0.22,4)});')

# name card
n0, n1 = NAME
els.append(f'    <div id="nm" class="card clip" data-start="{n0}" data-duration="{round(n1-n0,4)}" data-track-index="0" style="top:1040px">'
           f'<div class="nm-t">M Resort &amp; Hotel</div><div class="nm-s">Kuala Lumpur · Bukit Kiara</div>'
           f'<div class="nm-r"><span class="stars">{STARS}</span><span class="nm-5">5 bintang</span></div>'
           f'<div class="nm-g"><b>4.9</b> Excellent · 2.1K review</div></div>')
show("#nm", n0, n1, "rise")

# labels
for k, (txt, ic, a, b) in enumerate(LABELS):
    t0, t1 = at(a), end(b)
    els.append(f'    <div id="lb{k}" class="clip" data-start="{t0}" data-duration="{round(t1-t0,4)}" data-track-index="0" style="position:absolute;left:0;width:1080px;top:400px;text-align:center"><span id="lb{k}i" class="pill">{ICONS[ic]}<span>{txt}</span></span></div>')
    show(f"#lb{k}i", t0 + 0.05, None, "pop")
    anim.append(f'    tl.to("#lb{k}", {{ opacity: 0, duration: 0.15, ease: "power2.in" }}, {round(t1-0.15,4)});')

# review lines
for k, (txt, a, b) in enumerate(LINES):
    t0, t1 = at(a), end(b)
    els.append(f'    <div id="ln{k}" class="clip" data-start="{t0}" data-duration="{round(t1-t0,4)}" data-track-index="0" style="position:absolute;left:120px;width:740px;top:1090px;text-align:left"><span id="ln{k}i" class="line">{txt}</span></div>')
    show(f"#ln{k}i", t0 + 0.12, t1, "rise")

# CTA
c0, c1 = CTA
els.append(f'    <div id="cta" class="clip" data-start="{c0}" data-duration="{round(c1-c0,4)}" data-track-index="0" style="position:absolute;left:0;width:1080px;top:430px;text-align:center">'
           f'<div id="cta-pin" class="cta-pin">{ICONS["pin_g"]}</div>'
           f'<div id="cta-t1" class="cta-a">TEKAN <span class="loc">LOCATION HIJAU</span></div>'
           f'<div id="cta-t2" class="cta-b">untuk book 👇</div></div>')
els.append(f'    <div id="cta-c" class="card clip" data-start="{round(c0+0.6,4)}" data-duration="{round(c1-c0-0.6,4)}" data-track-index="0" style="top:1040px;width:800px;margin-left:-400px" data-layout-allow-safe-zone>'
           f'<div style="display:flex;align-items:center;gap:22px"><div class="pin-sq">{ICONS["pin_w"]}</div>'
           f'<div style="flex:1;text-align:left"><div class="nm-t" style="font-size:36px;white-space:nowrap">M Resort &amp; Hotel KL</div><div class="nm-s" style="margin-top:4px;font-size:28px;white-space:nowrap">Tekan location hijau 📍</div></div>'
           f'<div id="cta-btn" class="btn">Book</div></div></div>')
show("#cta-pin", c0 + 0.05, None, "slam")
anim.append(f'    tl.fromTo("#cta-pin svg", {{ y: 0 }}, {{ y: -26, duration: 0.32, ease: "power2.out", yoyo: true, repeat: 7 }}, {round(c0+0.45,4)});')
show("#cta-t1", c0 + 0.15, None, "slam")
show("#cta-t2", c0 + 0.45, None, "rise")
show("#cta-c", c0 + 0.6, None, "rise")
anim.append(f'    tl.fromTo("#cta-btn", {{ scale: 1 }}, {{ scale: 1.12, duration: 0.25, ease: "power2.out", yoyo: true, repeat: 5 }}, {round(c0+1.3,4)});')

overlay = f'''<template>
  <style>
    #root {{ position: absolute; inset: 0; pointer-events: none;
      --font-ui: "Montserrat", sans-serif;
      --font-num: "Oswald", "League Gothic", sans-serif;
      --gold: #f5c542; --green: #22c55e; --tt-red: #fe2c55; --tt-cyan: #25f4ee; --glass: rgba(14,15,19,.82); }}
    .hdr {{ display: flex; align-items: center; gap: 22px; padding: 16px 30px 16px 20px; border-radius: 30px;
      background: var(--glass); border: 1.5px solid rgba(255,255,255,.16); box-shadow: 0 12px 30px rgba(0,0,0,.35);
      color: #fff; font-family: var(--font-ui); font-weight: 800; font-size: 38px; letter-spacing: .12em; }}
    .hdr svg {{ width: 42px; height: 42px; flex: none; }}
    .hdr-l {{ flex: none; }} .hdr-tr {{ display: flex; align-items: center; gap: 10px; font-size: 30px; letter-spacing: .1em; }}
    .hdr-u {{ margin: 4px 0 0 52px; font-size: 28px; font-weight: 700; letter-spacing: .02em; color: var(--tt-cyan); }}
    .hdr-sep {{ width: 2px; align-self: stretch; background: rgba(255,255,255,.22); }}
    .hdr-r {{ flex: 1; text-align: right; min-width: 0; }} .hdr-h {{ font-size: 34px; letter-spacing: .01em; white-space: nowrap; }}
    .hdr-c {{ margin-top: 4px; font-size: 28px; font-weight: 600; letter-spacing: .02em; color: rgba(255,255,255,.72); }} .hdr-st {{ color: var(--gold); }}
    .hk-a, .hk-b {{ font-family: var(--font-num); font-weight: 700; color: #fff; line-height: .98; letter-spacing: .01em;
      text-shadow: 0 4px 0 rgba(0,0,0,.35), 0 10px 40px rgba(0,0,0,.75); }}
    .hk-a {{ font-size: 150px; }}
    .hk-b {{ font-size: 110px; margin-top: 34px; }}
    .t20 {{ color: var(--gold); }}
    .b40 {{ color: #fff; background: var(--tt-red); padding: 0 22px; border-radius: 22px; text-shadow: none; }}
    .tt-pill {{ display: inline-flex; align-items: center; gap: 14px; padding: 16px 34px; border-radius: 999px; background: #fff; color: #111;
      font-family: var(--font-ui); font-weight: 800; font-size: 46px; box-shadow: -5px 0 0 var(--tt-cyan), 5px 0 0 var(--tt-red), 0 14px 34px rgba(0,0,0,.4); }}
    .tt-dot {{ width: 22px; height: 22px; border-radius: 50%; background: var(--tt-red); box-shadow: -5px 0 0 var(--tt-cyan); }}
    .pill {{ display: inline-flex; align-items: center; gap: 12px; padding: 14px 30px; border-radius: 999px; background: #fff; color: #111;
      font-family: var(--font-ui); font-weight: 800; font-size: 40px; box-shadow: 0 12px 30px rgba(0,0,0,.35); white-space: nowrap; }}
    .pill svg {{ width: 38px; height: 38px; }}
    .line {{ display: inline; font-family: var(--font-ui); font-weight: 700; font-size: 46px; line-height: 1.34; color: #fff;
      background: rgba(10,10,14,.72); padding: 8px 20px; border-radius: 16px; -webkit-box-decoration-break: clone; box-decoration-break: clone; }}
    .line b {{ color: var(--gold); font-weight: 800; }}
    .card {{ position: absolute; left: 50%; width: 760px; margin-left: -380px; padding: 30px 36px; border-radius: 34px; background: var(--glass);
      border: 1.5px solid rgba(255,255,255,.14); box-shadow: 0 24px 60px rgba(0,0,0,.45); color: #fff; font-family: var(--font-ui); text-align: center; }}
    .nm-t {{ font-size: 54px; font-weight: 800; letter-spacing: .01em; }}
    .nm-s {{ font-size: 30px; font-weight: 600; color: rgba(255,255,255,.66); margin-top: 6px; }}
    .nm-r {{ display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 18px; }}
    .stars {{ display: inline-flex; gap: 4px; }} .stars svg {{ width: 38px; height: 38px; }}
    .nm-5 {{ font-size: 32px; font-weight: 700; }}
    .nm-g {{ margin-top: 14px; font-size: 32px; font-weight: 600; color: rgba(255,255,255,.8); }}
    .nm-g b {{ color: #fff; background: #1f9d55; padding: 2px 14px; border-radius: 10px; margin-right: 6px; }}
    .cta-pin svg {{ width: 170px; height: 170px; display: block; margin: 0 auto 10px; filter: drop-shadow(0 14px 24px rgba(0,0,0,.5)); }}
    .cta-a {{ font-family: var(--font-num); font-weight: 700; font-size: 86px; color: #fff; line-height: 1; text-shadow: 0 10px 40px rgba(0,0,0,.75); }}
    .cta-a .loc {{ color: var(--green); text-shadow: 0 4px 0 #0b5d2c, 0 10px 40px rgba(0,0,0,.6); }}
    .cta-b {{ font-family: var(--font-ui); font-weight: 800; font-size: 64px; color: #fff; margin-top: 12px; text-shadow: 0 6px 30px rgba(0,0,0,.8); }}
    .pin-sq {{ width: 96px; height: 96px; border-radius: 24px; background: #15803d; display: flex; align-items: center; justify-content: center; }}
    .pin-sq svg {{ width: 66px; height: 66px; }}
    .btn {{ padding: 18px 34px; border-radius: 999px; background: #15803d; color: #fff; font-weight: 800; font-size: 38px; }}
  </style>
  <div id="root" data-composition-id="overlay" data-width="1080" data-height="1920">
{chr(10).join(els)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(anim)}
    tl.to({{}}, {{ duration: {TOTAL} }}, 0);
    window.__timelines["overlay"] = tl;
  </script>
</template>
'''
open(os.path.join(ROOT, "compositions", "overlay.html"), "w").write(overlay)
print("total", TOTAL, "segs", len(cuts), "hook_end", HOOK_END, "cta", CTA)
