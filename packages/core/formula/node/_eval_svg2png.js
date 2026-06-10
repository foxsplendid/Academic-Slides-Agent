const fs = require("fs");
const { Resvg } = require("@resvg/resvg-js");
const [svgPath, outPath] = process.argv.slice(2);
const svg = fs.readFileSync(svgPath, "utf8");
const r = new Resvg(svg, { fitTo: { mode: "width", value: 1280 }, font: { loadSystemFonts: true } });
fs.writeFileSync(outPath, r.render().asPng());
