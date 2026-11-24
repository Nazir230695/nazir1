const { chromium } = require('playwright');
const path = require('path');
const dir = process.argv[2];
const TAG = 'REZEKI.NAZIR · TRUSTED AFFILIATE';
const jobs = [
  { out: 'cover-fasclean-1.png', img: 'f_e.jpg', pos: '50% 50%', top: 'KAKAK-KAKAK!', bot: 'SATU SABUN<br>BASUH SEMUA' },
  { out: 'cover-fasclean-2.png', img: 'f_h.jpg', pos: '50% 50%', top: 'PINGGAN BERMINYAK?', bot: 'SEKALI LAP<br>TERUS HILANG' },
  { out: 'cover-fasclean-3.png', img: 'f_d.jpg', pos: '50% 50%', top: 'BOTOL SUSU ANAK', bot: 'PUN BOLEH<br>BASUH' },
  { out: 'cover-fasclean-4.png', img: 'f_f.jpg', pos: '50% 50%', top: 'TANGAN TAK KERING', bot: 'ADA KOLAGEN<br>UNTUK TANGAN' },
];
const _old = [
  { out: 'cover-brush-1.png', img: 'f_a_37.0.jpg', pos: '50% 45%', top: '2 DALAM 1', bot: 'BERUS +<br>PENARIK AIR' },
  { out: 'cover-brush-2.png', img: 'f_e_28.8.jpg', pos: '50% 40%', top: 'DUDUK STATIC', bot: 'PUN BOLEH<br>CUCI LANTAI' },
  { out: 'cover-brush-3.png', img: 'f_c_20.0.jpg', pos: '50% 50%', top: 'LANTAI KERING', bot: 'BERSIH &amp;<br>BERKILAT' },
  { out: 'cover-brush-4.png', img: 'f_a_33.0.jpg', pos: '50% 40%', top: 'BINI SAYANG', bot: 'SUAMI RAJIN<br>CUCI LANTAI' },
  { out: 'cover-brush-5.png', img: 'f_e_24.5.jpg', pos: '50% 45%', top: 'PUSING 180°', bot: 'BERUS<br>BENTUK V' },
];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(dir, 'cover.html'));
  await p.evaluate(() => document.fonts.ready);
  for (const j of jobs) {
    await p.evaluate((j) => {
      const bg = document.getElementById('bg'); bg.style.backgroundImage = `url(${j.img})`; bg.style.backgroundPosition = j.pos;
      const top = document.getElementById('top'), bot = document.getElementById('bot');
      top.textContent = j.top; bot.innerHTML = j.bot; document.getElementById('tag').textContent = j.tag;
      // shrink each title until it fits 880 px wide (stays inside TikTok's 3:4 cover crop)
      for (const [el, size] of [[top, 210], [bot, 132]]) {
        let s = size; el.style.fontSize = s + 'px';
        const r = document.createRange();
        const w = () => { r.selectNodeContents(el); return r.getBoundingClientRect().width; };
        while (w() > 880 && s > 60) { s -= 4; el.style.fontSize = s + 'px'; }
      }
    }, { ...j, tag: TAG });
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(dir, j.out) });
  }
  await b.close();
})();
