#!/usr/bin/env python3
"""Realfit smartwatch — two short videos in the reference style (white label chips + round black icon, glass cards, neon accent),
calm pacing: lines kept whole with breathing room, phrase captions, soft long-held overlays, no zoom jumps.
Usage: python3 -I build.py <words.json> <project_dir> <1|2>   (1 = design & daily use, 2 = health & features)
       words are for raw.mp4 (the talking review); wear.mp4 is the wordless 'watch appears on the wrist' clip
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(WJ))
SRC = {"v": "assets/raw.mp4", "h": "assets/wear.mp4"}
PAD_IN, PAD_OUT = 0.18, 0.30


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(t):
    return min(WORDS, key=lambda w: abs(w["start"] - t))


# (id, src, first_word_start | src_in, last_word_start | src_out, volume)   — b-roll rows give raw in/out seconds
VARIANT = sys.argv[3] if len(sys.argv) > 3 else "1"
# (id, src, first_word_start | src_in, last_word_start | src_out, volume, {optional "in"/"out" overrides})
VARIANTS = {
    # video 1: design & daily use
    "1": [
        ("h0", "h", 6.80, 11.40, 0.35),                 # hook: the watch appears on the wrist
        ("a1", "v", 0.18, 7.54, 1.0),                   # jam realfit tau, daripada realfit, dia bagi dengan tiga tali, kau boleh tukar-tukar dia
        ("a2", "v", 12.30, 15.00, 1.0, {"in": 9.80, "out": 15.62}),  # (strap swap) memang lawa, cara nak pakai dia pun cukup mudah
        ("a3", "v", 28.28, 35.88, 1.0),                 # boleh jawab call, nak dial apa semua boleh, boleh tengok call record, contact pun semua boleh masuk kat sini
        ("a4", "v", 49.14, 55.30, 1.0, {"in": 49.00, "out": 55.62}),                 # tak mau ni, kau boleh tekan yang mana kau nak, dia boleh bubuh juga gambar, wallpaper
        ("a5", "v", 83.18, 91.06, 1.0, {"in": 83.10}),                 # dia bagi dengan 3 tali, ni tali jenis kulit, ni tali original dia, dia bagi dengan manual, charger pun ada kat sini
        ("a6", "v", 94.02, 95.80, 1.0, {"out": 96.10}), # nak dapat mana, tekan link
        ("e1", "h", 9.00, 11.60, 0.3),                  # end card on the watch
    ],
    # video 2: health & features
    "2": [
        ("t1", "v", 42.16, 45.06, 1.0, {"in": 42.05, "out": 45.45}), # kau boleh tekan treadmill ke apa kan, tiga dua satu
        ("t2", "v", 36.18, 41.10, 1.0, {"in": 36.10}),                 # lepas tu sports mode pun boleh, sport dia dekat seratus lebih tau
        ("t3", "v", 56.50, 59.66, 1.0, {"in": 56.40, "out": 60.05}), # masuk sleep, heart rate, semua boleh tengok, ni tahap stress
        ("t4", "v", 61.40, 73.78, 1.0, {"in": 61.30}),                 # weather, camera, muzik ... lampu SOS, find phone, bluetooth je
        ("t5", "v", 74.14, 75.88, 1.0),                 # so memang terbaik lah
        ("t6", "v", 94.02, 95.80, 1.0, {"out": 96.10}), # nak dapat mana, tekan link
        ("e2", "h", 6.80, 11.40, 0.3),                  # end card: the watch appears on the wrist
    ],
}
EDL = VARIANTS[VARIANT]

segs, f = [], 0
for sid, src, a, b, vol, *ob in EDL:
    o = ob[0] if ob and isinstance(ob[0], dict) else ({"out": ob[0]} if ob else {})
    if src == "v":
        w0, w1 = wat(a), wat(b)
        i0, i1 = WORDS.index(w0), WORDS.index(w1)
        prev_end = WORDS[i0 - 1]["end"] if i0 > 0 else 0
        next_start = WORDS[i1 + 1]["start"] if i1 + 1 < len(WORDS) else 1e9
        a = max(w0["start"] - PAD_IN, prev_end + 0.04) if i0 > 0 else max(0, w0["start"] - PAD_IN)
        b = min(w1["end"] + PAD_OUT, next_start - 0.06)
        a = o.get("in", a)
        b = o.get("out", b)
    fa, fb = round(a * FPS), round(b * FPS)
    segs.append(dict(id=sid, src=src, src_in=fa / FPS, src_out=fb / FPS, start=f / FPS, dur=(fb - fa) / FPS, vol=vol))
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
    return at(sid, wat(t)["start"])


# ---------------------------------------------------------------- phrase captions
FIX = {"main": "bagi", "dice": "dial", "mistake": "sports", "spot": "sport", "musik": "muzik", "3": "tiga", "kalender": "kalendar"}
DROP = {"haa", "ha", "tau", "eh", "okay", "terima", "kasih"}


def norm(w):
    t = w["text"]
    core = re.sub(r"[^\w]", "", t).lower()
    if core in DROP:
        return None
    if core in FIX:
        rep = FIX[core]
        if t[:1].isupper():
            rep = rep.capitalize()
        return rep + t[len(t.rstrip(".,!?")):]
    return t


kept = []
for s in segs:
    if s["src"] != "v":
        continue
    for w in WORDS:
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05:
            txt = norm(w)
            if txt:
                kept.append(dict(text=txt, start=at(s["id"], w["start"]), end=at(s["id"], min(w["end"], s["src_out"])), seg=s["id"]))
glued = []
for w in kept:   # "screw" + "driver", "Harga" + "-harga"
    if glued and glued[-1]["seg"] == w["seg"] and (w["text"].startswith("-") or (glued[-1]["text"].lower() == "screw" and w["text"].lower().startswith("driver"))):
        glued[-1]["text"] += w["text"]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued
for i, w in enumerate(kept):   # "apa boleh / apa nak" is how he says "kau boleh / kau nak"
    nxt = kept[i + 1]["text"].lower().strip(".,?!") if i + 1 < len(kept) else ""
    if w["text"].lower().strip(".,?!") == "apa" and nxt in {"boleh", "nak", "tengok"}:
        w["text"] = ("Kau" if w["text"][:1].isupper() else "kau") + w["text"][3:]
glued = []
for w in kept:                # "stock" + "watch" -> "stopwatch"
    if glued and glued[-1]["seg"] == w["seg"] and glued[-1]["text"].lower() == "stock" and w["text"].lower().startswith("watch"):
        glued[-1]["text"] = "stopwatch" + w["text"][5:]; glued[-1]["end"] = w["end"]
    else:
        glued.append(w)
kept = glued

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

# caption height per take: above the watch screen on wrist close-ups, under the watch when the face is at the top
CAP_Y = {"a1": 1180}
CAP_DEFAULT = 530 if VARIANT == "1" else 670
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
    cy = CAP_Y.get(ph[0]["seg"], CAP_DEFAULT)
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
# talking shots: face ~y 250-600, chainsaw at chest; overlays sit over the legs (y 960-1150), captions below at 1230
LOW = 1040      # chips over the strap / lower wrist when the face is at the top (a1)
TOPC = 370      # chips over the shirt above the watch on wrist close-ups (header sits above at y 200)
SIDE_Y = 760

G_ICONS = {
    "Cuaca": '<path d="M7 17h10a4 4 0 0 0 0-8 5.5 5.5 0 0 0-10.6 1.6A3.3 3.3 0 0 0 7 17z" fill="none" stroke="#fff" stroke-width="2"/>',
    "Kamera": '<rect x="3" y="7" width="18" height="13" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><circle cx="12" cy="13.5" r="3.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M8.5 7l1.5-3h4l1.5 3" fill="none" stroke="#fff" stroke-width="2"/>',
    "Muzik": '<path d="M9 18V5l11-2v13" fill="none" stroke="#fff" stroke-width="2"/><circle cx="6.5" cy="18" r="2.5" fill="#fff"/><circle cx="17.5" cy="16" r="2.5" fill="#fff"/>',
    "Alarm": '<circle cx="12" cy="13" r="7" fill="none" stroke="#fff" stroke-width="2"/><path d="M12 9v4l2.5 2M4 5l3-2.5M20 5l-3-2.5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
    "Stopwatch": '<circle cx="12" cy="14" r="7" fill="none" stroke="#fff" stroke-width="2"/><path d="M12 14V10M10 3h4M12 3v4" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
    "Kalendar": '<rect x="3" y="5" width="18" height="16" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
    "Kalkulator": '<rect x="5" y="3" width="14" height="18" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M8 7h8M8.5 12h.01M12 12h.01M15.5 12h.01M8.5 16h.01M12 16h.01M15.5 16h.01" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>',
    "Saham": '<path d="M3 20h18M5 16l4-5 4 3 6-8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>',
    "SOS": '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9V16h7v-2.1A6 6 0 0 0 12 3z" fill="none" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>',
    "Cari phone": '<rect x="7" y="2.5" width="10" height="19" rx="2.5" fill="none" stroke="#fff" stroke-width="2"/><path d="M11 18.5h2" stroke="#fff" stroke-width="2" stroke-linecap="round"/>',
}


def feature_grid(cid, items, start, dur, y):
    """glass card; each app tile lights up as he names it"""
    tiles = "".join(f'<div id="{cid}{k}" style="width:146px;text-align:center;margin:8px 4px">'
                    f'<div style="width:84px;height:84px;margin:0 auto;border-radius:24px;background:linear-gradient(150deg,#ff9a3c,#ff6a1a);display:flex;align-items:center;justify-content:center;box-shadow:0 8px 22px rgba(0,0,0,.35)">'
                    f'<svg viewBox="0 0 24 24" width="46" height="46">{G_ICONS[lbl]}</svg></div>'
                    f'<div style="margin-top:8px;font-weight:700;font-size:26px;color:#fff;white-space:nowrap">{lbl}</div></div>'
                    for k, (lbl, _) in enumerate(items))
    inner = f'<div style="display:flex;flex-wrap:wrap;justify-content:center;padding:18px 12px">{tiles}</div>'
    body = clip(cid, start, dur, inner, cls="glass", style=f"left:70px; top:{y}px; width:820px")
    js = [f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {fr(start)});',
          f'    tl.set([{", ".join(chr(34) + f"#{cid}{k}" + chr(34) for k in range(len(items)))}], {{ opacity: 0.18 }}, {fr(start)});']
    js += [f'    tl.to("#{cid}{k}", {{ opacity: 1, duration: 0.35, ease: "power2.out" }}, {fr(t)});' for k, (_, t) in enumerate(items)]
    js.append(out(f"#{cid}", start + dur))
    return body, "\n".join(js)


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


def scene_opt(name, parts):
    build_scene(name, [p for p in parts if p])


# ---- video 1
scene_opt("sc1", [
    opt(["h0"], lambda: head("hk-h", "Jam pintar<br/><em>Realfit</em>", 0.3, end("h0") - 0.3, 380)),
    opt(["a1"], lambda: chip("a1-tali", "3 tali, boleh tukar", "watch", W("a1", 5.42), end("a1") - W("a1", 5.42) + 0.1, LOW)),
    opt(["a2"], lambda: chip("a2-lawa", "Memang lawa", "star", W("a2", 12.30), W("a2", 13.54) - W("a2", 12.30), TOPC)),
    opt(["a2"], lambda: chip("a2-mudah", "Senang pakai", "watch", W("a2", 13.54), end("a2") - W("a2", 13.54), TOPC)),
    opt(["a2"], lambda: img_card("a2-img", "assets/img/bezel.jpg", None, W("a2", 13.54) + 0.2, end("a2") - W("a2", 13.54) - 0.2, 660, 470, w=240)),
    opt(["a3"], lambda: chip("a3-call", "Jawab call", "call", W("a3", 28.28), W("a3", 31.08) - W("a3", 28.28), TOPC)),
    opt(["a3"], lambda: chip("a3-dial", "Dail terus", "dial", W("a3", 31.08), W("a3", 33.36) - W("a3", 31.08), TOPC)),
    opt(["a3"], lambda: chip("a3-rec", "Rekod call &amp; contact", "contact", W("a3", 33.36), end("a3") - W("a3", 33.36), TOPC)),
    opt(["a4"], lambda: photo_insert("a4-faces", "assets/img/faces.jpg", W("a4", 50.72) - 0.1, W("a4", 53.80) - W("a4", 50.72) + 0.1)),
    opt(["a4"], lambda: photo_insert("a4-photo", "assets/img/photoface.jpg", W("a4", 53.80), end("a4") - W("a4", 53.80) + 0.9)),
    opt(["a4"], lambda: chip("a4-wall", "200+ muka jam", "image", W("a4", 50.72), W("a4", 53.80) - W("a4", 50.72), TOPC)),
    opt(["a4"], lambda: chip("a4-own", "Letak gambar sendiri", "image", W("a4", 53.80), end("a4") - W("a4", 53.80) + 0.9, TOPC)),
    opt(["a5"], lambda: chip("a5-tali", "3 tali: kulit &amp; original", "watch", max(W("a5", 83.70), st("a5") + 1.0), W("a5", 87.50) - max(W("a5", 83.70), st("a5") + 1.0), TOPC)),
    opt(["a5"], lambda: chip("a5-box", "Manual + charger", "box2", W("a5", 87.50), end("a5") - W("a5", 87.50), TOPC)),
])

# ---- video 2
scene_opt("sc2", [
    opt(["t1"], lambda: head("t1-h", "Treadmill?<br/><em>Tekan je</em>", 0.3, end("t1") - 0.3, 370)),
    opt(["t2"], lambda: img_card("t2-img", "assets/img/sports.jpg", None, W("t2", 37.42), end("t2") - W("t2", 37.42), 180, 340, w=600)),
    opt(["t2"], lambda: chip("t2-100", "100+ mod sukan", "run", W("t2", 39.72), end("t2") - W("t2", 39.72) + 0.1, TOPC + 200)),
    opt(["t3"], lambda: img_card("t3-img", "assets/img/health.jpg", None, st("t3") + 0.1, end("t3") - st("t3") - 0.1, 180, 340, w=600)),
    opt(["t3"], lambda: chip("t3-hr", "Tidur, jantung &amp; stres", "heart", W("t3", 57.20), end("t3") - W("t3", 57.20) + 0.1, TOPC + 200)),
    opt(["t4"], lambda: feature_grid("t4-g", [("Cuaca", W("t4", 61.40)), ("Kamera", W("t4", 62.64)), ("Muzik", W("t4", 63.46)), ("Alarm", W("t4", 65.52)),
                                              ("Stopwatch", W("t4", 66.32)), ("Kalendar", W("t4", 67.12)), ("Kalkulator", W("t4", 68.02)), ("Saham", W("t4", 69.26)),
                                              ("SOS", W("t4", 70.42)), ("Cari phone", W("t4", 72.64))], st("t4") + 0.05, end("t4") - st("t4") - 0.05, 370)),
    opt(["t5"], lambda: chip("t5-best", "Memang terbaik", "star", W("t5", 74.96), end("t5") - W("t5", 74.96) + 0.1, TOPC)),
])

shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:18px 20px">'
        f'<div style="width:120px;height:120px;border-radius:24px;background:#fff;flex:none;'
        f'overflow:hidden"><img src="assets/img/bezel.jpg" alt="" style="width:120px;height:120px;object-fit:cover"/></div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:38px">JAM PINTAR REALFIT</div>'
        f'<div style="margin-top:6px;display:flex;align-items:center;gap:10px;font-weight:700;font-size:30px;color:rgba(255,255,255,.85)">{STAR.replace("<svg", "<svg width=30 height=30")} 4.9 &middot; 95.5K terjual</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:12px;padding:16px 36px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:44px;white-space:nowrap;box-shadow:0 14px 36px rgba(0,0,0,.45)">'
       '<svg viewBox="0 0 24 24" width="40" height="40" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Tekan link sekarang</div>')
SHOP0 = st("a6" if "a6" in SEG else "t6") + 0.05
CTA0 = st("e1" if "e1" in SEG else "e2")
build_scene("outro", [
    (clip("ot-shop", SHOP0, TOTAL - SHOP0, shop, cls="glass", style="left:110px; top:360px; width:740px"),
     "\n".join([f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {SHOP0});',
                ])),
    (clip("ot-cta", CTA0, TOTAL - CTA0, cta, style="position:absolute; left:0; width:960px; top:1180px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.5)" }}, {fr(CTA0 + 0.2)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: 3, immediateRender: false }}, {fr(CTA0 + 0.9)});'])),
])

# ---- creator / product header, on screen the whole video (like the reference)
HEAD_L = ("REZEKI.NAZIR", "TRUSTED AFFILIATE")
HEAD_R = ("REALFIT", "AMOLED SMART WATCH")
hdr = (f'<div id="hd-l" style="position:absolute;left:84px;top:252px;display:flex;align-items:stretch;gap:16px">'
       f'<div style="width:7px;border-radius:4px;background:linear-gradient(180deg,#f3dfb1,#c9a25e 55%,#8f6a32)"></div>'
       f'<div class="hdt">{HEAD_L[0]}<br/>{HEAD_L[1]}</div></div>'
       f'<div id="hd-r" class="hdt" style="position:absolute;right:94px;top:252px;text-align:right">{HEAD_R[0]}<br/>{HEAD_R[1]}</div>')
write("brand.html", scene("brand", BASE + """
    .hdt { font-family: var(--font-ui); font-weight: 600; font-size: 29px; line-height: 1.22; letter-spacing: .05em; color: #f6f1e7;
      text-shadow: 0 1px 2px rgba(0,0,0,.7), 0 2px 12px rgba(0,0,0,.55); white-space: nowrap; }
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

SFX_ALL = [
    (["h0"], lambda: ("sx-h", "whoosh.mp3", 0.3, 0.2)),
    (["a1"], lambda: ("sx-tali", "pop.mp3", W("a1", 5.42), 0.2)),
    (["a2"], lambda: ("sx-lawa", "pop.mp3", W("a2", 12.30), 0.2)),
    (["a2"], lambda: ("sx-mudah", "pop.mp3", W("a2", 13.54), 0.2)),
    (["a3"], lambda: ("sx-call", "pop.mp3", W("a3", 28.28), 0.2)),
    (["a3"], lambda: ("sx-dial", "click-soft.mp3", W("a3", 31.08), 0.3)),
    (["a3"], lambda: ("sx-rec", "pop.mp3", W("a3", 33.36), 0.2)),
    (["a4"], lambda: ("sx-wall", "pop.mp3", W("a4", 50.72), 0.2)),
    (["a5"], lambda: ("sx-tali2", "pop.mp3", W("a5", 83.70), 0.2)),
    (["a5"], lambda: ("sx-box", "pop.mp3", W("a5", 87.50), 0.2)),
    (["t1"], lambda: ("sx-t1", "whoosh.mp3", 0.3, 0.2)),
    (["t2"], lambda: ("sx-t2", "whoosh-short.mp3", W("t2", 37.42), 0.2)),
    (["t2"], lambda: ("sx-100", "pop.mp3", W("t2", 39.72), 0.2)),
    (["t3"], lambda: ("sx-t3", "pop.mp3", W("t3", 57.20), 0.2)),
    (["t4"], lambda: ("sx-grid", "whoosh-short.mp3", st("t4") + 0.05, 0.2)),
    (["t5"], lambda: ("sx-best", "sparkle.mp3", W("t5", 74.96), 0.2)),
    (["e1"], lambda: ("sx-shop", "whoosh-short.mp3", SHOP0, 0.2)),
    (["e2"], lambda: ("sx-shop2", "whoosh-short.mp3", SHOP0, 0.2)),
    (["e1"], lambda: ("sx-cta", "sparkle.mp3", CTA0 + 0.2, 0.3)),
    (["e2"], lambda: ("sx-cta2", "sparkle.mp3", CTA0 + 0.2, 0.3)),
]
SFX = [f() for ids, f in SFX_ALL if all(i in SEG for i in ids)]


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

hosts = [("sc1" if VARIANT == "1" else "sc2", 2), ("outro", 7), ("captions", 8), ("brand", 9)]
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
      <!-- Footage: raw.mp4 (talking review), wear.mp4 (watch appears on the wrist). Trim in Studio by dragging clip edges. -->
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
