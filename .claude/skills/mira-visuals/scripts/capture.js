/**
 * Captura um HTML como PNG 1920x1920 usando Puppeteer.
 *
 * Uso: node capture.js <input.html> <output.png>
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function capture(inputHtml, outputPng) {
    const absoluteInput = path.resolve(inputHtml);
    const absoluteOutput = path.resolve(outputPng);

    if (!fs.existsSync(absoluteInput)) {
        console.error(`Arquivo nao encontrado: ${absoluteInput}`);
        process.exit(1);
    }

    // Garantir que o diretorio de saida existe
    const outputDir = path.dirname(absoluteOutput);
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
    }

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();

    // Viewport quadrado 1920x1920
    await page.setViewport({
        width: 1920,
        height: 1920,
        deviceScaleFactor: 1
    });

    // Carregar o HTML local
    await page.goto(`file:///${absoluteInput.replace(/\\/g, '/')}`, {
        waitUntil: 'networkidle0',
        timeout: 30000
    });

    // Pequena pausa para garantir renderizacao completa de animacoes D3
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Screenshot com clip exato de 1920x1920
    await page.screenshot({
        path: absoluteOutput,
        type: 'png',
        clip: {
            x: 0,
            y: 0,
            width: 1920,
            height: 1920
        }
    });

    await browser.close();

    console.log(`Infografico capturado: ${absoluteOutput}`);
    console.log(`Dimensoes: 1920 x 1920 px`);
}

// CLI
const args = process.argv.slice(2);
if (args.length < 2) {
    console.log('Uso: node capture.js <input.html> <output.png>');
    process.exit(1);
}

capture(args[0], args[1]).catch(err => {
    console.error('Erro na captura:', err.message);
    process.exit(1);
});
