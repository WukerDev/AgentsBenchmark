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
      height: 1050,
      deviceScaleFactor: 2 // High-DPI crisp screenshots
    },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  console.log('Navigating to http://127.0.0.1:8000 ...');
  await page.goto('http://127.0.0.1:8000', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));

  const tabs = await page.$$('.v-tab');
  console.log(`Found ${tabs.length} tabs`);

  // 1. Dashboard (Dark)
  console.log('Capturing 01_dashboard_control_center.png ...');
  await tabs[0].click();
  await page.setViewport({ width: 1600, height: 1020, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '01_dashboard_control_center.png') });

  // 2. Lab & Swarm Debate (with high-contrast theme text)
  console.log('Capturing 02_task_lab_debate.png ...');
  await tabs[1].click();
  await page.setViewport({ width: 1600, height: 1060, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 1200));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '02_task_lab_debate.png') });

  // 3. Agents Configuration
  console.log('Capturing 03_agents_configuration.png ...');
  await tabs[2].click();
  await page.setViewport({ width: 1600, height: 1020, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '03_agents_configuration.png') });

  // 4. Results & Publication Figures (Tall view showing table and uncropped 300 DPI charts)
  console.log('Capturing 04_results_and_charts.png ...');
  await tabs[3].click();
  await page.setViewport({ width: 1600, height: 1380, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04_results_and_charts.png') });

  // 4b. Publication Figures Gallery (Scrolled view showing uncropped full-size 300 DPI plots)
  console.log('Capturing 04b_publication_figures_gallery.png ...');
  await page.evaluate(() => {
    window.scrollBy(0, 340);
  });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '04b_publication_figures_gallery.png') });
  await page.evaluate(() => {
    window.scrollTo(0, 0);
  });

  // 5. Thesis Draft & LaTeX Preview (with high-contrast theme text)
  console.log('Capturing 05_thesis_chapter_draft.png ...');
  await tabs[4].click();
  await page.setViewport({ width: 1600, height: 1050, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 800));
  await page.screenshot({ path: path.join(OUTPUT_DIR, '05_thesis_chapter_draft.png') });

  // 6. Ollama Model Management Dialog
  console.log('Capturing 07_ollama_model_manager.png ...');
  const openedDialog = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent && (b.textContent.includes('Modele Ollama') || b.textContent.includes('Pobierz model Ollama')));
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  if (openedDialog) {
    await new Promise(r => setTimeout(r, 1200));
    await page.setViewport({ width: 1600, height: 1050, deviceScaleFactor: 2 });
    await page.screenshot({ path: path.join(OUTPUT_DIR, '07_ollama_model_manager.png') });
    await page.keyboard.press('Escape');
    await new Promise(r => setTimeout(r, 600));
  }

  // 7. Light Theme
  console.log('Capturing 06_dashboard_light_theme.png ...');
  await tabs[0].click();
  await page.setViewport({ width: 1600, height: 1020, deviceScaleFactor: 2 });
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
