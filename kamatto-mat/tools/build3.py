#!/usr/bin/env python3
"""Kamatto Classic II car mat — minimal premium style (one-word captions, iOS-style widgets).
Usage: python3 -I build3.py <words_dir> <project_dir>
words_dir holds v1_*.words.json, v2_*.words.json, v3_*.words.json
"""
import json, sys, html, os, re, glob, math, subprocess

WD, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = {k: json.load(open(glob.glob(os.path.join(WD, f"{k}_*.words.json"))[0])) for k in ("v1", "v2", "v3")}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))


# (id, src, first_word_start, last_word_start, cam_scale)
EDL = [
    ("h1", "v2", 0.84, 3.48, 1.00),   # Dalam kereta kalau anak-anak tertumpah air macam risau ni
    ("h2", "v2", 4.24, 4.68, 1.10),   # Nampak tengok
    ("h3", "v2", 7.34, 8.64, 1.00),   # Dia kalis air tau gang
    ("h4", "v2", 12.16, 13.10, 1.08), # dah kering dah
    ("p1", "v3", 6.20, 7.68, 1.00),   # Kamatto ni nampak premium elok
    ("p2", "v3", 8.10, 9.24, 1.00),   # tengok bentuk honeycomb ni
    ("c1", "v3", 11.56, 13.70, 1.08), # dia tertutup habis
    ("c2", "v3", 17.46, 21.44, 1.00), # full habis dia tutup, so pasti dia takkan jatuh ke bawah
    ("d1", "v3", 27.86, 29.48, 1.10), # tengok pasir-pasir terkumpul ni
    ("d2", "v3", 35.64, 40.66, 1.00), # bentuk dia honeycomb, kalau susu tumpah atau pasir... terkumpul kat sini
    ("f1", "v2", 18.56, 23.46, 1.00), # dia kalau air tertumpah ke apa pun, dia tak meninggalkan bau, memang terbaik lah
    ("s1", "v1", 0.92, 1.44, 1.00),   # tengok anti-slip
    ("s2", "v1", 2.68, 4.68, 1.08),   # dia ada strap macam ni kan, kiri dan kanan
    ("k1", "v3", 56.16, 57.46, 1.00), # kita boleh klik dia kat sini tau
    ("k2", "v3", 67.50, 70.86, 1.10), # dia tak akan bergerak, naik atas pedal ni kan, dia tak bergerak
    ("m1", "v1", 10.96, 12.94, 1.00), # masuk kereta, ngam-ngam cun-cun
    ("q1", "v3", 71.22, 75.52, 1.06), # memang elok, kualiti elok, spend duit sikit, nampak premium
    ("q2", "v3", 77.18, 78.10, 1.00), # ada macam-macam warna
    ("z1", "v3", 78.36, 80.30, 1.08), # nak tengok warna dia, tekan link di bawah
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
    if sid == "z1":
        b = 80.42  # hold to the end of the take so the CTA reads for 2 s+
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
FIX = {"ayak": "air", "kamato": "Kamatto", "leh": "kalis", "kan": "kan", "sia": "dia", "-slip": "-slip"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w-]", "", t).lower()
    if sid == "h3" and core == "kan":
        return None  # "dia kan leh air" -> "dia kalis air"
    if core in FIX:
        return FIX[core]
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
glued = []
for w in kept:
    if w["text"].startswith("-") and glued and glued[-1]["seg"] == w["seg"]:
        glued[-1]["text"] += w["text"]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
CTA_AT = W("z1", 79.32)
kept = [w for w in kept if w["start"] < CTA_AT - 0.05]

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
"""
BASE = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .widget {{ position: absolute; left: 50%; width: 640px; margin-left: -320px; padding: 26px 32px; border-radius: 34px;
      background: var(--glass); border: 1.5px solid var(--stroke); box-shadow: 0 24px 60px rgba(0,0,0,.45);
      backdrop-filter: blur(20px); color: var(--ink); font-family: var(--font-ui); }}
    .widget .hd {{ display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 28px; font-weight: 600; color: var(--muted); }}
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


# hook: question widget, KALIS AIR title, dry pill
build_scene("hook", [
    widget("hk-q", f'<div class="hd">{DROP}<span>Dalam kereta</span></div><div class="big" style="font-size:78px">Tumpah air?</div>',
           0.0, end("h2") - 0.0, top=280),
    wave_title("hk-t", "Kalis Air", W("h3", 8.20) - 0.15, end("h3") - W("h3", 8.20) + 0.15),
    pill("hk-dry", "Cepat kering", W("h4", 12.60), end("h4") - W("h4", 12.60) + 0.4, None, 330),
])

# product: tilted card, honeycomb callout
prod_card = ('<img src="assets/img/mat.jpg" alt="" style="width:150px;height:205px;object-fit:cover;border-radius:18px;display:block"/>'
             '<div><div style="font-family:var(--font-ui);font-weight:900;font-size:56px;letter-spacing:.04em">KAMATTO</div>'
             '<div style="font-size:28px;font-weight:600;letter-spacing:.3em;color:var(--muted)">CLASSIC II</div>'
             '<div style="margin-top:14px;display:inline-flex;align-items:center;gap:8px;font-size:30px;font-weight:700">'
             f'{STAR}<span data-var-text="cardTag">Nampak premium</span></div></div>')
p_start = SEG["p1"]["start"] + 0.15
card_body = clip("pc-card", p_start, end("p1") - p_start + 0.2, prod_card, cls="widget",
                 style="top:290px; display:flex; align-items:center; gap:28px; width:640px; margin-left:-320px")
card_js = "\n".join([
    f'    tl.fromTo("#pc-card", {{ opacity: 0, rotation: -14, scale: 0.7, y: -40 }}, {{ opacity: 1, rotation: -5, scale: 1, y: 0, duration: 0.6, ease: "back.out(1.4)" }}, {fr(p_start)});',
    fade_out("#pc-card", end("p1") + 0.2)])
build_scene("product", [
    (card_body, card_js),
    line_callout("pc-hc", "Honeycomb", W("p2", 8.78) - 0.1, end("p2") - W("p2", 8.78) + 0.25, dot=(300, 1060), lbl=(120, 760)),
    pill("pc-full", "Tertutup penuh", W("c1", 12.14), W("c2", 19.64) - W("c1", 12.14) - 0.25, None, 330),
    pill("pc-fall", "Takkan jatuh ke bawah", W("c2", 19.64), end("c2") - W("c2", 19.64), None, 330),
])

# dirt + smell
build_scene("benefits", [
    wave_title("bf-t", "Honeycomb", W("d2", 35.64) - 0.1, W("d2", 37.30) - W("d2", 35.64) + 0.1, top=290),
    widget("bf-trap", '<div class="hd"><span>Terkumpul dalam honeycomb</span></div>'
           '<div class="rowx"><span>Pasir</span><span class="v">✓</span></div>'
           '<div class="rowx"><span>Susu tumpah</span><span class="v">✓</span></div>',
           W("d2", 37.30), end("d2") - W("d2", 37.30), top=280),
    widget("bf-smell", f'<div class="hd">{DROP}<span>Air tertumpah?</span></div>'
           '<div class="rowx"><span>Meresap</span><span class="v" style="color:#ff6b6b">TIDAK</span></div>'
           '<div class="rowx"><span>Tinggal bau</span><span class="v" style="color:#ff6b6b">TIDAK</span></div>',
           W("f1", 18.56), end("f1") - W("f1", 18.56), top=280),
])

# grip + clips + fit
build_scene("grip", [
    line_callout("gr-as", "Anti-slip", SEG["s1"]["start"] + 0.05, end("s1") - SEG["s1"]["start"] + 0.5, dot=(600, 1060), lbl=(150, 800)),
    pill("gr-strap", "Strap kiri &amp; kanan", W("s2", 3.14), end("s2") - W("s2", 3.14), None, 800),
    rings("gr-klik", "Klik &amp; kunci", W("k1", 56.80), end("k1") - W("k1", 56.80) + 0.1, 530, 1170),
    pill("gr-move", "Tak bergerak", W("k2", 69.02), end("k2") - W("k2", 69.02), None, 330),
    wave_title("gr-fit", "Ngam-ngam", W("m1", 11.94) - 0.1, end("m1") - W("m1", 11.94) + 0.1, top=290),
])

# quality pills + colours + CTA
q_k, q_d = W("q1", 72.32), W("q1", 74.66)
CARD_AT = fr(SEG["z1"]["start"] + 0.05)
cta_body = clip("cta-card", CARD_AT, TOTAL - CARD_AT,
                '<div style="display:flex;align-items:center;gap:22px">'
                '<img src="assets/img/mat.jpg" alt="" style="width:110px;height:150px;object-fit:cover;border-radius:16px"/>'
                '<div style="flex:1"><div style="font-weight:900;font-size:42px;letter-spacing:.04em">KAMATTO</div>'
                '<div style="font-size:28px;color:var(--muted);font-weight:600">Classic II · Pelbagai warna</div></div>'
                '<div id="cta-btn" style="padding:14px 26px;border-radius:999px;background:#fe2c55;color:#fff;font-weight:800;font-size:30px">Tekan link</div></div>',
                cls="widget", style="top:290px; width:840px; margin-left:-420px")
cta_js = "\n".join([fade_in("#cta-card", CARD_AT, y=-20),
                    f'    tl.fromTo("#cta-btn", {{ scale: 1 }}, {{ scale: 1.08, duration: 0.25, ease: "power2.out", yoyo: true, repeat: 1 }}, {fr(CARD_AT + 0.6)});'])
def banner(cid, src, start, dur, top=280):
    inner = f'<img src="{src}" alt="" style="display:block;width:100%;border-radius:24px"/>'
    body = clip(cid, start, dur, inner, cls="widget",
                style=f"top:{top}px; width:940px; margin-left:-470px; padding:10px; border-radius:34px")
    js = "\n".join([
        f'    tl.fromTo("#{cid}", {{ opacity: 0, y: -40, scale: 0.92, filter: "blur(12px)" }}, {{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.6, ease: "expo.out" }}, {fr(start)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


q1s = SEG["q1"]["start"] + 0.1
q2w = W("q2", 77.18)
build_scene("outro", [
    banner("oq-trust", "assets/img/banner-trusted.jpg", q1s, end("q1") - q1s),
    pill("oq-k", "Kualiti", q_k, end("q1") - q_k, 290, 670, icon=STAR),
    pill("oq-d", "Design", q_d, end("q1") - q_d, 570, 670, icon=GEM),
    banner("oq-colour", "assets/img/banner-colours.jpg", q2w - 0.1, CARD_AT - q2w + 0.1),
    (cta_body, cta_js),
])

# captions
write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 800; font-size: 58px; color: #fff;
      letter-spacing: .01em; text-shadow: 0 3px 0 rgba(0,0,0,.35), 0 6px 22px rgba(0,0,0,.6); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/{s["src"]}.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
# slow premium push-in across the hook
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.05, duration: {end("h1")}, ease: "none", immediateRender: false }}, 0);')

SFX = [("sx-q", "pop.mp3", 0.05, 0.35),
       ("sx-t1", "whoosh.mp3", W("h3", 8.20) - 0.3, 0.3),
       ("sx-dry", "pop.mp3", W("h4", 12.60) + 0.03, 0.35),
       ("sx-card", "whoosh-short.mp3", SEG["p1"]["start"] + 0.05, 0.3),
       ("sx-hc", "click-soft.mp3", W("p2", 8.78), 0.5),
       ("sx-full", "pop.mp3", W("c1", 12.14) + 0.03, 0.3),
       ("sx-t2", "whoosh.mp3", W("d2", 35.64) - 0.3, 0.3),
       ("sx-smell", "whoosh-short.mp3", W("f1", 18.56) - 0.05, 0.3),
       ("sx-as", "click-soft.mp3", SEG["s1"]["start"] + 0.05, 0.5),
       ("sx-klik", "click.mp3", W("k1", 56.80), 0.45),
       ("sx-fit", "whoosh.mp3", W("m1", 11.94) - 0.35, 0.3),
       ("sx-k", "pop.mp3", q_k + 0.03, 0.3),
       ("sx-d", "pop.mp3", q_d + 0.03, 0.3),
       ("sx-cta", "sparkle.mp3", CTA_AT, 0.3)]


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

hosts = [("hook", 2), ("product", 3), ("benefits", 4), ("grip", 5), ("outro", 6), ("captions", 7)]
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
print(f"total={TOTAL}s segments={len(segs)} caption words={len(cap_items)}")
for s in segs:
    print(f'{s["id"]} {s["src"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}')
