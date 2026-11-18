#!/usr/bin/env python3
"""Shopee for Youth #2 — how to join, calm "santai tapi wow" pacing with a phone mockup of the real app screens.
Usage: python3 -I build6.py <words.json> <project_dir>
"""
import json, sys, html, os, re, glob, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = {"v": json.load(open(WJ))}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))

# (id, src, first_word_start, last_word_start, cam_scale)
EDL = [
    ("h1", "v", 2.54, 8.00, 1.00),    # kalau abang umur 18 hingga 24, abang tengok video aku sampai habis, pasal apa ni aku nak bagitahu abang
    ("h2", "v", 8.94, 12.72, 1.06),   # abang pernah dengar ShopeeVIP? banyak kan kelebihan dia kan
    ("p1", "v", 14.74, 21.20, 1.00),  # untuk umur 18 hingga 24 abang dapat peluang selama 6 bulan free
    ("p3", "v", 26.70, 35.90, 1.00),  # kalau sebelum ni orang lain kena bayar RM6.99, tapi untuk 6 bulan free dan hanya perlu bayar RM1 lepas 6 bulan
    ("p4", "v", 36.20, 36.74, 1.10),  # memang berbaloi
    ("c1", "v", 37.16, 39.52, 1.30),  # cara dia mudah, join je Shopee for Youth
    ("c2a", "v", 40.32, 40.92, 1.30), # cara nak
    ("c2b", "v", 42.76, 44.20, 1.30), # daftar dia, menggunakan IC
    ("c3a", "v", 44.74, 44.74, 1.30), # ataupun
    ("c3b", "v", 46.16, 47.78, 1.30), # cara kedua dia, boleh daftar
    ("c3c", "v", 48.84, 49.78, 1.30), # menggunakan student email
    ("c4", "v", 51.76, 53.86, 1.30),  # dah settle daftar tu, join je
    ("c5", "v", 54.46, 62.52, 1.30),  # boleh register untuk ShopeeVIP percuma selama 6 bulan untuk segala benefit dia
    ("z1", "v", 68.50, 72.04, 1.06),  # kalau abang rasa bermanfaat video ni, abang share banyak-banyak biar semua tau
    ("z2", "v", 72.68, 74.64, 1.00),  # special untuk umur 18 hingga 24
]


segs, f = [], 0
for sid, src, a, b, sc in EDL:
    W_ = WORDS[src]
    w0, w1 = wat(src, a), wat(src, b)
    i0, i1 = W_.index(w0), W_.index(w1)
    prev_end = W_[i0 - 1]["end"] if i0 > 0 else 0
    next_start = W_[i1 + 1]["start"] if i1 + 1 < len(W_) else 1e9
    a = min(w0["start"] - 0.02, max(w0["start"] - 0.07, prev_end + 0.02))
    b = max(w1["start"] + 0.15, min(min(w1["end"], w1["start"] + 1.2) + 0.1, next_start - 0.03))
    if sid == "z2":
        b = 76.40  # hold the end card
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
    """output time of source time t inside segment sid"""
    s = SEG[sid]
    return fr(s["start"] + (t - s["src_in"]))


def end(sid):
    s = SEG[sid]
    return fr(s["start"] + s["dur"])


def W(sid, t):
    return at(sid, wat(SEG[sid]["src"], t)["start"])




# ---------------------------------------------------------------- one-word captions
FIX = {"ampoh": "hampa", "ampuh": "hampa", "ampun": "hampa", "abang": "hampa", "yau": "tau", "shopee4u": "Shopee for Youth", "shopee": "Shopee",
       "vip": "VIP", "ic": "IC"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w%-]", "", t).lower()
    if sid == "c5" and core == "ip":
        return None  # "VIP IP" stutter
    if core in FIX:
        return FIX[core] + t[len(t.rstrip(".,!?")):]
    return t


kept = []
for s in segs:
    for w in WORDS[s["src"]]:
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05:
            txt = norm(s["id"], w)
            if not txt or re.sub(r"[^\w]", "", txt).lower() in {"haha", "haa", "ah", "tuh"}:
                continue
            st = at(s["id"], w["start"])
            en = at(s["id"], min(w["end"], s["src_out"]))
            kept.append(dict(text=txt, start=st, end=max(en, st + 0.12), seg=s["id"]))
# glue hyphen halves ("anak" "-anak", "anti" "-slip")
# glue hyphen halves and "%" tokens ("30" "%" -> "30%")
glued = []
for w in kept:
    if (w["text"][:1] in "-%." and w["text"][1:2].isdigit() or w["text"].startswith("-") or w["text"].startswith("%")) and glued and glued[-1]["seg"] == w["seg"]:
        glued[-1]["text"] += w["text"]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
CTA_AT = TOTAL
cap_items, cap_js = [], []
for i, w in enumerate(kept):
    nxt = kept[i + 1]["start"] if i + 1 < len(kept) else TOTAL
    st = fr(w["start"])
    en = fr(min(max(w["end"] + 0.05, st + 0.25), nxt, CTA_AT))
    if en - st < 0.1:
        continue
    word = re.sub(r"^[.,!?]+|[.,!?]+$", "", w["text"]).upper()  # keep the dot inside RM6.99
    cid = f"cw{i:03d}"
    cap_items.append(f'    <div id="{cid}" class="cw clip" data-start="{st}" data-duration="{fr(en - st)}" data-track-index="0">'
                     f'<span id="{cid}s">{html.escape(word)}</span></div>')
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, y: 6 }}, {{ opacity: 1, y: 0, duration: 0.08, ease: "power2.out" }}, {st});')

# ---------------------------------------------------------------- design tokens
TOK = """
      --ink: #ffffff;
      --muted: rgba(255,255,255,.62);
      --glass: rgba(18, 19, 22, 0.82);
      --stroke: rgba(255,255,255,.12);
      --gold: #f5c542;
      --rose: #c86b9a;
      --ok: #34c759;
      --font-ui: "Montserrat", sans-serif;
      --font-num: "Oswald", "League Gothic", sans-serif;
      --orange: #ee4d2d;
      --teal: #2de2c8;
"""
BASE = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .widget {{ position: absolute; left: 50%; width: 600px; margin-left: -330px; padding: 26px 32px; border-radius: 34px;
      background: var(--glass); border: 1.5px solid var(--stroke); box-shadow: 0 24px 60px rgba(0,0,0,.45);
      backdrop-filter: blur(20px); color: var(--ink); font-family: var(--font-ui); }}
    .widget .hd {{ display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 28px; font-weight: 600; color: var(--muted); text-align: center; }}
    .widget .hd svg {{ width: 30px; height: 30px; flex: none; }}
    .widget .rowx {{ display: flex; align-items: center; justify-content: space-between; margin-top: 18px; font-size: 32px; font-weight: 700; }}
    .widget .rowx .v {{ font-family: var(--font-num); font-size: 40px; font-weight: 700; color: var(--ok); letter-spacing: .02em; }}
    .widget .big {{ margin-top: 6px; text-align: center; font-family: var(--font-num); font-size: 92px; font-weight: 700; color: var(--gold); line-height: 1.05; letter-spacing: .01em; }}
    .pill {{ display: inline-flex; align-items: center; gap: 10px; padding: 12px 24px; border-radius: 999px;
      background: #fff; color: #111; font-family: var(--font-ui); font-weight: 800; font-size: 32px; box-shadow: 0 12px 30px rgba(0,0,0,.35); white-space: nowrap; }}
    .pill svg {{ width: 28px; height: 28px; }}
    .ttl {{ position: absolute; left: 0; width: 960px; text-align: center; font-family: var(--font-ui); font-weight: 800; color: #fff;
      font-size: 68px; letter-spacing: .22em; text-transform: uppercase; text-shadow: 0 2px 4px rgba(0,0,0,.6), 0 8px 30px rgba(0,0,0,.7); }}
    .ttl svg {{ display: block; margin: 8px auto 0; width: 700px; height: 70px; overflow: visible; }}
    .co-lbl {{ position: absolute; font-family: var(--font-ui); font-weight: 800; font-size: 44px; color: #fff; letter-spacing: .02em;
      text-transform: uppercase; text-shadow: 0 4px 18px rgba(0,0,0,.6); white-space: nowrap; padding-bottom: 8px; border-bottom: 3px solid #fff; }}
    .co svg {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }}
    .neon svg {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: visible; }}
    .neon path, .neon circle {{ filter: drop-shadow(0 0 10px rgba(45,226,200,.9)) drop-shadow(0 0 24px rgba(45,226,200,.55)); }}
    .fcard {{ position: absolute; width: 290px; padding: 22px 22px 20px; border-radius: 28px; background: var(--glass);
      border: 1.5px solid rgba(45,226,200,.45); box-shadow: 0 0 30px rgba(45,226,200,.25), 0 20px 50px rgba(0,0,0,.5);
      color: #fff; font-family: var(--font-ui); text-align: center; }}
    .fcard .n {{ font-family: var(--font-num); font-size: 70px; font-weight: 700; line-height: 1; color: var(--gold); }}
    .fcard .l {{ margin-top: 8px; font-size: 28px; font-weight: 700; }}
"""
CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 12.5l4.8 4.8L19.5 7"/></svg>'
STAR = '<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>'
GEM = '<svg viewBox="0 0 24 24" fill="#5ac8fa"><path d="M6 3h12l4 6-10 12L2 9z"/></svg>'
DROP = '<svg viewBox="0 0 24 24" fill="#5ac8fa"><path d="M12 2.5s7 7.6 7 12.6a7 7 0 0 1-14 0c0-5 7-12.6 7-12.6z"/></svg>'


def clip(cid, start, dur, inner, cls="", style="", lane=0, extra=""):
    return (f'    <div id="{cid}" class="{cls} clip" data-start="{fr(start)}" data-duration="{fr(dur)}" '
            f'data-track-index="{lane}" style="{style}"{extra}>{inner}</div>')


def fade_in(sel, t, y=24, blur=10, d=0.42):
    return f'    tl.fromTo("{sel}", {{ opacity: 0, y: {y}, filter: "blur({blur}px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: {d}, ease: "expo.out" }}, {fr(t)});'


def fade_out(sel, t):
    return f'    tl.to("{sel}", {{ opacity: 0, filter: "blur(8px)", duration: 0.2, ease: "power2.in" }}, {fr(t - 0.22)});'


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


def wave_title(cid, text, start, dur, top=290):
    paths = ('<path class="wv" d="M0 35 C 90 5, 170 65, 260 35 S 430 5, 520 35 S 650 65, 700 35" stroke="#f5c542" stroke-width="3" fill="none"/>'
             '<path class="wv" d="M0 40 C 110 70, 200 10, 300 40 S 480 70, 560 40 S 660 15, 700 40" stroke="rgba(255,255,255,.75)" stroke-width="2" fill="none"/>'
             '<path class="wv" d="M0 32 C 70 50, 150 15, 240 32 S 400 55, 500 30 S 640 20, 700 32" stroke="#c86b9a" stroke-width="2" fill="none"/>')
    inner = f'<div id="{cid}t">{text}</div><svg id="{cid}w" viewBox="0 0 700 70">{paths}</svg>'
    body = clip(cid, start, dur, inner, cls="ttl", style=f"top:{top}px")
    js = "\n".join([
        f'    tl.fromTo("#{cid}t", {{ opacity: 0, scaleX: 1.25, filter: "blur(10px)" }}, {{ opacity: 1, scaleX: 1, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}w .wv", {{ strokeDasharray: 900, strokeDashoffset: 900 }}, {{ strokeDashoffset: 0, duration: 0.9, ease: "power2.inOut", stagger: 0.08 }}, {fr(start + 0.1)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


def pill(cid, text, start, dur, x, y, icon=CHECK):
    """x=None centres the pill horizontally"""
    left, width = (0, 1080) if x is None else (x, 360)
    inner = f'<span id="{cid}i" class="pill" style="position:relative">{icon}<span>{text}</span></span>'
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{left}px; width:{width}px; top:{y}px; text-align:{'center' if x is None else 'left'}")
    js = "\n".join([f'    tl.fromTo("#{cid}i", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)" }}, {fr(start)});',
                    fade_out(f"#{cid}", start + dur)])
    return body, js


def line_callout(cid, label, start, dur, dot, lbl):
    """dot -> elbow -> label (label sits above the elbow, underlined)."""
    (dx, dy), (lx, ly) = dot, lbl
    svg = (f'<svg viewBox="0 0 1080 1920"><circle id="{cid}d" cx="{dx}" cy="{dy}" r="11" fill="#fff"/>'
           f'<path id="{cid}p" d="M{dx} {dy} L{dx} {ly} L{lx} {ly}" stroke="#fff" stroke-width="3.5" fill="none"/></svg>')
    lab = f'<div id="{cid}l" class="co-lbl" style="left:{min(lx, dx) }px; top:{ly - 66}px">{label}</div>'
    body = clip(cid, start, dur, svg + lab, cls="co", style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid}d", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}p", {{ strokeDasharray: 1400, strokeDashoffset: 1400 }}, {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }}, {fr(start + 0.1)});',
        fade_in(f"#{cid}l", start + 0.45, y=10, blur=6, d=0.3),
        fade_out(f"#{cid}", start + dur)])
    return body, js


def rings(cid, label, start, dur, cx, cy):
    rs = "".join(f'<circle class="rg" cx="{cx}" cy="{cy}" r="{r}" stroke="rgba(255,255,255,.8)" stroke-width="2.5" fill="none"/>' for r in (70, 130, 190))
    svg = f'<svg viewBox="0 0 1080 1920">{rs}</svg>'
    lab = f'<div id="{cid}l" class="pill" style="position:absolute; left:{cx - 140}px; top:{cy - 300}px">{label}</div>'
    body = clip(cid, start, dur, svg + lab, cls="co", style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid} .rg", {{ opacity: 0, scale: 0.4, transformOrigin: "{cx}px {cy}px" }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: "expo.out", stagger: 0.1 }}, {fr(start)});',
        f'    tl.fromTo("#{cid}l", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.6)" }}, {fr(start + 0.15)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


def widget(cid, inner, start, dur, top=280):
    body = clip(cid, start, dur, inner, cls="widget", style=f"top:{top}px")
    js = "\n".join([fade_in(f"#{cid}", start, y=-20), fade_out(f"#{cid}", start + dur)])
    return body, js


# ---------------------------------------------------------------- scenes
def build_scene(name, parts, css_extra=""):
    body = "\n".join(p[0] for p in parts)
    js = "\n".join(p[1] for p in parts)
    write(f"{name}.html", scene(name, BASE + css_extra, body, js))



def banner(cid, src, start, dur, top=235, width=600):
    inner = f'<img src="{src}" alt="" style="display:block;width:100%;border-radius:24px"/>'
    body = clip(cid, start, dur, inner, cls="widget",
                style=f"top:{top}px; width:{width}px; margin-left:-{width // 2 + 30}px; padding:10px; border-radius:34px")
    js = "\n".join([
        f'    tl.fromTo("#{cid}", {{ opacity: 0, y: -40, scale: 0.92, filter: "blur(12px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }}, {fr(start)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js



def neon_arc(cid, start, dur, cx, cy, r=330, a0=200, a1=340):
    """glowing teal arc behind the subject, drawn on like the reference's halo"""
    import math as _m
    p0 = (cx + r * _m.cos(_m.radians(a0)), cy + r * _m.sin(_m.radians(a0)))
    p1 = (cx + r * _m.cos(_m.radians(a1)), cy + r * _m.sin(_m.radians(a1)))
    d = f"M{p0[0]:.0f} {p0[1]:.0f} A{r} {r} 0 0 1 {p1[0]:.0f} {p1[1]:.0f}"
    svg = (f'<svg viewBox="0 0 1080 1920"><path id="{cid}p" d="{d}" stroke="#2de2c8" stroke-width="7" fill="none" stroke-linecap="round"/>'
           f'<path id="{cid}q" d="{d}" stroke="#ffffff" stroke-width="2" fill="none" stroke-linecap="round" opacity=".8"/></svg>')
    body = clip(cid, start, dur, svg, cls="neon", style="position:absolute; inset:0", extra=" data-layout-ignore")
    js = "\n".join([
        f'    tl.fromTo(["#{cid}p", "#{cid}q"], {{ strokeDasharray: 1600, strokeDashoffset: 1600 }}, {{ strokeDashoffset: 0, duration: 0.7, ease: "power2.inOut" }}, {fr(start)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


def fcard(cid, num, label, start, dur, x, y, rot=0):
    inner = f'<div class="n">{num}</div><div class="l">{label}</div>'
    body = clip(cid, start, dur, inner, cls="fcard", style=f"left:{x}px; top:{y}px")
    js = "\n".join([
        f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 40, scale: 0.7, rotation: {rot * 3} }}, {{ opacity: 1, y: 0, scale: 1, rotation: {rot}, duration: 0.5, ease: "back.out(1.6)" }}, {fr(start)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


ID = '<svg viewBox="0 0 24 24" fill="none" stroke="#2de2c8" stroke-width="2.2" stroke-linecap="round"><rect x="2.5" y="5" width="19" height="14" rx="2.5"/><circle cx="8.5" cy="11" r="2.2"/><path d="M5.5 16c.6-1.6 1.7-2.3 3-2.3s2.4.7 3 2.3M14 10h5M14 13.5h4"/></svg>'
MAIL = '<svg viewBox="0 0 24 24" fill="none" stroke="#2de2c8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3.5 7l8.5 6 8.5-6"/></svg>'
CUP = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5c542" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8h12l-1.4 12H7.4z"/><path d="M5 8h14M9 4h6l1 4H8z"/></svg>'
HEART = '<svg viewBox="0 0 24 24" fill="#ff4d6d"><path d="M12 20.5s-8-4.9-8-10.6A4.4 4.4 0 0 1 12 7.4a4.4 4.4 0 0 1 8 2.5c0 5.7-8 10.6-8 10.6z"/></svg>'
SHARE = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 5l6 6-6 6M20 11H10a6 6 0 0 0-6 6v1"/></svg>'
TAG = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.4"/></svg>'
TRUCK = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 6h12v10H2zM14 10h4l3 3v3h-7"/><circle cx="6" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/></svg>'
PLANE = '<svg viewBox="0 0 24 24" fill="#fff"><path d="M21 15.5v-1.8l-7.5-4.6V4a1.5 1.5 0 0 0-3 0v5.1L3 13.7v1.8l7.5-2.3v4.9l-2 1.5V21l3.5-1 3.5 1v-1.4l-2-1.5v-4.9z"/></svg>'


def benefits(cid, start, dur, rows, footer, footer_at):
    """ShopeeVIP benefits list: header, then each row pops in on the word that says it"""
    items = "".join(
        f'<div id="{cid}r{i}" style="display:flex;align-items:center;gap:16px;margin-top:14px;font-size:28px;font-weight:600">'
        f'<span style="width:48px;height:48px;border-radius:14px;background:#ee4d2d;display:flex;align-items:center;justify-content:center;flex:none">'
        f'{ic.replace("<svg", "<svg width=28 height=28")}</span><span>{txt}</span></div>'
        for i, (ic, txt, _) in enumerate(rows))
    inner = (f'<div class="hd"><span style="color:#fff;font-weight:800;font-size:30px">Shopee<span style="color:#ee4d2d">VIP</span> Benefits</span></div>'
             f'{items}<div id="{cid}f" style="margin-top:14px;text-align:center;font-size:28px;font-weight:700;color:var(--gold)">{footer}</div>')
    body = clip(cid, start, dur, inner, cls="widget", style=f"top:{Y - 70}px; width:660px; margin-left:-370px; padding:22px 26px")
    js = [fade_in(f"#{cid}", start, y=-20),
          f'    tl.set([{", ".join(f"{chr(34)}#{cid}r{i}{chr(34)}" for i in range(len(rows)))}, "#{cid}f"], {{ opacity: 0 }}, {fr(start)});']
    for i, (_, _, at_) in enumerate(rows):
        js.append(f'    tl.fromTo("#{cid}r{i}", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {fr(at_)});')
    js.append(f'    tl.fromTo("#{cid}f", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {fr(footer_at)});')
    js.append(fade_out(f"#{cid}", start + dur))
    return body, "\n".join(js)


Y = 860  # overlay band: chest, below his face
PX, PY, PW, PH = 540, 430, 400, 740  # phone mockup on the right during the how-to (he sits left after the reframe)
HOW0 = fr(SEG["c1"]["start"])        # how-to section
HOW1 = end("c5")


def phone(cid, start, dur, screens):
    """phone mockup; screens = [(id, src, t_in, t_out, top, zoom, origin, chip, tap)] — tap = (x, y, t) in screen px"""
    inner, js, chips, taps = [], [], [], []
    for i, (sid, src, t0, t1, top, zoom, origin, chip, tap) in enumerate(screens):
        inner.append(f'<img id="{sid}" class="clip" src="{src}" data-start="{fr(t0)}" data-duration="{fr(t1 - t0)}" data-track-index="1" '
                     f'style="position:absolute; left:0; top:{top}px; width:376px; border-radius:6px" alt=""/>')
        js.append(f'    tl.fromTo("#{sid}", {{ opacity: 0, scale: 0.96 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "power2.out" }}, {fr(t0)});')
        if zoom != 1:
            js.append(f'    tl.to("#{sid}", {{ scale: {zoom}, transformOrigin: "{origin}", duration: 1.2, ease: "power2.inOut" }}, {fr(t0 + 0.5)});')
        if chip:
            chips.append(clip(f"{cid}c{i}", t0, t1 - t0, f'<span id="{cid}c{i}i" class="pill" style="position:relative">{chip}</span>',
                              style=f"position:absolute; left:{PX - 60}px; width:{PW + 120}px; top:{PY - 86}px; text-align:center", lane=2))
            js.append(f'    tl.fromTo("#{cid}c{i}i", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }}, {fr(t0)});')
            js.append(fade_out(f"#{cid}c{i}", t1))
        if tap:
            tx, ty, tt = tap
            taps.append(clip(f"{cid}t{i}", tt, 1.0, f'<div id="{cid}t{i}r" style="position:absolute; left:{PX + 12 + tx - 34}px; top:{PY + 12 + ty - 34}px; width:68px; height:68px; border-radius:50%; border:4px solid #fff; box-shadow:0 0 18px rgba(255,255,255,.9)"></div>',
                             style="position:absolute; inset:0", lane=3, extra=" data-layout-ignore"))
            js.append(f'    tl.fromTo("#{cid}t{i}r", {{ opacity: 0, scale: 0.4 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {fr(tt)});')
            js.append(f'    tl.to("#{cid}t{i}r", {{ opacity: 0, scale: 1.5, duration: 0.45, ease: "power2.out" }}, {fr(tt + 0.45)});')
    body = clip(cid, start, dur,
                f'<div style="position:absolute; inset:12px; border-radius:44px; overflow:hidden; background:linear-gradient(180deg,#24326b,#16204a)">{"".join(inner)}</div>',
                style=(f"position:absolute; left:{PX}px; top:{PY}px; width:{PW}px; height:{PH}px; border-radius:56px; background:#0d0d0f; "
                       f"border:2px solid rgba(255,255,255,.18); box-shadow:0 30px 80px rgba(0,0,0,.55)"), extra=" data-layout-allow-overflow")
    js.insert(0, f'    tl.fromTo("#{cid}", {{ opacity: 0, x: 140, rotation: 5 }}, {{ opacity: 1, x: 0, rotation: 0, duration: 0.8, ease: "expo.out" }}, {fr(start)});')
    js.append(f'    tl.to("#{cid}", {{ opacity: 0, x: 140, duration: 0.4, ease: "power2.in" }}, {fr(start + dur - 0.42)});')
    return body + "\n" + "\n".join(chips + taps), "\n".join(js)


build_scene("hook", [
    widget("hk-q", '<div class="hd"><span>Umur 18–24?</span></div><div class="big" style="font-size:80px">Tengok sampai habis</div>',
           0.0, end("h1"), top=Y - 20),
    pill("hk-vip", "Kenal ShopeeVIP?", SEG["h2"]["start"] + 0.1, end("h2") - SEG["h2"]["start"] - 0.1, None, Y + 20, icon=STAR),
])

def price_card():
    """'orang lain bayar RM6.99' first; on 'RM1' the old price is struck and RM1 / bulan lands beside it"""
    t0, t1, t_end = W("p3", 28.86) - 0.15, W("p3", 34.94), end("p4")
    body, js = widget("vp-price",
        '<div style="position:relative;height:34px">'
        '<div id="vp-h1" class="hd" style="position:absolute;left:0;right:0">Orang lain bayar</div>'
        '<div id="vp-h2" class="hd" style="position:absolute;left:0;right:0;color:#fff">Hampa: lepas 6 bulan free</div></div>'
        '<div style="display:flex;align-items:baseline;justify-content:center;gap:22px;margin-top:8px;white-space:nowrap">'
        '<span id="vp-old" style="position:relative;font-family:var(--font-num);font-size:72px;font-weight:700;color:#fff">RM6.99'
        '<span id="vp-strike" style="position:absolute;left:-4px;right:-4px;top:54%;height:6px;border-radius:3px;background:#ee4d2d;transform-origin:0 50%"></span></span>'
        '<span id="vp-new" style="font-family:var(--font-num);font-size:84px;font-weight:700;color:var(--gold)">RM1'
        '<span style="font-family:var(--font-ui);font-size:28px;color:#fff"> /bulan</span></span></div>',
        t0, t_end - t0, top=Y - 30)
    js += "\n" + "\n".join([
        f'    tl.set(["#vp-new", "#vp-h2"], {{ opacity: 0 }}, {fr(t0)});',
        f'    tl.fromTo("#vp-strike", {{ scaleX: 0 }}, {{ scaleX: 0, duration: 0.01 }}, {fr(t0)});',
        f'    tl.to("#vp-strike", {{ scaleX: 1, duration: 0.3, ease: "power2.out" }}, {fr(t1 - 0.1)});',
        f'    tl.fromTo("#vp-old", {{ x: 126 }}, {{ x: 126, duration: 0.01 }}, {fr(t0)});',
        f'    tl.to("#vp-old", {{ x: 0, opacity: 0.5, duration: 0.4, ease: "power3.inOut" }}, {fr(t1 - 0.15)});',
        f'    tl.to("#vp-h1", {{ opacity: 0, duration: 0.2 }}, {fr(t1 - 0.1)});',
        f'    tl.fromTo("#vp-h2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {fr(t1)});',
        f'    tl.fromTo("#vp-new", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.7)" }}, {fr(t1)});'])
    return body, js


build_scene("vip", [
    widget("vp-free", '<div class="hd"><span style="color:#fff;font-weight:800">Shopee<span style="color:#ee4d2d">VIP</span> · umur 18–24</span></div>'
           '<div class="big" style="font-size:84px">PERCUMA</div><div style="text-align:center;font-size:30px;font-weight:700">untuk 6 bulan pertama</div>',
           W("p1", 19.46) - 0.2, end("p1") - W("p1", 19.46) + 0.2, top=Y - 30),
    price_card(),
])

T = lambda sid, t: W(sid, t)
build_scene("howto", [
    phone("ph", HOW0 + 0.1, HOW1 - HOW0 - 0.1, [
        ("ph-s1", "assets/img/app-home.jpg", HOW0 + 0.1, SEG["c2a"]["start"], 128, 1, "", "Buka Shopee for Youth", (310, 191, T("c1", 38.54))),
        ("ph-s2", "assets/img/app-ways.jpg", SEG["c2a"]["start"], SEG["c2b"]["start"] + 0.3, 180, 1, "", "2 cara untuk join", None),
        ("ph-s3", "assets/img/app-mykad.jpg", SEG["c2b"]["start"] + 0.3, SEG["c3b"]["start"], 8, 1, "", "Cara 1 · Scan MyKad", None),
        ("ph-s4", "assets/img/app-form.jpg", SEG["c3b"]["start"], end("c3c"), 9, 1, "", "Cara 2 · Email pelajar", (188, 582, T("c3c", 49.40))),
        ("ph-s5", "assets/img/app-home.jpg", SEG["c4"]["start"], SEG["c5"]["start"], 128, 1, "", "Siap! Dah jadi member ✓", None),
        ("ph-s6", "assets/img/app-home.jpg", SEG["c5"]["start"], HOW1, 128, 1.7, "25% 84%", "Claim VIP percuma", (150, 460, T("c5", 57.58))),
    ]),
])

build_scene("cta", [
    pill("ct-share", "Jom ajak kawan!", SEG["z1"]["start"] + 0.1, end("z1") - SEG["z1"]["start"] - 0.1, None, Y + 20, icon=SHARE),
    banner("ct-banner", "assets/img/sfy-banner.jpg", SEG["z2"]["start"] + 0.05, TOTAL - SEG["z2"]["start"] - 0.05, top=Y - 20, width=940),
])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: "Archivo Black", var(--font-ui); font-size: 56px; color: #fff; text-transform: uppercase;
      letter-spacing: .01em; -webkit-text-stroke: 2px rgba(0,0,0,.55); paint-order: stroke fill; text-shadow: 0 3px 0 rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.6); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/raw.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
# slow push-in across the hook
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.05, duration: {end("h1")}, ease: "none", immediateRender: false }}, 0);')
cam.append(f'      tl.fromTo("#cam", {{ x: 0 }}, {{ x: -150, duration: 0.6, ease: "power2.inOut", immediateRender: false }}, {fr(HOW0)});')
cam.append(f'      tl.to("#cam", {{ x: 0, duration: 0.35, ease: "power2.inOut" }}, {fr(HOW1 - 0.36)});')

# warm flash cuts, like the reference (light leak right on the cut)
FLASH = [("flash1", SEG["p1"]["start"])]  # one flash only: calm, not hectic

SFX = [("sx-hook", "pop.mp3", 0.05, 0.3),
       ("sx-vip", "pop.mp3", SEG["h2"]["start"] + 0.13, 0.3),
       ("sx-f1", "whoosh.mp3", SEG["p1"]["start"] - 0.25, 0.3),
       ("sx-free", "sparkle.mp3", W("p1", 19.46) - 0.2, 0.25),
       ("sx-price", "pop.mp3", W("p3", 28.86) - 0.12, 0.3),
       ("sx-baloi", "sparkle.mp3", SEG["p4"]["start"] + 0.03, 0.22),
       ("sx-rm1", "pop.mp3", W("p3", 34.94) + 0.03, 0.35),
       ("sx-phone", "whoosh-short.mp3", HOW0, 0.3),
       ("sx-tap1", "click-soft.mp3", W("c1", 38.54), 0.45),
       ("sx-tap2", "click-soft.mp3", W("c3c", 49.40), 0.45),
       ("sx-done", "sparkle.mp3", SEG["c4"]["start"] + 0.05, 0.25),
       ("sx-tap3", "click-soft.mp3", W("c5", 57.58), 0.45),
       ("sx-end", "pop.mp3", SEG["z2"]["start"] + 0.08, 0.3)]
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

hosts = [("hook", 2), ("vip", 3), ("howto", 4), ("cta", 5), ("captions", 6)]
host_html = "\n".join(
    f'      <div id="{n}" data-composition-id="{n}" data-composition-src="compositions/{n}.html" data-start="0" data-duration="{TOTAL}" '
    f'data-track-index="{tr}" data-track-kind="{"captions" if n == "captions" else "graphics"}" data-width="1080" data-height="1920" style="z-index:{5 + tr}"></div>'
    for n, tr in hosts)
host_html += "\n" + "\n".join(
    f'      <div id="{n}" data-composition-id="{n}" data-composition-src="compositions/{n}.html" data-start="{fr(t - 0.8 * 0.58)}" '
    f'data-duration="0.8" data-track-index="{10 + i}" data-track-kind="graphics" data-width="1080" data-height="1920" style="z-index:20"></div>'
    for i, (n, t) in enumerate(FLASH))

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
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: one clip per kept take. Trim in Studio by dragging clip edges. -->
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
