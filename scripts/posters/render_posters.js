// Renders every platform poster in posters.html to public/subway/posters/<id>.jpg.
// Usage (from the repo root): node scripts/posters/render_posters.js
// Needs Playwright (npm i -D playwright, then npx playwright install chromium) and a network
// connection for the Google Fonts.
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const IDS = ["college-app-atlas", "purchase-intent", "new-york-census", "folio", "agent00hl7", "dream-team", "neurobiome"];

(async () => {
  const src = "file://" + path.join(__dirname, "posters.html");
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1376, height: 816 } });
  const dir = path.join(__dirname, "../../public/subway/posters");
  fs.mkdirSync(dir, { recursive: true });
  for (const id of IDS) {
    await page.goto(`${src}?id=${id}`);
    await page.waitForLoadState("networkidle");
    await page.waitForFunction(() => window.__fitted === true);
    await page.waitForTimeout(800); // let the inline SVG art (and its fonts) finish
    await page.screenshot({ path: path.join(dir, id + ".jpg"), type: "jpeg", quality: 88 });
    console.log(id);
  }
  await browser.close();
})();
