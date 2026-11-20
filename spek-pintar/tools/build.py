#!/usr/bin/env python3
"""AI smart glasses — styled after the 'contoh style editing' reference: small one-word captions, white label chips
with a round black icon, chrome headline with a neon ring + waveform, glass music/call cards, dot-and-line tags,
neon arc under product cards. Overlays sit on the lower half (over the shirt) so the face stays clear.
Usage: python3 -I build.py <transcript.json> <project_dir>   (transcript.json = {"v": words of raw.mp4, "w": words of raw2.mp4})
"""
import json, sys, html, os, re, math, subprocess

TJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(TJ))
SRC = {"v": "assets/raw.mp4", "w": "assets/raw2.mp4"}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))


# (id, src, first_word_start, last_word_start, cam_scale, in_override, out_override)
EDL = [
    ("a1", "v", 0.00, 1.64, 1.00, None, None),    # AI smart glasses
    ("b1", "v", 3.98, 10.78, 1.06, None, 11.40),  # tengok ni, haa... separuh, haa, gelap   (lens tint demo)
    ("c1", "v", 14.04, 17.28, 1.00, None, 17.95), # memang padu lah, nampak? smart kan, memang smart, serius padu
    ("d1", "v", 20.56, 23.44, 1.00, 20.05, None), # dia punya ni, dekat bawah-bawah ni, dia ada speaker dia tau
    ("d2", "v", 25.30, 27.34, 1.08, None, None),  # dia ada speaker, hidden speaker dia, memang rare
    ("e1", "v", 29.68, 30.52, 1.00, 29.30, None), # (lepas) tu lawa dia memang lawa
    ("f1", "v", 31.18, 34.18, 1.00, None, None),  # boleh bluetooth speaker, boleh dengar lagu, boleh angkat call
    ("g0", "w", 0.76, 1.92, 1.00, 0.70, 20.17),  # okay, ni apa dengar lah  + the song playing from the glasses speaker (held to the mic)
    ("g1", "w", 20.24, 21.30, 1.06, None, 21.75), # oh layan weh, syok oh       (second clip, listening)
    ("g2", "w", 25.58, 26.00, 1.10, None, 26.70), # memang terbaik lah
    ("h1", "v", 34.54, 35.90, 1.00, 34.70, None), # yang best dia yang ni
    ("i1", "v", 41.10, 44.78, 1.00, None, None),  # kalau nak drive kereta, nak pergi mancing, nak pergi berjalan
    ("j1", "v", 45.16, 49.50, 1.06, None, None),  # dia electrochromic, dia boleh tukar warna, tiga rasa
    ("l1", "v", 51.34, 54.16, 1.00, None, None),  # nak dapat mana kalau nak berkenan? memang lawa, memang cun
    ("l2", "v", 56.34, 57.34, 1.04, None, 57.66), # tekan link di bawah
]

segs, f = [], 0
for sid, src, a, b, sc, ia, ob in EDL:
    W_ = WORDS[src]
    w0, w1 = wat(src, a), wat(src, b)
    i0, i1 = W_.index(w0), W_.index(w1)
    prev_end = W_[i0 - 1]["end"] if i0 > 0 else 0
    next_start = W_[i1 + 1]["start"] if i1 + 1 < len(W_) else 1e9
    a = max(0, min(w0["start"] - 0.02, max(w0["start"] - 0.07, prev_end + 0.02)))
    b = max(w1["start"] + 0.15, min(min(w1["end"], w1["start"] + 1.2) + 0.1, next_start - 0.03))
    a = ia if ia is not None else a
    b = ob if ob is not None else b
    fa, fb = round(a * FPS), round(b * FPS)
    segs.append(dict(id=sid, src=src, src_in=fa / FPS, src_out=fb / FPS, start=f / FPS, dur=(fb - fa) / FPS, scale=sc))
    f += fb - fa
for sg in segs:
    sg["src_in"] = round(sg["src_in"], 4); sg["src_out"] = round(sg["src_out"], 4)
    sg["start"] = math.ceil(sg["start"] * 10000 - 1e-6) / 10000
    sg["dur"] = math.floor(sg["dur"] * 10000 + 1e-6) / 10000 - 0.0001
TOTAL = round(f / FPS, 4)
SEG = {s["id"]: s for s in segs}


def at(sid, t):
    s = SEG[sid]
    return fr(s["start"] + (t - s["src_in"]))


def st(sid):
    return fr(SEG[sid]["start"])


def end(sid):
    s = SEG[sid]
    return fr(s["start"] + s["dur"])


def W(sid, t):
    return at(sid, wat(SEG[sid]["src"], t)["start"])


# ---------------------------------------------------------------- one-word captions
FIX = {"layar": "layan", "elektro": "electro"}
DROP = {"ha", "haa", "hu", "oh", "la", "weh", "game", "okay", "lepas"}


def norm(w):
    t = w["text"]
    core = re.sub(r"[^\w-]", "", t).lower()
    if core in DROP:
        return None
    if core in FIX:
        return FIX[core]
    return t


kept = []
for s in segs:
    for w in WORDS[s["src"]]:
        if s["src_in"] - 0.05 <= w["start"] < s["src_out"] - 0.05:
            txt = norm(w)
            if not txt:
                continue
            s0 = max(at(s["id"], w["start"]), s["start"])
            en = at(s["id"], min(w["end"], s["src_out"]))
            kept.append(dict(text=txt, start=s0, end=max(en, s0 + 0.12), seg=s["id"]))
glued = []
for w in kept:
    g = glued[-1] if glued and glued[-1]["seg"] == w["seg"] else None
    if g and (w["text"].startswith("-") or w["text"].startswith(".I") or w["text"].startswith("chromic")):
        g["text"] = (g["text"] + w["text"]).replace("A.I.", "AI"); g["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
cap_items, cap_js = [], []
for i, w in enumerate(kept):
    nxt = kept[i + 1]["start"] if i + 1 < len(kept) else TOTAL
    s0 = fr(w["start"])
    en = fr(min(max(w["end"] + 0.05, s0 + 0.25), nxt, TOTAL))
    if en - s0 < 0.1:
        continue
    word = re.sub(r"[.,!?]", "", w["text"]).upper()
    cid = f"cw{i:03d}"
    cap_items.append(f'    <div id="{cid}" class="cw clip" data-start="{s0}" data-duration="{fr(en - s0)}" data-track-index="0">'
                     f'<span id="{cid}s">{html.escape(word)}</span></div>')
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.1, ease: "power2.out" }}, {s0});')

# ---------------------------------------------------------------- design tokens (reference style)
TOK = """
      --ink: #ffffff;
      --dark: #0d0e10;
      --neon: #3dff8b;
      --neon-soft: rgba(61,255,139,.55);
      --glass: rgba(16, 17, 20, 0.78);
      --stroke: rgba(255,255,255,.14);
      --font-ui: "Montserrat", sans-serif;
"""
BASE = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .chip {{ position: absolute; left: 0; width: 960px; text-align: center; }}
    .chip > span {{ display: inline-flex; align-items: center; gap: 14px; }}
    .chip .lb {{ background: #fff; color: #111; font-family: var(--font-ui); font-weight: 600; font-size: 40px; letter-spacing: .01em;
      padding: 8px 18px; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,.35); white-space: nowrap; text-transform: uppercase; }}
    .chip .ic {{ width: 70px; height: 70px; border-radius: 50%; background: var(--dark); border: 2.5px solid rgba(255,255,255,.9);
      display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 30px rgba(0,0,0,.4); }}
    .chip .ic svg {{ width: 38px; height: 38px; }}
    .tag {{ position: absolute; font-family: var(--font-ui); font-weight: 600; font-size: 40px; color: #111; background: #fff;
      border: 3px solid #111; padding: 6px 16px; white-space: nowrap; text-transform: uppercase; }}
    .co svg {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }}
    .glass {{ position: absolute; background: var(--glass); border: 1.5px solid var(--stroke); border-radius: 30px;
      box-shadow: 0 24px 60px rgba(0,0,0,.5); backdrop-filter: blur(18px); color: #fff; font-family: var(--font-ui); }}
    .head {{ position: absolute; left: 0; width: 960px; text-align: center; font-family: var(--font-ui); font-weight: 800; color: #fff;
      font-size: 62px; line-height: 1.08; text-shadow: 0 3px 6px rgba(0,0,0,.5), 0 10px 34px rgba(0,0,0,.6); }}
    .chrome {{ position: absolute; left: 0; width: 960px; text-align: center; font-family: var(--font-ui); font-weight: 900; font-size: 150px;
      letter-spacing: .02em; line-height: 1; }}
    .chrome span {{ display: inline-block; background: linear-gradient(180deg, #ffffff 0%, #d9dde3 38%, #7d838c 52%, #f4f6f8 70%, #a9afb7 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent; filter: drop-shadow(0 6px 18px rgba(0,0,0,.55)); }}
    .pilltag {{ display: inline-flex; align-items: center; gap: 10px; padding: 10px 26px 10px 16px; border-radius: 12px; background: rgba(255,255,255,.94);
      color: #111; font-family: var(--font-ui); font-weight: 700; font-size: 32px; box-shadow: 0 10px 28px rgba(0,0,0,.35); white-space: nowrap; }}
    .pilltag svg {{ width: 30px; height: 30px; }}
"""
I = {  # white line icons for the round black badge
    "touch": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V11"/><path d="M12 10.5V9a1.5 1.5 0 0 1 3 0v2"/><path d="M15 10.5a1.5 1.5 0 0 1 3 0V15a6 6 0 0 1-6 6h-1a6 6 0 0 1-4.6-2.2L4 15.6a1.5 1.5 0 0 1 2.3-1.9L9 16"/></svg>',
    "sun": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>',
    "half": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="#fff"/></svg>',
    "moon": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg>',
    "spark": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7z"/></svg>',
    "bt": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7l10 10-5 4V3l5 4L7 17"/></svg>',
    "car": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 16V11l2-5h10l2 5v5"/><path d="M3.5 16h17v3h-17z"/><circle cx="7.5" cy="13.5" r="1"/><circle cx="16.5" cy="13.5" r="1"/></svg>',
    "fish": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12c3-5 9-6 13-3l5-3-1.5 6L21 18l-5-3c-4 3-10 2-13-3z"/><circle cx="8" cy="11" r=".8" fill="#fff"/></svg>',
    "walk": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="4" r="1.8"/><path d="M10 21l2-6-2-3 1-4 4 3 3 1M11 8l-4 2-1 4M12 15l3 6"/></svg>',
    "palette": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 3a9 9 0 1 0 0 18c1.4 0 2-1 1.6-2.2-.5-1.3.4-2.8 1.9-2.8H18a3 3 0 0 0 3-3c0-5.5-4-10-9-10z"/><circle cx="7.5" cy="11" r="1.2" fill="#fff"/><circle cx="10.5" cy="7" r="1.2" fill="#fff"/><circle cx="15" cy="7.5" r="1.2" fill="#fff"/></svg>',
}
STAR = '<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>'
GEM = '<svg viewBox="0 0 24 24" fill="#5ac8fa"><path d="M6 3h12l4 6-10 12L2 9z"/></svg>'


def clip(cid, start, dur, inner, cls="", style="", lane=0, extra=""):
    return (f'    <div id="{cid}" class="{cls} clip" data-start="{fr(start)}" data-duration="{fr(dur)}" '
            f'data-track-index="{lane}" style="{style}"{extra}>{inner}</div>')


def out(sel, t):
    return f'    tl.to("{sel}", {{ opacity: 0, scale: 0.92, duration: 0.18, ease: "power2.in" }}, {fr(t - 0.2)});'


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


def write(name, txt):
    open(os.path.join(P, "compositions", name), "w").write(txt)


def build_scene(name, parts):
    write(f"{name}.html", scene(name, BASE, "\n".join(p[0] for p in parts), "\n".join(p[1] for p in parts)))


# ---------------------------------------------------------------- reference-style pieces
def chip(cid, label, icon, start, dur, y, icon_first=False):
    """white label + round black icon badge (HUJAN / WATERPROOF in the reference)"""
    ic = f'<span id="{cid}c" class="ic">{I[icon]}</span>'
    lb = f'<span id="{cid}b" class="lb">{label}</span>'
    inner = f'<span>{ic + lb if icon_first else lb + ic}</span>'
    body = clip(cid, start, dur, inner, cls="chip", style=f"top:{y}px")
    js = "\n".join([
        f'    tl.fromTo("#{cid}b", {{ opacity: 0, x: -24, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}c", {{ opacity: 0, scale: 0.3, rotation: -60 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.4, ease: "back.out(2)" }}, {fr(start + 0.06)});',
        out(f"#{cid}", start + dur)])
    return body, js


def chip_swap(cid, items, end_t, y):
    """one chip slot whose label/icon changes in place (TERANG -> SEPARUH -> GELAP)"""
    parts = []
    for i, (label, icon, t) in enumerate(items):
        t_end = items[i + 1][2] if i + 1 < len(items) else end_t
        body, js = chip(f"{cid}{i}", label, icon, t, t_end - t + (0.2 if i + 1 < len(items) else 0), y)
        parts.append((body, js))
    return "\n".join(p[0] for p in parts), "\n".join(p[1] for p in parts)


def tag(cid, label, start, dur, dot, box):
    """black-bordered white tag joined to a dot by an elbow line (TANPA GETAH in the reference)"""
    (dx, dy), (bx, by) = dot, box
    svg = (f'<svg viewBox="0 0 1080 1920"><path id="{cid}p" d="M{dx} {dy} L{dx - 30} {by + 30} L{bx} {by + 30}" stroke="#fff" stroke-width="3.5" fill="none"/>'
           f'<circle id="{cid}d" cx="{dx}" cy="{dy}" r="10" fill="#fff"/></svg>')
    lab = f'<div id="{cid}l" class="tag" style="left:{bx - 330}px; top:{by}px; width:330px; text-align:center">{label}</div>'
    body = clip(cid, start, dur, svg + lab, cls="co", style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid}d", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.25, ease: "back.out(2)" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}p", {{ strokeDasharray: 900, strokeDashoffset: 900 }}, {{ strokeDashoffset: 0, duration: 0.4, ease: "power2.inOut" }}, {fr(start + 0.08)});',
        f'    tl.fromTo("#{cid}l", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.8)" }}, {fr(start + 0.35)});',
        out(f"#{cid}", start + dur)])
    return body, js


def chrome(cid, text, start, dur, y, ring=None):
    """big chrome word, letters land one by one; optional neon ring + waveform centred at ring=(cx, cy, r)"""
    letters = "".join(f'<span class="ch{cid}">{html.escape(c) if c != " " else "&nbsp;"}</span>' for c in text)
    inner = f'<div class="chrome" style="top:{y}px">{letters}</div>'
    js = [f'    tl.fromTo(".ch{cid}", {{ opacity: 0, y: 40, scale: 1.4, filter: "blur(12px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.35, ease: "expo.out", stagger: 0.06 }}, {fr(start)});']
    if ring:
        cx, cy, r = ring
        blob = (f'M{cx - r} {cy} C {cx - r} {cy - r * 0.7}, {cx - r * 0.5} {cy - r * 1.05}, {cx} {cy - r} S {cx + r * 1.05} {cy - r * 0.55}, {cx + r} {cy} '
                f'S {cx + r * 0.6} {cy + r * 1.05}, {cx} {cy + r} S {cx - r * 1.02} {cy + r * 0.6}, {cx - r} {cy} Z')
        bars = "".join(f'<rect class="wb{cid}" x="{x}" y="{cy - h / 2}" width="5" height="{h}" rx="2.5" fill="#fff"/>'
                       for x, h in [(cx - r - 40 - k * 14, 14 + (k * 37) % 70) for k in range(14)] + [(cx + r + 35 + k * 14, 14 + (k * 53) % 70) for k in range(14)])
        inner = (f'<svg viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:visible">'
                 f'<path id="{cid}r1" d="{blob}" stroke="#3dff8b" stroke-width="7" fill="none" style="filter:drop-shadow(0 0 14px #3dff8b) drop-shadow(0 0 30px rgba(61,255,139,.7))"/>'
                 f'<path id="{cid}r2" d="{blob}" stroke="rgba(220,255,235,.9)" stroke-width="2.5" fill="none"/>{bars}</svg>') + inner
        js += [f'    tl.fromTo(["#{cid}r1", "#{cid}r2"], {{ opacity: 0, scale: 0.6, rotation: -30, transformOrigin: "{cx}px {cy}px" }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.6, ease: "expo.out" }}, {fr(start)});',
               f'    tl.to(["#{cid}r1", "#{cid}r2"], {{ rotation: 40, duration: {fr(dur)}, ease: "none", transformOrigin: "{cx}px {cy}px" }}, {fr(start + 0.6)});',
               f'    tl.fromTo(".wb{cid}", {{ scaleY: 0.1, transformOrigin: "50% 50%" }}, {{ scaleY: 1, duration: 0.25, ease: "power2.out", stagger: {{ each: 0.02, from: "center" }} }}, {fr(start + 0.1)});',
               f'    tl.to(".wb{cid}", {{ scaleY: 0.35, duration: 0.18, ease: "sine.inOut", yoyo: true, repeat: {max(1, int(dur / 0.18) - 3)}, stagger: {{ each: 0.03, from: "random" }} }}, {fr(start + 0.4)});']
    body = clip(cid, start, dur, inner, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js.append(out(f"#{cid}", start + dur))
    return body, "\n".join(js)


def head(cid, text, start, dur, y):
    body = clip(cid, start, dur, f'<div id="{cid}t">{text}</div>', cls="head", style=f"top:{y}px")
    js = "\n".join([f'    tl.fromTo("#{cid}t", {{ opacity: 0, y: 30, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def sound_arcs(cid, start, dur, cx, cy):
    """green sound arcs either side of the head (Bunyi still sedap in the reference)"""
    arcs = ""
    for side in (-1, 1):
        for k, r in enumerate((60, 100, 140)):
            x0 = cx + side * 250
            arcs += (f'<path class="sa{cid}" d="M{x0 + side * r * 0.35} {cy - r} Q {x0 + side * r} {cy} {x0 + side * r * 0.35} {cy + r}" '
                     f'stroke="#3dff8b" stroke-width="{9 - k * 2}" stroke-linecap="round" fill="none" style="filter:drop-shadow(0 0 10px #3dff8b)"/>')
    body = clip(cid, start, dur, f'<svg viewBox="0 0 1080 1920" style="position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:visible">{arcs}</svg>',
                style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo(".sa{cid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2, stagger: 0.07 }}, {fr(start)});',
                    f'    tl.to(".sa{cid}", {{ opacity: 0.25, duration: 0.25, ease: "sine.inOut", yoyo: true, repeat: {max(1, int(dur / 0.25) - 2)}, stagger: 0.08 }}, {fr(start + 0.45)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def music_card(cid, start, dur, y, title="Dengar lagu", sub="Bluetooth 5.3"):
    bars = "".join(f'<span class="mb{cid}" style="display:inline-block;width:5px;height:{10 + (k * 29) % 34}px;margin:0 2px;border-radius:3px;background:rgba(255,255,255,.75)"></span>' for k in range(22))
    inner = (f'<div style="display:flex;align-items:center;gap:22px;padding:20px 24px">'
             f'<div style="width:96px;height:96px;border-radius:18px;background:linear-gradient(135deg,#ff6a88,#7b5cff 55%,#22d3ee);flex:none"></div>'
             f'<div style="flex:1;min-width:0"><div style="font-weight:800;font-size:36px">{title}</div>'
             f'<div style="font-weight:600;font-size:28px;color:rgba(255,255,255,.65);margin-top:2px">{sub}</div>'
             f'<div style="margin-top:12px;height:44px;display:flex;align-items:center">{bars}</div></div>'
             f'<div style="width:78px;height:78px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex:none">'
             f'<svg viewBox="0 0 24 24" width="34" height="34" fill="#111"><path d="M8 5v14l11-7z"/></svg></div>'
             f'<div style="width:54px;height:54px;border-radius:50%;background:#1ed760;flex:none;display:flex;align-items:center;justify-content:center">'
             f'<svg viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round"><path d="M6 9.5c4-1.3 8.5-1 12 1M7 13c3.3-1 6.8-.7 9.5.8M8 16.3c2.6-.7 5-.5 7 .6"/></svg></div></div>')
    body = clip(cid, start, dur, inner, cls="glass", style=f"left:80px; top:{y}px; width:800px")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 40, rotation: -4, scale: 0.9 }}, {{ opacity: 1, y: 0, rotation: -2, scale: 1, duration: 0.5, ease: "back.out(1.5)" }}, {fr(start)});',
                    f'    tl.fromTo(".mb{cid}", {{ scaleY: 0.2, transformOrigin: "50% 50%" }}, {{ scaleY: 1, duration: 0.2, ease: "sine.inOut", yoyo: true, repeat: {max(1, int(dur / 0.2) - 2)}, stagger: {{ each: 0.025, from: "random" }} }}, {fr(start + 0.2)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def call_card(cid, start, dur, y):
    inner = (f'<div style="display:flex;align-items:center;gap:20px;padding:18px 24px">'
             f'<div style="width:82px;height:82px;border-radius:50%;background:linear-gradient(135deg,#f4a261,#e76f51);flex:none;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:38px">M</div>'
             f'<div style="flex:1"><div style="font-weight:800;font-size:40px">Angkat call</div></div>'
             f'<div id="{cid}a" style="width:76px;height:76px;border-radius:50%;background:#34c759;flex:none;display:flex;align-items:center;justify-content:center">'
             f'<svg viewBox="0 0 24 24" width="36" height="36" fill="#fff"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg></div></div>')
    body = clip(cid, start, dur, inner, cls="glass", style=f"left:120px; top:{y}px; width:720px")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 40, rotation: 4, scale: 0.9 }}, {{ opacity: 1, y: 0, rotation: 2, scale: 1, duration: 0.5, ease: "back.out(1.5)" }}, {fr(start)});',
                    f'    tl.fromTo("#{cid}a", {{ scale: 1 }}, {{ scale: 1.15, duration: 0.22, ease: "sine.inOut", yoyo: true, repeat: {max(1, int(dur / 0.22) - 3)} }}, {fr(start + 0.3)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def touch_card(cid, start, dur, x, y):
    """tilted dark card 'Touch Control' (reference 16.5s)"""
    inner = (f'<div style="width:250px;height:250px;border-radius:26px;background:linear-gradient(150deg,#2a2d33,#0b0c0e);border:1.5px solid rgba(255,255,255,.18);'
             f'box-shadow:0 24px 60px rgba(0,0,0,.6);display:flex;flex-direction:column;justify-content:flex-end;padding:22px;font-family:var(--font-ui);color:#fff">'
             f'<div style="width:62px;height:62px;border-radius:50%;border:3px solid #3dff8b;margin-bottom:auto;box-shadow:0 0 18px #3dff8b"></div>'
             f'<div style="font-weight:800;font-size:34px;line-height:1.05">Touch<br/>Control</div></div>')
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{x}px; top:{y}px")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, rotation: -25, scale: 0.6, y: 30 }}, {{ opacity: 1, rotation: -10, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def product_card(cid, src, start, dur, y, w=760, label=None):
    """floating product image card with a neon arc beneath (reference 30s)"""
    arc = (f'<svg viewBox="0 0 1080 400" style="position:absolute;left:-{(1080 - w) // 2}px;top:-60px;width:1080px;height:400px;overflow:visible">'
           f'<path id="{cid}arc" d="M60 360 Q 540 -40 1020 360" stroke="#3dff8b" stroke-width="6" fill="none" style="filter:drop-shadow(0 0 16px #3dff8b) drop-shadow(0 0 34px rgba(61,255,139,.6))"/></svg>')
    lab = f'<div style="margin-top:16px;text-align:center"><span class="pilltag">{label}</span></div>' if label else ""
    inner = arc + f'<div style="position:relative;border-radius:26px;overflow:hidden;box-shadow:0 30px 70px rgba(0,0,0,.6)"><img src="{src}" alt="" style="display:block;width:{w}px"/></div>' + lab
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{(960 - w) // 2}px; top:{y}px; width:{w}px", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}arc", {{ strokeDasharray: 1300, strokeDashoffset: 1300 }}, {{ strokeDashoffset: 0, duration: 0.6, ease: "power2.out" }}, {fr(start)});',
                    f'    tl.fromTo("#{cid} > div", {{ opacity: 0, y: 50, scale: 0.85 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(1.4)", stagger: 0.1 }}, {fr(start + 0.05)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def pill_pair(cid, start, dur, y):
    """Kualiti / Design pair (reference 33s)"""
    inner = (f'<span id="{cid}a" class="pilltag" style="margin-right:18px">{STAR}Kualiti</span>'
             f'<span id="{cid}b" class="pilltag">{GEM}Design</span>')
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:0; width:960px; top:{y}px; text-align:center")
    js = "\n".join([f'    tl.fromTo(["#{cid}a", "#{cid}b"], {{ opacity: 0, y: 20, scale: 0.7 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.8)", stagger: 0.12 }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


# ---------------------------------------------------------------- scenes  (face sits ~y 250-760; overlays live at y 860-1260)
LOW, LOW2 = 940, 1040   # chip rows over the shirt
CAP_Y = 1200

build_scene("hook", [
    head("hk-t", "AI Smart<br/>Glasses", 0.05, end("a1") - 0.05, 900),
    touch_card("hk-touch", W("b1", 4.38), W("b1", 9.34) - W("b1", 4.38) - 0.3, 40, 770),
    chip_swap("hk-tint", [("Terang", "sun", W("b1", 5.32)), ("Separuh", "half", W("b1", 9.34) - 0.25), ("Gelap", "moon", W("b1", 10.78) - 0.25)], end("b1"), LOW2),
    chip("hk-smart", "Smart", "spark", W("c1", 15.68), end("c1") - W("c1", 15.68), LOW),
])

build_scene("speaker", [
    tag("sp-tag", "Speaker", W("d1", 22.80) - 0.2, end("d1") - W("d1", 22.80) + 0.2, (560, 1020), (900, 1120)),
    chrome("sp-hid", "HIDDEN", W("d2", 26.10) - 0.15, end("d2") - W("d2", 26.10) + 0.15, 870, ring=(480, 950, 190)),
    pill_pair("sp-kd", st("e1") + 0.05, end("e1") - st("e1") - 0.05, LOW),
])

build_scene("sound", [
    music_card("sd-music", W("f1", 31.48), W("f1", 33.90) - W("f1", 31.48), 900, title="Bluetooth speaker", sub="Boleh dengar lagu"),
    call_card("sd-call", W("f1", 33.90), end("f1") - W("f1", 33.90) + 0.6, 900),
    music_card("sd-play", W("g0", 1.92) + 0.3, end("g0") - W("g0", 1.92) - 0.3, 1150, title="Lagu dari speaker spek", sub="Dengar sendiri"),
    sound_arcs("sd-arcs0", W("g0", 1.92) + 0.3, end("g0") - W("g0", 1.92) - 0.3, 540, 640),
    head("sd-sedap", "Bunyi sedap", st("g1") + 0.9, end("g1") - st("g1") - 0.9, 1080),
    sound_arcs("sd-arcs", st("g1") + 0.05, end("g2") - st("g1") - 0.05, 610, 600),
    music_card("sd-music2", st("g2"), end("g2") - st("g2"), 1000, title="Memang terbaik", sub="Hidden speaker"),
])

build_scene("uses", [
    chip("us-best", "Yang paling best", "spark", st("h1") + 0.05, end("h1") - st("h1") - 0.05, LOW),
    chip("us-car", "Drive", "car", W("i1", 42.04), end("i1") - W("i1", 42.04) + 0.5, 840, icon_first=True),
    chip("us-fish", "Mancing", "fish", W("i1", 43.60), end("i1") - W("i1", 43.60) + 0.5, 940, icon_first=True),
    chip("us-walk", "Berjalan", "walk", W("i1", 44.78), end("i1") - W("i1", 44.78) + 0.5, 1040, icon_first=True),
])

build_scene("tint", [
    product_card("tn-card", "assets/img/tint.jpg", W("j1", 45.70) - 0.1, end("j1") - W("j1", 45.70) + 0.1, 870, w=620),
])

CTA0 = st("l1") + 0.05
shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:16px">'
        f'<div style="width:190px;height:116px;border-radius:16px;overflow:hidden;background:#e9eaec;flex:none"><img src="assets/img/front.jpg" alt="" style="width:190px;height:116px;object-fit:cover"/></div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:40px;letter-spacing:.02em">AI SMART GLASSES</div>'
        f'<div style="margin-top:6px;display:flex;align-items:center;gap:10px;font-weight:700;font-size:30px;color:rgba(255,255,255,.8)">{STAR.replace("<svg", "<svg width=30 height=30")} 4.8 &middot; 103.9K terjual</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:10px;padding:11px 26px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:34px;white-space:nowrap;box-shadow:0 12px 30px rgba(0,0,0,.4)">'
       '<svg viewBox="0 0 24 24" width="32" height="32" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Tekan link di bawah</div>')
build_scene("outro", [
    (clip("ot-shop", CTA0, TOTAL - CTA0, shop, cls="glass", style="left:110px; top:880px; width:740px"),
     "\n".join([f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 40, scale: 0.9 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.5, ease: "back.out(1.5)" }}, {CTA0});'])),
    (clip("ot-cta", CTA0 + 0.35, TOTAL - CTA0 - 0.35, cta, style="position:absolute; left:0; width:960px; top:1060px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.8)" }}, {fr(CTA0 + 0.35)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.07, duration: 0.25, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }}, {W("l2", 56.92)});'])),
])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: {CAP_Y}px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 900; font-size: 46px; color: #fff; letter-spacing: .02em;
      text-shadow: 0 2px 0 rgba(0,0,0,.4), 0 4px 16px rgba(0,0,0,.65); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="{SRC[s["src"]]}" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1"{" data-fade-out=\"0.08\"" if s["id"] == "l2" else ""} playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.07, duration: {end("a1")}, ease: "none", immediateRender: false }}, 0);')
# quick punch-in on each cut, like the reference
cam += [f'      tl.fromTo("#cam", {{ scale: {round(s["scale"] * 1.04, 3)} }}, {{ scale: {s["scale"]}, duration: 0.25, ease: "power2.out", immediateRender: false }}, {s["start"]});' for s in segs[1:]]

SFX = [("sx-hk", "whoosh.mp3", 0.0, 0.3),
       ("sx-touch", "click-soft.mp3", W("b1", 4.38), 0.45),
       ("sx-t1", "pop.mp3", W("b1", 5.32), 0.3),
       ("sx-t2", "pop.mp3", W("b1", 9.34) - 0.25, 0.3),
       ("sx-t3", "pop.mp3", W("b1", 10.78) - 0.25, 0.3),
       ("sx-smart", "sparkle.mp3", W("c1", 15.68), 0.25),
       ("sx-tag", "click.mp3", W("d1", 22.80) - 0.2, 0.4),
       ("sx-hid", "whoosh.mp3", W("d2", 26.10) - 0.2, 0.3),
       ("sx-kd", "pop.mp3", st("e1") + 0.05, 0.3),
       ("sx-bt", "pop.mp3", W("f1", 31.48), 0.3),
       ("sx-music", "whoosh-short.mp3", W("f1", 33.18), 0.3),
       ("sx-call", "click-soft.mp3", W("f1", 33.90), 0.4),
       ("sx-play", "whoosh-short.mp3", W("g0", 1.92) + 0.3, 0.2),
       ("sx-sedap", "sparkle.mp3", st("g1"), 0.22),
       ("sx-best", "pop.mp3", st("h1") + 0.05, 0.3),
       ("sx-car", "pop.mp3", W("i1", 42.04), 0.3),
       ("sx-fish", "pop.mp3", W("i1", 43.60), 0.3),
       ("sx-walk", "pop.mp3", W("i1", 44.78), 0.3),
       ("sx-tint", "whoosh.mp3", W("j1", 45.70) - 0.1, 0.3),
              ("sx-shop", "whoosh-short.mp3", CTA0, 0.3),
       ("sx-cta", "sparkle.mp3", W("l2", 56.92), 0.3)]


def adur(fn):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          os.path.join(P, "assets/sfx", fn)]).decode().strip())


lanes, sfx = [], []
for sid, fn, t0, vol in sorted(SFX, key=lambda x: x[2]):
    t0 = max(0, fr(t0)); d = fr(min(adur(fn), TOTAL - t0))
    lane = next((i for i, e in enumerate(lanes) if e <= t0), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = t0 + d
    sfx.append(f'      <audio id="{sid}" class="clip" src="assets/sfx/{fn}" data-start="{t0}" data-duration="{d}" data-track-index="{20 + lane}" data-volume="{vol}"></audio>')

hosts = [("hook", 2), ("speaker", 3), ("sound", 4), ("uses", 5), ("tint", 6), ("outro", 7), ("captions", 8)]
host_html = "\n".join(
    f'      <div id="{n}" data-composition-id="{n}" data-composition-src="compositions/{n}.html" data-start="0" data-duration="{TOTAL}" '
    f'data-track-index="{tr}" data-track-kind="{"captions" if n == "captions" else "graphics"}" data-width="1080" data-height="1920" style="z-index:{5 + tr}"></div>'
    for n, tr in hosts)

open(os.path.join(P, "index.html"), "w").write(f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{{TOK}      --ground: #000;
      }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--ground); }}
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 35%; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: kept takes from raw.mp4 (talking) and raw2.mp4 (listening test). Trim in Studio by dragging clip edges. -->
      <div id="cam">
{chr(10).join(videos)}
      </div>
{host_html}
{chr(10).join(sfx)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cam)}
      tl.to({{}}, {{ duration: {TOTAL} }}, 0);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""")
json.dump(dict(total=TOTAL, segs=segs, words=[w["text"] for w in kept]), open(os.path.join(P, ".edl.json"), "w"), indent=1, ensure_ascii=False)
print(f"total={TOTAL}s segments={len(segs)} caption words={len(cap_items)}")
for s in segs:
    print(f'{s["id"]} {s["src"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}')
print(" ".join(w["text"] for w in kept))
