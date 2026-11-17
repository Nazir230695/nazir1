import sys, json
from faster_whisper import WhisperModel
m = WhisperModel(sys.argv[3] if len(sys.argv)>3 else "large-v3", device="cpu", compute_type="int8")
import wave, numpy as np
wf=wave.open(sys.argv[1]); audio=np.frombuffer(wf.readframes(wf.getnframes()),np.int16).astype(np.float32)/32768
segs, info = m.transcribe(audio, language="ms", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False, temperature=0,
    initial_prompt=(sys.argv[4] if len(sys.argv)>4 else None))
out=[]
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}", flush=True)
    for w in s.words: out.append({"text":w.word.strip(),"start":round(w.start,3),"end":round(w.end,3),"p":round(w.probability,2)})
json.dump(out, open(sys.argv[2],"w"), ensure_ascii=False, indent=0)
