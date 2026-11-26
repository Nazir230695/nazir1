# Default editing style (rezeki.nazir)

Use the normal bright style for every new video (templates: `lampu-base/tools/build.py`, `bidai2-base/tools/build.py`).
Do NOT use the cinematic style (`build_cine.py`, plastik/bidai3) unless asked — the user prefers the normal one.

- Bright, clear HD grade with rich colour.
- Each video under 40s, split into several videos where possible; keep whole lines, not rushed.
- Hook is one continuous shot with a yellow headline.
- Product images are big centre zoom cards.
- Header: REZEKI.NAZIR · TRUSTED AFFILIATE (left) and the shop/product (right), no dark band.
- Captions are white, bold and uppercase, kept off the face; chips are used sparingly.
- Ending is a shop card plus "Tekan link sekarang"; the video ends right after "tekan link". Never write "bio".
- Covers (new, from Nov 2026): a bright video frame with the product big and clear, plus a 2-line title in white Archivo Expanded Black
  with a soft shadow, kept inside the 3:4 crop. Template: `tools/cover-v2` (`node make.js <dir> jobs.json`). No more dark/gold covers.
- Motion graphics (projector onwards): dial counters, icon pills, focus brackets, tick tags, light leaks, price tag + disclaimer,
  one-word captions (`proj-base/tools/build.py`).
- Price: when showing a promo price, add "Disclaimer: Harga mungkin berubah apabila promosi tamat".
- Show storyboards and covers for review before rendering.
