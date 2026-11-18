#!/usr/bin/env python3
"""Dalwa spectacles — same minimal premium style as the Kamatto edit.
Usage: python3 -I build4.py <words.json> <project_dir>
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
    ("a1", "v", 0.18, 1.88, 1.00),    # spek Dalwa ni memang best lah
    ("a2", "v", 2.14, 4.22, 1.08),    # nampak-nampak, design dia pun cantik kalau pakai pun
    ("a3", "v", 4.84, 6.02, 1.00),    # sesuai untuk outdoor dan indoor
    ("b1", "v", 8.26, 9.64, 1.00),    # dia ada dua tau, material
    ("b2", "v", 10.68, 12.66, 1.08),  # depan ni metal, belakang ni plastik
    ("b3", "v", 13.34, 15.84, 1.00),  # lepas tu nose pad dia pun memang sedap, selesa tau
    ("b4", "v", 16.44, 17.82, 1.08),  # memang abang pakai ni tak de bekas
    ("b5", "v", 18.68, 21.00, 1.00),  # lepas tu dia punya bingkai dia silikon tau
    ("b6", "v", 21.64, 22.80, 1.08),  # dia ni tahan lasak tau
    ("c1", "v", 25.30, 26.10, 1.00),  # warna dia pun cantik
    ("c2", "v", 26.68, 28.00, 1.06),  # lepas tu yang best dia
    ("c3", "v", 29.02, 30.06, 1.00),  # fungsi dia lagi
    ("c4", "v", 30.38, 37.44, 1.06),  # ni anti UV light tau ... photochromic, dia jadi warna hitam kalau kena cahaya matahari
    ("d1", "v", 38.50, 43.46, 1.00),  # kalau abang tengok pun lama ke ataupun bekerja depan laptop ataupun komputer kan
    ("d2", "v", 43.76, 48.06, 1.08),  # abang boleh tengok lama-lama, jangan risau, sebab dia anti UV light, so mata pun takkan penat
    ("d3", "v", 48.44, 49.52, 1.00),  # abang takkan jadi mengantuk
    ("e1", "v", 50.58, 54.78, 1.06),  # yang mana drive, kalau lama-lama kena cahaya matahari tu kan, boleh microsleep
    ("z1", "v", 55.32, 56.14, 1.00),  # abang pakai ni memang selesa
    ("z2", "v", 58.44, 59.48, 1.08),  # nak dapat mana, tekan link
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
        b = 60.40  # hold to the end of the take so the shop card reads for 2 s+
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
FIX = {"dalwa": "Dalwa", "apa": "abang", "ampun": "abang", "pack": "pad", "rasak": "lasak", "bantuan": "mata",
       "selesor": "selesa", "mic": "pakai", "bubuh": "pakai", "berkejar": "bekerja", "photochromic": "photochromic"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w-]", "", t).lower()
    if sid == "d2" and core == "apa":
        return t  # "sebab apa" is a real "apa"
    if sid == "b4" and core == "dekat":
        return "ada"
    if sid == "c4" and core == "anti" and w["start"] > 33:
        return None  # "anti photochromic" -> "photochromic"
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
glued = []
for w in kept:
    if w["text"].startswith("-") and glued and glued[-1]["seg"] == w["seg"]:
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


SCREEN = '<svg viewBox="0 0 24 24" fill="none" stroke="#5ac8fa" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/></svg>'
SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5c542" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>'
CAR = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5c542" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 16v-3l2-5h14l2 5v3H3z"/><circle cx="7.5" cy="16.5" r="1.6"/><circle cx="16.5" cy="16.5" r="1.6"/></svg>'
Y = 780  # close-up shots: chest band, below the face
YT = 235  # talking-head shots: above the head

build_scene("intro", [
    widget("hk-q", f'<div class="hd">{SCREEN}<span>Selalu depan skrin?</span></div><div class="big" style="font-size:80px">Mata cepat penat?</div>',
           0.0, end("a1") + 0.35, top=YT),
    pill("in-design", "Design cantik", W("a2", 2.58), end("a2") - W("a2", 2.58), None, YT + 20, icon=STAR),
    pill("in-out", "Outdoor", W("a3", 5.42), end("a3") - W("a3", 5.42) + 0.2, 290, YT + 20, icon=SUN),
    pill("in-in", "Indoor", W("a3", 6.02), end("a3") - W("a3", 6.02) + 0.2, 560, YT + 20, icon=GEM),
])

build_scene("build", [
    widget("bd-mat", '<div class="hd"><span>Dua material</span></div>'
           '<div class="rowx"><span>Depan</span><span class="v" style="color:#fff">METAL</span></div>'
           '<div class="rowx"><span>Belakang</span><span class="v" style="color:#fff">PLASTIK</span></div>',
           W("b1", 9.64) - 0.3, end("b2") - W("b1", 9.64) + 0.3, top=Y),
    pill("bd-nose", "Nose pad selesa", W("b3", 14.00), end("b3") - W("b3", 14.00), None, Y + 40),
    pill("bd-mark", "Tak tinggal bekas", W("b4", 17.42) - 0.4, end("b4") - W("b4", 17.42) + 0.4, None, Y + 40),
    pill("bd-sil", "Bingkai silikon", W("b5", 20.32) - 0.3, end("b5") - W("b5", 20.32) + 0.3, None, Y + 40),
    wave_title("bd-lasak", "Tahan Lasak", W("b6", 22.20) - 0.15, end("b6") - W("b6", 22.20) + 0.15, top=Y + 20),
])

build_scene("tech", [
    pill("tc-warna", "Warna cantik", W("c1", 25.30), end("c1") - W("c1", 25.30), None, Y + 40, icon=STAR),
    banner("tc-hd", "assets/img/banner-hd.jpg", W("c4", 31.08) - 0.1, W("c4", 33.56) - W("c4", 31.08)),
    widget("tc-photo", f'<div class="hd">{SUN}<span>Photochromic</span></div><div class="big" style="font-size:66px">Kena matahari, jadi gelap</div>',
           W("c4", 33.56), end("c4") - W("c4", 33.56), top=YT),
])

build_scene("eyes", [
    widget("ey-lap", f'<div class="hd">{SCREEN}<span>Lama depan laptop / komputer?</span></div><div class="big" style="font-size:70px">Jangan risau</div>',
           W("d1", 39.96), end("d1") - W("d1", 39.96) + 0.4, top=YT),
    banner("ey-strain", "assets/img/banner-eyestrain.jpg", W("d2", 45.34) - 0.1, end("d2") - W("d2", 45.34) + 0.1),
    pill("ey-sleep", "Tak mengantuk", W("d3", 49.52) - 0.5, end("d3") - W("d3", 49.52) + 0.5, None, YT + 20),
    widget("ey-drive", f'<div class="hd">{CAR}<span>Drive lama bawah matahari?</span></div><div class="big" style="font-size:70px">Elak microsleep</div>',
           W("e1", 51.54), end("e1") - W("e1", 51.54), top=YT),
])

build_scene("outro", [
    wave_title("ot-selesa", "Selesa", SEG["z1"]["start"] + 0.05, end("z1") - SEG["z1"]["start"] - 0.05, top=YT + 20),
    banner("ot-shop", "assets/img/shop-card.jpg", SEG["z2"]["start"] + 0.05, TOTAL - SEG["z2"]["start"] - 0.05),
])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 800; font-size: 58px; color: #fff;
      letter-spacing: .01em; text-shadow: 0 3px 0 rgba(0,0,0,.35), 0 6px 22px rgba(0,0,0,.6); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/dalwa.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
# slow premium push-in across the hook
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {end("a1")}, ease: "none", immediateRender: false }}, 0);')

SFX = [("sx-q", "pop.mp3", 0.05, 0.35),
       ("sx-design", "pop.mp3", W("a2", 2.58) + 0.03, 0.3),
       ("sx-out", "pop.mp3", W("a3", 5.42) + 0.03, 0.3),
       ("sx-in", "pop.mp3", W("a3", 6.02) + 0.03, 0.3),
       ("sx-mat", "whoosh-short.mp3", W("b1", 9.64) - 0.35, 0.3),
       ("sx-nose", "pop.mp3", W("b3", 14.00) + 0.03, 0.3),
       ("sx-sil", "pop.mp3", W("b5", 20.32) - 0.27, 0.3),
       ("sx-lasak", "whoosh.mp3", W("b6", 22.20) - 0.4, 0.3),
       ("sx-hd", "whoosh-short.mp3", W("c4", 31.08) - 0.15, 0.3),
       ("sx-photo", "click-soft.mp3", W("c4", 33.56), 0.45),
       ("sx-strain", "whoosh-short.mp3", W("d2", 45.34) - 0.15, 0.3),
       ("sx-sleep", "pop.mp3", W("d3", 49.52) - 0.47, 0.3),
       ("sx-drive", "whoosh-short.mp3", W("e1", 51.54) - 0.1, 0.3),
       ("sx-shop", "sparkle.mp3", SEG["z2"]["start"] + 0.05, 0.3)]

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

hosts = [("intro", 2), ("build", 3), ("tech", 4), ("eyes", 5), ("outro", 6), ("captions", 7)]
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

