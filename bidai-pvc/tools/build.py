#!/usr/bin/env python3
"""PVC venetian blinds — same look as the work-jacket edit (one-word captions, glass cards, full-screen inserts,
wave title, CTA "tekan link di bawah"), plus muted b-roll cutaways from the second clip.
Usage: python3 -I build.py <words.json> <project_dir>
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = {"v": json.load(open(WJ))}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))


# (id, src, first_word_start, last_word_start, cam_scale)
EDL = [
    ("h1", "v", 1.46, 5.32, 1.00),    # haa tu dia, nampak? memang syok haa
    ("o1", "v", 5.56, 9.60, 1.08),    # kalau aku nak cahaya matahari dari luar, aku buka macam ni lah. kalau tak mahu, aku tutup lah
    ("b1", "v", 10.42, 11.66, 1.00),  # memang best pakai blind ni            (b-roll on top)
    ("p1", "v", 14.12, 16.94, 1.08),  # dia rasa privacy sikit tau. lawa bentuk dia   (b-roll on "lawa bentuk")
    ("w1", "v", 22.38, 28.72, 1.00),  # kalau nak basuh ke, ada habuk-habuk ke. jangan risau, sebab ni PVC tau, dia waterproof
    ("c1", "v", 29.36, 39.02, 1.00),  # macam-macam warna ... ruang tamu, dapur, bilik, tempat study. memang lawa memang cantik
    ("f1", "v", 39.60, 40.90, 1.08),  # setiap pembelian dia ada yang ni
    ("f2", "v", 47.88, 51.22, 1.00),  # dia ada bagi juga dua ni. lepas tu skru pun dia bagi
    ("t1", "v", 52.42, 53.12, 1.10),  # memang terbaik lah
    ("s1", "v", 53.42, 57.90, 1.00),  # ni kalau tengok kedai ni, dua juta barang dah ter-sold lah. memang trusted
    ("k1", "v", 62.38, 66.30, 1.00),  # boleh buka juga separuh, 50%, menggunakan tarik, tarik tali ni je
    ("k2", "v", 70.84, 73.56, 1.06),  # nak buka macam ni pun boleh, nak tutup sampai habis pun boleh
    ("z1", "v", 75.40, 78.30, 1.04),  # memang berbaloi gang. nak dapat mana? tekan link bawah
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
    if sid == "p1":
        b = 17.0    # stop before "aku main tengok ni"
    if sid == "w1":
        b = 29.05   # "water-proof" is split in two by whisper; keep the whole word
    if sid == "z1":
        b = 78.85   # full "tekan link bawah"
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


def end(sid):
    s = SEG[sid]
    return fr(s["start"] + s["dur"])


def W(sid, t):
    return at(sid, wat(SEG[sid]["src"], t)["start"])


# ---------------------------------------------------------------- one-word captions
FIX = {"cair": "cahaya", "ampun": "kalau", "bubur": "letak", "rusted": "trusted", "ter": "ter"}


def norm(sid, w):
    t = w["text"]
    core = re.sub(r"[^\w%-]", "", t).lower()
    if core in {"pro", "terima", "kasih", "menonton"}:
        return None
    if core in FIX:
        return FIX[core] + t[len(t.rstrip(".,!?")):]
    return t


kept = []
for s in segs:
    for w in WORDS[s["src"]]:
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05:
            txt = norm(s["id"], w)
            if not txt or re.sub(r"[^\w]", "", txt).lower() in {"haha", "haa", "ha", "ah", "tuh"}:
                continue
            st = at(s["id"], w["start"])
            en = at(s["id"], min(w["end"], s["src_out"]))
            if re.sub(r"[^\w]", "", txt).lower() == "lingguan":   # "link bawah" heard as one word
                mid = fr((st + en) / 2)
                kept.append(dict(text="link", start=st, end=mid, seg=s["id"]))
                kept.append(dict(text="bawah", start=mid, end=max(en + 0.3, mid + 0.3), seg=s["id"]))
                continue
            kept.append(dict(text=txt, start=st, end=max(en, st + 0.12), seg=s["id"]))
# glue hyphen halves ("habuk" "-habuk", "ter" "-sold") and "50" "%"
glued = []
for w in kept:
    if (w["text"].startswith("-") or w["text"] == "%") and glued and glued[-1]["seg"] == w["seg"]:
        glued[-1]["text"] += w["text"]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
kept = [w for i, w in enumerate(kept) if not (i and w["text"].lower() == kept[i - 1]["text"].lower() and w["start"] - kept[i - 1]["start"] < 0.6)]
cap_items, cap_js = [], []
for i, w in enumerate(kept):
    nxt = kept[i + 1]["start"] if i + 1 < len(kept) else TOTAL
    st = fr(w["start"])
    en = fr(min(max(w["end"] + 0.05, st + 0.25), nxt, TOTAL))
    if en - st < 0.1:
        continue
    word = re.sub(r"[.,!?]", "", w["text"]).upper()
    cid = f"cw{i:03d}"
    cap_items.append(f'    <div id="{cid}" class="cw clip" data-start="{st}" data-duration="{fr(en - st)}" data-track-index="0">'
                     f'<span id="{cid}s">{html.escape(word)}</span></div>')
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, y: 6 }}, {{ opacity: 1, y: 0, duration: 0.08, ease: "power2.out" }}, {st});')

# ---------------------------------------------------------------- design tokens (same as the jacket edit)
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
    .widget .rowx {{ display: flex; align-items: center; justify-content: space-between; margin-top: 18px; font-size: 34px; font-weight: 700; }}
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
DROP = '<svg viewBox="0 0 24 24" fill="#5ac8fa"><path d="M12 2.5s7 7.6 7 12.6a7 7 0 0 1-14 0c0-5 7-12.6 7-12.6z"/></svg>'
SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="#f5a623" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="4.2" fill="#f5c542"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>'
MOON = '<svg viewBox="0 0 24 24" fill="#5b6cff"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg>'
LOCK = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/></svg>'
SPARK = '<svg viewBox="0 0 24 24" fill="#5ac8fa"><path d="M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7z"/></svg>'
CORD = '<svg viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.6" stroke-linecap="round"><path d="M12 2v14"/><circle cx="12" cy="19" r="3" fill="#f5c542"/></svg>'


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


def build_scene(name, parts, css_extra=""):
    write(f"{name}.html", scene(name, BASE + css_extra, "\n".join(p[0] for p in parts), "\n".join(p[1] for p in parts)))


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


def pill(cid, text, start, dur, y, x=None, icon=CHECK):
    """x=None centres the pill horizontally (inside the 960 px caption-safe column, like the jacket edit)"""
    left, width = (0, 960) if x is None else (x, 600)
    inner = f'<span id="{cid}i" class="pill" style="position:relative">{icon}<span>{text}</span></span>'
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{left}px; width:{width}px; top:{y}px; text-align:{'center' if x is None else 'left'}")
    js = "\n".join([f'    tl.fromTo("#{cid}i", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)" }}, {fr(start)});',
                    fade_out(f"#{cid}", start + dur)])
    return body, js


def line_callout(cid, label, start, dur, dot, lbl):
    (dx, dy), (lx, ly) = dot, lbl
    svg = (f'<svg viewBox="0 0 1080 1920"><circle id="{cid}d" cx="{dx}" cy="{dy}" r="11" fill="#fff"/>'
           f'<path id="{cid}p" d="M{dx} {dy} L{dx} {ly} L{lx} {ly}" stroke="#fff" stroke-width="3.5" fill="none"/></svg>')
    lab = f'<div id="{cid}l" class="co-lbl" style="left:{min(lx, dx)}px; top:{ly - 66}px">{label}</div>'
    body = clip(cid, start, dur, svg + lab, cls="co", style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid}d", {{ scale: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}p", {{ strokeDasharray: 1400, strokeDashoffset: 1400 }}, {{ strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }}, {fr(start + 0.1)});',
        fade_in(f"#{cid}l", start + 0.45, y=10, blur=6, d=0.3),
        fade_out(f"#{cid}", start + dur)])
    return body, js


def rings(cid, label, start, dur, cx, cy, icon=DROP):
    rs = "".join(f'<circle class="rg" cx="{cx}" cy="{cy}" r="{r}" stroke="rgba(255,255,255,.8)" stroke-width="2.5" fill="none"/>' for r in (70, 130, 190))
    svg = f'<svg viewBox="0 0 1080 1920">{rs}</svg>'
    lab = f'<div style="position:absolute; left:0; width:1080px; top:{cy - 34}px; text-align:center"><span id="{cid}l" class="pill">{icon}<span>{label}</span></span></div>'
    body = clip(cid, start, dur, svg + lab, cls="co", style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid} .rg", {{ opacity: 0, scale: 0.4, transformOrigin: "{cx}px {cy}px" }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: "expo.out", stagger: 0.1 }}, {fr(start)});',
        f'    tl.fromTo("#{cid}l", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.6)" }}, {fr(start + 0.15)});',
        fade_out(f"#{cid}", start + dur)])
    return body, js


def widget(cid, inner, start, dur, top=280, js_extra=()):
    body = clip(cid, start, dur, inner, cls="widget", style=f"top:{top}px")
    js = "\n".join([fade_in(f"#{cid}", start, y=-20), *js_extra, fade_out(f"#{cid}", start + dur)])
    return body, js


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


CW = 760
CL = (1080 - CW) // 2 - 60   # card left, centred on the 960 caption column
HEAD = 'font-family:var(--font-ui);font-weight:800;font-size:44px;color:#fff;letter-spacing:.06em;text-align:center;margin-bottom:22px;text-shadow:0 4px 18px rgba(0,0,0,.6)'


def card_img(src, extra=""):
    return f'<div style="border-radius:30px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6){extra}"><img src="{src}" style="display:block;width:{CW}px" alt=""/></div>'


def colours_insert(start, dur):
    inner = (f'<div id="cl-c" style="position:absolute;left:{CL}px;top:290px;width:{CW}px">'
             f'<div style="{HEAD}">MACAM-MACAM WARNA</div>{card_img("assets/img/colours.jpg")}</div>')
    return insert("cl", start, dur, inner)


RK = CW / 1280
ROOMS = {"tamu": (30, 175), "bilik": (653, 175), "study": (653, 673)}


def rooms_insert(start, dur, hl):
    """room grid; each room the speaker names lights up in turn; 'dapur' gets a pill (no kitchen tile)"""
    boxes, js = [], []
    for i, (key, label, t) in enumerate(hl):
        if key in ROOMS:
            x, y = ROOMS[key]
            boxes.append(f'<div id="rm-h{i}" style="position:absolute;left:{x * RK:.0f}px;top:{y * RK + 88:.0f}px;width:{597 * RK:.0f}px;height:{470 * RK:.0f}px;'
                         f'border:6px solid #f5c542;border-radius:18px;box-shadow:0 0 0 4px rgba(245,197,66,.25),0 0 34px rgba(245,197,66,.85)"></div>')
        else:
            boxes.append(f'<div id="rm-h{i}" style="position:absolute;left:0;width:{CW}px;top:{88 + 410 * RK:.0f}px;text-align:center">'
                         f'<span class="pill">{CHECK}<span>{label}</span></span></div>')
        js.append(f'    tl.fromTo("#rm-h{i}", {{ opacity: 0, scale: 1.12 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }}, {fr(t)});')
        if i + 1 < len(hl):
            js.append(f'    tl.to("#rm-h{i}", {{ opacity: 0, duration: 0.2 }}, {fr(hl[i + 1][2] - 0.05)});')
    inner = (f'<div id="rm-c" style="position:absolute;left:{CL}px;top:290px;width:{CW}px">'
             f'<div style="{HEAD}">SESUAI SEMUA RUANG</div>{card_img("assets/img/rooms.jpg")}' + "".join(boxes) + '</div>')
    js.insert(0, f'    tl.set([{", ".join(chr(34) + f"#rm-h{i}" + chr(34) for i in range(len(hl)))}], {{ opacity: 0 }}, {fr(start)});')
    return insert("rm", start, dur, inner, js)


def shop_insert(start, dur, t_num, t_trust):
    stars = "".join(f'<span id="sh-s{i}" style="display:inline-block;margin:0 5px">'
                    f'<svg viewBox="0 0 24 24" width="70" height="70" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg></span>' for i in range(5))
    inner = (f'<div id="sh-c" style="position:absolute;left:{CL}px;top:300px;width:{CW}px;text-align:center">'
             f'{card_img("assets/img/shop.jpg")}'
             f'<div id="sh-n" style="margin-top:34px;font-family:var(--font-num);font-weight:700;font-size:150px;line-height:1;color:var(--gold);text-shadow:0 8px 30px rgba(0,0,0,.6)">2 JUTA+</div>'
             f'<div id="sh-l" style="margin-top:6px;font-family:var(--font-ui);font-weight:800;font-size:44px;color:#fff;letter-spacing:.08em">DAH TERJUAL</div>'
             f'<div id="sh-t" style="margin-top:40px">{stars}<div style="margin-top:8px;font-family:var(--font-ui);font-weight:700;font-size:34px;color:var(--muted)">4.8/5 &middot; 8.6K review</div></div></div>')
    js = [f'    tl.fromTo(["#sh-n", "#sh-l"], {{ opacity: 0, scale: 1.4, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.5, ease: "expo.out", stagger: 0.08 }}, {fr(t_num)});',
          f'    tl.fromTo("#sh-t", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, {fr(t_trust)});']
    js += [f'    tl.fromTo("#sh-s{i}", {{ opacity: 0, scale: 0.2, rotation: -40 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.35, ease: "back.out(2.2)" }}, {fr(t_trust + i * 0.08)});' for i in range(5)]
    return insert("sh", start, dur, inner, js)


# ---------------------------------------------------------------- scenes
build_scene("intro", [
    wave_title("in-ttl", "BIDAI PVC", 0.1, end("h1") - 0.1),
    pill("in-buka", "Buka &amp; tutup ikut suka", W("o1", 6.30), end("o1") - W("o1", 6.30), 300, icon=SUN),
    pill("in-best", "Memang best!", SEG["b1"]["start"] + 0.05, end("b1") - SEG["b1"]["start"] - 0.05, 300, icon=STAR),
    pill("in-priv", "Lebih privacy", W("p1", 14.62), W("p1", 16.08) - W("p1", 14.62), 300, icon=LOCK),
    pill("in-lawa", "Bentuk lawa", W("p1", 16.08), end("p1") - W("p1", 16.08), 300, icon=STAR),
])

build_scene("clean", [
    pill("cl-dust", "Habuk? Lap je", W("w1", 24.28), W("w1", 26.54) - W("w1", 24.28), 300, icon=SPARK),
    line_callout("cl-pvc", "PVC 25MM", W("w1", 26.88), W("w1", 28.40) - W("w1", 26.88), (560, 900), (180, 620)),
    rings("cl-wp", "Waterproof", W("w1", 28.40), end("w1") - W("w1", 28.40) + 0.15, 480, 860, icon=DROP),
])

ROOM_HL = [("tamu", "Ruang tamu", W("c1", 31.78)), ("dapur", "Dapur pun cantik", W("c1", 34.04)),
           ("bilik", "Bilik", W("c1", 36.16)), ("study", "Study", W("c1", 37.44))]
build_scene("style", [
    colours_insert(SEG["c1"]["start"] + 0.05, W("c1", 31.64) - SEG["c1"]["start"] - 0.05),
    rooms_insert(W("c1", 31.64), W("c1", 38.28) - W("c1", 31.64) + 0.1, ROOM_HL),
    pill("st-lawa", "Lawa &amp; cantik", W("c1", 38.28), end("c1") - W("c1", 38.28), 300, icon=STAR),
])

kit_rows = ('<div class="hd">' + CHECK.replace('#111', '#fff') + 'Setiap pembelian dapat</div>'
            '<div id="kt-r1" class="rowx"><span>Bracket hujung</span><span class="v">x2</span></div>'
            '<div id="kt-r2" class="rowx"><span>Skru pemasangan</span><span class="v">&#10003;</span></div>')
build_scene("kit", [
    widget("kt", kit_rows, SEG["f1"]["start"] + 0.05, end("f2") - SEG["f1"]["start"] - 0.05, top=280,
           js_extra=[f'    tl.set(["#kt-r1", "#kt-r2"], {{ opacity: 0 }}, {SEG["f1"]["start"]});',
                     f'    tl.fromTo("#kt-r1", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {W("f2", 48.94)});',
                     f'    tl.fromTo("#kt-r2", {{ opacity: 0, x: -30 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "expo.out" }}, {W("f2", 50.58)});']),
    pill("kt-best", "Memang terbaik", SEG["t1"]["start"] + 0.03, end("t1") - SEG["t1"]["start"] - 0.03, 300, icon=STAR),
])

build_scene("shop", [shop_insert(SEG["s1"]["start"] + 0.05, end("s1") - SEG["s1"]["start"] - 0.05, W("s1", 54.92), W("s1", 56.16))])

half = ('<div class="hd">' + CORD.replace('#111', '#fff') + 'Boleh buka separuh</div>'
        '<div id="pl-n" class="big">50%</div>'
        '<div style="margin-top:14px;height:22px;border-radius:999px;background:rgba(255,255,255,.14);overflow:hidden">'
        '<div id="pl-bar" style="height:100%;width:50%;border-radius:999px;background:linear-gradient(90deg,#f5c542,#f59e42);transform-origin:0 50%"></div></div>')
build_scene("pull", [
    widget("pl", half, W("k1", 63.08), W("k1", 65.16) - W("k1", 63.08), top=280,
           js_extra=[f'    tl.fromTo("#pl-bar", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.7, ease: "power2.out" }}, {fr(W("k1", 63.08) + 0.15)});']),
    pill("pl-tali", "Tarik tali je", W("k1", 65.16), end("k1") - W("k1", 65.16), 300, icon=CORD),
    pill("pl-full", "Buka penuh", W("k2", 71.04), W("k2", 72.60) - W("k2", 71.04), 300),
    pill("pl-shut", "Tutup habis", W("k2", 72.60), end("k2") - W("k2", 72.60), 300),
])

YT = 880
CTA0 = fr(SEG["z1"]["start"] + 0.05)
cta_body = clip("cta-card", CTA0, TOTAL - CTA0,
                '<div style="font-size:30px;font-weight:600;color:var(--muted)">Nak dapatkan bidai ni?</div>'
                '<div style="margin-top:10px;display:inline-flex;align-items:center;gap:14px;padding:16px 34px;border-radius:999px;background:#fe2c55;color:#fff;font-weight:900;font-size:46px;white-space:nowrap">'
                '<svg viewBox="0 0 24 24" width="44" height="44" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
                'Tekan link di bawah</div>',
                cls="widget", style=f"top:{YT}px; width:720px; margin-left:-390px; text-align:center")
cta_js = "\n".join([fade_in("#cta-card", CTA0, y=-20),
                    f'    tl.fromTo("#cta-card div:last-child", {{ scale: 1 }}, {{ scale: 1.06, duration: 0.3, ease: "power2.out", yoyo: true, repeat: 1 }}, {W("z1", 78.30)});'])
build_scene("outro", [
    (cta_body, cta_js)])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 800; font-size: 58px; color: #fff;
      letter-spacing: .01em; text-shadow: 0 3px 0 rgba(0,0,0,.35), 0 6px 22px rgba(0,0,0,.6); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- b-roll (second clip, muted) laid over the talking take
BROLL = [  # (id, out_start, out_end, broll_src_in)
    ("br1", SEG["b1"]["start"], end("b1"), 0.3),             # wide shot of the blinds
    ("br2", W("p1", 16.08) - 0.05, end("p1"), 22.4),          # close-up of the slats
    ("br3", W("k2", 72.60) - 0.1, end("k2"), 7.0),           # blinds fully closed
]
broll = [f'        <video id="{bid}" class="clip" src="assets/broll.mp4" data-start="{fr(a)}" data-duration="{fr(b - a)}" '
         f'data-media-start="{src}" data-track-index="8" muted playsinline></video>' for bid, a, b, src in BROLL]

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/raw.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1"{" data-fade-out=\"0.08\"" if s["id"] == "z1" else ""} playsinline></video>' for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
cam.append(f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.06, duration: {end("h1")}, ease: "none", immediateRender: false }}, 0);')
cam += [f'      tl.fromTo("#broll", {{ scale: 1.0 }}, {{ scale: 1.08, duration: {fr(b - a)}, ease: "none", immediateRender: false }}, {fr(a)});' for _, a, b, _ in BROLL]

SFX = [("sx-ttl", "whoosh.mp3", 0.05, 0.3),
       ("sx-buka", "pop.mp3", W("o1", 6.30) + 0.03, 0.3),
       ("sx-br1", "whoosh-short.mp3", SEG["b1"]["start"] - 0.1, 0.3),
       ("sx-priv", "pop.mp3", W("p1", 14.62) + 0.03, 0.3),
       ("sx-dust", "pop.mp3", W("w1", 24.28) + 0.03, 0.3),
       ("sx-pvc", "click.mp3", W("w1", 26.88), 0.4),
       ("sx-wp", "sparkle.mp3", W("w1", 28.40), 0.25),
       ("sx-cl", "whoosh.mp3", SEG["c1"]["start"], 0.3),
       ("sx-rm", "whoosh-short.mp3", W("c1", 31.64), 0.3),
       ("sx-r1", "click-soft.mp3", W("c1", 31.78), 0.4),
       ("sx-r2", "click-soft.mp3", W("c1", 34.04), 0.4),
       ("sx-r3", "click-soft.mp3", W("c1", 36.16), 0.4),
       ("sx-r4", "click-soft.mp3", W("c1", 37.44), 0.4),
       ("sx-kit", "whoosh-short.mp3", SEG["f1"]["start"], 0.3),
       ("sx-k1", "pop.mp3", W("f2", 48.94), 0.3),
       ("sx-k2", "pop.mp3", W("f2", 50.58), 0.3),
       ("sx-shop", "whoosh.mp3", SEG["s1"]["start"] - 0.1, 0.3),
       ("sx-num", "pop.mp3", W("s1", 54.92), 0.35),
       ("sx-stars", "sparkle.mp3", W("s1", 56.16), 0.3),
       ("sx-half", "whoosh-short.mp3", W("k1", 63.08), 0.3),
       ("sx-tali", "pop.mp3", W("k1", 65.16), 0.3),
       ("sx-full", "pop.mp3", W("k2", 71.04), 0.3),
       ("sx-shut", "click-soft.mp3", W("k2", 72.60), 0.4),
       ("sx-cta", "sparkle.mp3", CTA0, 0.3)]


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

hosts = [("intro", 2), ("clean", 3), ("style", 4), ("kit", 5), ("shop", 6), ("pull", 7), ("outro", 9), ("captions", 10)]
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
      #cam, #broll {{ position: absolute; inset: 0; transform-origin: 50% 45%; }}
      #broll {{ z-index: 2; }}
      #cam video, #broll video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: one clip per kept take from the talking video. Trim in Studio by dragging clip edges. -->
      <div id="cam">
{chr(10).join(videos)}
      </div>
      <!-- B-roll: muted cutaways from the second video; the talking audio keeps running underneath. -->
      <div id="broll">
{chr(10).join(broll)}
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
json.dump(dict(total=TOTAL, segs=segs, broll=BROLL, words=[w["text"] for w in kept]), open(os.path.join(P, ".edl.json"), "w"), indent=1, ensure_ascii=False)
print(f"total={TOTAL}s segments={len(segs)} caption words={len(cap_items)}")
for s in segs:
    print(f'{s["id"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}')
print(" ".join(w["text"] for w in kept))
