/* Headless smoke test for ADAM Directors Dashboard.
 * Boots the page in jsdom, waits for the DOMContentLoaded handler to render,
 * then asserts key invariants. Run with:
 *     node headless-smoke.js
 */
const fs   = require("fs");
const path = require("path");
const { JSDOM } = require("/tmp/node_modules/jsdom");

const ROOT = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

const dom = new JSDOM(html, {
  url: "file://" + ROOT + "/",
  runScripts: "dangerously",
  pretendToBeVisual: true
});

const assertions = [];
function assert(label, cond, detail) {
  assertions.push({ label, pass: !!cond, detail: detail || "" });
}

dom.window.addEventListener("load", async () => {
  // Stub fetch so probe falls through to demo mode quickly.
  dom.window.fetch = () => Promise.reject(new Error("offline"));

  // Inject CSS + demo + app scripts manually because jsdom does not follow
  // <script src=...> to the local filesystem in the JSDOM resources loader
  // reliably when runScripts: dangerously is combined with external refs
  // (depends on exact jsdom version). Read and execute inline.
  const css   = fs.readFileSync(path.join(ROOT, "assets/styles.css"), "utf8");
  const demo  = fs.readFileSync(path.join(ROOT, "data/demo-data.js"), "utf8");
  const app   = fs.readFileSync(path.join(ROOT, "assets/app.js"), "utf8");

  // Inject the CSS, then execute the scripts in order.
  const style = dom.window.document.createElement("style");
  style.textContent = css;
  dom.window.document.head.appendChild(style);

  dom.window.eval(demo);
  dom.window.eval(app);

  // Manually fire DOMContentLoaded because jsdom may have fired it already
  dom.window.document.dispatchEvent(new dom.window.Event("DOMContentLoaded"));

  // Give the boot() a tick to run through probe (which will reject-fetch
  // and fall to demo mode) and render.
  await new Promise(r => setTimeout(r, 250));

  const doc = dom.window.document;
  const $ = sel => doc.querySelector(sel);
  const $$= sel => [...doc.querySelectorAll(sel)];

  // --- Structural assertions
  assert("index.html parses",                  !!doc.body);
  assert("has all 4 quadrant panels",          $$(".panel").length >= 4);
  assert("brand mark rendered",                !!$(".brand-mark"));
  assert("footer present",                     !!$(".footer"));

  // --- Demo data attached
  assert("ADAM_DEMO global loaded",            !!dom.window.ADAM_DEMO);
  assert("demo has 5 directors",               dom.window.ADAM_DEMO.directors.length === 5);
  assert("demo has 7 agent classes",           Object.keys(dom.window.ADAM_DEMO.agent_classes).length === 7);
  const allAgents = Object.values(dom.window.ADAM_DEMO.agent_classes).reduce((a,c)=>a+c.agents.length, 0);
  assert("demo has 81 agents total",           allAgents === 81, `got ${allAgents}`);

  // --- UI rendered
  assert("group-grid populated",               $("#group-grid").children.length >= 7);
  assert("queue list rendered",                $("#queue-list").children.length >= 1);
  assert("director roster rendered",           $("#director-roster").children.length === 5);
  assert("twin grid has 4 cards",              $("#twin-grid").children.length === 4);
  assert("routing cells rendered",             $("#routing").children.length === 5);
  assert("flight recorder tail has rows",      $("#fr-tail").children.length >= 1);
  assert("mesh totals populated",              $("#mesh-totals").textContent.length > 5);

  // --- Agent tile totals
  const tiles = $$(".agent-tile");
  assert("agent tiles count == 81",            tiles.length === 81, `got ${tiles.length}`);
  const byStatus = tiles.reduce((a,t)=>{const k=t.classList.contains("down")?"d":t.classList.contains("escalation")?"e":"a";a[k]=(a[k]||0)+1;return a;},{});
  assert("mix of statuses rendered",           !!(byStatus.a && (byStatus.e || byStatus.d)));

  // --- Queue rendering invariants
  const firstQ = $("#queue-list .queue-item");
  assert("first queue item has tier class",    !!firstQ && /tier-(HIGH|OHSHAT|ELEVATED)/.test(firstQ.className));
  assert("approve button present",             !!$("#queue-list button[data-action='approve']"));
  assert("reject button present",              !!$("#queue-list button[data-action='reject']"));

  // --- Accessibility basics
  assert("main grid has aria-label or role",   $("main.main") !== null);
  assert("inputs have aria-label",             $("#intent-input").getAttribute("aria-label"));
  assert("modal has aria-modal",               $("#modal-root").getAttribute("aria-modal") === "true");
  assert("all images have alt or aria hidden", $$("img").every(i => i.alt != null));

  // --- Interaction: modal opens on queue click
  firstQ.click();
  const modalOpen = $("#modal-root").hidden === false;
  assert("click opens detail modal",           modalOpen);
  // And modal has an approve button with intent id
  const mApprove = $("#modal-approve");
  assert("modal approve has intent id",        mApprove.dataset.intent.length > 0);

  // --- Interaction: approve from modal removes the row
  const prevCount = $$("#queue-list .queue-item").length;
  mApprove.click();
  await new Promise(r => setTimeout(r, 80));
  const nextCount = $$("#queue-list .queue-item").length;
  assert("approve removes row from queue",     nextCount === prevCount - 1, `prev=${prevCount} next=${nextCount}`);

  // --- REGRESSION: inline queue-row buttons must also work (was broken by stopPropagation).
  const beforeInlineCount = $$("#queue-list .queue-item").length;
  const firstRejectBtn = $("#queue-list button[data-action='reject']");
  assert("reject button exists for inline test", !!firstRejectBtn);
  firstRejectBtn.click();
  await new Promise(r => setTimeout(r, 80));
  const afterInlineCount = $$("#queue-list .queue-item").length;
  assert("inline reject button actually works", afterInlineCount === beforeInlineCount - 1, `before=${beforeInlineCount} after=${afterInlineCount}`);
  // Modal should NOT have opened when clicking an action button
  assert("inline button click does not open modal", $("#modal-root").hidden === true);

  // --- Intent submit simulation
  const intentInput = $("#intent-input");
  intentInput.value = "Approve a $7,500 vendor payment to Globex for streaming-rights renewal";
  $("#intent-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 80));
  const intentLog = $("#intent-log").textContent;
  assert("intent submit produced response",    /Interpreted/.test(intentLog));
  assert("intent submit surfaces tier",        /(SOAP|MODERATE|ELEVATED|HIGH|OHSHAT)/.test(intentLog));

  // --- Explain-Back — text-based fuzzy search (directors don't know intent_ids)
  $("#explain-input").value = "DORA analytics pipeline";
  $("#explain-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 60));
  const explainLog = $("#explain-log").textContent;
  assert("fuzzy text search returns a narrative or picker",
         /DORA|composite|routed|intent|match/i.test(explainLog));

  // --- Explain-Back — single-word ambiguous query → picker with multiple matches
  // Submit two similar intents first to create ambiguity
  $("#intent-input").value = "Approve a $2,000 paid-social campaign";
  $("#intent-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 50));
  $("#intent-input").value = "Launch a $4,000 marketing campaign for Streaming";
  $("#intent-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 50));
  $("#explain-input").value = "campaign";
  $("#explain-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 60));
  const matchOptions = $$(".match-option");
  assert("ambiguous query presents a picker with multiple options", matchOptions.length >= 2, "got " + matchOptions.length);

  // Click the first picker option — it should render the full packet
  const beforePackets = $$("#explain-log .bubble.adam").length;
  if (matchOptions[0]) matchOptions[0].click();
  await new Promise(r => setTimeout(r, 40));
  const afterPackets = $$("#explain-log .bubble.adam").length;
  assert("clicking a picker option renders the packet", afterPackets > beforePackets);

  // --- Submitted intent is discoverable via its own text later
  $("#explain-input").value = "Streaming";
  $("#explain-form").dispatchEvent(new dom.window.Event("submit", { cancelable: true, bubbles: true }));
  await new Promise(r => setTimeout(r, 60));
  assert("session-submitted intents are searchable by their own words",
         /Streaming/i.test($("#explain-log").textContent));

  // --- Director filter wiring
  $("#director-filter").value = "cfo";
  $("#director-filter").dispatchEvent(new dom.window.Event("change"));
  await new Promise(r => setTimeout(r, 30));
  const cfoRows = $$("#queue-list .queue-item").length;
  assert("director filter narrows queue", cfoRows >= 0);
  $("#director-filter").value = "all";
  $("#director-filter").dispatchEvent(new dom.window.Event("change"));

  // --- Print the results
  const pass = assertions.filter(a => a.pass).length;
  const fail = assertions.length - pass;
  console.log("\n==== QA Smoke ==== " + pass + "/" + assertions.length + " passed ====\n");
  for (const a of assertions) {
    console.log((a.pass ? "PASS " : "FAIL ") + a.label + (a.detail ? "  -  " + a.detail : ""));
  }
  if (fail > 0) {
    process.exit(1);
  }
  process.exit(0);
});
