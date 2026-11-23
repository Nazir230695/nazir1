const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const dir = process.argv[2];
const jobs = [
  { out: 'cover-realfit-1.png', img: 'c_3.5.jpg', pos: '50% 40%', top: 'REALFIT', tag: 'REZEKI.NAZIR · TRUSTED AFFILIATE', bot: 'AMOLED<br>SMART WATCH' },
  { out: 'cover-realfit-2.png', img: 'c_39.0.jpg', pos: '50% 45%', top: 'REALFIT', tag: 'REZEKI.NAZIR · TRUSTED AFFILIATE', bot: '100+ MOD<br>SUKAN' },
];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(dir, 'cover.html'));
  await p.evaluate(() => document.fonts.ready);
  for (const j of jobs) {
    await p.evaluate((j) => {
      const bg = document.getElementById('bg'); bg.style.backgroundImage = `url(${j.img})`; bg.style.backgroundPosition = j.pos;
      document.getElementById('top').textContent = j.top;
      document.getElementById('bot').innerHTML = j.bot;
      document.getElementById('tag').textContent = j.tag;
    }, j);
    await p.waitForTimeout(300);
    await p.screenshot({ path: path.join(dir, j.out) });
  }
  await b.close();
})();
