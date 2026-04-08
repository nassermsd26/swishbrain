const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({ headless: 'new' });
    const page = await browser.newPage();
    await page.goto('file:///Users/nassermsd/Desktop/blackjack/index.html');

    // Configure Table
    await page.select('#decksSelect', '6');
    await page.select('#rulesSelect', 'S17');
    await page.select('#playersSelect', '3');
    await page.select('#seatSelect', '2');
    await page.click('#btnNouvelleManche');
    console.log("Table Configured: 6 Decks, S17, 3 Players, Seat 2");

    const ranks = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2'];
    const results = ['btnWin', 'btnLose', 'btnPush'];
    
    // Play 10 random rounds
    for (let round = 1; round <= 10; round++) {
        console.log(`\n--- Round ${round} ---`);
        
        // Initial Deal (3 players + dealer = 7 cards)
        let initialCards = 7;
        for (let c = 0; c < initialCards; c++) {
            let rank = ranks[Math.floor(Math.random() * ranks.length)];
            await page.click(`button[data-val="${rank}"]`);
            // await page.waitForTimeout(50);
        }

        // Add 0-2 random player hits manually
        let hits = Math.floor(Math.random() * 3);
        await page.click('#filterPlayer'); // Ensure target is player for hits
        for (let h = 0; h < hits; h++) {
            let rank = ranks[Math.floor(Math.random() * ranks.length)];
            await page.click(`button[data-val="${rank}"]`);
        }
        
        // Read State
        const advice = await page.$eval('#adviceMain', el => el.textContent);
        const adviceReason = await page.$eval('#adviceReason', el => el.textContent);
        const tc = await page.$eval('#valTC', el => el.textContent);
        const dt = await page.$eval('#totalDealer', el => el.textContent);
        const pt = await page.$eval('#totalPlayer', el => el.textContent);
        
        console.log(`Dealer Hand: ${dt}`);
        console.log(`Player Hand: ${pt}`);
        console.log(`True Count: ${tc}`);
        console.log(`Advice: ${advice} (${adviceReason})`);

        // Record a random outcome to advance history
        let resBtn = results[Math.floor(Math.random() * results.length)];
        await page.click(`#${resBtn}`);
    }

    await page.screenshot({ path: '/Users/nassermsd/.gemini/antigravity/brain/729c64e8-12a5-4178-907e-756de58d40fd/swishbrain_10_rounds.png' });
    console.log(`\nFinished 10 rounds. Screenshot saved.`);
    
    await browser.close();
})();
