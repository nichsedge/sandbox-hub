const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

require('dotenv').config();
const EVM_ADDRESS = process.env.EVM_ADDRESS || "your_default_address_here";

const PROFILE_URL = `https://debank.com/profile/${EVM_ADDRESS}`;
const OUTPUT_PATH = path.join(__dirname, 'debank_raw.json');

async function extractAssetData(page) {
  return await page.evaluate(() => {
    const allElements = document.querySelectorAll("*");
    for (let element of allElements) {
      const text = element.textContent || "";
      const match = text.match(/\$[\d,]+.*?[+\-]\d+\.\d+%/);
      if (match) {
        const dollarMatch = text.match(/\$[\d,]+/);
        const percentMatch = text.match(/[+\-]\d+\.\d+%/);
        return {
          found: true,
          amount: dollarMatch ? dollarMatch[0] : "",
          change: percentMatch ? percentMatch[0] : "",
        };
      }
    }
    return { found: false, message: "No asset data found" };
  });
}

async function extractProfileData(page) {
  await page.waitForSelector("div[class*='HeaderInfo_totalAssetInner']", { timeout: 10000 });
  return await page.evaluate(() => {
    const data = {};
    const items = document.querySelectorAll("div[class*='HeaderInfo_infoItem']");
    items.forEach((item) => {
      if (item.closest("a")) return;
      const title = item.querySelector("div[class*='HeaderInfo_title']")?.innerText.trim();
      const value = item.querySelector("div[class*='HeaderInfo_value']")?.innerText.trim();
      if (title && value) data[title] = value;
    });
    return data;
  });
}

async function extractWallets(page) {
  await page.waitForSelector("div[class*='TokenWallet_table']", { timeout: 10000 });

  return await page.evaluate(() => {
    const table = document.querySelector("div[class*='TokenWallet_table']");
    if (!table) return [];

    const headerEls = table.querySelectorAll("div[class*='db-table-headerItem']");
    const headers = Array.from(headerEls).map((el) => el.innerText.trim());

    const rowEls = table.querySelectorAll("div[class*='db-table-row']");
    return Array.from(rowEls).map((row) => {
      const cells = row.querySelectorAll("div[class*='db-table-cell']");
      const values = Array.from(cells).map((cell, i) => {
        if (i === 0) {
          const tokenLink = cell.querySelector("a");
          return tokenLink?.innerText.trim() || "";
        }
        return cell.innerText.trim();
      });

      // Extract the href and chain
      const tokenLink = cells[0]?.querySelector("a");
      let chain = "";
      if (tokenLink?.getAttribute("href")) {
        const hrefParts = tokenLink.getAttribute("href").split("/");
        if (hrefParts.length >= 3) {
          chain = hrefParts[2]; // /token/{chain}/{token} -> get {chain}
        }
      }

      const rowObj = {};
      headers.forEach((key, i) => {
        rowObj[key] = values[i] || "";
      });
      rowObj.chain = chain;

      return rowObj;
    });
  });
}


async function extractProtocols(page) {
  await page.waitForSelector('div[class^="Project_project__"]', { timeout: 10000 });

  return await page.$$eval('div[class^="Project_project__"]', (projects) => {
    return projects.map((project) => {
      const nameElem = project.querySelector('span[class^="ProjectTitle_protocolLink"]');
      const usdValueElem = project.querySelector('div[class^="projectTitle-number"]');

      const protocolName = nameElem?.innerText.trim() || null;
      const usdValue = usdValueElem?.innerText.trim() || null;

      // Extract headers
      const headerElems = project.querySelectorAll('div[class^="table_header__"] div > span');
      const headers = Array.from(headerElems).map((el) => el.innerText.trim());

      // Extract rows
      const rowElems = project.querySelectorAll('div[class^="table_contentRow__"]');
      const rows = Array.from(rowElems).map((row) => {
        const cols = row.querySelectorAll('div > span');
        return Array.from(cols).map((col) => col.innerText.trim());
      });

      // Combine headers with values
      const data = rows.map((values) => {
        const obj = {};
        headers.forEach((key, i) => {
          obj[key] = values[i] || null;
        });
        return obj;
      });

      return {
        name: protocolName,
        usdValue,
        data,
      };
    });
  });
}

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto(PROFILE_URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(5000);

  const assetData = await extractAssetData(page);
  const profileData = await extractProfileData(page);
  const wallets = await extractWallets(page);
  const protocols = await extractProtocols(page);

  const mergedData = {
    assetData,
    profileData,
    wallets,
    protocols,
    timestamp: new Date().toISOString(),
    profileUrl: PROFILE_URL,
  };

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(mergedData, null, 2));
  console.log(`Data saved to ${OUTPUT_PATH}`);

  await browser.close();
})();
