#!/usr/bin/env python3
"""65W GaN charger with a retractable USB-C cable — two videos in the current format (bright HD, motion graphics, one-word captions).
Usage: python3 -I build.py <transcript.json> <project_dir> <1..3>
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(WJ))     # {"a": [...], "b": [...], ...} word lists per raw clip
SRC = {"a": "assets/raw_a.mp4", "b": "assets/raw_b.mp4"}


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(src, t):
    return min(WORDS[src], key=lambda w: abs(w["start"] - t))


VARIANT = sys.argv[3] if len(sys.argv) > 3 else "1"
# HOOK: (voice_src, voice_in, voice_out, headline, [(src, src_in), ...] montage shots, split evenly over the voice line)
# BODY: (id, src, src_in, src_out, volume, zone)
HOOKS = {
    "1": ("a", 0.56, 6.70, "CHARGER 65W<br>FAST CHARGE!", []),
    "2": ("b", 0.67, 8.25, "WAJIB BAWA<br>MASA TRAVEL!", []),
}
VARIANTS = {
    "1": [("a1", "a", 10.16, 16.60, 1.0, "low"), ("a2", "a", 17.30, 26.60, 1.0, "low"),
          ("a4", "a", 37.40, 41.20, 1.0, "low"), ("a4b", "a", 44.27, 47.38, 1.0, "low"), ("a5", "a", 51.97, 57.20, 1.0, "low"),
          ("a6", "a", 59.39, 62.98, 1.0, "low"), ("cta", "a", 63.09, 65.60, 1.0, "low")],
    "2": [("b1", "b", 8.27, 13.95, 1.0, "low"), ("b2", "b", 15.35, 20.50, 1.0, "low"), ("b2b", "b", 20.53, 25.45, 1.0, "low"),
          ("b3", "b", 33.24, 36.90, 1.0, "low"), ("b4", "b", 42.66, 44.76, 1.0, "low"), ("b4b", "b", 48.28, 51.70, 1.0, "low"),
          ("b5", "b", 60.06, 63.82, 1.0, "low"), ("cta", "b", 63.82, 67.05, 1.0, "low")],
}
HV_SRC, HV_IN, HV_OUT, HEADLINE, _MONTAGE = HOOKS[VARIANT]
SHOTS = [(HV_SRC, HV_IN)]   # one continuous shot (the montage list is kept above for reference only)
n_shots = len(SHOTS)
hook_frames = round((HV_OUT - HV_IN) * FPS)
EDL = []
acc = 0
for k, (src, t0) in enumerate(SHOTS):
    nfr = round(hook_frames * (k + 1) / n_shots) - acc
    acc += nfr
    EDL.append((f"m{k}", src, t0, t0 + nfr / FPS, 1.0, "low"))
EDL += VARIANTS[VARIANT]
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
for sg in segs:
    sg["kind"] = "broll" if sg["vol"] == 0 else "talk"
HOOK_END = fr(hook_frames / FPS)
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


# ---------------------------------------------------------------- muted b-roll overlays over the talking audio (src, src_in, t0, t1)
OVS = {"1": lambda: [], "2": lambda: []}
OV = [(f"ov{k}", src, a, fr(t0), fr(t1)) for k, (src, a, t0, t1) in enumerate(OVS[VARIANT]())]

# ---------------------------------------------------------------- phrase captions
FIX = {"mic": "main", "ampun": "korang", "hampir": "korang", "list": "link", "stay": "standby", "by": "", "lho": "", "gan,": "GaN,"}
DROP = {"haa", "haa,", "ha", "haha", "okay", "ok", "ok,", "oh", "eh", "apa", "apa,", "lah", "tau", "tau,", "kan", "kan,"}
CAP_SKIP = []


def norm(w, prev):
    t = w["text"]
    core = re.sub(r"[^\w]", "", t).lower()
    if core in DROP:
        return None
    key = t.lower().rstrip(".,!?")
    if key in FIX:
        rep = FIX[key]
    elif core in FIX:
        rep = FIX[core]
    else:
        return t
    if not rep:
        return None
    if t[:1].isupper():
        rep = rep[:1].upper() + rep[1:]
    if t.startswith("-") and key not in ("-angi",):
        rep = "-" + rep
    return rep + t[len(t.rstrip(".,!?")):]


CAP_STOP = {}
kept = []
for s in segs:
    if s["kind"] in ("mute", "broll"):
        continue
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
    if glued and glued[-1]["seg"] == w["seg"] and (w["text"].startswith("-") or w["text"].startswith("%") or w["text"].startswith(".")):
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
        phrases += [[w] for w in cl]

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
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, scale: 1.35 }}, {{ opacity: 1, scale: 1, duration: 0.14, ease: "power3.out" }}, {s0});')

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


def bigzoom(cid, img, origin, tag, t0, t1, zoom=1.65):
    """'dulu botol, sekarang pack' image as a big centre card: footage dims, card eases in, then it zooms onto the new pouch"""
    w = 880
    t1 = max(t1, t0 + 3.0)
    body = clip(cid, t0, t1 - t0,
                f'<div id="{cid}bg" style="position:absolute;inset:0;background:rgba(8,9,12,.74)"></div>'
                f'<div id="{cid}c" style="position:absolute;left:{(960 - w) // 2 + 60}px;top:330px;width:{w}px;height:{w}px;border-radius:30px;overflow:hidden;background:#fff;box-shadow:0 30px 80px rgba(0,0,0,.6)">'
                f'<img id="{cid}i" src="assets/img/{img}" alt="" style="display:block;width:{w}px;height:{w}px;object-fit:cover;transform-origin:{origin}"/></div>'
                f'<div id="{cid}t" style="position:absolute;left:0;width:1080px;top:{330 + w - 36}px;text-align:center">'
                f'<span style="display:inline-block;padding:14px 34px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:44px;letter-spacing:.04em;box-shadow:0 12px 30px rgba(0,0,0,.4)">{tag}</span></div>',
                style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}bg", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power2.out" }}, {fr(t0)});',
                    f'    tl.fromTo("#{cid}c", {{ opacity: 0, y: 40, scale: 0.92 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.55, ease: "power3.out" }}, {fr(t0 + 0.05)});',
                    f'    tl.fromTo("#{cid}i", {{ scale: 1 }}, {{ scale: {zoom}, duration: 1.1, ease: "power2.inOut", immediateRender: false }}, {fr(t0 + 1.0)});',
                    f'    tl.fromTo("#{cid}t", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {fr(t0 + 1.6)});',
                    f'    tl.to("#{cid}", {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, {fr(t1 - 0.32)});'])
    return body, js


def newpack(cid, sid, t0, t1):
    return bigzoom(cid, "newpack.jpg", "76% 52%", "SEKARANG PACK BARU", t0, t1)


def opt(ids, f):
    return f() if all(i in SEG for i in ids) else None


def C(cid, label, icon, sid, t0, t1=None):
    t1 = end(sid) if t1 is None else t1
    return chip(cid, label, icon, t0, t1 - t0, Y(sid))


V = VARIANT
HL_STYLE = ("font-family:var(--font-ui);font-weight:900;font-size:76px;line-height:1.08;letter-spacing:.14em;color:#ffe45c;"
            "-webkit-text-stroke:3px #1a1406;paint-order:stroke fill;text-shadow:0 4px 0 rgba(0,0,0,.6),0 8px 26px rgba(0,0,0,.7)")


def hook_headline():
    inner = f'<div id="hl-t" style="{HL_STYLE}">{HEADLINE}</div>'
    body = clip("hl", 0.0, HOOK_END + 0.4, inner, style="position:absolute; left:0; width:960px; top:440px; text-align:center")
    js = "\n".join(['    tl.fromTo("#hl-t", { opacity: 0, scaleX: 1.6, scaleY: 1.15 }, { opacity: 1, scaleX: 1, scaleY: 1, duration: 0.55, ease: "expo.out" }, 0.05);',
                    out("#hl", HOOK_END + 0.4)])
    return body, js


def flashes():
    cuts = [st(f"m{k}") for k in range(1, n_shots)] + [st(segs[n_shots]["id"])]
    divs = "".join(f'<div id="fl{k}" style="position:absolute;inset:0;background:#fff;opacity:0"></div>' for k in range(len(cuts)))
    body = clip("fl", 0.0, HOOK_END + 0.5, divs, style="position:absolute; inset:0")
    js = "\n".join(f'    tl.fromTo("#fl{k}", {{ opacity: 0.55 }}, {{ opacity: 0, duration: 0.16, ease: "power2.out", immediateRender: false }}, {fr(t)});' for k, t in enumerate(cuts))
    return body, js



# ---------------------------------------------------------------- reference-style motion graphics
ORANGE = "#ff8a1f"
WIFI = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><path d="M2.5 9a14 14 0 0 1 19 0"/><path d="M5.5 12.5a9.5 9.5 0 0 1 13 0"/><path d="M8.7 15.8a5 5 0 0 1 6.6 0"/><circle cx="12" cy="19" r="1.3" fill="#fff"/></svg>'
BT = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7l10 10-5 4V3l5 4L7 17"/></svg>'


def dial(cid, t0, t1, num, unit, label, cy=640):
    """semi-circle speedometer: orange ticks sweep in while the number counts up (the mAh gauge in the reference)"""
    r, cx = 330, 540
    arc = f"M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"
    L = round(math.pi * r)
    svg = (f'<svg width="1080" height="{cy + 60}" viewBox="0 0 1080 {cy + 60}" style="position:absolute;left:0;top:0">'
           f'<defs><mask id="{cid}m"><path id="{cid}mp" d="{arc}" stroke="#fff" stroke-width="90" fill="none" stroke-dasharray="{L}" stroke-dashoffset="{L}"/></mask>'
           f'<linearGradient id="{cid}g" x1="0" x2="1"><stop offset="0" stop-color="#ffb347"/><stop offset="1" stop-color="#ff5a1f"/></linearGradient></defs>'
           f'<path d="{arc}" stroke="rgba(255,255,255,.35)" stroke-width="46" fill="none" stroke-dasharray="4 10"/>'
           f'<path d="{arc}" stroke="url(#{cid}g)" stroke-width="58" fill="none" stroke-dasharray="4 10" mask="url(#{cid}m)" style="filter:drop-shadow(0 0 14px rgba(255,120,30,.9))"/></svg>')
    txt = (f'<div style="position:absolute;left:0;width:1080px;top:{cy - 150}px;text-align:center;font-family:var(--font-ui);color:#fff;'
           f'text-shadow:0 3px 14px rgba(0,0,0,.7)"><span id="{cid}n" style="font-weight:900;font-size:120px;letter-spacing:-.01em">0</span>'
           f'<span style="font-weight:900;font-size:64px;color:{ORANGE}">{unit}</span>'
           f'<div style="font-weight:800;font-size:40px;letter-spacing:.14em;margin-top:-6px">{label}</div></div>')
    body = clip(cid, t0, t1 - t0, svg + txt, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([
        f'    tl.fromTo("#{cid}", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "power3.out" }}, {fr(t0)});',
        f'    tl.to("#{cid}mp", {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.8, ease: "power2.out" }}, {fr(t0 + 0.1)});',
        f'    {{ const o = {{ v: 0 }}; tl.to(o, {{ v: {num}, duration: 0.8, ease: "power2.out", onUpdate: () => {{ document.querySelector("#{cid}n").textContent = Math.round(o.v); }} }}, {fr(t0 + 0.1)}); }}',
        f'    tl.to("#{cid}", {{ opacity: 0, scale: 1.05, duration: 0.3, ease: "power2.in" }}, {fr(t1 - 0.32)});'])
    return body, js


def pills(cid, items, t1, y=470):
    """icon pills that pop in one by one: items = [(svg, label, t)]"""
    inner = "".join(f'<span id="{cid}{k}" style="display:inline-flex;align-items:center;gap:14px;margin:0 10px;padding:14px 28px 14px 18px;border-radius:999px;'
                    f'background:rgba(14,15,18,.72);border:2px solid rgba(255,255,255,.25);backdrop-filter:blur(14px);box-shadow:0 14px 34px rgba(0,0,0,.45)">'
                    f'<span style="width:58px;height:58px;border-radius:50%;background:{ORANGE};display:inline-flex;align-items:center;justify-content:center">'
                    f'<span style="width:34px;height:34px;display:block">{ic}</span></span>'
                    f'<span style="font-family:var(--font-ui);font-weight:800;font-size:40px;color:#fff">{lb}</span></span>' for k, (ic, lb, t) in enumerate(items))
    t0 = min(t for _, _, t in items)
    body = clip(cid, t0, t1 - t0, inner, style=f"position:absolute; left:0; width:1080px; top:{y}px; text-align:center")
    js = "\n".join([f'    tl.fromTo("#{cid}{k}", {{ opacity: 0, scale: 0.5, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.45, ease: "back.out(1.8)" }}, {fr(t)});'
                    for k, (_, _, t) in enumerate(items)] + [out(f"#{cid}", t1)])
    return body, js


def ring360(cid, t0, t1, cy=700):
    r = 230
    svg = (f'<svg width="560" height="560" viewBox="0 0 560 560" style="position:absolute;left:260px;top:{cy - 280}px;overflow:visible">'
           f'<g id="{cid}r" style="transform-origin:280px 280px"><circle cx="280" cy="280" r="{r}" fill="none" stroke="rgba(255,255,255,.85)" stroke-width="5" stroke-dasharray="14 12"/>'
           f'<path d="M 280 {280 - r - 22} l 30 22 l -30 22" fill="none" stroke="{ORANGE}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></g></svg>')
    txt = (f'<div style="position:absolute;left:0;width:1080px;top:{cy - 90}px;text-align:center;font-family:var(--font-ui);font-weight:900;color:#fff;'
           f'text-shadow:0 3px 16px rgba(0,0,0,.75)"><div style="font-size:130px;line-height:1">360°</div><div style="font-size:38px;letter-spacing:.16em;color:{ORANGE}">ADJUSTABLE</div></div>')
    body = clip(cid, t0, t1 - t0, svg + txt, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.6)" }}, {fr(t0)});',
                    f'    tl.fromTo("#{cid}r", {{ rotation: 0 }}, {{ rotation: 360, duration: {fr(t1 - t0)}, ease: "none", immediateRender: false }}, {fr(t0)});',
                    out(f"#{cid}", t1)])
    return body, js


def brackets(cid, label, t0, t1, box=(250, 430, 580, 520)):
    x, y, w, h = box
    L, T = 90, 8
    c = lambda st_: f'<div style="position:absolute;width:{L}px;height:{L}px;{st_}"></div>'
    corners = (c(f"left:0;top:0;border-left:{T}px solid #fff;border-top:{T}px solid #fff") + c(f"right:0;top:0;border-right:{T}px solid #fff;border-top:{T}px solid #fff")
               + c(f"left:0;bottom:0;border-left:{T}px solid #fff;border-bottom:{T}px solid #fff") + c(f"right:0;bottom:0;border-right:{T}px solid #fff;border-bottom:{T}px solid #fff"))
    inner = (f'<div id="{cid}b" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;filter:drop-shadow(0 2px 6px rgba(0,0,0,.6))">{corners}</div>'
             f'<div style="position:absolute;left:0;width:1080px;top:{y + h - 40}px;text-align:center"><span id="{cid}l" style="display:inline-block;background:#fff;color:#111;'
             f'font-family:var(--font-ui);font-weight:800;font-size:42px;padding:8px 22px;transform-origin:0 50%">{label}</span></div>')
    body = clip(cid, t0, t1 - t0, inner, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}b", {{ opacity: 0, scale: 1.25 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "power3.out" }}, {fr(t0)});',
                    f'    tl.fromTo("#{cid}l", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power3.out" }}, {fr(t0 + 0.3)});',
                    out(f"#{cid}", t1)])
    return body, js


def tick(cid, label, t0, t1, y=520):
    svg = (f'<svg width="76" height="76" viewBox="0 0 76 76" style="flex:none"><circle cx="38" cy="38" r="33" fill="#0d0e10" stroke="#25d366" stroke-width="6"/>'
           f'<path id="{cid}p" d="M23 39l10 10 20-22" fill="none" stroke="#fff" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="50" stroke-dashoffset="50"/></svg>')
    inner = (f'<span style="display:inline-flex;align-items:center;filter:drop-shadow(0 10px 26px rgba(0,0,0,.5))">{svg}'
             f'<span id="{cid}l" style="background:#fff;color:#111;font-family:var(--font-ui);font-weight:900;font-size:46px;padding:8px 24px 8px 18px;margin-left:-6px;transform-origin:0 50%">{label}</span></span>')
    body = clip(cid, t0, t1 - t0, inner, style=f"position:absolute; left:0; width:1080px; top:{y}px; text-align:center")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.8)" }}, {fr(t0)});',
                    f'    tl.to("#{cid}p", {{ attr: {{ "stroke-dashoffset": 0 }}, duration: 0.35, ease: "power2.out" }}, {fr(t0 + 0.2)});',
                    f'    tl.fromTo("#{cid}l", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power3.out" }}, {fr(t0 + 0.25)});',
                    out(f"#{cid}", t1)])
    return body, js


def leak(cid, t):
    """orange light-leak flash between beats"""
    inner = (f'<div id="{cid}i" style="position:absolute;inset:-10%;opacity:0;mix-blend-mode:screen;'
             f'background:radial-gradient(ellipse 60% 50% at 30% 40%,rgba(255,200,90,.95),transparent 70%),radial-gradient(ellipse 70% 60% at 80% 70%,rgba(255,110,30,.9),transparent 70%)"></div>')
    body = clip(cid, max(0, t - 0.05), 0.75, inner, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}i", {{ opacity: 0, x: -60 }}, {{ opacity: 0.9, x: 0, duration: 0.25, ease: "power2.out" }}, {fr(max(0, t - 0.05))});',
                    f'    tl.to("#{cid}i", {{ opacity: 0, x: 60, duration: 0.4, ease: "power2.in" }}, {fr(t + 0.25)});'])
    return body, js


DISCLAIMER = "Disclaimer: Harga mungkin berubah apabila promosi tamat"


def pricetag(cid, t0, t1, t_new, cx=380):
    dx = cx - 540
    """HARGA ASAL RM749 (struck) -> RM322.91 with -57%, product in a dashed circle, disclaimer under it"""
    inner = (f'<div style="position:absolute;left:{dx}px;width:1080px;top:380px;text-align:center;font-family:var(--font-ui);font-weight:900;font-size:84px;color:#fff;'
             f'letter-spacing:.01em;text-shadow:0 4px 18px rgba(0,0,0,.7)" id="{cid}h">HARGA ASAL</div>'
             f'<div id="{cid}c" style="position:absolute;left:{330 + dx}px;top:560px;width:420px;height:420px;border-radius:50%;border:6px dashed rgba(255,255,255,.9)"></div>'
             f'<div id="{cid}im" style="position:absolute;left:{390 + dx}px;top:620px;width:300px;height:300px;border-radius:50%;overflow:hidden;background:#fff;box-shadow:0 16px 40px rgba(0,0,0,.5)">'
             f'<img src="assets/img/img1.jpg" alt="" style="width:300px;height:300px;object-fit:cover;object-position:50% 45%"/></div>'
             f'<div style="position:absolute;left:{dx}px;width:1080px;top:490px;text-align:center"><span id="{cid}o" style="position:relative;display:inline-flex;align-items:baseline;gap:8px;padding:10px 34px;border-radius:999px;'
             f'background:#16171a;border:3px solid {ORANGE};font-family:var(--font-ui);font-weight:900;color:#fff;box-shadow:0 12px 30px rgba(0,0,0,.5)">'
             f'<span style="font-size:36px;color:{ORANGE}">RM</span><span style="font-size:64px">749</span>'
             f'<svg id="{cid}x" viewBox="0 0 100 10" preserveAspectRatio="none" style="position:absolute;left:18px;width:calc(100% - 36px);top:50%;height:10px;margin-top:-5px;overflow:visible;transform-origin:0 50%"><line x1="0" y1="5" x2="100" y2="5" stroke="#ff2d55" stroke-width="7" vector-effect="non-scaling-stroke" stroke-linecap="round"/></svg></span></span></div>'
             f'<div style="position:absolute;left:{dx}px;width:1080px;top:990px;text-align:center"><span id="{cid}n" style="display:inline-flex;align-items:center;gap:18px;padding:12px 18px 12px 38px;border-radius:999px;'
             f'background:linear-gradient(90deg,#ff9a3c,#ff5a1f);font-family:var(--font-ui);font-weight:900;color:#fff;box-shadow:0 16px 40px rgba(255,90,30,.45)">'
             f'<span style="font-size:40px">RM</span><span style="font-size:82px;margin-left:-10px">322.91</span>'
             f'<span style="font-size:40px;background:#fff;color:#ff2d55;border-radius:999px;padding:6px 18px">-57%</span></span></div>'
             f'<div id="{cid}d" style="position:absolute;left:20px;width:720px;top:1120px;text-align:center;font-family:var(--font-ui);font-weight:600;font-size:24px;color:rgba(255,255,255,.92);'
             f'text-shadow:0 2px 8px rgba(0,0,0,.8)">{DISCLAIMER}</div>')
    body = clip(cid, t0, t1 - t0, '<div style="position:absolute;inset:0;background:rgba(6,7,9,.55)"></div>' + inner, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25, ease: "power2.out" }}, {fr(t0)});',
                    f'    tl.fromTo("#{cid}h", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, {fr(t0 + 0.05)});',
                    f'    tl.fromTo("#{cid}c", {{ rotation: 0, scale: 0.8, opacity: 0 }}, {{ rotation: 90, scale: 1, opacity: 1, duration: {fr(t1 - t0)}, ease: "none", immediateRender: false }}, {fr(t0)});',
                    f'    tl.fromTo("#{cid}im", {{ opacity: 0, scale: 0.7 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.6)" }}, {fr(t0 + 0.15)});',
                    f'    tl.fromTo("#{cid}o", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.8)" }}, {fr(t0 + 0.35)});',
                    f'    tl.fromTo("#{cid}x", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power2.out" }}, {fr(t_new - 0.3)});',
                    f'    tl.fromTo("#{cid}n", {{ opacity: 0, scale: 0.5, y: 30 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "back.out(1.8)" }}, {fr(t_new)});',
                    f'    tl.fromTo("#{cid}d", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {fr(t_new + 0.2)});',
                    f'    tl.to("#{cid}", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {fr(t1 - 0.27)});'])
    return body, js


DROP_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/></svg>'
SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/></svg>'
RAIN = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><path d="M7 15a4.5 4.5 0 1 1 1.2-8.8A5.5 5.5 0 0 1 18.5 9 3.5 3.5 0 0 1 18 16H7z"/><path d="M8 19l-1 2M12 19l-1 2M16 19l-1 2"/></svg>'
WIND = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><path d="M3 8h11a3 3 0 1 0-3-3M3 12h16a3 3 0 1 1-3 3M3 16h8"/></svg>'
SIZE_ROWS = ["M", "L", "XL", "2XL", "3XL", "4XL", "5XL"]   # row centres in size-crop.jpg (1185 x 515): 185 + 49.5 * i
CW = 980


def size_insert(cid, t0, t1):
    """full-screen size chart; a gold bar runs M -> 5XL, then a 'SAIZ M - 5XL' tag and the true-to-size line"""
    k = CW / 1185
    ys = [(185 + 49.5 * i) * k for i in range(len(SIZE_ROWS))]
    step = min(0.2, (t1 - t0 - 1.6) / len(SIZE_ROWS))
    inner = (f'<div style="position:absolute;inset:0;background:rgba(6,7,9,.72)"></div>'
             f'<div style="position:absolute;left:0;width:1080px;top:400px;text-align:center;font-family:var(--font-ui);font-weight:900;font-size:64px;color:#fff;letter-spacing:.06em;text-shadow:0 4px 16px rgba(0,0,0,.6)">SIZE CHART</div>'
             f'<div id="{cid}c" style="position:absolute;left:{(1080 - CW) // 2}px;top:510px;width:{CW}px">'
             f'<div style="border-radius:26px;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6);background:#fff"><img src="assets/img/size-crop.jpg" style="display:block;width:{CW}px" alt=""/></div>'
             f'<div id="{cid}bar" style="position:absolute;left:2px;right:2px;top:{ys[0] - 22:.0f}px;height:44px;border:5px solid #f5c542;border-radius:12px;'
             f'box-shadow:0 0 0 4px rgba(245,197,66,.25),0 0 30px rgba(245,197,66,.85)"></div></div>'
             f'<div style="position:absolute;left:0;width:1080px;top:{510 + 515 * k + 40:.0f}px;text-align:center">'
             f'<span id="{cid}t" style="display:inline-block;padding:14px 38px;border-radius:999px;background:linear-gradient(90deg,#ffcf4a,#f5a623);color:#1a1406;'
             f'font-family:var(--font-ui);font-weight:900;font-size:50px;letter-spacing:.04em;box-shadow:0 14px 34px rgba(245,166,35,.45)">SAIZ M – 5XL</span>'
             f'<div id="{cid}f" style="margin-top:18px;font-family:var(--font-ui);font-weight:700;font-size:34px;color:#fff;text-shadow:0 2px 10px rgba(0,0,0,.8)">82% pembeli kata saiz tepat</div></div>')
    js = [f'    tl.fromTo("#{cid}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, {fr(t0)});',
          f'    tl.fromTo("#{cid}c", {{ opacity: 0, scale: 0.85, y: 40 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.5, ease: "expo.out" }}, {fr(t0 + 0.05)});',
          f'    tl.fromTo("#{cid}bar", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15 }}, {fr(t0 + 0.45)});']
    for i in range(1, len(SIZE_ROWS)):
        js.append(f'    tl.to("#{cid}bar", {{ y: {ys[i] - ys[0]:.1f}, duration: {step * 0.7:.3f}, ease: "power2.out" }}, {fr(t0 + 0.5 + step * i)});')
    js += [f'    tl.to("#{cid}bar", {{ opacity: 0.35, duration: 0.3 }}, {fr(t0 + 0.6 + step * len(SIZE_ROWS))});',
           f'    tl.fromTo("#{cid}t", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }}, {fr(t0 + 0.7 + step * len(SIZE_ROWS))});',
           f'    tl.fromTo("#{cid}f", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, {fr(t0 + 0.95 + step * len(SIZE_ROWS))});',
           f'    tl.to("#{cid}", {{ opacity: 0, duration: 0.25, ease: "power2.in" }}, {fr(t1 - 0.27)});']
    body = clip(cid, t0, t1 - t0, inner, style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    return body, "\n".join(js)


BOLT = '<svg viewBox="0 0 24 24" fill="#fff"><path d="M13 2L4 14h7l-1 8 9-12h-7z"/></svg>'
USBC = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"><rect x="3" y="8.5" width="18" height="7" rx="3.5"/><path d="M8 12h8"/></svg>'
USBA = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><rect x="4" y="7" width="16" height="10" rx="1.5"/><path d="M8 10.5h2.5M13.5 10.5H16"/></svg>'
PLANE = '<svg viewBox="0 0 24 24" fill="#fff"><path d="M21 15.5v-2l-8-5V4a1.5 1.5 0 0 0-3 0v4.5l-8 5v2l8-2.5V18l-2 1.5V21l3.5-1 3.5 1v-1.5L13 18v-5z"/></svg>'
HOME = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/></svg>'
PARTS = {
    "1": lambda: [
        dial("d-65", W("m0", 3.62), HOOK_END + 0.3, 65, "W", "GaN CHARGER", cy=1380),
        brackets("bk", "Ada display watt", W("a1", 11.32), W("a1", 13.88), box=(230, 520, 620, 560)),
        pills("pl", [(USBC, "Type-C", W("a1", 13.88)), (USBA, "USB-A", W("a1", 15.10))], end("a1"), y=1250),
        leak("lk1", st("a2")),
        tick("tk1", "KABEL BOLEH TARIK", W("a2", 18.44), at("a2", 24.4), y=1250),
        tick("tk1b", "LEPAS, AUTO MASUK", at("a2", 24.5), end("a2"), y=1250),
        leak("lk2", st("a4")),
        tick("tk3", "SUPER FAST CHARGING", W("a4", 39.23), end("a4"), y=1250),
        dial("d-w", W("a4b", 45.27), end("a4b"), 37, "W", "TERUS CHARGE", cy=820),
        leak("lk3", st("a5")),
        tick("tk4", "SIMPAN BALIK, KEMAS", W("a5", 53.49), end("a5"), y=1250),
        bigzoom("p-mag", "img4.jpg", "75% 25%", "MAGNET, BOLEH LEKAT", W("a6", 59.41), end("a6"), zoom=1.08),
    ],
    "2": lambda: [
        pills("pl-t", [(PLANE, "Travel", W("m0", 7.45))], HOOK_END + 0.3, y=1250),
        brackets("bk", "Ada display watt", W("b1", 8.87), W("b1", 11.81), box=(230, 520, 620, 560)),
        pills("pl", [(USBC, "Type-C", W("b1", 11.81)), (USBA, "USB-A", W("b1", 13.21))], end("b1"), y=1250),
        leak("lk1", st("b2")),
        tick("tk1", "TARIK, DIA STOP", W("b2", 19.05), end("b2"), y=1250),
        tick("tk2", "TARIK LAGI, MASUK BALIK", W("b2b", 22.59), end("b2b"), y=1250),
        bigzoom("p-len", "img4.jpg", "50% 75%", "TARIK IKUT PANJANG", st("b3") + 0.1, end("b3"), zoom=1.08),
        leak("lk2", st("b4")),
        tick("tk3", "SUPER FAST CHARGING", st("b4") + 0.1, end("b4"), y=1250),
        dial("d-w", W("b4b", 48.30), end("b4b"), 37, "W", "TERUS CHARGE", cy=820),
        pills("pl-tr", [(PLANE, "Travel", W("b5", 61.66)), (HOME, "Balik kampung", W("b5", 62.14))], end("b5"), y=1250),
    ],
}
build_scene("sc", [hook_headline()] + PARTS[V]())


shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:18px 20px">'
        f'<div style="width:120px;height:120px;border-radius:24px;background:#fff;flex:none;'
        f'overflow:hidden"><img src="assets/img/img1.jpg" alt="" style="width:120px;height:120px;object-fit:cover;object-position:40% 50%"/></div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:34px">CHARGER GaN 65W</div>'
        f'<div style="margin-top:6px;font-weight:700;font-size:28px;color:rgba(255,255,255,.85)">3 dalam 1 &middot; Kabel tarik &middot; Display</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:12px;padding:16px 36px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:44px;white-space:nowrap;box-shadow:0 14px 36px rgba(0,0,0,.45)">'
       '<svg viewBox="0 0 24 24" width="40" height="40" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Klik link di bawah</div>')
SHOP0 = st("cta") - 0.3
CTA0 = st("cta")
build_scene("outro", [
    (clip("ot-shop", SHOP0, TOTAL - SHOP0, shop, cls="glass", style="left:50px; top:1040px; width:660px"),
     "\n".join([f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {SHOP0});',
                ])),
    (clip("ot-cta", CTA0, TOTAL - CTA0, cta, style="position:absolute; left:50px; width:660px; top:1225px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.5)" }}, {fr(CTA0 + 0.2)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: 3, immediateRender: false }}, {fr(CTA0 + 0.9)});'])),
])

# ---- creator / product header, on screen the whole video (like the reference)
HEAD_L = ("REZEKI.NAZIR", "TRUSTED AFFILIATE")
HEAD_R = ("GaN CHARGER", "65W FAST CHARGE")
hdr = (f'<div id="hd-l" style="position:absolute;left:84px;top:252px;display:flex;align-items:stretch;gap:16px">'
       f'<div style="width:7px;border-radius:4px;background:linear-gradient(180deg,#f3dfb1,#c9a25e 55%,#8f6a32)"></div>'
       f'<div class="hdt">{HEAD_L[0]}<br/>{HEAD_L[1]}</div></div>'
       f'<div id="hd-r" class="hdt" style="position:absolute;right:94px;top:252px;text-align:right">{HEAD_R[0]}<br/>{HEAD_R[1]}</div>')
hdr = '<div style="position:absolute;left:0;top:0;width:1080px;height:460px;background:linear-gradient(180deg,rgba(0,0,0,.6) 0%,rgba(0,0,0,.5) 60%,rgba(0,0,0,0) 100%)"></div>' + hdr
write("brand.html", scene("brand", BASE + """
    .hdt { font-family: var(--font-ui); font-weight: 600; font-size: 29px; line-height: 1.22; letter-spacing: .05em; color: #f6f1e7;
      text-shadow: 0 0 2px rgba(0,0,0,.95), 0 1px 3px rgba(0,0,0,.9), 0 0 10px rgba(0,0,0,.7), 0 2px 18px rgba(0,0,0,.6); white-space: nowrap; }
""", clip("hd", 0, TOTAL, hdr, style="position:absolute; inset:0"),
    f'    tl.fromTo(["#hd-l", "#hd-r"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, 0.1);'))

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1180px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 900; font-size: 52px; color: #fff; letter-spacing: .03em;
      text-shadow: 0 0 3px rgba(0,0,0,.9), 0 2px 0 rgba(0,0,0,.5), 0 4px 18px rgba(0,0,0,.8); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index
videos = [f'        <video id="{s["id"]}" class="clip seg" src="{SRC[s["src"]]}" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" '
          + ('muted ' if s["kind"] in ("mute", "broll") else f'data-has-audio="true" data-volume="{s["vol"]}" data-fade-in="0.06" data-fade-out="0.1" ')
          + 'playsinline></video>' for s in segs if s["kind"] != "voice"]
videos += [f'        <video id="{oid}" class="clip ov" src="{SRC[src]}" data-start="{t0}" data-duration="{fr(t1 - t0)}" data-media-start="{a}" data-track-index="4" muted playsinline></video>'
           for oid, src, a, t0, t1 in OV]
voice_audio = ""
cam = [f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.035, duration: {fr(s["dur"])}, ease: "none", immediateRender: false }}, {s["start"]});' for s in segs if s["kind"] not in ("mute", "voice")]

cam += [f'      tl.fromTo("#cam", {{ scale: 1.22, rotation: {(-4 if k % 2 else 4)} }}, {{ scale: 1.06, rotation: 0, duration: 0.3, ease: "power3.out", immediateRender: false }}, {st(f"m{k}")});' for k in range(1, n_shots)]

import re as _re
SFX = [("sx-hk", "whoosh.mp3", 0.0, 0.3)] + [(f"sx-m{k}", "whoosh-short.mp3", st(f"m{k}"), 0.22) for k in range(1, n_shots)]
SFX += [(f"sx-{oid}", "whoosh-short.mp3", t0, 0.15) for oid, src, a, t0, t1 in OV]

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
{voice_audio}
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
