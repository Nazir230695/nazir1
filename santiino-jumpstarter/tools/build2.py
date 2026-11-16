#!/usr/bin/env python3
"""Santiino 4-in-1 jump starter: EDL + transcript -> HyperFrames project.
Usage: python3 -I build2.py <words.json> <project_dir>
"""
import json, sys, html, os, re, subprocess

WORDS = json.load(open(sys.argv[1]))
P = sys.argv[2]
FPS = 30
VIDEO = "assets/santiino.mp4"


def fr(t):
    return round(round(t * FPS) / FPS, 4)


def wat(t):
    """word whose start is closest to t"""
    return min(WORDS, key=lambda w: abs(w["start"] - t))


# ---------------------------------------------------------------- EDL
# ("w", first_word_start, last_word_start) -> padded word span; ("r", in, out) -> raw source span
EDL = [
    # hook: flash-forward to the payoff
    ("h1", "r", 98.40, 99.95, 1.00, "engine cranks"),
    ("h2", "w", 101.68, 102.58, 1.10, "Memang terbaik lah."),
    # problem
    ("a1", "w", 1.34, 2.62, 1.00, "Abang nampak bateri dah kong"),
    ("a2", "w", 5.08, 6.88, 1.12, "kalau kereta pun jenis parking lama"),
    ("a3", "w", 8.66, 9.88, 1.00, "abang kena standby satu benda ni"),
    ("a4", "w", 19.00, 19.86, 1.12, "all in one, jump starter"),
    # design
    ("b1", "w", 22.42, 24.82, 1.00, "abang nampak ni dia main sekali dengan tempat pegang sini"),
    ("b2", "w", 34.46, 36.22, 1.12, "daripada Santiino memang lawa"),
    # features
    ("c1", "w", 44.96, 47.18, 1.00, "dia kegunaan dia nak pump tayar pun boleh"),
    ("c2", "w", 48.28, 50.28, 1.10, "nak jumper pun boleh, 2 dalam 1"),
    ("c3", "w", 51.56, 53.98, 1.00, "abang nampak dia boleh cas guna Type-C memang mudah"),
    # demo
    ("d1", "w", 67.40, 69.26, 1.12, "abang boleh cucuk kat sini je tau"),
    ("d2", "w", 70.74, 73.42, 1.00, "nampak dia akan menyala lampu macam ni tau"),
    ("d3", "w", 76.42, 78.20, 1.12, "abang masuk yang hitam ke hitam"),
    ("d4", "w", 81.98, 83.52, 1.00, "yang merah ni masuk ke merah"),
    ("d5", "w", 91.28, 91.96, 1.10, "jom kita start tengok"),
    # payoff
    ("p1", "w", 96.94, 96.94, 1.00, "Bismillahirrahmanirrahim"),
    ("p2", "r", 98.02, 100.40, 1.08, "engine start"),
    ("p3", "w", 100.48, 102.58, 1.00, "Tengok. Sekali lah. Memang terbaik lah."),
    # travel / emergency
    ("e1", "w", 108.54, 114.12, 1.10, "kalau suka travel... untuk emergency memang mudah benda ni"),
    # pump
    ("f1", "w", 115.46, 117.08, 1.00, "nak isi tayar angin pun boleh"),
    ("f2", "w", 141.60, 146.58, 1.12, "untuk tayar basikal, motor, bola, kereta"),
    ("f3", "w", 161.46, 162.34, 1.00, "dia bagi sekali dengan tube ni"),
    # light + CTA
    ("g1", "w", 164.44, 166.32, 1.10, "kat sini abang boleh tekan lampu dia juga"),
    ("z1", "w", 171.62, 174.10, 1.00, "memang sangat sesuai benda ni. nak dapat, tekan link"),
]

segs, f = [], 0
for sid, kind, a, b, sc, note in EDL:
    if kind == "w":
        w0, w1 = wat(a), wat(b)
        i0, i1 = WORDS.index(w0), WORDS.index(w1)
        prev_end = WORDS[i0 - 1]["end"] if i0 > 0 else 0
        next_start = WORDS[i1 + 1]["start"] if i1 + 1 < len(WORDS) else 1e9
        a = min(w0["start"] - 0.02, max(w0["start"] - 0.07, prev_end + 0.02))
        b = max(w1["start"] + 0.15, min(min(w1["end"], w1["start"] + 1.2) + 0.1, next_start - 0.03))
    fa, fb = round(a * FPS), round(b * FPS)
    segs.append(dict(id=sid, src_in=fa / FPS, src_out=fb / FPS, start=f / FPS, dur=(fb - fa) / FPS,
                     scale=sc, note=note))
    f += fb - fa
import math
for sg in segs:
    sg["src_in"] = round(sg["src_in"], 4); sg["src_out"] = round(sg["src_out"], 4)
    sg["start"] = math.ceil(sg["start"] * 10000 - 1e-6) / 10000
    sg["dur"] = math.floor(sg["dur"] * 10000 + 1e-6) / 10000 - 0.0001
TOTAL = round(f / FPS, 4)
HOOK_END = next(s for s in segs if s["id"] == "a1")["start"]


def out(src, prefer=None):
    """source time -> output time; prefer a segment id (the payoff also appears in the hook)."""
    cands = [s for s in segs if s["src_in"] - 1e-6 <= src <= s["src_out"] + 1e-6]
    if prefer:
        cands = [s for s in cands if s["id"].startswith(prefer)] or cands
    cands = [s for s in cands if not s["id"].startswith("h")] or cands
    if not cands:
        return None
    s = cands[0]
    return fr(s["start"] + (src - s["src_in"]))


def W(t):
    o = out(wat(t)["start"])
    if o is None:
        raise ValueError(t)
    return o


# ---------------------------------------------------------------- captions
ABANG = {"apa", "ampun", "ampo", "aku", "mumpa"}
FIX = {"tayo": "tayar", "bisikal": "basikal", "cah": "cas", "tire": "tayar", "limbo": "link",
       "beletak": "letak", "santino": "Santiino", "tube": "tiub", "pump": "pam", "jumpa": "jumper"}
HL = {"bateri", "kong", "parking", "lama", "standby", "all", "in", "one", "jump", "starter", "pegang",
      "santiino", "lawa", "pam", "tayar", "jumper", "2", "1", "type-c", "c", "mudah", "cucuk", "lampu",
      "hitam", "merah", "start", "terbaik", "sekali", "travel", "emergency", "angin", "basikal", "motor",
      "bola", "kereta", "tiub", "sesuai", "link"}


def norm(txt):
    core = re.sub(r"[^\w-]", "", txt).lower()
    punct = txt[len(txt.rstrip(".,!?")):]
    if core in ABANG:
        return "abang" + punct
    if core in FIX:
        return FIX[core] + punct
    return txt


kept = []
for s in segs:
    if s["id"].startswith("h"):
        continue  # the hook carries its own headline
    for w in WORDS:
        if s["src_in"] <= w["start"] < s["src_out"] - 0.05:
            st = fr(s["start"] + w["start"] - s["src_in"])
            en = fr(s["start"] + min(w["end"], s["src_out"]) - s["src_in"])
            txt = norm(w["text"])
            if re.sub(r"[^\w]", "", txt).lower() in {"haa", "ok", "okay", "tuh", "tu"}:
                continue
            if txt.lower().strip(".,") == "bismillahirrahmanirrahim":
                txt = "Bismillah."
            kept.append(dict(text=txt, start=st, end=max(en, st + 0.1), seg=s["id"]))
# merge "type" + "C"
merged = []
for w in kept:
    if merged and merged[-1]["text"].lower() == "type" and w["text"].lower().startswith("c"):
        merged[-1]["text"] = "Type-C"; merged[-1]["end"] = w["end"]
    else:
        merged.append(w)
kept = merged

phrases, cur = [], []
for w in kept:
    if cur and (w["start"] - cur[-1]["end"] >= 0.15 or w["seg"] != cur[-1]["seg"]
                or re.search(r"[.!?,]$", cur[-1]["text"])):
        phrases.append(cur); cur = []
    cur.append(w)
phrases.append(cur)
groups = []
for ph in phrases:
    n = len(ph); k = max(1, -(-n // 3)); base, extra = divmod(n, k); i = 0
    for c in range(k):
        size = base + (1 if c < extra else 0); groups.append(ph[i:i + size]); i += size
# lone 1-word groups join a neighbour in the same segment when it stays <= 3 words
fixed = []
for g in groups:
    if fixed and (len(g) == 1 or len(fixed[-1]) == 1) and len(fixed[-1]) + len(g) <= 3 \
            and fixed[-1][-1]["seg"] == g[0]["seg"] and g[0]["start"] - fixed[-1][-1]["end"] < 0.4:
        fixed[-1] = fixed[-1] + g
    else:
        fixed.append(g)
groups = fixed

CTA_AT = W(171.62) - 0.05
groups = [g for g in groups if g[0]["start"] < CTA_AT - 0.05]
cap_items, cap_js = [], []
for gi, g in enumerate(groups):
    gid = f"cap{gi:02d}"
    g_start = fr(max(g[0]["start"] - 0.04, HOOK_END + 0.05))
    nxt = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else TOTAL
    g_end = fr(min(max(g[-1]["end"] + 0.12, g_start + 0.45), nxt - 0.02, TOTAL - 0.04, CTA_AT))
    spans = []
    for wi, w in enumerate(g):
        word = w["text"].strip(",.!?").upper()
        hl = " hl" if word.lower() in HL else ""
        spans.append(f'<span id="{gid}w{wi}" class="w{hl}">{html.escape(word)}</span>')
        cap_js.append(f'  pop("#{gid}w{wi}", {max(w["start"], g_start):.3f});')
    cap_items.append(f'    <div id="{gid}" class="cap clip" data-start="{g_start}" data-duration="{fr(g_end - g_start)}" '
                     f'data-track-index="0"><div id="{gid}l" class="line">{" ".join(spans)}</div></div>')
    cap_js.append(f'  kill("#{gid}l", {g_end:.3f});')

# ---------------------------------------------------------------- moments (output seconds)
crank = out(98.10, "p2")
T = dict(
    parking=W(6.64), all=W(19.00), pegang=W(24.44), santiino=W(34.86), kegunaan=W(45.26),
    pump=W(46.28), jumper=W(48.84), duadalam=W(49.76), typec=W(53.28), cucuk=W(68.48),
    lampu=W(71.34), hitam=W(77.68), merah=W(82.26), start=W(91.62), crank=crank, sekali=W(100.94),
    travel=W(109.42), emergency=W(112.46), angin=W(116.42), basikal=W(142.94), motor=W(144.20),
    bola=W(145.28), kereta=W(146.58), tube=W(162.10), lampuled=W(165.88), cta=CTA_AT,
)
json.dump(dict(total=TOTAL, segs=segs, T=T, groups=[[w["text"] for w in g] for g in groups]),
          open(os.path.join(P, ".edl.json"), "w"), indent=1, ensure_ascii=False)


def seg_end(sid):
    s = next(x for x in segs if x["id"] == sid)
    return fr(s["start"] + s["dur"])


# ---------------------------------------------------------------- styles + icons
TOK = """
      --accent: #ffc21a;
      --ink: #ffffff;
      --glass: rgba(10, 14, 16, 0.80);
      --teal: #1f8f7a;
      --danger: #ff3b4e;
      --font-display: "Archivo Black", "Montserrat", sans-serif;
      --font-ui: "Montserrat", sans-serif;
"""
SV = 'viewBox="0 0 24 24" fill="none" stroke="#111" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"'
ICON = {
    "battery": f'<svg {SV}><rect x="2.5" y="7" width="17" height="10" rx="2"/><path d="M21.5 10.5v3"/><path d="M6 10v4"/></svg>',
    "bolt": f'<svg {SV}><path d="M13 2 4.5 13.5H12L11 22l8.5-11.5H12z"/></svg>',
    "gauge": f'<svg {SV}><path d="M4 16a8 8 0 1 1 16 0"/><path d="M12 16l4-5"/><circle cx="12" cy="16" r="1.4"/></svg>',
    "usb": f'<svg {SV}><rect x="7" y="9" width="10" height="12" rx="2"/><path d="M9.5 9V4.5h5V9"/><path d="M10.5 6h0M13.5 6h0"/></svg>',
    "hand": f'<svg {SV}><path d="M7 11V6.5a1.5 1.5 0 0 1 3 0V11"/><path d="M10 10.5V5a1.5 1.5 0 0 1 3 0v5.5"/><path d="M13 10.5V6.5a1.5 1.5 0 0 1 3 0V13"/><path d="M16 11a1.5 1.5 0 0 1 3 0v3a7 7 0 0 1-7 7h-1a6 6 0 0 1-5-2.7L3.6 14.6a1.5 1.5 0 0 1 2.5-1.7L7 14"/></svg>',
    "star": f'<svg {SV}><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
    "plug": f'<svg {SV}><path d="M9 2v5M15 2v5"/><path d="M6 7h12v4a6 6 0 0 1-12 0z"/><path d="M12 17v5"/></svg>',
    "light": f'<svg {SV}><path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/></svg>',
    "minus": f'<svg {SV} stroke-width="3.2"><path d="M6 12h12"/></svg>',
    "plus": f'<svg {SV} stroke-width="3.2"><path d="M6 12h12M12 6v12"/></svg>',
    "key": f'<svg {SV}><circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l2 2M15 8l2 2"/></svg>',
    "car": f'<svg {SV}><path d="M3 16v-3l2-5h14l2 5v3"/><path d="M3 16h18"/><circle cx="7.5" cy="16.5" r="1.8"/><circle cx="16.5" cy="16.5" r="1.8"/></svg>',
    "bike": f'<svg {SV}><circle cx="5.5" cy="16" r="3.5"/><circle cx="18.5" cy="16" r="3.5"/><path d="M5.5 16l4-7h6l3 7M9.5 9l3 7h-7M14 6h3"/></svg>',
    "moto": f'<svg {SV}><circle cx="5" cy="16" r="3"/><circle cx="19" cy="16" r="3"/><path d="M5 16h6l3-5h4l1 5M14 11l-2-4h-2M16 7h3"/></svg>',
    "ball": f'<svg {SV}><circle cx="12" cy="12" r="9"/><path d="M12 7l4 3-1.5 4.5h-5L8 10z"/><path d="M12 3v4M21 10l-5 0M3 10h5M7 20l2.5-5.5M17 20l-2.5-5.5"/></svg>',
    "tube": f'<svg {SV}><path d="M4 20c4 0 4-6 8-6s4-6 8-6"/><rect x="2" y="18" width="4" height="4" rx="1"/><path d="M19 4l2 2-3 3-2-2z"/></svg>',
    "shield": f'<svg {SV}><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></svg>',
    "check": f'<svg {SV} stroke-width="3"><path d="M4 12.5l5 5L20 6.5"/></svg>',
}

CARD_CSS = f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .card {{ position: absolute; left: 92px; top: 860px; display: flex; align-items: center; gap: 22px;
      padding: 20px 34px 20px 22px; border-radius: 28px; background: var(--glass);
      border: 2px solid rgba(255,255,255,.14); box-shadow: 0 18px 50px rgba(0,0,0,.5);
      backdrop-filter: blur(18px); color: var(--ink); font-family: var(--font-ui); }}
    .card .ic {{ width: 80px; height: 80px; border-radius: 20px; background: var(--accent);
      display: flex; align-items: center; justify-content: center; flex: none; }}
    .card .ic svg {{ width: 50px; height: 50px; }}
    .card .ic.num {{ font-family: var(--font-display); font-size: 48px; color: #111; }}
    .card .k {{ font-size: 30px; font-weight: 600; opacity: .8; letter-spacing: .05em; text-transform: uppercase; }}
    .card .t {{ font-size: 46px; font-weight: 800; line-height: 1.05; text-transform: uppercase; }}
    .card .t b {{ color: var(--accent); font-weight: 800; }}
    .row {{ position: absolute; left: 40px; right: 120px; top: 760px; text-align: center; font-family: var(--font-ui); }}
    .row .ttl {{ display: inline-block; padding: 10px 26px; border-radius: 999px; background: var(--accent); color: #111;
      font-weight: 800; font-size: 34px; letter-spacing: .06em; text-transform: uppercase; }}
    .row .items {{ margin-top: 22px; display: flex; justify-content: center; gap: 14px; }}
    .row .it {{ width: 180px; padding: 22px 8px 18px; border-radius: 26px; background: var(--glass);
      border: 2px solid rgba(255,255,255,.14); box-shadow: 0 18px 50px rgba(0,0,0,.45); color: var(--ink); }}
    .row .it .ic {{ width: 88px; height: 88px; margin: 0 auto; border-radius: 24px; background: var(--accent);
      display: flex; align-items: center; justify-content: center; }}
    .row .it .ic svg {{ width: 56px; height: 56px; }}
    .row .it .n {{ margin-top: 12px; font-weight: 800; font-size: 32px; text-transform: uppercase; }}
"""


def card(cid, icon, k, t, start, dur, top=860, num=None, var=None):
    dur = max(dur, 1.0)
    ic = f'<div class="ic num">{num}</div>' if num else f'<div class="ic">{ICON[icon]}</div>'
    vt = f' data-var-text="{var}"' if var else ""
    return (f'    <div id="{cid}" class="card clip" data-start="{start}" data-duration="{dur}" data-track-index="0" '
            f'style="top:{top}px">{ic}<div><div class="k">{k}</div><div class="t"{vt}>{t}</div></div></div>')


def card_js(cid, start, dur):
    dur = max(dur, 1.0)
    return (f'    tl.fromTo("#{cid}", {{ opacity: 0, x: -60, filter: "blur(10px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, {start});\n'
            f'    tl.to("#{cid}", {{ opacity: 0, x: 40, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(start + dur - 0.24)});')


def row(rid, title, items, start, dur, top=760):
    its = "".join(f'<div id="{rid}-i{i}" class="it"><div class="ic">{ICON[ic]}</div><div class="n">{n}</div></div>'
                  for i, (ic, n, _) in enumerate(items))
    return (f'    <div id="{rid}" class="row clip" data-start="{start}" data-duration="{dur}" data-track-index="1" style="top:{top}px">'
            f'<div id="{rid}-ttl" class="ttl">{title}</div><div class="items">{its}</div></div>')


def row_js(rid, items, start, dur):
    js = [f'    tl.fromTo("#{rid}-ttl", {{ opacity: 0, y: -16 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, {start});',
          f'    tl.set([{", ".join(f"{chr(34)}#{rid}-i{i}{chr(34)}" for i in range(len(items)))}], {{ opacity: 0 }}, {start});']
    for i, (_, _, at) in enumerate(items):
        js.append(f'    tl.fromTo("#{rid}-i{i}", {{ opacity: 0, y: 40, scale: 0.8 }}, {{ opacity: 1, y: 0, scale: 1, duration: 0.42, ease: "back.out(1.6)" }}, {at});')
    js.append(f'    tl.to("#{rid}", {{ opacity: 0, y: -30, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(start + dur - 0.24)});')
    return "\n".join(js)


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


# ---- hook
hook_dur = HOOK_END
h2s = next(s for s in segs if s["id"] == "h2")["start"]
write("hook.html", scene("hook", CARD_CSS + f"""
    #hk-shade {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(0,0,0,.7) 0%, rgba(0,0,0,.2) 38%, rgba(0,0,0,0) 60%); }}
    #hk-copy {{ position: absolute; left: 0; right: 120px; top: 250px; text-align: center; }}
    #hk-q {{ font-family: var(--font-display); font-size: 120px; line-height: .95; color: #fff; text-transform: uppercase;
      text-shadow: 0 10px 40px rgba(0,0,0,.6); }}
    #hk-a {{ margin-top: 14px; display: inline-block; padding: 8px 30px 14px; font-family: var(--font-display); font-size: 92px;
      color: #111; background: var(--accent); border-radius: 22px; text-transform: uppercase; transform: rotate(-3deg); }}
""", f"""    <div id="hk-shade" class="clip" data-start="0" data-duration="{hook_dur}" data-track-index="0"></div>
    <div id="hk-copy" class="clip" data-start="0" data-duration="{hook_dur}" data-track-index="1">
      <div id="hk-q" data-var-text="hookQ">Bateri kong?</div>
      <div><span id="hk-a" data-var-text="hookA">Sekali start je</span></div>
    </div>""", f"""    tl.fromTo("#hk-q", {{ opacity: 0.0, scale: 1.2 }}, {{ opacity: 1, scale: 1, duration: 0.22, ease: "power4.out" }}, 0);
    tl.fromTo("#hk-a", {{ opacity: 0, scale: 0.4, rotation: -12 }}, {{ opacity: 1, scale: 1, rotation: -3, duration: 0.4, ease: "back.out(1.8)" }}, {fr(h2s)});
    tl.to("#hk-copy", {{ opacity: 0, y: -40, filter: "blur(10px)", duration: 0.2, ease: "power3.in" }}, {fr(hook_dur - 0.22)});"""))

# ---- callouts-a: problem / reveal / design / brand
d_park = fr(W(8.66) - T["parking"] - 0.05)
d_all = fr(seg_end("a4") - T["all"] + 0.6)
T["pegang"] = fr(next(x for x in segs if x["id"] == "b1")["start"] + 0.9)
d_peg = fr(T["santiino"] - T["pegang"] - 0.08)
d_br = fr(seg_end("b2") - T["santiino"])
write("callouts-a.html", scene("callouts-a", CARD_CSS + """
    #ca-rev { position: absolute; left: 40px; right: 160px; top: 380px; text-align: center; }
    #ca-prod { width: 330px; height: 518px; object-fit: cover; border-radius: 30px; border: 4px solid var(--accent);
      box-shadow: 0 24px 70px rgba(0,0,0,.6); display: block; margin: 0 auto; }
    #ca-ttl { display: inline-block; margin-top: 22px; padding: 18px 34px 22px; border-radius: 28px; background: var(--glass);
      border: 2px solid rgba(255,255,255,.14); font-family: var(--font-display); font-size: 66px; line-height: .98; color: #fff;
      text-transform: uppercase; box-shadow: 0 18px 50px rgba(0,0,0,.5); }
    #ca-ttl b { color: var(--accent); font-weight: inherit; }
""", "\n".join([
    card("ca-park", "battery", "Parking lama?", "Bateri <b>kong</b>", T["parking"], d_park),
    f'    <div id="ca-rev" class="clip" data-start="{T["all"]}" data-duration="{d_all}" data-track-index="1">'
    f'<img id="ca-prod" src="assets/img/product.jpg" alt="" /><div id="ca-ttl">All in one<br/><b>Jump Starter</b></div></div>',
    card("ca-peg", "hand", "Rekaan", "Ada <b>tempat pegang</b>", T["pegang"], d_peg),
    card("ca-brand", "star", "Daripada", "<b>Santiino</b> · lawa", T["santiino"], d_br, var="brand"),
]), "\n".join([
    card_js("ca-park", T["parking"], d_park),
    f'    tl.fromTo("#ca-prod", {{ opacity: 0, scale: 0.5, rotation: -8 }}, {{ opacity: 1, scale: 1, rotation: 0, duration: 0.55, ease: "back.out(1.5)" }}, {T["all"]});',
    f'    tl.fromTo("#ca-ttl", {{ opacity: 0, y: 30, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {fr(T["all"] + 0.25)});',
    f'    tl.to("#ca-rev", {{ opacity: 0, scale: 0.9, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(T["all"] + d_all - 0.24)});',
    card_js("ca-peg", T["pegang"], d_peg),
    card_js("ca-brand", T["santiino"], d_br),
])))

# ---- callouts-b: features (2-in-1 row, Type-C)
items_b = [("gauge", "Pam tayar", T["pump"]), ("bolt", "Jump start", T["jumper"])]
d_rowb = fr(seg_end("c2") - T["kegunaan"] + 0.9)
d_tc = fr(seg_end("c3") - T["typec"] + 0.1)
write("callouts-b.html", scene("callouts-b", CARD_CSS + """
    #cb-21 { position: absolute; left: 0; right: 120px; top: 1040px; text-align: center; }
    #cb-21 span { display: inline-block; font-family: var(--font-display); font-size: 64px; color: var(--accent);
      text-transform: uppercase; text-shadow: 0 8px 26px rgba(0,0,0,.6); }
""", "\n".join([
    row("cb-row", "Kegunaan", items_b, T["kegunaan"], d_rowb),
    f'    <div id="cb-21" class="clip" data-start="{T["duadalam"]}" data-duration="{fr(seg_end("c2") - T["duadalam"] + 0.9)}" data-track-index="2"><span id="cb-21s">2 dalam 1</span></div>',
    card("cb-tc", "usb", "Cas mudah", "Guna <b>Type-C</b>", T["typec"], d_tc),
]), "\n".join([
    row_js("cb-row", items_b, T["kegunaan"], d_rowb),
    f'    tl.fromTo("#cb-21s", {{ opacity: 0, scale: 1.8 }}, {{ opacity: 1, scale: 1, duration: 0.25, ease: "power4.in" }}, {T["duadalam"]});',
    card_js("cb-tc", T["typec"], d_tc),
])))

# ---- callouts-c: demo steps
steps = [("cc-s1", "1", "Langkah 1", "Cucuk <b>smart clamp</b>", T["cucuk"], seg_end("d1")),
         ("cc-s2", None, "Lampu hijau", "<b>Sedia</b> guna", T["lampu"], seg_end("d2")),
         ("cc-s3", "2", "Langkah 2", "<b>Hitam</b> ke negatif (−)", T["hitam"], seg_end("d3")),
         ("cc-s4", "3", "Langkah 3", "<b>Merah</b> ke positif (+)", T["merah"], seg_end("d4")),
         ("cc-s5", "4", "Langkah 4", "<b>Start</b> enjin", T["start"], seg_end("d5"))]
body_c, js_c = [], []
for i, (cid, num, k, txt, st, en) in enumerate(steps):
    nxt = steps[i + 1][4] if i + 1 < len(steps) else 1e9
    d = fr(min(nxt - 0.06, max(en - st, 1.45)))
    body_c.append(card(cid, "light", k, txt, st, d, num=num))
    js_c.append(card_js(cid, st, d))
write("callouts-c.html", scene("callouts-c", CARD_CSS, "\n".join(body_c), "\n".join(js_c)))

# ---- callouts-d: payoff + emergency
d_ok = fr(seg_end("p3") - T["sekali"])
d_em = fr(seg_end("e1") - T["travel"])
write("callouts-d.html", scene("callouts-d", CARD_CSS + """
    #cd-start { position: absolute; left: 40px; right: 160px; top: 700px; text-align: center; }
    #cd-start span { display: inline-block; padding: 10px 46px 20px; font-family: var(--font-display); font-size: 136px;
      color: var(--accent); border: 12px solid var(--accent); border-radius: 30px; text-transform: uppercase;
      background: rgba(0,0,0,.3); text-shadow: 0 10px 34px rgba(0,0,0,.5); }
""", "\n".join([
    f'    <div id="cd-start" class="clip" data-start="{fr(T["crank"] - 0.1)}" data-duration="{fr(seg_end("p2") - T["crank"] + 0.1)}" data-track-index="1"><span id="cd-start-s">Start!</span></div>',
    card("cd-ok", "check", "Terbukti", "Sekali <b>start</b> je!", T["sekali"], d_ok),
    card("cd-em", "shield", "Wajib dalam kereta", "Travel &amp; <b>emergency</b>", T["travel"], d_em),
]), "\n".join([
    f'    tl.fromTo("#cd-start-s", {{ opacity: 0, scale: 2.4, rotation: -10 }}, {{ opacity: 1, scale: 1, rotation: -6, duration: 0.28, ease: "power4.in" }}, {fr(T["crank"] - 0.1)});',
    f'    tl.to("#cd-start-s", {{ opacity: 0, scale: 1.1, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, {fr(seg_end("p2") - 0.24)});',
    card_js("cd-ok", T["sekali"], d_ok),
    card_js("cd-em", T["travel"], d_em),
])))

# ---- callouts-e: pump, uses, tube, light
items_e = [("bike", "Basikal", T["basikal"]), ("moto", "Motor", T["motor"]), ("ball", "Bola", T["bola"]), ("car", "Kereta", T["kereta"])]
f1s = next(x for x in segs if x["id"] == "f1")["start"]
T["angin"] = fr(f1s + 0.1)
d_ang = fr(seg_end("f1") - T["angin"])
f2s = next(s for s in segs if s["id"] == "f2")["start"]
d_rowe = fr(seg_end("f2") - f2s + 0.7)
T["tube"] = max(T["tube"], fr(f2s + d_rowe + 0.05))
d_tube = fr(seg_end("f3") - T["tube"] + 0.05)
d_led = fr(seg_end("g1") - T["lampuled"])
write("callouts-e.html", scene("callouts-e", CARD_CSS, "\n".join([
    card("ce-ang", "gauge", "Pam angin", "Isi <b>angin tayar</b>", T["angin"], d_ang),
    row("ce-row", "Boleh isi angin", items_e, f2s, d_rowe),
    card("ce-tube", "tube", "Free", "<b>Tiub</b> disertakan", T["tube"], d_tube),
    card("ce-led", "light", "Bonus", "<b>Lampu LED</b>", T["lampuled"], d_led),
]), "\n".join([
    card_js("ce-ang", T["angin"], d_ang),
    row_js("ce-row", items_e, f2s, d_rowe),
    card_js("ce-tube", T["tube"], d_tube),
    card_js("ce-led", T["lampuled"], d_led),
])))

# ---- CTA
d_cta = fr(TOTAL - CTA_AT)
write("cta.html", scene("cta", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    #ct-box {{ position: absolute; left: 40px; right: 200px; top: 720px; text-align: center; font-family: var(--font-ui); }}
    #ct-prod {{ display: inline-block; padding: 12px 30px; border-radius: 999px; background: var(--teal); color: #fff;
      font-weight: 900; font-size: 40px; letter-spacing: .05em; text-transform: uppercase; }}
    #ct-main {{ margin-top: 18px; font-family: var(--font-display); font-size: 104px; line-height: .95; color: #fff;
      text-transform: uppercase; text-shadow: 0 10px 34px rgba(0,0,0,.6); }}
    #ct-main b {{ color: var(--accent); font-weight: inherit; }}
    #ct-arrow {{ position: absolute; left: 110px; top: 1150px; width: 150px; height: 150px; }}
""", f"""    <div id="ct-box" class="clip" data-start="{CTA_AT}" data-duration="{d_cta}" data-track-index="0">
      <div><span id="ct-prod" data-var-text="ctaProduct">Santiino 4-in-1</span></div>
      <div id="ct-main">Tekan<br/><b>link</b> sekarang</div>
    </div>
    <svg id="ct-arrow" class="clip" data-start="{fr(CTA_AT + 0.3)}" data-duration="{fr(d_cta - 0.3)}" data-track-index="1" viewBox="0 0 100 100" fill="none" stroke="#ffc21a" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"><path d="M78 12 C70 50 50 70 22 84 M22 84 L26 58 M22 84 L48 84"/></svg>""",
    f"""    tl.fromTo("#ct-prod", {{ opacity: 0, scale: 0.5 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.7)" }}, {CTA_AT});
    tl.fromTo("#ct-main", {{ opacity: 0, y: 30, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {fr(CTA_AT + 0.12)});
    tl.fromTo("#ct-arrow", {{ opacity: 0, x: 30, y: -30 }}, {{ opacity: 1, x: 0, y: 0, duration: 0.3, ease: "expo.out" }}, {fr(CTA_AT + 0.3)});
    tl.to("#ct-arrow", {{ x: -10, y: 10, duration: 0.3, ease: "power2.inOut" }}, {fr(CTA_AT + 0.7)});"""))

# ---- captions
write("captions.html", scene("captions", f"""
    #root {{ position: absolute; inset: 0; pointer-events: none; {TOK} }}
    .cap {{ position: absolute; left: 80px; width: 760px; top: 1110px; text-align: center; overflow: visible; }}
    .cap .line {{ display: inline-block; max-width: 760px; font-family: var(--font-display); font-size: 72px; line-height: 1.04;
      color: var(--ink); text-transform: uppercase; -webkit-text-stroke: 3px rgba(0,0,0,.85); paint-order: stroke fill;
      text-shadow: 0 6px 0 rgba(0,0,0,.55), 0 10px 30px rgba(0,0,0,.55); }}
    .cap .w {{ display: inline-block; }}
    .cap .w.hl {{ color: var(--accent); }}
""", "\n".join(cap_items), """    const pop = (sel, t) => tl.fromTo(sel, { scale: 0.7, opacity: 0, y: 14 }, { scale: 1, opacity: 1, y: 0, duration: 0.16, ease: "back.out(2)" }, t);
    const kill = (sel, end) => { tl.to(sel, { opacity: 0, duration: 0.08, ease: "power2.in" }, end - 0.08); };
""" + "\n".join("  " + l for l in cap_js)))

# ---------------------------------------------------------------- index.html
videos = [f'        <video id="{s["id"]}" class="clip seg" src="{VIDEO}" data-start="{s["start"]}" data-duration="{s["dur"]}" '
          f'data-media-start="{s["src_in"]}" data-track-index="1" data-has-audio="true" data-volume="1" playsinline></video>'
          for s in segs]
cam = [f'      tl.set("#cam", {{ scale: {s["scale"]} }}, {s["start"]});' for s in segs]
cam += [f'      tl.to("#cam", {{ scale: 1.2, duration: 0.2, ease: "power4.out" }}, {fr(T["crank"])});',
        f'      tl.to("#cam", {{ scale: 1.08, duration: 0.6, ease: "power2.inOut" }}, {fr(T["crank"] + 1.0)});']

SFX = [("sfx-hook", "impact-bass-1.mp3", 0.0, 0.5),
       ("sfx-hook-a", "pop.mp3", fr(h2s + 0.03), 0.5),
       ("sfx-whoosh-hook", "whoosh-cinematic.mp3", fr(HOOK_END - 0.35), 0.4),
       ("sfx-park", "click-soft.mp3", fr(T["parking"] + 0.03), 0.6),
       ("sfx-reveal", "whoosh.mp3", fr(T["all"] - 0.1), 0.4),
       ("sfx-reveal-hit", "impact-bass-2.mp3", fr(T["all"] - 0.3), 0.4),
       ("sfx-pump", "pop.mp3", fr(T["pump"] + 0.03), 0.45),
       ("sfx-jumper", "pop.mp3", fr(T["jumper"] + 0.03), 0.45),
       ("sfx-21", "click.mp3", fr(T["duadalam"] + 0.2), 0.5),
       ("sfx-s1", "whoosh-short.mp3", fr(T["cucuk"] - 0.05), 0.35),
       ("sfx-s3", "whoosh-short.mp3", fr(T["hitam"] - 0.05), 0.35),
       ("sfx-s4", "whoosh-short.mp3", fr(T["merah"] - 0.05), 0.35),
       ("sfx-riser", "riser.mp3", fr(T["crank"] - 2.6), 0.3),
       ("sfx-start", "impact-bass-1.mp3", fr(T["crank"] - 0.05), 0.5),
       ("sfx-ok", "sparkle.mp3", fr(T["sekali"]), 0.35),
       ("sfx-b1", "pop.mp3", fr(T["basikal"] + 0.03), 0.4),
       ("sfx-b2", "pop.mp3", fr(T["motor"] + 0.03), 0.4),
       ("sfx-b3", "pop.mp3", fr(T["bola"] + 0.03), 0.4),
       ("sfx-b4", "pop.mp3", fr(T["kereta"] + 0.03), 0.4),
       ("sfx-cta", "pop.mp3", fr(CTA_AT + 0.03), 0.5)]


def adur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          os.path.join(P, "assets/sfx", f)]).decode().strip())


lanes, sfx = [], []
for sid, f, at, vol in sorted(SFX, key=lambda x: x[2]):
    at = max(0, at)
    d = fr(min(adur(f), TOTAL - at))
    lane = next((i for i, e in enumerate(lanes) if e <= at), None)
    if lane is None:
        lanes.append(0); lane = len(lanes) - 1
    lanes[lane] = at + d
    sfx.append(f'      <audio id="{sid}" class="clip" src="assets/sfx/{f}" data-start="{at}" data-duration="{d}" data-track-index="{20 + lane}" data-volume="{vol}"></audio>')

flash_at = fr(HOOK_END - 0.8 * 0.58)
hosts = [("hook", 0, HOOK_END, 2, 5, "graphics"), ("editorial-flash-overlay", flash_at, 0.8, 3, 9, "graphics")]
for i, n in enumerate(["callouts-a", "callouts-b", "callouts-c", "callouts-d", "callouts-e"]):
    hosts.append((n, 0, TOTAL, 4 + i, 6, "graphics"))
hosts += [("cta", 0, TOTAL, 9, 7, "graphics"), ("captions", 0, TOTAL, 10, 8, "captions")]
host_html = "\n".join(
    f'      <div id="{n}" data-composition-id="{n}" data-composition-src="compositions/{n}.html" data-start="{st}" '
    f'data-duration="{d}" data-track-index="{tr}" data-track-kind="{kind}" data-width="1080" data-height="1920" style="z-index:{z}"></div>'
    for n, st, d, tr, z, kind in hosts)

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
      #cam {{ position: absolute; inset: 0; transform-origin: 50% 40%; }}
      #cam video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
      <!-- Footage: one clip per kept take. Trim in Studio by dragging clip edges. -->
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

print(f"total={TOTAL}s segments={len(segs)} captions={len(groups)}")
for s in segs:
    print(f'{s["id"]} out {s["start"]:6.2f}-{s["start"]+s["dur"]:6.2f} src {s["src_in"]:7.2f}-{s["src_out"]:7.2f} {s["note"]}')
