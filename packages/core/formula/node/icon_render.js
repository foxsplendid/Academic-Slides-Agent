// Tabler icon -> tinted PNG sidecar (arms-length subprocess, mirrors sidecar.js).
// Usage: node icon_render.js <icon_name> <hex_color> <size_px> <out_png>
// Icons are MIT (tabler/tabler-icons via npm @tabler/icons); resvg is MPL-2.0 — both stay
// out-of-process from the Apache Python code.
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const [name, color, sizeArg, outPath] = process.argv.slice(2);
if (!name || !color || !sizeArg || !outPath) {
  console.error("usage: node icon_render.js <icon_name> <hex_color> <size_px> <out_png>");
  process.exit(2);
}
const safe = name.replace(/[^a-z0-9-]/g, "");
const svgPath = path.join(__dirname, "node_modules", "@tabler", "icons", "icons", "outline", `${safe}.svg`);
if (!fs.existsSync(svgPath)) {
  console.error(`icon not found: ${safe}`);
  process.exit(3);
}
let svg = fs.readFileSync(svgPath, "utf8");
svg = svg.replace(/stroke="currentColor"/g, `stroke="${color}"`);
const size = parseInt(sizeArg, 10) || 64;
const png = new Resvg(svg, { fitTo: { mode: "width", value: size } }).render().asPng();
fs.writeFileSync(outPath, png);
