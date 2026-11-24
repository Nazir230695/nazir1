#!/usr/bin/env python3
"""A BIG HOME LIVING auto umbrella (2 sizes) — six short (<40 s) videos with different hooks from five raw clips
(raw_b is wordless open/close b-roll, kept silent), reference style, HD grade baked into raw_*.mp4.
Usage: python3 -I build.py <transcript.json> <project_dir> <1..6>
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(WJ))     # {"a": [...], "b": [...], ...} word lists per raw clip
SRC = {k: f"assets/raw_{k}.mp4" for k in "abcde"}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))


VARIANT = sys.argv[3] if len(sys.argv) > 3 else "1"
# (id, src, src_in, src_out, volume, zone)  zone: "top" = overlays on the wall above the floor action, "low" = under the face
TAIL = [("tail", "b", 18.00, 20.50, 0.0, "low")]
VARIANTS = {
    "1": [  # wajib ada dalam kereta (A)
        ("a1", "a", 0.00, 10.00, 1.0, "low"),
        ("a2", "a", 10.90, 17.45, 1.0, "low"),
        ("cta", "a", 17.45, 18.95, 1.0, "low"),
    ] + TAIL,
    "2": [  # nampak premium (C)
        ("c1", "c", 2.60, 23.95, 1.0, "low"),
        ("c2", "c", 24.55, 25.75, 1.0, "low"),
        ("c3", "c", 27.85, 33.40, 1.0, "low"),
        ("cta", "c", 33.40, 36.30, 1.0, "low"),
    ] + TAIL,
    "3": [  # hujan? jangan risau (D)
        ("d0", "d", 3.70, 5.25, 1.0, "low"),
        ("d1", "d", 0.00, 2.25, 1.0, "low"),
        ("d2", "d", 14.30, 20.30, 1.0, "low"),
        ("d3", "d", 21.40, 24.90, 1.0, "low"),
        ("d4", "d", 25.10, 29.70, 1.0, "low"),
        ("d5", "d", 30.00, 33.55, 1.0, "low"),
        ("cta", "d", 37.00, 39.95, 1.0, "low"),
    ] + TAIL,
    "4": [  # viral kat TikTok (E)
        ("e1", "e", 0.00, 2.40, 1.0, "low"),
        ("e2", "e", 8.50, 16.95, 1.0, "low"),
        ("e3", "e", 18.20, 19.20, 1.0, "low"),
        ("e4", "e", 21.70, 23.85, 1.0, "low"),
        ("e5", "e", 24.90, 31.00, 1.0, "low"),
        ("cta", "e", 31.00, 34.70, 1.0, "low"),
    ] + TAIL,
    "5": [  # 1 tekan terus terbuka (remix)
        ("h", "e", 12.30, 14.00, 1.0, "low"),
        ("b1", "b", 15.00, 17.00, 0.0, "low"),
        ("v1", "a", 15.00, 17.45, 1.0, "low"),
        ("v2", "c", 15.00, 17.95, 1.0, "low"),
        ("v3", "c", 20.35, 22.80, 1.0, "low"),
        ("b2", "b", 18.00, 20.00, 0.0, "low"),
        ("v4", "d", 29.95, 33.50, 1.0, "low"),
        ("cta", "e", 31.00, 34.70, 1.0, "low"),
        ("tail", "b", 27.00, 29.00, 0.0, "low"),
    ],
    "6": [  # 2 saiz, 2 warna (b-roll led)
        ("b0", "b", 12.50, 15.50, 0.0, "low"),
        ("v1", "d", 0.00, 2.25, 1.0, "low"),
        ("v2", "c", 12.75, 14.10, 1.0, "low"),
        ("b1", "b", 18.00, 21.00, 0.0, "low"),
        ("v3", "e", 14.00, 15.35, 1.0, "low"),
        ("v4", "d", 35.00, 38.10, 1.0, "low"),
        ("cta", "a", 17.45, 18.95, 1.0, "low"),
        ("tail", "b", 27.00, 29.50, 0.0, "low"),
    ],
}
EDL = VARIANTS[VARIANT]

segs, f = [], 0
for sid, src, a, b, vol, zone in EDL:
    fa, fb = round(a * FPS), round(b * FPS)
    segs.append(dict(id=sid, src=src, src_in=fa / FPS, src_out=fb / FPS, start=f / FPS, dur=(fb - fa) / FPS, vol=vol, zone=zone))
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


# ---------------------------------------------------------------- phrase captions
FIX = {"ampun": "kau", "bukak": "buka", "lamak": "alamak", "hulamak": "alamak", "asap": "lasak"}
DROP = {"haa", "ha", "okay", "ok", "oh", "belik"}
CAP_SKIP = [("d", 22.40, 23.10)]   # "cukup nak?" is unclear


def norm(w, prev):
    t = w["text"]
    core = re.sub(r"[^\w]", "", t).lower()
    if core in DROP:
        return None
    if core == "ayak":                      # "air" after tarik / penarik, otherwise "lantai"
        rep = "air" if prev in {"tarik", "penarik"} else "lantai"
    elif core in FIX:
        rep = FIX[core]
    else:
        return t
    if t[:1].isupper():
        rep = rep[:1].upper() + rep[1:]
    return rep + t[len(t.rstrip(".,!?")):]


CAP_STOP = {}
kept = []
for s in segs:
    ws = WORDS[s["src"]]
    for i, w in enumerate(ws):
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05 and not any(s["src"] == k and t0 <= w["start"] <= t1 for k, t0, t1 in CAP_SKIP):
            prev = re.sub(r"[^\w]", "", ws[i - 1]["text"]).lower() if i else ""
            nxt = re.sub(r"[^\w]", "", ws[i + 1]["text"]).lower() if i + 1 < len(ws) else ""
            if re.sub(r"[^\w]", "", w["text"]).lower() == "lepas" and nxt == "mana":
                txt = "nak dapat"
            else:
                txt = norm(w, prev)
            if txt:
                kept.append(dict(text=txt, start=at(s["id"], w["start"]), end=at(s["id"], min(w["end"], s["src_out"])), seg=s["id"]))
glued = []
for w in kept:   # "Celah" + "-celah", "tarik" + "-tarik"
    if glued and glued[-1]["seg"] == w["seg"] and w["text"].startswith("-"):
        glued[-1]["text"] += w["text"]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
for i, w in enumerate(kept):   # "apa tengok" is how he says "kau tengok"
    nxt = kept[i + 1]["text"].lower().strip(".,?!") if i + 1 < len(kept) else ""
    if w["text"].lower().strip(".,?!") == "apa" and nxt in {"boleh", "nak", "tengok", "buka", "tekan"}:
        w["text"] = ("Kau" if w["text"][:1].isupper() else "kau") + w["text"][3:]

sents, cur = [], []
for i, w in enumerate(kept):
    cur.append(w)
    nxt = kept[i + 1] if i + 1 < len(kept) else None
    if nxt is None or nxt["seg"] != w["seg"] or re.search(r"[.?!]$", w["text"]) or nxt["start"] - w["end"] > 0.35:
        sents.append(cur); cur = []
merged = []
for snt in sents:
    if merged and len(merged[-1]) == 1 and merged[-1][0]["seg"] == snt[0]["seg"] and snt[0]["start"] - merged[-1][0]["end"] < 0.6:
        merged[-1] = merged[-1] + snt
    else:
        merged.append(snt)


def even_chunks(ws):
    k = math.ceil(len(ws) / 3)
    base, extra = divmod(len(ws), k)
    out_, i = [], 0
    for j in range(k):
        n = base + (1 if j < extra else 0)
        out_.append(ws[i:i + n]); i += n
    return out_


phrases = []
for snt in merged:
    clauses, c = [], []
    for w in snt:
        c.append(w)
        if w["text"].endswith(","):
            clauses.append(c); c = []
    if c:
        clauses.append(c)
    packed = []
    for cl in clauses:
        if packed and len(packed[-1]) + len(cl) <= 3 and (len(cl) == 1 or len(packed[-1]) == 1):
            packed[-1] = packed[-1] + cl
        else:
            packed.append(cl)
    for cl in packed:
        phrases += even_chunks(cl)

CHIP_Y = {"top": 440, "low": 1330}
CAP_ZONE_Y = {"top": 615, "low": 1450}
cap_items, cap_js = [], []
for i, ph in enumerate(phrases):
    s0 = fr(ph[0]["start"])
    nxt = phrases[i + 1][0]["start"] if i + 1 < len(phrases) else TOTAL
    same_seg_next = i + 1 < len(phrases) and phrases[i + 1][0]["seg"] == ph[0]["seg"]
    en = fr(min(max(ph[-1]["end"] + 0.25, s0 + 0.7), nxt if same_seg_next else min(nxt, end(ph[0]["seg"])), TOTAL))
    if en - s0 < 0.2:
        continue
    text = re.sub(r"[.,!?]", "", " ".join(w["text"] for w in ph)).upper()
    cid = f"cp{i:03d}"
    cy = CAP_ZONE_Y[SEG[ph[0]["seg"]]["zone"]]
    cap_items.append(f'    <div id="{cid}" class="cw clip" data-start="{s0}" data-duration="{fr(en - s0)}" data-track-index="0" style="top:{cy}px">'
                     f'<span id="{cid}s">{html.escape(text)}</span></div>')
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }}, {s0});')

# ---------------------------------------------------------------- tokens + pieces
TOK = """
      --ink: #ffffff;
      --dark: #0d0e10;
      --neon: #ff8a1f;
      --glass: rgba(16, 17, 20, 0.80);
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
    .glass {{ position: absolute; background: var(--glass); border: 1.5px solid var(--stroke); border-radius: 30px;
      box-shadow: 0 24px 60px rgba(0,0,0,.5); backdrop-filter: blur(18px); color: #fff; font-family: var(--font-ui); }}
    .head {{ position: absolute; left: 0; width: 960px; text-align: center; font-family: var(--font-ui); font-weight: 800; color: #fff;
      font-size: 62px; line-height: 1.1; text-shadow: 0 0 4px rgba(0,0,0,.9), 0 3px 8px rgba(0,0,0,.75), 0 10px 34px rgba(0,0,0,.75); }}
    .head > div {{ display: inline-block; padding: 14px 30px; border-radius: 26px; background: rgba(10,11,13,.42); }}
    .head em {{ font-style: normal; color: var(--neon); }}
    .pilltag {{ display: inline-flex; align-items: center; gap: 10px; padding: 10px 26px 10px 16px; border-radius: 12px; background: rgba(255,255,255,.95);
      color: #111; font-family: var(--font-ui); font-weight: 700; font-size: 34px; box-shadow: 0 10px 28px rgba(0,0,0,.35); white-space: nowrap; }}
"""
I = {
    "spin": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v4h-4"/></svg>',
    "brush": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14l8-8 8 8"/><path d="M6 14v5M9 14v6M12 14v6M15 14v6M18 14v5"/></svg>',
    "drop": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/></svg>',
    "watch": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5.5"/><path d="M9 6.8L9.6 2.5h4.8l.6 4.3M9 17.2l.6 4.3h4.8l.6-4.3M12 10v2l1.3 1"/></svg>',
    "call": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1z"/></svg>',
    "dial": '<svg viewBox="0 0 24 24" fill="#fff"><circle cx="6" cy="5" r="1.8"/><circle cx="12" cy="5" r="1.8"/><circle cx="18" cy="5" r="1.8"/><circle cx="6" cy="11" r="1.8"/><circle cx="12" cy="11" r="1.8"/><circle cx="18" cy="11" r="1.8"/><circle cx="6" cy="17" r="1.8"/><circle cx="12" cy="17" r="1.8"/><circle cx="18" cy="17" r="1.8"/><circle cx="12" cy="22" r="1.4"/></svg>',
    "contact": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="3.5"/><path d="M5 20c.8-3.6 3.6-5.5 7-5.5s6.2 1.9 7 5.5"/></svg>',
    "image": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2.5"/><circle cx="9" cy="9.5" r="1.8"/><path d="M21 16l-5-5-8 9"/></svg>',
    "run": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="14" cy="4" r="1.8"/><path d="M8 21l3-6 3 2v5M6 11l3-3 4 1 3 4 3 1M11 15l-1-5"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M12 20.5s-7.5-4.6-7.5-10A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.9c0 5.4-7.5 10-7.5 10z"/></svg>',
    "box2": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7.5l9-4.5 9 4.5v9l-9 4.5-9-4.5z"/><path d="M3 7.5l9 4.5 9-4.5M12 12v9"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12.2l2.2 2.2 4.4-4.6"/></svg>',
    "power": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><path d="M12 3v8"/><path d="M6.3 6.8a8 8 0 1 0 11.4 0"/></svg>',
    "battery": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="16" height="10" rx="2"/><path d="M21 10.5v3"/><path d="M6 10v4M9 10v4M12 10v4" stroke-width="2.4"/></svg>',
    "oil": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/></svg>',
    "plug": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3v5M15 3v5"/><path d="M6 8h12v3a6 6 0 0 1-12 0z"/><path d="M12 17v4"/></svg>',
    "box": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="11" rx="2"/><path d="M9 8V5.5h6V8M3 12.5h18"/></svg>',
    "chain": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1 1"/><path d="M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1-1"/></svg>',
    "tool": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4l6 6-2 2-6-6z"/><path d="M12 8l-8.5 8.5a1.8 1.8 0 0 0 2.5 2.5L14.5 10.5"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>',
    "tag": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12V4h8l10 10-8 8z"/><circle cx="7.5" cy="8.5" r="1.4" fill="#fff"/></svg>',
}
STAR = '<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>'


def clip(cid, start, dur, inner, cls="", style="", extra=""):
    return (f'    <div id="{cid}" class="{cls} clip" data-start="{fr(start)}" data-duration="{fr(dur)}" '
            f'data-track-index="0" style="{style}"{extra}>{inner}</div>')


def out(sel, t):
    return f'    tl.to("{sel}", {{ opacity: 0, y: -10, duration: 0.35, ease: "power2.inOut" }}, {fr(t - 0.37)});'


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


def chip(cid, label, icon, start, dur, y, x=None):
    ic = f'<span id="{cid}c" class="ic">{I[icon]}</span>'
    lb = f'<span id="{cid}b" class="lb">{label}</span>'
    style = f"top:{y}px" + (f"; left:{x}px; width:auto; text-align:left" if x is not None else "")
    body = clip(cid, start, dur, f'<span>{ic}{lb}</span>', cls="chip", style=style)
    js = "\n".join([
        f'    tl.fromTo("#{cid}c", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }}, {fr(start)});',
        f'    tl.fromTo("#{cid}b", {{ opacity: 0, x: -20 }}, {{ opacity: 1, x: 0, duration: 0.55, ease: "power3.out" }}, {fr(start + 0.08)});',
        out(f"#{cid}", start + dur)])
    return body, js


def head(cid, text, start, dur, y):
    body = clip(cid, start, dur, f'<div id="{cid}t">{text}</div>', cls="head", style=f"top:{y}px")
    js = "\n".join([f'    tl.fromTo("#{cid}t", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def img_card(cid, src, label, start, dur, x, y, w=340, crop=None):
    """crop=(height, object-position) shows a window of a tall image"""
    img = (f'<img src="{src}" alt="" style="display:block;width:{w}px;height:{crop[0]}px;object-fit:cover;object-position:{crop[1]}"/>' if crop
           else f'<img src="{src}" alt="" style="display:block;width:{w}px"/>')
    lab = f'<div style="margin-top:12px;text-align:center"><span class="pilltag">{label}</span></div>' if label else ""
    inner = f'<div style="border-radius:22px;overflow:hidden;border:3px solid rgba(255,255,255,.9);box-shadow:0 24px 60px rgba(0,0,0,.5)">{img}</div>{lab}'
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{x}px; top:{y}px; width:{w}px")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 30, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power3.out" }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


# ---------------------------------------------------------------- scenes


def Y(sid):
    return CHIP_Y[SEG[sid]["zone"]]


def IMG(cid, src, sid, t0, t1, w=300):
    """side product card: on the wall (right, under the chip) in top zone, beside the body in low zone"""
    return img_card(cid, src, None, t0, t1 - t0, 50, 420, w=w)


def photo_insert(cid, src, start, dur, w=880):
    """full-screen cut-away: footage dims, a big white product-photo card eases in"""
    body = clip(cid, start, dur,
                f'<div id="{cid}bg" style="position:absolute;inset:0;background:rgba(8,9,12,.72)"></div>'
                f'<div id="{cid}c" style="position:absolute;left:{(960 - w) // 2 + 60}px;top:600px;width:{w}px;border-radius:30px;overflow:hidden;'
                f'background:#fff;box-shadow:0 30px 80px rgba(0,0,0,.6)"><img src="{src}" alt="" style="display:block;width:{w}px"/></div>',
                style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}bg", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power2.out" }}, {fr(start)});',
                    f'    tl.fromTo("#{cid}c", {{ opacity: 0, y: 40, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power3.out" }}, {fr(start + 0.05)});',
                    f'    tl.to("#{cid}", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {fr(start + dur - 0.32)});'])
    return body, js


def opt(ids, f):
    return f() if all(i in SEG for i in ids) else None


def C(cid, label, icon, sid, t0, t1=None):
    t1 = end(sid) if t1 is None else t1
    return chip(cid, label, icon, t0, t1 - t0, Y(sid))


V = VARIANT
PARTS = {
    "1": lambda: [
        head("hk", "Wajib ada<br/><em>dalam kereta</em>", 0.3, W("a1", 4.9) - 0.1, 1290),
        C("c-jimat", "Jimat masa &amp; tenaga", "star", "a1", W("a1", 5.64), W("a1", 9.14)),
        C("c-btn", "Ada button auto", "spin", "a1", W("a1", 9.14)),
        IMG("i-1t", "assets/img/onetouch.jpg", "a2", st("a2") + 0.2, W("a2", 15.1)),
        C("c-tekan", "1 tekan, terus buka", "spin", "a2", W("a2", 12.06), W("a2", 15.1)),
        C("c-ruang", "Jimat ruang", "star", "a2", W("a2", 15.1)),
    ],
    "2": lambda: [
        head("hk", "Nampak<br/><em>premium</em>", 0.3, W("c1", 6.78) - 0.1, 1290),
        C("c-btn", "Ada button", "spin", "c1", W("c1", 8.32), W("c1", 11.5)),
        C("c-cantik", "Buka pun cantik", "star", "c1", W("c1", 11.5), W("c1", 12.8)),
        C("c-kain", "Kain tebal", "star", "c1", W("c1", 12.8), W("c1", 15.04)),
        C("c-uv", "Lindung UV", "star", "c1", W("c1", 15.04), W("c1", 20.4)),
        C("c-fiber", "Fiber bone, tak mudah patah", "brush", "c1", W("c1", 20.4)),
        IMG("i-hero", "assets/img/onetouch.jpg", "c1", W("c1", 20.4) + 0.2, end("c2"), w=320),
        C("c-tutup", "Tekan, terus tutup", "spin", "c3", W("c3", 29.2), W("c3", 30.88)),
        C("c-basah", "Masuk kereta tak basah", "drop", "c3", W("c3", 30.88)),
    ],
    "3": lambda: [
        head("hk", "Hujan?<br/><em>Jangan risau</em>", 0.2, end("d0") + 0.4, 1290),
        C("c-magic", "Payung magic", "star", "d1", st("d1") + 0.6),
        C("c-tekan", "Tekan button", "spin", "d2", W("d2", 15.94), W("d2", 18.2)),
        C("c-auto", "Buka auto", "spin", "d2", W("d2", 18.2)),
        C("c-kering", "Tak basah pun", "drop", "d3", W("d3", 23.8)),
        C("c-masuk", "Masuk kereta dulu", "drop", "d4", W("d4", 27.68)),
        C("c-tutup", "Tutup automatik", "spin", "d5", W("d5", 32.46)),
        C("c-baloi", "Memang berbaloi", "star", "cta", st("cta") + 0.1, W("cta", 38.14)),
    ],
    "4": lambda: [
        head("hk", "Viral<br/><em>kat TikTok</em>", 0.2, end("e1") + 0.6, 1290),
        C("c-btn", "Ada button", "spin", "e2", W("e2", 8.65), W("e2", 12.35)),
        C("c-auto", "Auto buka", "spin", "e2", W("e2", 12.35), W("e2", 14.01)),
        C("c-cun", "Memang cun", "star", "e2", W("e2", 14.01), W("e2", 15.41)),
        C("c-fiber", "Ada fiber bone", "brush", "e2", W("e2", 15.41)),
        IMG("i-hero", "assets/img/onetouch.jpg", "e2", W("e2", 15.41) + 0.2, end("e3"), w=320),
        C("c-ribut", "Tahan ribut", "drop", "e4", st("e4") + 0.1),
        C("c-tutup", "Tekan je, terus tutup", "spin", "e5", W("e5", 26.69)),
    ],
    "5": lambda: [
        head("hk", "1 tekan<br/><em>terus terbuka</em>", 0.2, end("h") + 0.4, 1290),
        C("c-1t", "1 Touch Automatic", "spin", "b1", st("b1") + 0.3),
        C("c-jimat", "Jimat masa, ruang, tenaga", "star", "v1", st("v1") + 0.1),
        C("c-uv", "Lindung UV", "star", "v2", st("v2") + 0.1),
        C("c-fiber", "Fiber bone, tak mudah patah", "brush", "v3", st("v3") + 0.1),
        C("c-125", "Stormproof, tahan ribut", "drop", "b2", st("b2") + 0.1),
        IMG("i-hero", "assets/img/onetouch.jpg", "b2", st("b2") + 0.2, end("b2"), w=320),
        C("c-tutup", "Tutup automatik", "spin", "v4", st("v4") + 0.4),
    ],
    "6": lambda: [
        head("hk", "Payung<br/><em>2 saiz</em>", 0.2, end("b0") - 0.1, 1290),
        C("c-magic", "Memang best", "star", "v1", st("v1") + 0.3),
        C("c-kain", "Kain tebal", "star", "v2", st("v2") + 0.1),
        photo_insert("p-size", "assets/img/size.jpg", st("b1") + 0.1, end("b1") - st("b1") - 0.1),
        C("c-xl", "Ada 2 saiz", "drop", "b1", st("b1") + 0.2),
        C("c-cun", "Krim &amp; hitam", "heart", "v3", st("v3") + 0.1),
        C("c-baloi", "Keluar masuk kereta, berbaloi", "star", "v4", st("v4") + 0.1),
    ],
}
build_scene("sc", PARTS[V]())

shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:18px 20px">'
        f'<div style="width:120px;height:120px;border-radius:24px;background:#fff;flex:none;'
        f'overflow:hidden"><img src="assets/img/pack.jpg" alt="" style="width:120px;height:120px;object-fit:cover"/></div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:38px">PAYUNG AUTO STORMPROOF</div>'
        f'<div style="margin-top:6px;display:flex;align-items:center;gap:10px;font-weight:700;font-size:30px;color:rgba(255,255,255,.85)">{STAR.replace("<svg", "<svg width=30 height=30")} 4.8 &middot; 1.2M terjual</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:12px;padding:16px 36px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:44px;white-space:nowrap;box-shadow:0 14px 36px rgba(0,0,0,.45)">'
       '<svg viewBox="0 0 24 24" width="40" height="40" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Tekan link sekarang</div>')
SHOP0 = st("cta") + 0.05
CTA0 = st("cta") + 0.6
build_scene("outro", [
    (clip("ot-shop", SHOP0, TOTAL - SHOP0, shop, cls="glass", style="left:110px; top:1040px; width:740px"),
     "\n".join([f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {SHOP0});',
                ])),
    (clip("ot-cta", CTA0, TOTAL - CTA0, cta, style="position:absolute; left:0; width:960px; top:1225px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.5)" }}, {fr(CTA0 + 0.2)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: 3, immediateRender: false }}, {fr(CTA0 + 0.9)});'])),
])

# ---- creator / product header, on screen the whole video (like the reference)
HEAD_L = ("REZEKI.NAZIR", "TRUSTED AFFILIATE")
HEAD_R = ("A BIG HOME LIVING", "PAYUNG AUTO")
hdr = (f'<div id="hd-l" style="position:absolute;left:84px;top:252px;display:flex;align-items:stretch;gap:16px">'
       f'<div style="width:7px;border-radius:4px;background:linear-gradient(180deg,#f3dfb1,#c9a25e 55%,#8f6a32)"></div>'
       f'<div class="hdt">{HEAD_L[0]}<br/>{HEAD_L[1]}</div></div>'
       f'<div id="hd-r" class="hdt" style="position:absolute;right:94px;top:252px;text-align:right">{HEAD_R[0]}<br/>{HEAD_R[1]}</div>')
write("brand.html", scene("brand", BASE + """
    .hdt { font-family: var(--font-ui); font-weight: 600; font-size: 29px; line-height: 1.22; letter-spacing: .05em; color: #f6f1e7;
      text-shadow: 0 0 2px rgba(0,0,0,.95), 0 1px 3px rgba(0,0,0,.9), 0 0 10px rgba(0,0,0,.7), 0 2px 18px rgba(0,0,0,.6); white-space: nowrap; }
""", clip("hd", 0, TOTAL, hdr, style="position:absolute; inset:0"),
    f'    tl.fromTo(["#hd-l", "#hd-r"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, 0.1);'))

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 900; font-size: 48px; color: #fff; letter-spacing: .01em;
      text-shadow: 0 0 3px rgba(0,0,0,.9), 0 2px 0 rgba(0,0,0,.5), 0 4px 18px rgba(0,0,0,.8); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="{SRC[s["src"]]}" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="{s["vol"]}" data-fade-in="0.06" data-fade-out="0.1" playsinline></video>' for s in segs]
cam = [f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.035, duration: {fr(s["dur"])}, ease: "none", immediateRender: false }}, {s["start"]});' for s in segs]

import re as _re
SFX = [("sx-hk", "whoosh.mp3", 0.3, 0.2)]
for m in _re.finditer(r'id="(c-[a-z0-9-]+)" class="chip clip" data-start="([0-9.]+)"', open(os.path.join(P, "compositions", "sc.html")).read()):
    SFX.append((f"sx-{m.group(1)}", "pop.mp3", float(m.group(2)), 0.2))
for m in _re.finditer(r'id="(p-[a-z0-9-]+)" class=" clip" data-start="([0-9.]+)"', open(os.path.join(P, "compositions", "sc.html")).read()):
    SFX.append((f"sx-{m.group(1)}", "whoosh-short.mp3", float(m.group(2)), 0.2))
SFX += [("sx-shop", "whoosh-short.mp3", SHOP0, 0.2), ("sx-cta", "sparkle.mp3", CTA0 + 0.2, 0.3)]


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

hosts = [("sc", 2), ("outro", 7), ("captions", 8), ("brand", 9)]
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
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 50%; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: kept takes from raw_a..raw_e.mp4. Trim in Studio by dragging clip edges. -->
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
json.dump(dict(total=TOTAL, segs=segs, phrases=[" ".join(w["text"] for w in p) for p in phrases]), open(os.path.join(P, ".edl.json"), "w"), indent=1, ensure_ascii=False)
print(f"total={TOTAL}s segments={len(segs)} caption phrases={len(cap_items)}")
for s in segs:
    print(f'{s["id"]} {s["src"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}')
print(" | ".join(" ".join(w["text"] for w in p) for p in phrases))
