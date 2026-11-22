#!/usr/bin/env python3
"""Cordless chainsaw — reference style (white label chips + round black icon, glass cards, neon accent), calm pacing like
the insulated-bucket edit: lines kept whole with breathing room, phrase captions, soft long-held overlays, no zoom jumps.
Opens on the branch-cutting clip, closes on the box contents with a 'Tekan link sekarang' card.
Usage: python3 -I build.py <words.json> <project_dir>     (words of raw.mp4; cut.mp4 / box.mp4 are wordless b-roll)
"""
import json, sys, html, os, re, math, subprocess

WJ, P = sys.argv[1], sys.argv[2]
FPS = 30
WORDS = json.load(open(WJ))
SRC = {"v": "assets/raw.mp4", "c": "assets/cut.mp4", "b": "assets/box.mp4"}
PAD_IN, PAD_OUT = 0.18, 0.30


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(t):
    return min(WORDS, key=lambda w: abs(w["start"] - t))


# (id, src, first_word_start | src_in, last_word_start | src_out, volume)   — b-roll rows give raw in/out seconds
EDL = [
    ("c0", "c", 0.00, 4.40, 0.55),     # hook: cutting a branch (chainsaw sound, lowered)
    ("s1", "v", 0.78, 6.90, 1.0),      # kau tekan, tak ada apa. ni bukan aku kena tipu. ni ada safety tau. kau tekan button ni, kau tekan
    ("s2", "v", 9.92, 14.30, 1.0),     # memang padu kan. memang terbaik lah. kat sini kau boleh tengok dia punya peratus bateri
    ("s3", "v", 17.88, 22.46, 1.0),    # lepas tu kat sini kau boleh isi minyak rantai dia ... kau buka ni, kau isi minyak rantai dia
    ("s4", "v", 22.78, 31.38, 1.0),    # nak safety dia, dia dah bagi juga ... so safety lah. kalau potong pokok kau pun dia tak terbang kena tangan kau
    ("s5", "v", 33.02, 41.90, 1.0),    # setiap pembelian dia bagi charger, adapter. dia bagi sekali dengan box, memang lawa. kau boleh letak dalam ni. nak pindah, mudah alih
    ("s6", "v", 43.76, 47.20, 1.0),    # kat sini dia bagi sekali dengan cordless dia, bateri cordless dia
    ("s7", "v", 49.90, 53.58, 1.0),    # kau boleh masuk dari sini. mudah kan? memang lawa, memang terbaik
    ("s8", "v", 54.16, 58.46, 1.0),    # kau dah tengok tadi kan, aku potong pokok tadi kan? memang padu tak padu?
    ("c1", "c", 6.40, 8.70, 0.55),     # cutting again
    ("s9", "v", 63.86, 72.34, 1.0),    # paket pembelian ni ... rantai ... jangan risau ... screwdriver, kau boleh pasang
    ("sa", "v", 72.86, 77.60, 1.0),    # nak dapat mana benda ni? harga-harga memang kau boleh terkejut lah, sebab sekarang tengah ada promosi
    ("b0", "b", 0.20, 4.60, 0.6),      # box contents, CTA card
]

segs, f = [], 0
for sid, src, a, b, vol in EDL:
    if src == "v":
        w0, w1 = wat(a), wat(b)
        i0, i1 = WORDS.index(w0), WORDS.index(w1)
        prev_end = WORDS[i0 - 1]["end"] if i0 > 0 else 0
        next_start = WORDS[i1 + 1]["start"] if i1 + 1 < len(WORDS) else 1e9
        a = max(w0["start"] - PAD_IN, prev_end + 0.04) if i0 > 0 else max(0, w0["start"] - PAD_IN)
        b = min(w1["end"] + PAD_OUT, next_start - 0.06)
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
FIX = {"amrak": "kau", "ampak": "kau", "persen": "peratus", "main": "bagi", "school": "screw", "level": "driver"}
DROP = {"haa", "okay", "betul"}


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

# ---------------------------------------------------------------- tokens + pieces
TOK = """
      --ink: #ffffff;
      --dark: #0d0e10;
      --neon: #ffc72c;
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
LOW = 990
SIDE_Y = 760

build_scene("hook", [
    head("hk-h", "Potong dahan<br/><em>sekali lalu</em>", 0.3, end("c0") - 0.3, 300),
])

build_scene("safety", [
    chip("sf-safe", "Ada safety", "shield", W("s1", 4.00), W("s1", 5.32) - W("s1", 4.00), LOW),
    chip("sf-btn", "Tekan butang + picu", "power", W("s1", 5.32), end("s1") - W("s1", 5.32) + 0.2, LOW),
    chip("sf-best", "Memang terbaik", "star", W("s2", 9.92), W("s2", 11.88) - W("s2", 9.92), LOW),
    chip("sf-bat", "Paparan peratus bateri", "battery", W("s2", 11.88), end("s2") - W("s2", 11.88), LOW),
    img_card("sf-batimg", "assets/img/battery-led.jpg", None, W("s2", 12.14), end("s2") - W("s2", 12.14), 600, SIDE_Y - 140, w=330),
])

build_scene("oil", [
    chip("ol-oil", "Isi minyak rantai", "oil", W("s3", 18.78), end("s3") - W("s3", 18.78), LOW),
    img_card("ol-img", "assets/img/oil.jpg", None, W("s3", 19.18), end("s3") - W("s3", 19.18), 620, SIDE_Y - 60, w=300),
    chip("ol-guard", "Penghadang keselamatan", "shield", W("s4", 22.78), W("s4", 29.16) - W("s4", 22.78), LOW),
    chip("ol-hand", "Tak kena tangan", "shield", W("s4", 29.16), end("s4") - W("s4", 29.16) + 0.2, LOW),
])

build_scene("kit", [
    chip("kt-chg", "Charger + adapter", "plug", W("s5", 33.86), W("s5", 36.30) - W("s5", 33.86), LOW),
    chip("kt-box", "Kotak simpanan", "box", W("s5", 36.30), end("s5") - W("s5", 36.30), LOW),
    img_card("kt-boximg", "assets/img/storage.jpg", None, W("s5", 38.68), end("s5") - W("s5", 38.68), 590, SIDE_Y - 140, w=330),
    chip("kt-bat", "Bateri cordless", "battery", W("s6", 44.58), end("s6") - W("s6", 44.58), LOW),
    chip("kt-easy", "Senang pasang", "star", W("s7", 49.90), end("s7") - W("s7", 49.90), LOW),
    chip("kt-padu", "Memang padu", "star", W("s8", 57.10), end("s8") - W("s8", 57.10) + 0.2, LOW),
    head("kt-cut", "Laju &amp; <em>padu</em>", st("c1") + 0.2, end("c1") - st("c1") - 0.2, 300),
])

build_scene("pack", [
    chip("pk-chain", "Rantai ganti", "chain", W("s9", 66.34), W("s9", 69.64) - W("s9", 66.34), LOW),
    chip("pk-tool", "Screwdriver sekali", "tool", W("s9", 69.64), end("s9") - W("s9", 69.64), LOW),
    chip("pk-promo", "Tengah promosi", "tag", W("sa", 76.98), end("sa") - W("sa", 76.98) + 0.2, LOW),
])

shop = (f'<div style="display:flex;align-items:center;gap:20px;padding:18px 20px">'
        f'<div style="width:120px;height:120px;border-radius:50%;background:#111;flex:none;display:flex;align-items:center;justify-content:center;'
        f'font-weight:900;font-style:italic;font-size:29px;color:#ffc72c;letter-spacing:.02em">KEELAT</div>'
        f'<div style="flex:1"><div style="font-weight:900;font-size:38px">CHAINSAW CORDLESS</div>'
        f'<div style="margin-top:6px;display:flex;align-items:center;gap:10px;font-weight:700;font-size:30px;color:rgba(255,255,255,.85)">{STAR.replace("<svg", "<svg width=30 height=30")} 4.5 &middot; 415.3K terjual</div></div></div>')
cta = ('<div style="display:inline-flex;align-items:center;gap:12px;padding:16px 36px;border-radius:999px;background:#fe2c55;color:#fff;font-family:var(--font-ui);font-weight:900;font-size:44px;white-space:nowrap;box-shadow:0 14px 36px rgba(0,0,0,.45)">'
       '<svg viewBox="0 0 24 24" width="40" height="40" style="flex:none" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v15"/><path d="M5.5 12.5L12 19l6.5-6.5"/></svg>'
       'Tekan link sekarang</div>')
SHOP0 = W("sa", 72.86)
CTA0 = st("b0")
build_scene("outro", [
    (clip("ot-shop", SHOP0, TOTAL - SHOP0, shop, cls="glass", style=f"left:110px; top:{LOW - 200}px; width:740px"),
     "\n".join([f'    tl.fromTo("#ot-shop", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, {SHOP0});',
                f'    tl.to("#ot-shop", {{ y: -280, duration: 0.6, ease: "power3.inOut" }}, {CTA0});'])),
    (clip("ot-cta", CTA0, TOTAL - CTA0, cta, style="position:absolute; left:0; width:960px; top:860px; text-align:center"),
     "\n".join([f'    tl.fromTo("#ot-cta > div", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.55, ease: "back.out(1.5)" }}, {fr(CTA0 + 0.2)});',
                f'    tl.fromTo("#ot-cta > div", {{ scale: 1 }}, {{ scale: 1.05, duration: 0.45, ease: "sine.inOut", yoyo: true, repeat: 3, immediateRender: false }}, {fr(CTA0 + 0.9)});'])),
])

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

SFX = [("sx-h", "whoosh.mp3", 0.3, 0.2),
       ("sx-safe", "pop.mp3", W("s1", 4.00), 0.2),
       ("sx-btn", "click-soft.mp3", W("s1", 5.32), 0.35),
       ("sx-best", "pop.mp3", W("s2", 9.92), 0.2),
       ("sx-bat", "pop.mp3", W("s2", 11.88), 0.2),
       ("sx-oil", "pop.mp3", W("s3", 18.78), 0.2),
       ("sx-guard", "pop.mp3", W("s4", 22.78), 0.2),
       ("sx-chg", "pop.mp3", W("s5", 33.86), 0.2),
       ("sx-box", "pop.mp3", W("s5", 36.30), 0.2),
       ("sx-bat2", "pop.mp3", W("s6", 44.58), 0.2),
       ("sx-easy", "pop.mp3", W("s7", 49.90), 0.2),
       ("sx-padu", "sparkle.mp3", W("s8", 57.10), 0.2),
       ("sx-chain", "pop.mp3", W("s9", 66.34), 0.2),
       ("sx-tool", "pop.mp3", W("s9", 69.64), 0.2),
       ("sx-shop", "whoosh-short.mp3", SHOP0, 0.2),
       ("sx-promo", "pop.mp3", W("sa", 76.98), 0.2),
       ("sx-cta", "sparkle.mp3", CTA0 + 0.2, 0.3)]


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

hosts = [("hook", 2), ("safety", 3), ("oil", 4), ("kit", 5), ("pack", 6), ("outro", 7), ("captions", 8)]
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
      <!-- Footage: raw.mp4 (talking review), cut.mp4 (cutting branches), box.mp4 (box contents). Trim in Studio by dragging clip edges. -->
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
