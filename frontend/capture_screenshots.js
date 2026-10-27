import puppeteer from 'puppeteer-core';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const OUTPUT_DIR = path.resolve(__dirname, '..', 'docs', 'screenshots');

if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

async function run() {
  console.log('Launching Chrome from:', CHROME_PATH);
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    defaultViewport: {
      width: 1600,
      height: 1020,
      deviceScaleFactor: 2 // Crisp high-DPI screenshots
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  console.log('Navigating to http://127.0.0.1:8000 ...');
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });

  // Wait for all data to load
  await new Promise(r => setTimeout(r, 2000));

  // Find all tab buttons
  const tabs = await page.$$('.v-tab');
  console.log(`Found ${tabs.length} tabs`);

  // 1. Dashboard (Dark)
  console.log('Capturing 01_dashboard_control_center.png ...');
  await tabs[0].click();
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_dashboard_control_center.png') });

  // 2. Lab & Debate
  console.log('Capturing 02_task_lab_debate.png ...');
  await tabs[1].click();
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_task_lab_debate.png') });

  // 3. Agents Configuration
  console.log('Capturing 03_agents_configuration.png ...');
  await tabs[2].click();
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_agents_configuration.png') });

  // 4. Results & Charts
  console.log('Capturing 04_results_and_charts.png ...');
  await tabs[3].click();
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_results_and_charts.png') });

  // 5. Thesis Draft & LaTeX
  console.log('Capturing 05_thesis_chapter_draft.png ...');
  await tabs[4].click();
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_thesis_chapter_draft.png') });

  // 6. Light Theme
  console.log('Capturing 06_dashboard_light_theme.png ...');
  await tabs[0].click();
  const themeBtn = await page.$('button[title*="Tryb"], button .mdi-weather-sunny, button .mdi-weather-night');
  if (themeBtn) {
    await themeBtn.click();
    await new Promise(r => setTimeout(r, 800));
    await page.screenshot({ path: path.join(OUTPUT_DIR, '06_dashboard_light_theme.png') });
  }

  await browser.close();
  console.log('All screenshots captured successfully in:', OUTPUT_DIR);
}

run().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
