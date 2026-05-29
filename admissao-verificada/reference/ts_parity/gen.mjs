// Gera BASE e RATEIO pelo exportador TypeScript (lib/export/xlsx.ts), a partir
// da MESMA fixture do harness Python (passada como JSON), para a verificação de
// paridade (P2). Uso:
//   node gen.mjs <bundle_xlsx.mjs> <fixture.json> <outdir>
import { writeFileSync, readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const [bundlePath, fixturePath, outdir] = process.argv.slice(2);
const { gerarBase, gerarRateio } = await import(pathToFileURL(bundlePath).href);
const { cotas, eventos } = JSON.parse(readFileSync(fixturePath, "utf8"));

writeFileSync(`${outdir}/BASE_202606.xlsx`, await gerarBase(cotas));
writeFileSync(`${outdir}/RATEIO_202606.xlsx`, await gerarRateio(eventos));
console.log("ok");
