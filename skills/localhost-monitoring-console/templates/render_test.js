/* DOM-shim render harness — verifies static HTML+JS against a LIVE API, without a browser.
 *
 * Usage:  node tools/render_test.js          (server must already be running)
 * Copy into <project>/tools/, edit CFG + the TESTS block per page.
 *
 * Why: there is usually no headless Chrome on the target device. node:vm + a fake
 * document lets you execute the real app.js and inspect the HTML it produces.
 * It catches field-name drift (undefined/NaN in output), missing panels and broken
 * detail render paths long before a human opens the tab.
 */
const fs = require("fs");
const vm = require("vm");
const path = require("path");

const CFG = {
  base: "http://127.0.0.1:8787",       // live server
  app: path.join(__dirname, "..", "static", "app.js"),
  wait: 1200,                          // boot() settle time
  selectorValues: { "#wlimit": "100" }, // <select> defaults app.js reads on boot
};

const nodes = {};
const mkEl = (sel) => ({
  sel,
  innerHTML: "",
  textContent: "",
  value: CFG.selectorValues[sel] || "",
  classList: { add() {}, remove() {}, toggle() {}, contains: () => false },
  dataset: {},
  scrollTop: 0,
  addEventListener() {},
  insertAdjacentHTML() {},
  querySelector: () => null,
  querySelectorAll: () => [],
});
// q() must be used (not nodes[sel]) because the map fills lazily on first query.
const q = (s) => (nodes[s] = nodes[s] || mkEl(s));

const ctx = {
  console,
  fetch: (u, o) => fetch(`${CFG.base}${u}`, o),
  setTimeout, clearTimeout,
  setInterval: () => 0, clearInterval: () => {},   // keep the process from hanging
  Intl, Date, Math, JSON, Number, String, Object, Array, Promise, Error,
  encodeURIComponent, decodeURIComponent,
  document: {
    querySelector: q,
    querySelectorAll: () => [],                     // only global queries; per-tab tests use q()
    body: { insertAdjacentHTML() {} },
    activeElement: null,
  },
  location: { reload() {} },
};
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(CFG.app, "utf8"), ctx, { filename: "app.js" });

const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const text = (h) => h.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
const need = (cond, msg) => {
  if (!cond) { console.log("GAGAL:", msg); process.exitCode = 1; }
  else console.log("OK:", msg);
};
const clean = (h) => h.length > 200 && !h.includes("undefined") && !h.includes("NaN");

(async () => {
  await wait(CFG.wait); // boot() + first tab

  // --- per-tab render smoke ------------------------------------------------
  for (const [tab, sel] of [["overview", "#ov-cards"], ["work", "#w-list"], ["system", "#sys-homes"]]) {
    q(sel).innerHTML = "";
    await ctx.setTab(tab);
    await wait(900);
    need(clean(q(sel).innerHTML), `${tab.toUpperCase()} → ${sel} (${q(sel).innerHTML.length}b)`);
    console.log("   ", text(q(sel).innerHTML).slice(0, 140));
  }

  // --- structural counts (catch data-shape regressions) --------------------
  // need((q("#org-systems").innerHTML.match(/class="sys"/g) || []).length === 8, "8 system cards");

  // --- detail render path --------------------------------------------------
  // await ctx.openSession("20260101_000000_abc123"); await wait(700);
  // need(q("#w-detail").innerHTML.includes("msg "), "session timeline rendered");

  console.log("\nSelesai ujian render.");
})();
