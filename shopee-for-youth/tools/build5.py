#!/usr/bin/env python3
"""Shopee for Youth — talking head promo in the "neon UI + flash cut" style of the reference edit.
Usage: python3 -I build5.py <words.json> <project_dir>
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
    ("h1", "v", 3.06, 11.20, 1.00),   # Aduh, zaman aku dulu takda pun macam ni. Untung Gen Z, umur 18 hingga 24 memang untung lah
    ("h2", "v", 12.40, 12.72, 1.10),  # sekarang ni
    ("h3", "v", 13.94, 15.50, 1.10),  # Shopee tengah buat Shopee for Youth
    ("r1", "v", 15.80, 22.04, 1.00),  # nak daftar dah lah mudah, guna IC, kalau tak nak guna IC boleh guna student email
    ("r2", "v", 22.46, 23.88, 1.08),  # bila dah daftar
    ("p1", "v", 65.76, 67.78, 1.00),  # abang dapat join ShopeeVIP free
    ("p2", "v", 73.00, 77.80, 1.08),  # abang percuma 6 bulan, bulan berikutnya hanya bayar RM1 je
    ("p3", "v", 78.12, 79.34, 1.16),  # oh la mak, untung gila
    ("v1", "v", 31.66, 35.90, 1.00),  # banyak kelebihan dia, ada 30% off voucher, free shipping
    ("v2", "v", 39.44, 40.78, 1.08),  # macam-macam lagi
    ("z1", "v", 44.94, 51.18, 1.00),  # selain tu, yang mana kaki ZUS Coffee, nak pergi dating ke apa kan, boleh dapat free juga ZUS Coffee
    ("z2", "v", 58.10, 61.22, 1.08),  # tapi abang join Shopee for Youth, free je ZUS Coffee ni. Free tau
    ("c1", "v", 83.32, 84.76, 1.00),  # inilah peluang abang join benda ni
    ("c2", "v", 85.16, 88.26, 1.06),  # nak tahu macam mana, tekan link untuk tahu lebih lanjut
    ("c3", "v", 88.60, 92.52, 1.00),  # abang rasa bermanfaat share video ni, biar ramai lagi tau. Jangan makan seorang gang
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
    if sid == "c3":
        b = 93.40  # hold the CTA a beat longer
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
FIX = {"jenzy": "Gen Z", "use": "Youth", "you": "Youth", "you.": "Youth", "ampun": "abang", "zeus": "ZUS", "sukofi": "ZUS Coffee",
       "hola": "la", "buntung": "untung", "shopee": "Shopee", "vip": "VIP", "ic": "IC"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w%-]", "", t).lower()
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
    if (w["text"].startswith("-") or w["text"].startswith("%")) and glued and glued[-1]["seg"] == w["seg"]:
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
    word = re.sub(r"[.,!?]", "", w["text"]).upper()
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
Y = 890  # overlay band: on the chest, below his face (the head sits high in this frame)

build_scene("hook", [
    widget("hk-q", '<div class="hd"><span>Umur 18–24?</span></div><div class="big" style="font-size:88px">Korang untung!</div>',
           0.0, W("h1", 8.98) - 0.25, top=Y - 30),
    neon_arc("hk-arc0", 0.0, W("h1", 8.98) - 0.25, 540, 700),
    neon_arc("hk-arc", W("h1", 8.98) - 0.2, end("h1") - W("h1", 8.98) + 0.2, 540, 700),
    pill("hk-age", "Exclusively age 18–24", W("h1", 8.98), end("h1") - W("h1", 8.98), None, Y + 20, icon=STAR),
    banner("hk-logo", "assets/img/sfy-logo.jpg", SEG["h3"]["start"] + 0.05, end("h3") - SEG["h3"]["start"] + 0.2, top=Y - 10, width=640),
])

build_scene("register", [
    widget("rg-how", f'<div class="hd"><span>Cara daftar</span></div>'
           f'<div class="rowx" id="rg-r1"><span style="display:flex;gap:12px;align-items:center">{ID.replace("<svg", "<svg width=40 height=40")}Guna IC</span><span class="v">✓</span></div>'
           f'<div class="rowx" id="rg-r2"><span style="display:flex;gap:12px;align-items:center">{MAIL.replace("<svg", "<svg width=40 height=40")}Student email</span><span class="v">✓</span></div>',
           W("r1", 18.48) - 0.2, end("r1") - W("r1", 18.48) + 0.2, top=Y - 20),
])

vip_at = SEG["p1"]["start"] + 0.05
build_scene("vip", [
    widget("vp-card", '<div class="hd"><span style="color:#fff;font-weight:800">Shopee<span style="color:#ee4d2d">VIP</span></span></div>'
           '<div class="big" style="font-size:84px">PERCUMA</div>'
           '<div style="text-align:center;font-size:30px;font-weight:700">untuk 6 bulan pertama</div>',
           vip_at, W("p2", 75.08) - vip_at, top=Y - 30),
    widget("vp-rm1", '<div class="hd"><span>Bulan seterusnya</span></div><div class="big" style="font-size:96px">RM1 <span style="font-size:44px;color:#fff">/ bulan</span></div>',
           W("p2", 75.08), end("p2") - W("p2", 75.08), top=Y - 30),
    neon_arc("vp-arc", SEG["p3"]["start"], end("p3") - SEG["p3"]["start"], 540, 640, r=360, a0=195, a1=345),
    pill("vp-untung", "Untung gila!", SEG["p3"]["start"] + 0.1, end("p3") - SEG["p3"]["start"] - 0.1, None, Y + 30, icon=STAR),
    fcard("vp-v30", "30%", "Off voucher", W("v1", 33.48), end("v2") - W("v1", 33.48), 190, Y - 40, rot=-4),
    fcard("vp-ship", "FREE", "Shipping", W("v1", 35.68), end("v2") - W("v1", 35.68), 540, Y - 40, rot=4),
    pill("vp-more", "&amp; macam-macam lagi", SEG["v2"]["start"] + 0.05, end("v2") - SEG["v2"]["start"] - 0.05, None, Y + 230),
])

build_scene("zus", [
    widget("zs-card", f'<div class="hd">{CUP}<span>Kaki ZUS Coffee?</span></div><div class="big" style="font-size:96px">FREE</div>'
           '<div style="text-align:center;font-size:30px;font-weight:700">ZUS Coffee</div>',
           W("z1", 46.34) - 0.1, end("z1") - W("z1", 46.34) + 0.1, top=Y - 30),
    pill("zs-free", "Free je, tau!", W("z2", 59.90), end("z2") - W("z2", 59.90), None, Y + 20),
])

build_scene("cta", [
    banner("ct-banner", "assets/img/sfy-banner.jpg", SEG["c1"]["start"] + 0.05, end("c2") - SEG["c1"]["start"], top=Y - 20, width=940),
    pill("ct-share", "Share dengan kawan", SEG["c3"]["start"] + 0.1, TOTAL - SEG["c3"]["start"] - 0.1, None, Y + 20, icon=SHARE),
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
# slow premium push-in across the hook
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {end("h1")}, ease: "none", immediateRender: false }}, 0);')

# warm flash cuts, like the reference (light leak right on the cut)
FLASH = [("flash1", SEG["h3"]["start"]), ("flash2", SEG["p1"]["start"]), ("flash3", SEG["z1"]["start"])]

SFX = [("sx-hook", "pop.mp3", 0.05, 0.35),
       ("sx-age", "pop.mp3", W("h1", 8.98) + 0.03, 0.35),
       ("sx-f1", "whoosh.mp3", SEG["h3"]["start"] - 0.25, 0.35),
       ("sx-ic", "click-soft.mp3", W("r1", 18.48) - 0.2, 0.45),
       ("sx-f2", "whoosh.mp3", SEG["p1"]["start"] - 0.25, 0.35),
       ("sx-rm1", "pop.mp3", W("p2", 75.08) + 0.03, 0.35),
       ("sx-untung", "sparkle.mp3", SEG["p3"]["start"] + 0.1, 0.3),
       ("sx-v30", "pop.mp3", W("v1", 33.48) + 0.03, 0.35),
       ("sx-ship", "pop.mp3", W("v1", 35.68) + 0.03, 0.35),
       ("sx-f3", "whoosh.mp3", SEG["z1"]["start"] - 0.25, 0.35),
       ("sx-free", "pop.mp3", W("z1", 46.34) - 0.07, 0.4),
       ("sx-cta", "whoosh-short.mp3", SEG["c1"]["start"], 0.3),
       ("sx-share", "sparkle.mp3", SEG["c3"]["start"] + 0.1, 0.3)]
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

hosts = [("hook", 2), ("register", 3), ("vip", 4), ("zus", 5), ("cta", 6), ("captions", 7)]
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
      <!-- Footage: one clip per kept take, from three source videos. Trim in Studio by dragging clip edges. -->
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
