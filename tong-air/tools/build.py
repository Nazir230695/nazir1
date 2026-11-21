#!/usr/bin/env python3
"""10 L insulated drink bucket — same reference style as the smart-glasses edit (white label chips with a round black icon,
glass cards, neon accent), paced calmly: almost every line kept with natural breathing room, phrase captions instead of
single flashing words, soft long-held overlays, no zoom jumps on the cuts.
Usage: python3 -I build.py <words.json> <project_dir>
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(WJ))
PAD_IN, PAD_OUT = 0.18, 0.30   # breathing room around each kept line


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(t):
    return min(WORDS, key=lambda w: abs(w["start"] - t))


# (id, first_word_start, last_word_start, in_override, out_override)
EDL = [
    ("s1", 0.00, 2.54, None, None),    # kalau boleh beli yang murah, kenapa nak beli yang mahal?
    ("s2", 3.80, 8.76, None, None),    # bukan RM200, bukan RM100, bukan RM50, tapi bawah lagi
    ("s3", 10.30, 23.18, None, None),  # ni memang terbaik tau ... kaki boleh buka, lock siap, letak cawan, memang terbaik lah ni
    ("s4", 23.62, 30.28, None, None),  # paip dia pun elok, tempat pegang pun terbaik, ada tempat pegang, 10 liter
    ("s5", 31.54, 34.38, None, None),  # lepas tu tengok dalam dia, ni, stainless steel tau
    ("s6", 36.28, 46.74, None, None),  # panas 40 celsius tahan 24 jam, sejuk 15 celsius tahan 24 jam, memang berbaloi
    ("s7", 48.00, 53.64, None, 54.40), # ada warna hitam, warna lain, boleh pilih kat bawah, 10 liter, nak dapat mana? tekan link bawah ni
]

segs, f = [], 0
for sid, a, b, ia, ob in EDL:
    w0, w1 = wat(a), wat(b)
    i0, i1 = WORDS.index(w0), WORDS.index(w1)
    prev_end = WORDS[i0 - 1]["end"] if i0 > 0 else 0
    next_start = WORDS[i1 + 1]["start"] if i1 + 1 < len(WORDS) else 1e9
    a = max(0, max(w0["start"] - PAD_IN, prev_end + 0.04)) if i0 > 0 else 0
    b = min(w1["end"] + PAD_OUT, next_start - 0.06)
    a = ia if ia is not None else a
    b = ob if ob is not None else b
    fa, fb = round(a * FPS), round(b * FPS)
    segs.append(dict(id=sid, src_in=fa / FPS, src_out=fb / FPS, start=f / FPS, dur=(fb - fa) / FPS))
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


# ---------------------------------------------------------------- phrase captions (2-3 words, calm)
FIX = {"muah": "murah", "rm200": "RM200", "rm100": "RM100", "rm50": "RM50"}
DROP = {"ha", "haa", "okay"}


def norm(w):
    t = w["text"]
    core = re.sub(r"[^\w]", "", t).lower()
    if core in DROP:
        return None
    if core in FIX:
        return FIX[core] + t[len(t.rstrip(".,!?")):]
    return t


kept = []
for s in segs:
    for w in WORDS:
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05:
            txt = norm(w)
            if txt:
                kept.append(dict(text=txt, start=at(s["id"], w["start"]), end=at(s["id"], min(w["end"], s["src_out"])), seg=s["id"]))
# sentences (split at . ? ! or a pause), then each sentence into even chunks of at most 3 words
sents, cur = [], []
for i, w in enumerate(kept):
    cur.append(w)
    nxt = kept[i + 1] if i + 1 < len(kept) else None
    if nxt is None or nxt["seg"] != w["seg"] or re.search(r"[.?!]$", w["text"]) or nxt["start"] - w["end"] > 0.35:
        sents.append(cur); cur = []
merged = []
for snt in sents:   # a lone word ("Ni.", "Tau,") joins the next sentence when it follows straight on
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
    for w in snt:                      # clauses end at a comma
        c.append(w)
        if w["text"].endswith(","):
            clauses.append(c); c = []
    if c:
        clauses.append(c)
    packed = []
    for cl in clauses:                 # pack short clauses together up to 3 words
        if packed and len(packed[-1]) + len(cl) <= 3 and (len(cl) == 1 or len(packed[-1]) == 1):
            packed[-1] = packed[-1] + cl
        else:
            packed.append(cl)
    for cl in packed:
        phrases += even_chunks(cl)
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
    cap_items.append(f'    <div id="{cid}" class="cw clip" data-start="{s0}" data-duration="{fr(en - s0)}" data-track-index="0">'
                     f'<span id="{cid}s">{html.escape(text)}</span></div>')
    cap_js.append(f'    tl.fromTo("#{cid}s", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "power2.out" }}, {s0});')

# ---------------------------------------------------------------- tokens + pieces (reference style, calm motion)
TOK = """
      --ink: #ffffff;
      --dark: #0d0e10;
      --neon: #3dff8b;
      --hot: #ff6b3d;
      --cold: #4cc3ff;
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
      font-size: 60px; line-height: 1.1; text-shadow: 0 3px 6px rgba(0,0,0,.5), 0 10px 34px rgba(0,0,0,.6); }}
    .chrome {{ position: absolute; left: 0; width: 960px; text-align: center; font-family: var(--font-ui); font-weight: 900; font-size: 170px; line-height: 1; }}
    .chrome span {{ display: inline-block; background: linear-gradient(180deg, #ffffff 0%, #d9dde3 38%, #7d838c 52%, #f4f6f8 70%, #a9afb7 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent; filter: drop-shadow(0 6px 18px rgba(0,0,0,.55)); }}
    .pilltag {{ display: inline-flex; align-items: center; gap: 10px; padding: 10px 26px 10px 16px; border-radius: 12px; background: rgba(255,255,255,.95);
      color: #111; font-family: var(--font-ui); font-weight: 700; font-size: 34px; box-shadow: 0 10px 28px rgba(0,0,0,.35); white-space: nowrap; }}
    .pilltag svg {{ width: 32px; height: 32px; }}
"""
I = {
    "stand": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="3" width="12" height="13" rx="3"/><path d="M8 16l-2 5M16 16l2 5M12 16v5"/></svg>',
    "lock": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="10.5" width="14" height="10" rx="2.5"/><path d="M8.5 10.5V7.5a3.5 3.5 0 0 1 7 0v3"/></svg>',
    "cup": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 8h11v6a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z"/><path d="M16 10h1.5a2.5 2.5 0 0 1 0 5H16"/><path d="M8 3c0 1.5 1 1.5 1 3M12 3c0 1.5 1 1.5 1 3"/></svg>',
    "tap": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9h9a4 4 0 0 1 4 4v1"/><path d="M8 5h4M10 5v4"/><path d="M17 17.5c0 1-.7 2-1.5 2s-1.5-1-1.5-2 1.5-3 1.5-3 1.5 2 1.5 3z"/></svg>',
    "hand": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12a7 7 0 0 1 14 0"/><path d="M3.5 12h3M17.5 12h3"/></svg>',
    "steel": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><ellipse cx="12" cy="6" rx="7" ry="2.5"/><path d="M5 6v11c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V6"/><path d="M9 10v6M12 11v6"/></svg>',
    "palette": '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 3a9 9 0 1 0 0 18c1.4 0 2-1 1.6-2.2-.5-1.3.4-2.8 1.9-2.8H18a3 3 0 0 0 3-3c0-5.5-4-10-9-10z"/><circle cx="7.5" cy="11" r="1.2" fill="#fff"/><circle cx="10.5" cy="7" r="1.2" fill="#fff"/><circle cx="15" cy="7.5" r="1.2" fill="#fff"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="#fff"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>',
}
STAR = '<svg viewBox="0 0 24 24" fill="#f5c542"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/></svg>'
FLAME = '<svg viewBox="0 0 24 24" fill="#ff6b3d"><path d="M12 2c1 3.5 5 6 5 11a5 5 0 0 1-10 0c0-2.4 1.2-3.8 2.5-5 .3 1.6 1 2.6 2 3-.4-3 0-6 .5-9z"/></svg>'
SNOW = '<svg viewBox="0 0 24 24" fill="none" stroke="#4cc3ff" stroke-width="2.2" stroke-linecap="round"><path d="M12 2v20M3.3 7l17.4 10M3.3 17L20.7 7"/><path d="M9.5 3.5L12 6l2.5-2.5M9.5 20.5L12 18l2.5 2.5"/></svg>'


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


def img_card(cid, src, label, start, dur, x, y, w=380):
    lab = f'<div style="margin-top:12px;text-align:center"><span class="pilltag">{label}</span></div>' if label else ""
    inner = (f'<div style="border-radius:22px;overflow:hidden;border:3px solid rgba(255,255,255,.9);box-shadow:0 24px 60px rgba(0,0,0,.5)">'
             f'<img src="{src}" alt="" style="display:block;width:{w}px"/></div>{lab}')
    body = clip(cid, start, dur, inner, style=f"position:absolute; left:{x}px; top:{y}px; width:{w}px")
    js = "\n".join([f'    tl.fromTo("#{cid}", {{ opacity: 0, y: 30, scale: 0.94 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "power3.out" }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


def price_card(start, dur, marks, final_t, y):
    """RM200 / RM100 / RM50 struck through one by one, then 'Bawah lagi!'"""
    rows = "".join(f'<div id="pr{i}" style="position:relative;display:inline-block;margin:0 14px;font-weight:900;font-size:58px;color:#fff">{lbl}'
                   f'<span id="pr{i}x" style="position:absolute;left:-6px;right:-6px;top:50%;height:7px;margin-top:-3px;background:#ff3b5c;border-radius:4px;transform-origin:0 50%"></span></div>'
                   for i, (lbl, _) in enumerate(marks))
    inner = (f'<div style="padding:22px 26px;text-align:center">{rows}'
             f'<div id="prf" style="margin-top:12px;font-weight:900;font-size:64px;color:var(--neon);text-shadow:0 0 24px rgba(61,255,139,.55)">Bawah lagi!</div></div>')
    body = clip("price", start, dur, inner, cls="glass", style=f"left:90px; top:{y}px; width:780px")
    js = [f'    tl.fromTo("#price", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {fr(start)});',
          f'    tl.set([{", ".join(chr(34) + f"#pr{i}" + chr(34) for i in range(len(marks)))}, "#prf"], {{ opacity: 0 }}, {fr(start)});']
    for i, (_, t) in enumerate(marks):
        js += [f'    tl.fromTo("#pr{i}", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "power3.out" }}, {fr(t)});',
               f'    tl.fromTo("#pr{i}x", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power2.inOut" }}, {fr(t + 0.45)});']
    js += [f'    tl.fromTo("#prf", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, {fr(final_t)});',
           out("#price", start + dur)]
    return body, "\n".join(js)


def temp_card(start, dur, hot_t, cold_t, y):
    def row(rid, icon, lbl, deg, col):
        return (f'<div id="{rid}" style="display:flex;align-items:center;gap:18px;padding:14px 0">'
                f'<div style="width:72px;height:72px;border-radius:50%;background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;flex:none">'
                f'{icon.replace("<svg", "<svg width=42 height=42")}</div>'
                f'<div style="flex:1;font-weight:700;font-size:38px">{lbl}</div>'
                f'<div style="font-weight:900;font-size:54px;color:{col}">{deg}</div>'
                f'<div style="margin-left:14px;padding:8px 16px;border-radius:10px;background:#fff;color:#111;font-weight:800;font-size:32px">24 JAM</div></div>')
    inner = (f'<div style="padding:16px 28px">'
             f'<div style="font-weight:600;font-size:30px;color:rgba(255,255,255,.65);text-align:center;padding:6px 0 4px">Tahan suhu</div>'
             + row("tc-h", FLAME, "Panas", "40°C", "var(--hot)") + row("tc-c", SNOW, "Sejuk", "15°C", "var(--cold)") + '</div>')
    body = clip("temp", start, dur, inner, cls="glass", style=f"left:90px; top:{y}px; width:780px")
    js = "\n".join([f'    tl.fromTo("#temp", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {fr(start)});',
                    f'    tl.set(["#tc-h", "#tc-c"], {{ opacity: 0 }}, {fr(start)});',
                    f'    tl.fromTo("#tc-h", {{ opacity: 0, x: -24 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {fr(hot_t)});',
                    f'    tl.fromTo("#tc-c", {{ opacity: 0, x: -24 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, {fr(cold_t)});',
                    out("#temp", start + dur)])
    return body, js


def chrome(cid, text, start, dur, y):
    letters = "".join(f'<span class="ch{cid}">{html.escape(c)}</span>' for c in text)
    body = clip(cid, start, dur, f'<div class="chrome" style="top:{y}px">{letters}</div>', style="position:absolute; inset:0", extra=" data-layout-allow-overflow")
    js = "\n".join([f'    tl.fromTo(".ch{cid}", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out", stagger: 0.08 }}, {fr(start)});',
                    out(f"#{cid}", start + dur)])
    return body, js


# ---------------------------------------------------------------- scenes
# zones: first half the wall above / beside him is free (y 180-440); from s6 on his face is at the top, so overlays sit on the chest (y 520-860)
TOP = 270
CHEST = 540

build_scene("open", [
    head("op-h", "Kenapa nak beli<br/>yang mahal?", W("s1", 1.86) - 0.3, end("s1") - W("s1", 1.86) + 0.3, TOP),
    price_card(st("s2") + 0.1, end("s2") - st("s2") - 0.1, [("RM200", W("s2", 4.20)), ("RM100", W("s2", 5.44)), ("RM50", W("s2", 7.06))], W("s2", 8.10), TOP),
])

build_scene("legs", [
    chip("lg-best", "Memang terbaik", "star", W("s3", 10.70), W("s3", 12.34) - W("s3", 10.70), TOP),
    chip("lg-fold", "Kaki boleh lipat", "stand", W("s3", 13.96), W("s3", 19.14) - W("s3", 13.96), TOP, x=60),
    img_card("lg-img", "assets/img/tripod.jpg", None, W("s3", 14.82), W("s3", 19.14) - W("s3", 14.82), 60, TOP + 110, w=330),
    chip("lg-lock", "Lock kemas", "lock", W("s3", 19.14), W("s3", 20.26) - W("s3", 19.14) + 0.3, TOP),
    chip("lg-cup", "Muat cawan bawah paip", "cup", W("s3", 20.26) + 0.3, end("s3") - W("s3", 20.26) - 0.3, TOP),
])

build_scene("parts", [
    chip("pt-tap", "Paip getah", "tap", W("s4", 23.62), W("s4", 26.46) - W("s4", 23.62), TOP, x=430),
    img_card("pt-tapimg", "assets/img/faucet.jpg", None, W("s4", 23.62) + 0.2, W("s4", 26.46) - W("s4", 23.62) - 0.2, 600, TOP + 110, w=300),
    chip("pt-grip", "Pemegang kukuh", "hand", W("s4", 26.46), W("s4", 30.00) - W("s4", 26.46), TOP, x=60),
    chrome("pt-10l", "10L", W("s4", 30.00), end("s4") - W("s4", 30.00) + 0.5, 240),
])

build_scene("inside", [
    chip("in-steel", "Stainless steel", "steel", W("s5", 33.58), end("s5") - W("s5", 33.58), 1060),
    img_card("in-img", "assets/img/steel.jpg", "Dua lapis", W("s5", 32.92), end("s5") - W("s5", 32.92), 600, 1290, w=320),
])

build_scene("temp", [
    temp_card(W("s6", 36.28), W("s6", 46.28) - W("s6", 36.28), W("s6", 36.28) + 0.2, W("s6", 40.56), CHEST),
    chip("tp-baloi", "Memang berbaloi", "star", W("s6", 46.28), end("s6") - W("s6", 46.28) + 0.2, CHEST + 40),
])

shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:16px">'
        f'<div style="width:150px;height:150px;border-radius:18px;overflow:hidden;background:#fff;flex:none"><img src="assets/img/hero.jpg" alt="" style="width:150px;height:150px;object-fit:cover;object-position:30% 50%"/></div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:40px;letter-spacing:.01em">TONG AIR 10L</div>'
        f'<div style="font-weight:600;font-size:28px;color:rgba(255,255,255,.7);margin-top:4px">Panas &amp; sejuk 24 jam</div>'
        f'<div style="margin-top:6px;display:flex;align-items:center;gap:10px;font-weight:700;font-size:30px;color:rgba(255,255,255,.85)">{STAR.replace("<svg", "<svg width=30 height=30")} 4.3 &middot; 183.2K terjual</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:10px;padding:11px 26px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:34px;white-space:nowrap;box-shadow:0 12px 30px rgba(0,0,0,.4)">'
       '<svg viewBox="0 0 24 24" width="32" height="32" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Tekan link di bawah</div>')
SHOP0 = W("s7", 51.22)
build_scene("outro", [
    chip("ot-col", "Hitam &amp; warna lain", "palette", W("s7", 48.34), SHOP0 - W("s7", 48.34), CHEST),
    (clip("ot-shop", SHOP0, TOTAL - SHOP0, shop, cls="glass", style=f"left:110px; top:{CHEST}px; width:740px"),
     f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {SHOP0});'),
    (clip("ot-cta", SHOP0 + 0.5, TOTAL - SHOP0 - 0.5, cta, style=f"position:absolute; left:0; width:960px; top:{CHEST + 215}px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power3.out" }}, {fr(SHOP0 + 0.5)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.35, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }}, {W("s7", 52.94)});'])),
])

write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cw {{ position: absolute; left: 0; width: 960px; top: 1200px; text-align: center; }}
    .cw span {{ display: inline-block; font-family: var(--font-ui); font-weight: 900; font-size: 48px; color: #fff; letter-spacing: .01em;
      text-shadow: 0 0 3px rgba(0,0,0,.9), 0 2px 0 rgba(0,0,0,.5), 0 4px 18px rgba(0,0,0,.8); }}
""", "\n".join(cap_items), "\n".join(cap_js)))

# ---------------------------------------------------------------- index (no zoom jumps: one slow drift per take)
videos = [f'        <video id="{s["id"]}" class="clip seg" src="assets/raw.mp4" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" data-fade-in="0.06" data-fade-out="0.1" playsinline></video>' for s in segs]
cam = [f'      tl.fromTo("#cam", {{ scale: 1.0 }}, {{ scale: 1.035, duration: {fr(s["dur"])}, ease: "none", immediateRender: false }}, {s["start"]});' for s in segs]

SFX = [("sx-h", "whoosh.mp3", W("s1", 1.86) - 0.3, 0.2),
       ("sx-p", "whoosh-short.mp3", st("s2") + 0.1, 0.2),
       ("sx-p1", "click-soft.mp3", W("s2", 4.20) + 0.45, 0.3),
       ("sx-p2", "click-soft.mp3", W("s2", 5.44) + 0.45, 0.3),
       ("sx-p3", "click-soft.mp3", W("s2", 7.06) + 0.45, 0.3),
       ("sx-pf", "sparkle.mp3", W("s2", 8.10), 0.2),
       ("sx-best", "pop.mp3", W("s3", 10.70), 0.2),
       ("sx-fold", "pop.mp3", W("s3", 13.96), 0.2),
       ("sx-lock", "click-soft.mp3", W("s3", 19.14), 0.35),
       ("sx-cup", "pop.mp3", W("s3", 20.26) + 0.3, 0.2),
       ("sx-tap", "pop.mp3", W("s4", 23.62), 0.2),
       ("sx-grip", "pop.mp3", W("s4", 26.46), 0.2),
       ("sx-10l", "whoosh.mp3", W("s4", 30.00) - 0.1, 0.2),
       ("sx-steel", "sparkle.mp3", W("s5", 33.58), 0.2),
       ("sx-temp", "whoosh-short.mp3", W("s6", 36.28), 0.2),
       ("sx-cold", "pop.mp3", W("s6", 40.56), 0.2),
       ("sx-baloi", "sparkle.mp3", W("s6", 46.28), 0.2),
       ("sx-col", "pop.mp3", W("s7", 48.34), 0.2),
       ("sx-shop", "whoosh-short.mp3", SHOP0, 0.2)]


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

hosts = [("open", 2), ("legs", 3), ("parts", 4), ("inside", 5), ("temp", 6), ("outro", 7), ("captions", 8)]
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
      <!-- Footage: kept lines from raw.mp4 with natural pauses. Trim in Studio by dragging clip edges. -->
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
    print(f'{s["id"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:6.2f}-{s["src_out"]:6.2f}')
print(" | ".join(" ".join(w["text"] for w in p) for p in phrases))
