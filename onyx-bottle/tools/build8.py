#!/usr/bin/env python3
"""Work jacket (reflective uniform) — minimal premium style, side cards beside the speaker, CTA "link di bio".
Usage: python3 -I build8.py <words.json> <project_dir>
"""
import json, sys, html, os, re, glob, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
SECOND_SIZE = os.environ.get("SECOND_SIZE")  # e.g. "M"
SIZE_ROWS = {"S": 305, "M": 360, "L": 415, "XL": 470, "XXL": 525, "XXXL": 580}  # row centres in the 823 px chart
WORDS = {"v": json.load(open(WJ))}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))

# (id, src, first_word_start, last_word_start, cam_scale)
EDL = [
    ("a1", "v", 2.46, 4.96, 1.00),    # botol air ni memang padu lah daripada Onyx tau
    ("a2", "v", 5.16, 6.94, 1.08),    # kamu nampak dia boleh juga jadi dumbbell
    ("a3", "v", 8.38, 10.38, 1.00),   # selain tu kamu tengok lah yang best dia lagi
    ("m1", "v", 10.98, 10.98, 1.00),  # ni (he clips the phone on the magnet)
    ("m2", "v", 13.42, 13.42, 1.00),  # haa
    ("m3", "v", 15.10, 18.74, 1.00),  # boleh record tau sambil nak main dumbbell ke main gym ke apa kan
    ("m4", "v", 18.94, 20.48, 1.08),  # tak payah tau, sekarang ni (bawa) tripod
    ("z1", "v", 22.38, 24.74, 1.00),  # botol air ni, fuhlamak memang padu lah
    ("z2", "v", 24.86, 26.28, 1.06),  # nak dapat mana, pergi ke link tu
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
    if sid == "m1":
        b = 12.60  # keep the magnet clip-on action
    if sid == "m2":
        b = 14.60
    if sid == "z2":
        b = 27.60  # hold on the smile for the shop card
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
FIX = {"boto": "Botol", "ayak": "air", "onyx": "Onyx"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w-]", "", t).lower()
    if sid in ("m1", "m2") or core in {"haa", "ni"} and sid in ("m1", "m2"):
        return None
    if sid == "m4" and core in {"bukan", "sama", "-sama"}:
        return None  # garbled; the pill says "tak payah tripod"
    if sid == "z1" and core == "oh":
        return "Fuhlamak"
    if sid == "z1" and core == "lah" and w["start"] < 23.8:
        return None
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
kept = [w for i, w in enumerate(kept) if not (i and w["text"].lower() == kept[i - 1]["text"].lower() and w["start"] - kept[i - 1]["start"] < 0.4)]
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


SX, SW = 70, 300   # side column on the left of the speaker


def side_img(cid, src, start, dur, top=780, w=SW):
    body = clip(cid, start, dur, f'<img src="{src}" alt="" style="display:block;width:100%;border-radius:20px"/>',
                style=f"position:absolute; left:{SX}px; top:{top}px; width:{w}px; padding:8px; border-radius:28px; background:var(--glass); border:1.5px solid var(--stroke); box-shadow:0 20px 50px rgba(0,0,0,.45)")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, x: -60, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.5, ease: "expo.out" }}, {fr(start)});',
                    fade_out(f"#{cid}", start + dur)])
    return body, js


def side_pill(cid, text, start, dur, top, icon=CHECK):
    return pill(cid, text, start, dur, SX, top, icon=icon)


TAPE = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5c542" stroke-width="2.4" stroke-linecap="round"><path d="M3 9h18M3 15h18"/></svg>'
YT = 880

def insert(cid, start, dur, inner, js_extra=()):
    """full-screen cut-away: video dims, a big card zooms in"""
    body = clip(cid, start, dur,
                f'<div id="{cid}bg" style="position:absolute;inset:0;background:rgba(8,9,12,.72)"></div>{inner}',
                style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = [f'    tl.fromTo("#{cid}bg", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, {fr(start)});',
          f'    tl.fromTo("#{cid}-c", {{ opacity: 0, scale: 0.82, y: 40 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.55, ease: "expo.out" }}, {fr(start + 0.05)});',
          *js_extra,
          f'    tl.to("#{cid}", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {fr(start + dur - 0.27)});']
    return body, "\n".join(js)


CW = 900  # insert card width
k = CW / 823


def size_insert(start, dur, hl):
    """size chart big, the rows the speaker names light up in turn"""
    bars, js = [], []
    for i, (size, t) in enumerate(hl):
        y = SIZE_ROWS[size] * k
        bars.append(f'<div id="sz-hl{i}" style="position:absolute;left:4px;right:4px;top:{y - 30:.0f}px;height:60px;border:5px solid #f5c542;border-radius:14px;'
                    f'box-shadow:0 0 0 4px rgba(245,197,66,.25),0 0 30px rgba(245,197,66,.8)"></div>'
                    f'<div id="sz-tag{i}" class="pill" style="position:absolute;right:24px;top:{y - 70:.0f}px">{"Aku pakai" if i == 0 else "Nak fit"}: {size}</div>')
        js += [f'    tl.fromTo(["#sz-hl{i}", "#sz-tag{i}"], {{ opacity: 0, scale: 1.15 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {fr(t)});']
        if i + 1 < len(hl):
            js.append(f'    tl.to(["#sz-hl{i}", "#sz-tag{i}"], {{ opacity: 0.25, duration: 0.25 }}, {fr(hl[i + 1][1] - 0.05)});')
    inner = (f'<div id="sz-c" style="position:absolute;left:{(1080 - CW) // 2 - 30}px;top:300px;width:{CW}px;border-radius:30px;overflow:visible">'
             f'<div style="border-radius:30px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6)"><img src="assets/img/size-crop.jpg" style="display:block;width:{CW}px" alt=""/></div>'
             + "".join(bars) + '</div>')
    js.insert(0, f'    tl.set([{", ".join(chr(34) + f"#sz-hl{i}" + chr(34) + ", " + chr(34) + f"#sz-tag{i}" + chr(34) for i in range(len(hl)))}], {{ opacity: 0 }}, {fr(start)});')
    return insert("sz", start, dur, inner, js)


def review_insert(start, dur):
    stars = "".join(f'<span id="rv-s{i}" style="display:inline-block;margin:0 6px">'
                    f'<svg viewBox="0 0 24 24" width="88" height="88" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg></span>' for i in range(5))
    inner = (f'<div id="rv-c" style="position:absolute;left:{(1080 - CW) // 2 - 30}px;top:300px;width:{CW}px;text-align:center">'
             f'<div style="font-family:var(--font-ui);font-weight:800;font-size:40px;color:#fff;letter-spacing:.04em">REVIEW PEMBELI</div>'
             f'<div style="margin:10px 0 18px">{stars}</div>'
             f'<div style="border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6)"><img src="assets/img/review.jpg" style="display:block;width:{CW}px" alt=""/></div></div>')
    js = [f'    tl.fromTo("#rv-s{i}", {{ opacity: 0, scale: 0.2, rotation: -40 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2.2)" }}, {fr(start + 0.3 + i * 0.09)});' for i in range(5)]
    return insert("rv", start, dur, inner, js)


def shine_img(cid, src, start, dur, top=780, w=SW):
    """side card with a light sweep across it, like a reflector catching headlights"""
    body = clip(cid, start, dur,
                f'<div style="position:relative;border-radius:20px;overflow:hidden"><img src="{src}" alt="" style="display:block;width:100%"/>'
                f'<div id="{cid}sh" style="position:absolute;top:-20%;bottom:-20%;width:45%;left:0;background:linear-gradient(100deg,transparent,rgba(255,255,255,.85),transparent);mix-blend-mode:screen"></div></div>',
                style=f"position:absolute; left:{SX}px; top:{top}px; width:{w}px; padding:8px; border-radius:28px; background:var(--glass); border:1.5px solid var(--stroke); box-shadow:0 20px 50px rgba(0,0,0,.45)")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, y: -50, rotation: -4 }}, {{ opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: "back.out(1.5)" }}, {fr(start)});',
                    f'    tl.fromTo("#{cid}sh", {{ xPercent: -120 }}, {{ xPercent: 260, duration: 0.8, ease: "power2.inOut" }}, {fr(start + 0.45)});',
                    f'    tl.fromTo("#{cid}sh", {{ xPercent: -120 }}, {{ xPercent: 260, duration: 0.8, ease: "power2.inOut", immediateRender: false }}, {fr(start + 2.6)});',
                    fade_out(f"#{cid}", start + dur)])
    return body, js


def center_img(cid, src, start, dur, top=640, w=560):
    body = clip(cid, start, dur, f'<img src="{src}" alt="" style="display:block;width:100%;border-radius:22px"/>',
                style=f"position:absolute; left:{540 - w // 2}px; top:{top}px; width:{w}px; padding:8px; border-radius:30px; background:var(--glass); border:1.5px solid var(--stroke); box-shadow:0 24px 60px rgba(0,0,0,.5)")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, scale: 0.6, y: 80 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.6, ease: "back.out(1.4)" }}, {fr(start)});',
                    fade_out(f"#{cid}", start + dur)])
    return body, js


YT = 280   # top band, above his head
DUMB = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round"><path d="M6 7v10M18 7v10M3 9.5v5M21 9.5v5M6 12h12"/></svg>'
MAG = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3v8a6 6 0 0 0 12 0V3"/><path d="M6 7h3M15 7h3"/></svg>'
CAM = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2.5" y="6.5" width="13" height="11" rx="2"/><path d="M15.5 10.5l6-3v9l-6-3"/></svg>'


def features_insert(start, dur):
    inner = (f'<div id="ft-c" style="position:absolute;left:{(1080 - CW) // 2 - 30}px;top:300px;width:{CW}px;text-align:center">'
             f'<div style="font-family:var(--font-ui);font-weight:800;font-size:40px;color:#fff;letter-spacing:.08em">ONYX BOTTLE 2.0</div>'
             f'<div style="margin-top:16px;border-radius:28px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6)"><img src="assets/img/features.jpg" style="display:block;width:{CW}px" alt=""/></div></div>')
    return insert("ft", start, dur, inner)


build_scene("intro", [
    wave_title("in-t", "Onyx Bottle", 0.1, end("a1") - 0.1, top=YT),
    pill("in-dumb", "Boleh jadi dumbbell", W("a2", 5.74), end("a2") - W("a2", 5.74), None, YT + 20, icon=DUMB),
    features_insert(fr(W("a3", 9.64) - 0.1), fr(end("a3") - W("a3", 9.64) + 0.5)),
])

build_scene("magnet", [
    pill("mg-mag", "Magnet · lekat phone", SEG["m1"]["start"] + 0.5, end("m2") - SEG["m1"]["start"] - 0.5, None, YT + 20, icon=MAG),
    pill("mg-rec", "Record masa workout", W("m3", 15.54), end("m3") - W("m3", 15.54), None, YT + 20, icon=CAM),
    pill("mg-tri", "Tak payah tripod", SEG["m4"]["start"] + 0.05, end("m4") - SEG["m4"]["start"] - 0.05, None, YT + 20, icon=CHECK),
])

# ending, like the Dalwa edit: wave title, then the shop card
build_scene("outro", [
    wave_title("ot-padu", "Padu", W("z1", 23.46) - 0.1, end("z1") - W("z1", 23.46) + 0.1, top=YT),
    banner("ot-shop", "assets/img/shop-card.jpg", SEG["z2"]["start"] + 0.05, TOTAL - SEG["z2"]["start"] - 0.05, top=YT, width=640),
])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 800; font-size: 58px; color: #fff;
      letter-spacing: .01em; text-shadow: 0 3px 0 rgba(0,0,0,.35), 0 6px 22px rgba(0,0,0,.6); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/raw.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
# slow premium push-in across the hook
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {end("a1")}, ease: "none", immediateRender: false }}, 0);')

SFX = [("sx-t", "whoosh.mp3", 0.0, 0.3),
       ("sx-dumb", "pop.mp3", W("a2", 5.74) + 0.03, 0.35),
       ("sx-ft", "whoosh.mp3", W("a3", 9.64) - 0.35, 0.3),
       ("sx-mag", "click.mp3", SEG["m1"]["start"] + 0.5, 0.45),
       ("sx-rec", "pop.mp3", W("m3", 15.54) + 0.03, 0.3),
       ("sx-tri", "pop.mp3", SEG["m4"]["start"] + 0.08, 0.3),
       ("sx-padu", "whoosh.mp3", W("z1", 23.46) - 0.4, 0.3),
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

hosts = [("intro", 2), ("magnet", 3), ("outro", 4), ("captions", 5)]
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

