// LaTeX -> MathJax SVG (with mhchem) -> resvg PNG.  Usage: node sidecar.js "<latex>" <outPath>
const fs = require("fs");
const { mathjax } = require("mathjax-full/js/mathjax.js");
const { TeX } = require("mathjax-full/js/input/tex.js");
const { SVG } = require("mathjax-full/js/output/svg.js");
const { liteAdaptor } = require("mathjax-full/js/adaptors/liteAdaptor.js");
const { RegisterHTMLHandler } = require("mathjax-full/js/handlers/html.js");
const { AllPackages } = require("mathjax-full/js/input/tex/AllPackages.js");
const { Resvg } = require("@resvg/resvg-js");

const latex = process.argv[2];
const outPath = process.argv[3];
try {
  const adaptor = liteAdaptor();
  RegisterHTMLHandler(adaptor);
  const tex = new TeX({ packages: AllPackages });
  const svgjax = new SVG({ fontCache: "none", exFactor: 0.5 });
  const doc = mathjax.document("", { InputJax: tex, OutputJax: svgjax });
  const node = doc.convert(latex, { display: true, em: 16, ex: 8, containerWidth: 1000 });
  const svgNode = adaptor.firstChild(node);  // the bare <svg> inside the mjx-container wrapper
  let svg = adaptor.outerHTML(svgNode);
  if (!/xmlns=/.test(svg)) svg = svg.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ');
  const resvg = new Resvg(svg, { fitTo: { mode: "zoom", value: 4.0 }, background: "white" });
  fs.writeFileSync(outPath, resvg.render().asPng());
  const m = svg.match(/width="([^"]+)"/);
  process.stderr.write("ok width=" + (m ? m[1] : "?") + "\n");
} catch (e) {
  process.stderr.write("ERROR: " + e.message + "\n");
  process.exit(1);
}
