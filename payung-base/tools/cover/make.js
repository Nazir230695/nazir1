const { chromium } = require('playwright');
const path = require('path');
const dir = process.argv[2];
const TAG = 'REZEKI.NAZIR · TRUSTED AFFILIATE';
const jobs = [
  { out: 'cover-payung-1.png', img: 'f_a_14.5.jpg', pos: '50% 50%', top: 'WAJIB DALAM KERETA', bot: 'PAYUNG AUTO<br>1 TEKAN' },
  { out: 'cover-payung-2.png', img: 'f_c_21.jpg', pos: '50% 50%', top: 'NAMPAK PREMIUM', bot: 'FIBER BONE<br>TAK MUDAH PATAH' },
  { out: 'cover-payung-3.png', img: 'f_d_4.jpg', pos: '50% 50%', top: 'HUJAN? RELAKS', bot: 'KELUAR KERETA<br>TAK BASAH' },
  { out: 'cover-payung-4.png', img: 'f_e_13.5.jpg', pos: '50% 50%', top: 'VIRAL DI TIKTOK', bot: 'PAYUNG AUTO<br>TAHAN RIBUT' },
  { out: 'cover-payung-5.png', img: 'f_b_16.jpg', pos: '50% 50%', top: '1 TEKAN', bot: 'TERUS<br>TERBUKA' },
  { out: 'cover-payung-6.png', img: 'f_b_19.jpg', pos: '50% 50%', top: 'PAYUNG AUTO', bot: 'ADA 2 SAIZ<br>2 WARNA' },
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
