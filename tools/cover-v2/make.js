// usage: node make.js <dir> <jobs.json>   jobs: [{out, img, pos, l1, l2, place:"top"|"bottom"}]
const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs');
const dir = process.argv[2]; const jobs = JSON.parse(fs.readFileSync(process.argv[3]));
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + path.join(dir, 'cover.html'));
  await p.evaluate(() => document.fonts.ready);
  for (const j of jobs) {
    await p.evaluate((j) => {
      document.body.className = j.place || 'top';
      const bg = document.getElementById('bg'); bg.style.backgroundImage = `url(${j.img})`; bg.style.backgroundPosition = j.pos || 'center'; bg.style.backgroundSize = j.size || 'cover';
      const els = [document.getElementById('l1'), document.getElementById('l2')];
      els[0].textContent = j.l1; els[1].textContent = j.l2 || '';
      // same size on both lines, as big as fits 900 px (inside TikTok's 3:4 crop)
      let s = 112; const r = document.createRange();
      const w = () => Math.max(...els.map(e => { r.selectNodeContents(e); return r.getBoundingClientRect().width; }));
      els.forEach(e => e.style.fontSize = s + 'px');
      while (w() > 900 && s > 50) { s -= 2; els.forEach(e => e.style.fontSize = s + 'px'); }
    }, j);
    await p.waitForTimeout(250);
    await p.screenshot({ path: path.join(dir, j.out) });
  }
  await b.close();
})();
