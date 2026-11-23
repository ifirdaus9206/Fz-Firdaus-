/* HERMES CONSOLE — frontend (tiada dependency) */
const S = {
  home: "hermes20", tab: "pusat", meta: null, pendingHome: null, sessions: [], sel: null, busy: false, auto: true,
  ag: { div: "", q: "", sel: null, data: null },
  av: { data: null, slug: null, q: "", arch: "", sort: "skor", limit: 60 },
  kr: { data: null, q: "", tier: "", arch: "" },
  da: { run: null, timer: null, loaded: false },
  pusat: { chart: null, sig: "", es: null, seen: {} },
};
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const NF = new Intl.NumberFormat("en-US");

const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const num = (v) => (v == null ? "–" : NF.format(Math.round(Number(v))));
const kb = (v) => (v == null ? "–" : Number(v).toLocaleString("en-US", { maximumFractionDigits: 1 }));
const mb = (v) => (v == null ? "mengira…" : `${kb(v)} MB`);
const dt = (iso) => (iso ? iso.replace("T", " ").slice(0, 19) : "–");
const ago = (iso) => {
  if (!iso) return "–";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return `${Math.max(0, Math.round(s))}s lalu`;
  if (s < 3600) return `${Math.round(s / 60)}m lalu`;
  if (s < 86400) return `${Math.round(s / 3600)}j lalu`;
  return `${Math.round(s / 86400)}h lalu`;
};
const dur = (s) => {
  if (s == null) return "–";
  if (s < 120) return `${Math.round(s)}s`;
  if (s < 7200) return `${Math.round(s / 60)}m`;
  return `${(s / 3600).toFixed(1)}j`;
};

async function api(path, opts) {
  const o = opts || {};
  const headers = { ...(o.headers || {}) };
  if (S.meta && S.meta.csrf) headers["X-Console-Token"] = S.meta.csrf;
  // Had masa: permintaan yang tergantung TIDAK boleh membekukan seluruh UI.
  const ac = new AbortController();
  const ms = o.timeout || 25000;
  const timer = setTimeout(() => ac.abort(), ms);
  let r;
  try {
    r = await fetch(path, { cache: "no-store", ...o, headers, signal: ac.signal });
  } catch (e) {
    throw new Error(e && e.name === "AbortError" ? `tamat masa (${ms / 1000}s): ${path}` : e.message);
  } finally {
    clearTimeout(timer);
  }
  const j = await r.json().catch(() => ({ error: "respons bukan JSON" }));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

/* ---------------- shell ---------------- */
function renderHomes() {
  $("#homes").innerHTML = S.meta.homes
    .map((h) => `<button class="hbtn ${h.key === S.home ? "active" : ""}" data-home="${h.key}"
      style="${h.key === S.home ? `background:${esc(h.accent)}` : ""}">${esc(h.label)}</button>`)
    .join("");
  $$("#homes .hbtn").forEach((b) =>
    b.addEventListener("click", () => {
      S.home = b.dataset.home;
      S.sel = null;
      renderHomes();
      loadTab();
    })
  );
}

function setTab(tab) {
  S.tab = tab;
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === tab));
  $$(".pane").forEach((p) => p.classList.toggle("active", p.id === `tab-${tab}`));
  loadTab();
}

async function loadTab() {
  // Kalau satu render masih berjalan, JANGAN buang permintaan ini —
  // tandakan pending dan ulang selepas render semasa habis. Tanpa ini,
  // tukar tab dengan cepat akan meninggalkan tab kosong ("memuat…").
  if (S.busy) { S.pending = true; return; }
  S.busy = true;
  try {
    do {
      S.pending = false;
      try {
if (S.tab === "pusat") await loadPusat();
if (S.tab === "overview") await loadOverview();
if (S.tab === "work") await loadWork();
if (S.tab === "org") await loadOrg();
if (S.tab === "agency") await loadAgency();
if (S.tab === "ejen") await loadEjen();
if (S.tab === "trading") await loadTrading();
if (S.tab === "panduan") { await loadPanduan(); }
if (S.tab === "system") await loadSystem();
if (S.tab === "gudang") await loadGudang();
if (S.tab === "skill") await loadSkills();
if (S.tab === "watak") await loadWatak();
if (S.tab === "cron") await loadCron();
if (S.tab === "email") await loadEmail();
if (S.tab === "mcp") await loadMcp();
if (S.tab === "buka") await loadBuka();
if (S.tab === "sofia") await loadSofia();
if (S.tab === "web") await loadWeb();
if (S.tab === "sandaran") await window.loadSandaran();
        $("#livedot").classList.remove("bad");
      } catch (e) {
        $("#livedot").classList.add("bad");
        console.error(e);
      }
    } while (S.pending);
  } finally {
    S.busy = false;
  }
}

/* ---------------- overview ---------------- */
async function loadOverview() {
  const d = await api(`/api/overview?home=${S.home}`);
  const g = d.gateway || {};
  const online = g.pid_alive === true;
  const plat = Object.entries(g.platforms || {})
    .map(([k, v]) => `${k}:${v.state}`)
    .join(" · ") || "tiada platform";
  $("#ov-cards").innerHTML = [
    card("STATUS", g.pid_alive === true ? "HIDUP" : g.pid_alive === false ? "MATI" : "TIADA",
      `pid ${g.pid ?? "–"} · ${plat}`, g.pid_alive === true ? "" : "bad"),
    card("MODEL", "", d.model, "mono"),
    card("SESI", num(d.totals.sessions), `hari ini +${num(d.today.n)}`),
    card("MESEJ", num(d.totals.messages), `${num(d.totals.tools)} tool call`),
    card("TOKEN", num(d.totals.tin + d.totals.tout), `in ${num(d.totals.tin)} · out ${num(d.totals.tout)}`),
    card("KOS", `$${Number(d.totals.cost || 0).toFixed(2)}`, "anggaran USD", "warn"),
    card("STORAN", mb(d.storage.home_mb), `state.db ${kb(d.storage.state_db_mb)} MB`),
    card("AKTIVITI", ago(d.last ? d.last.started_iso : null), d.last ? dt(d.last.started_iso) : "tiada", "warn"),
  ].join("");

  const maxS = Math.max(1, ...d.series.map((x) => x.sessions));
  const maxT = Math.max(1, ...d.series.map((x) => x.tools));
  $("#ov-chart").innerHTML = d.series
    .map((x) => {
      const h = Math.round((x.sessions / maxS) * 100);
      const t = Math.round((x.tools / maxT) * 100);
      return `<div class="col" title="${x.date} · ${x.sessions} sesi · ${x.tools} tool · ${num(x.tokens)} token">
        <div class="bar" style="height:${Math.max(2, h)}%"><i style="height:${Math.min(100, t)}%"></i></div>
        <div class="lbl">${x.date.slice(8)}</div></div>`;
    })
    .join("");

  const L = d.last;
  $("#ov-last").innerHTML = L
    ? `<div class="kv"><span class="k">Sesi</span><span class="v">${esc(L.title || L.id)}</span></div>
       <div class="kv"><span class="k">Mula</span><span class="v">${dt(L.started_iso)}</span></div>
       <div class="kv"><span class="k">Sumber</span><span class="v">${esc(L.source)}</span></div>
       <div class="kv"><span class="k">Mesej / tool</span><span class="v">${num(L.message_count)} / ${num(L.tool_call_count)}</span></div>
       <div class="kv"><span class="k">Token</span><span class="v">${num(L.input_tokens)} → ${num(L.output_tokens)}</span></div>
       <div class="kv"><span class="k">Kos</span><span class="v">$${Number(L.estimated_cost_usd || 0).toFixed(3)}</span></div>
       <div class="kv"><span class="k">Aktiviti</span><span class="v">${esc(L.last_activity_description || "–")}</span></div>`
    : `<div class="empty">Tiada sesi.</div>`;

  $("#ov-recent").innerHTML = table(
    ["Mula", "Tajuk", "Sumber", "Mesej", "Tool", "Token", "Kos"],
    d.recent.map(
      (r) => `<tr><td class="n">${dt(r.started_iso)}</td>
      <td class="t">${esc(r.title || r.id)}</td>
      <td><span class="tag">${esc(r.source)}</span></td>
      <td class="n">${num(r.message_count)}</td><td class="n">${num(r.tool_call_count)}</td>
      <td class="n">${num((r.input_tokens || 0) + (r.output_tokens || 0))}</td>
      <td class="n">$${Number(r.estimated_cost_usd || 0).toFixed(3)}</td></tr>`
    )
  );
}

function card(k, v, s, cls = "", mono = "") {
  return `<div class="card ${cls}"><div class="k">${esc(k)}</div>
    ${v !== "" ? `<div class="v ${mono}">${esc(v)}</div>` : ""}${s ? `<div class="s">${esc(s)}</div>` : ""}</div>`;
}
function table(head, rows) {
  if (!rows.length) return `<div class="empty">Tiada data.</div>`;
  return `<table class="tbl"><thead><tr>${head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
}

/* ---------------- work ---------------- */
async function loadWork() {
  const q = $("#wq").value.trim();
  const lim = $("#wlimit").value;
  const d = await api(`/api/sessions?home=${S.home}&limit=${lim}&q=${encodeURIComponent(q)}`);
  S.sessions = d.sessions;
  $("#wcount").textContent = `${d.count} sesi · ${S.home}`;
  $("#w-list").innerHTML = `<div class="pbody">${table(
    ["Mula", "Tajuk", "Sumber", "Mesej", "Tool", "Tempoh"],
    d.sessions.map(
      (r) => `<tr class="rowlink ${S.sel === r.id ? "sel" : ""}" data-id="${esc(r.id)}">
        <td class="n">${dt(r.started_iso).slice(5)}</td>
        <td class="t">${esc(r.title || r.id)}</td>
        <td><span class="tag ${r.source === "cli" ? "blue" : "ok"}">${esc(r.source)}</span></td>
        <td class="n">${num(r.message_count)}</td>
        <td class="n">${num(r.tool_call_count)}</td>
        <td class="n">${dur(r.duration_s)}</td></tr>`
    )
  )}</div>`;
  $$("#w-list tr.rowlink").forEach((tr) =>
    tr.addEventListener("click", () => openSession(tr.dataset.id))
  );
  if (S.sel) openSession(S.sel);
}

async function openSession(id) {
  S.sel = id;
  $$("#w-list tr.rowlink").forEach((tr) => tr.classList.toggle("sel", tr.dataset.id === id));
  $("#w-detail").innerHTML = `<div class="pbody"><div class="empty">memuat ${esc(id)}…</div></div>`;
  const d = await api(`/api/session/${S.home}/${encodeURIComponent(id)}`);
  const s = d.session;
  const head = `<div class="ph"><h2>${esc(s.title || s.id)}</h2><span class="hint">${esc(s.source)} · ${dt(s.started_iso)}</span></div>
    <div class="pbody" style="border-bottom:1px solid var(--line)">
      <div class="kv"><span class="k">Model</span><span class="v">${esc(s.model || "–")}</span></div>
      <div class="kv"><span class="k">Tempoh</span><span class="v">${dur((s.ended_at || Date.now() / 1000) - s.started_at)}</span></div>
      <div class="kv"><span class="k">Mesej / tool</span><span class="v">${num(s.message_count)} / ${num(s.tool_call_count)}</span></div>
      <div class="kv"><span class="k">Token</span><span class="v">in ${num(s.input_tokens)} · out ${num(s.output_tokens)} · cache ${num(s.cache_read_tokens)}</span></div>
      <div class="kv"><span class="k">Kos</span><span class="v">$${Number(s.estimated_cost_usd || 0).toFixed(3)}</span></div>
      <div class="kv"><span class="k">Status</span><span class="v">${s.ended_at ? esc(s.end_reason || "tamat") : "aktif"}</span></div>
    </div>`;
  const msgs = d.messages
    .map((m) => {
      const tools = (m.tools || [])
        .map((t) => `<div class="toolcall">⚙ ${esc(t.name)}  ${esc(t.args)}</div>`)
        .join("");
      const label = m.role === "tool" ? `TOOL · ${esc(m.tool_name || "?")}` : m.role.toUpperCase();
      return `<div class="msg ${esc(m.role)}"><div class="mh"><b>${label}</b><span>#${m.id}</span><span>${dt(m.ts).slice(11)}</span>${m.tokens ? `<span>${num(m.tokens)}t</span>` : ""}</div>
        ${m.content ? `<div class="body">${esc(m.content)}</div>` : ""}${tools}</div>`;
    })
    .join("");
  $("#w-detail").innerHTML = `${head}<div class="pbody">${msgs || `<div class="empty">Tiada mesej aktif.</div>`}</div>`;
  $("#w-detail").scrollTop = 0;
}

/* ---------------- org ---------------- */
async function loadOrg() {
  const d = await api("/api/org");
  $("#org-hero").innerHTML = `<h1>${esc(d.identity || "KETUA")}</h1>
    <p>8 sistem enjin · ${d.systems.length} modul prompt · ${d.laws.length} undang-undang tetap · aliran wajib ${d.flow.length} langkah.</p>
    <p>${esc(d.language || "")}</p>`;
  $("#org-systems").innerHTML = d.systems
    .map(
      (s, i) => `<div class="sys"><div class="n"><span>${i + 1}. ${esc(s.name)}</span>
      <span class="tag ${s.exists ? "ok" : "bad"}">${s.exists ? kb(s.kb) + "K" : "TIADA"}</span></div>
      <div class="r">${esc(s.role)}</div><div class="w">Bila: ${esc(s.when)}</div>
      <div class="f">${esc(s.file)}</div></div>`
    )
    .join("");
  const gates = new Set(["qa_system", "recovery_system", "completion_system"]);
  $("#org-flow").innerHTML = d.flow
    .map(
      (f, i) => `<div class="step ${gates.has(f) ? "gate" : ""}"><span class="idx">${String(i + 1).padStart(2, "0")}</span>
      <span class="nm">${esc(f)}</span></div>`
    )
    .join("");
  $("#org-laws").innerHTML = d.laws
    .map((l) => `<li><b>${esc(l.title)}</b> <span>${esc(l.text)}</span></li>`)
    .join("");
  $("#org-lawcount").textContent = `${d.laws.length} undang-undang`;
  $("#org-skills").innerHTML = Object.entries(d.skills)
    .map(
      ([k, v]) => `<div><div class="sh">${esc(k.toUpperCase())} · ${v.count} skill</div>
      <div class="chips">${v.names.map((n) => `<span class="chip">${esc(n)}</span>`).join("") || "–"}</div></div>`
    )
    .join("");
}








/* ------------- muat naik imej pengguna (tab PANDUAN) ------------- */
function upPick() {
  const f = $("#up-file") && $("#up-file").files && $("#up-file").files[0];
  const img = $("#up-preview");
  if (!f) {
    $("#up-info").textContent = "tiada imej dipilih";
    if (img) { img.style.display = "none"; img.removeAttribute("src"); }
    return;
  }
  $("#up-info").textContent = `${f.name} · ${(f.size / 1024).toFixed(0)} KB`;
  if (img) { img.src = URL.createObjectURL(f); img.style.display = "block"; }
  $("#up-msg").textContent = "imej dipilih — tekan SIMPAN KE GALERI";
}

function upClear() {
  const i = $("#up-file");
  if (i) i.value = "";
  const img = $("#up-preview");
  if (img) { img.removeAttribute("src"); img.style.display = "none"; }
  $("#up-info").textContent = "tiada imej dipilih";
  $("#up-msg").textContent = "dikosongkan";
}

async function upSend() {
  const f = $("#up-file").files && $("#up-file").files[0];
  if (!f) { $("#up-msg").textContent = "pilih imej dahulu"; return; }
  const msg = $("#up-msg");
  msg.textContent = "menyimpan… (imej besar ambil masa)";
  const b64 = await new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(fr.result);
    fr.onerror = rej;
    fr.readAsDataURL(f);
  });
  try {
    const r = await api("/api/steps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        filename: f.name,
        caption: ($("#up-caption").value || "").trim() || f.name,
        content_b64: b64,
      }),
    });
    msg.textContent = `disimpan ✓ (${r.count} langkah dalam galeri)`;
    $("#up-caption").value = "";
    upClear();
    msg.textContent = `disimpan ✓ (${r.count} langkah dalam galeri)`;
    await loadPanduan();
  } catch (e) {
    msg.textContent = "gagal: " + e.message;
  }
}

/* ------------- tambah tangkapan skrin + ADB (tab SISTEM) ------------- */
function pdPreview() {
  const f = $("#pd-file") && $("#pd-file").files && $("#pd-file").files[0];
  const img = $("#pd-preview");
  if (!f) {
    $("#pd-fileinfo").textContent = "tiada imej dipilih";
    if (img) { img.style.display = "none"; img.removeAttribute("src"); }
    return;
  }
  $("#pd-fileinfo").textContent = `${f.name} · ${(f.size / 1024).toFixed(0)} KB`;
  if (img) {
    img.src = URL.createObjectURL(f);
    img.style.display = "block";
  }
}

function pdClear() {
  const inp = $("#pd-file");
  if (inp) inp.value = "";
  const img = $("#pd-preview");
  if (img) { img.removeAttribute("src"); img.style.display = "none"; }
  $("#pd-fileinfo").textContent = "tiada imej dipilih";
  $("#pd-msg").textContent = "imej dikosongkan";
  $("#cap-meta").textContent = "pilih imej + keterangan";
}

async function pdShot() {
  $("#pd-msg").textContent = "menangkap skrin…";
  try {
    const r = await api("/api/device/shot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ caption: ($("#pd-caption").value || "").trim() || "Tangkapan skrin peranti" }),
    });
    $("#pd-msg").textContent = `ditangkap ✓ ${(r.bytes / 1024).toFixed(0)} KB`;
    $("#pd-caption").value = "";
    if (S.tab === "panduan") loadPanduan();
    else toast("Tangkapan skrin ditambah ke PANDUAN", "ok");
  } catch (e) {
    $("#pd-msg").textContent = "gagal: " + e.message;
  }
}

async function adbPairFromUI() {
  const host = ($("#adb-host").value || "").trim();
  const code = ($("#adb-code").value || "").trim();
  const conn = ($("#adb-conn").value || "").trim();
  const log = $("#adb-log");
  if (!host || !code) { log.textContent = "Isi IP:port dan kod 6 digit."; return; }
  log.textContent = "menyambung…";
  try {
    const r = await api("/api/device/adb-pair", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host, code, connect: conn }),
    });
    log.textContent = (r.log || []).map((x) => `$ ${x.step}\n${x.out}`).join("\n\n") +
      `\n\nperanti: ${(r.devices || []).join(", ") || "tiada"}`;
    if (r.ok) {
      toast("ADB bersambung: " + r.devices.join(","), "ok");
      $("#adb-log").insertAdjacentHTML("afterbegin", `<div class="tag ok">BERSAMBUNG</div><br>`);
    } else {
      $("#adb-log").insertAdjacentHTML("afterbegin", `<div class="tag bad">BELUM BERSAMBUNG</div><br>`);
    }
  } catch (e) {
    log.textContent = "gagal: " + e.message;
  }
}

/* ---------------- panduan ---------------- */
async function loadPanduan() {
  try {
    const [st, sp] = await Promise.all([api("/api/device/status"), api("/api/steps")]);
    const f = st.fdroid || {}, apk = st.apk || {}, api2 = st.termux_api || {}, adb = st.adb || {};
    $("#pd-checked").textContent = "disemak " + String(st.checked_at || "").replace("T", " ");
    $("#pd-status").innerHTML = `
      <span class="tag ${f.installed ? "ok" : "bad"}">F-Droid: ${f.installed ? "ADA" : "TIADA"}</span>
      <span class="tag ${apk.exists ? "ok" : "bad"}">APK: ${apk.exists ? num(apk.bytes) + " bait" : "tiada"}</span>
      <span class="tag ${api2.working ? "ok" : "warn"}">Termux:API: ${api2.working ? "berfungsi" : api2.cli ? "ada, gagal" : "tiada"}</span>
      <span class="tag ${(adb.devices || []).length ? "ok" : "warn"}">ADB: ${(adb.devices || []).length ? esc(adb.devices.join(",")) : "belum paired"}</span>`;
    $("#pd-caveat").textContent = st.caveat || "";
    if (apk.sha256) {
      $("#pd-status").insertAdjacentHTML("beforeend",
        `<span class="copybox" style="margin-left:6px">sha256 ${esc(apk.sha256.slice(0, 24))}…</span>`);
    }

    const steps = sp.steps || [];
    $("#pd-count").textContent = steps.length + " langkah · " + (apk.path || "");
    $("#pd-steps").innerHTML = steps.map((s, i) => `
      <figure class="stepcard">
        <div class="stepnum">${i + 1}</div>
        <a href="${s.url}" target="_blank"><img class="stepimg" src="${s.url}" alt="${esc(s.caption || "")}" loading="lazy"></a>
        <figcaption>${esc(s.caption || "(tiada keterangan)")}
          <span class="hint">${esc(String(s.created || "").slice(0, 16).replace("T", " "))}</span></figcaption>
      </figure>`).join("") || `<div class="empty">Belum ada langkah.</div>`;
  } catch (e) {
    $("#pd-steps").innerHTML = `<div class="empty">gagal: ${esc(e.message)}</div>`;
  }
  try { await loadBoot(); } catch (_) {}
}

async function panduanUpload() {
  const f = $("#pd-file").files && $("#pd-file").files[0];
  if (!f) { $("#pd-msg").textContent = "pilih imej dahulu"; return; }
  const cap = ($("#pd-caption").value || "").trim();
  $("#pd-msg").textContent = "menghantar…";
  const b64 = await new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(fr.result);
    fr.onerror = rej;
    fr.readAsDataURL(f);
  });
  try {
    await api("/api/steps", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: f.name, caption: cap, content_b64: b64 }),
    });
    $("#pd-msg").textContent = "ditambah ✓";
    $("#pd-caption").value = "";
    pdClear();
    $("#pd-msg").textContent = "ditambah ✓";
    loadPanduan();
  } catch (e) {
    $("#pd-msg").textContent = "gagal: " + e.message;
  }
}

/* ---------------- inbox + laporan ---------------- */
async function loadInbox() {
  try {
    const d = await api("/api/inbox");
    $("#inbox-meta").textContent = `${d.count} item · ${d.dir}`;
    $("#inbox-list").innerHTML = (d.items || []).map((it) => `
      <div class="inbox-item" data-id="${esc(it.id)}">
        <div class="nm">${it.kind === "image" ? "🖼" : it.kind === "text" ? "📄" : it.kind === "note" ? "📝" : "📎"}
          ${esc(it.filename)} <span class="abadge">${esc(it.kind)}</span>
          <span class="abadge">${num(it.bytes)}b</span></div>
        ${it.kind === "image" && it.stored ? `<img class="thumb" src="/api/inbox/${esc(it.id)}/file" alt="${esc(it.filename)}" loading="lazy">` : ""}
        ${it.note ? `<div class="note">${esc(it.note)}</div>` : ""}
        <div class="acts">
          <button class="btn" data-act="task" data-id="${esc(it.id)}">→ Tugasan baru</button>
          <button class="btn" data-act="run" data-id="${esc(it.id)}">→ Run aktif</button>
          ${it.stored ? `<a class="btn" href="/api/inbox/${esc(it.id)}/file" target="_blank">lihat fail</a>` : ""}
        </div>
      </div>`).join("") || `<div class="empty">Inbox kosong. Tambah fail atau nota di atas.</div>`;
    $$("#inbox-list button[data-act]").forEach((b) =>
      b.addEventListener("click", () => b.dataset.act === "task" ? inboxToTask(b.dataset.id) : inboxToRun(b.dataset.id))
    );
  } catch (e) {
    $("#inbox-list").innerHTML = `<div class="empty">gagal: ${esc(e.message)}</div>`;
  }
}

async function inboxUpload(files) {
  if (!files || !files.length) return;
  const note = ($("#inbox-note").value || "").trim();
  $("#inbox-status").textContent = `menghantar ${files.length} fail…`;
  for (const f of files) {
    const b64 = await new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result);
      fr.onerror = rej;
      fr.readAsDataURL(f);
    });
    try {
      await api("/api/inbox", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: f.name, note, content_b64: b64 }),
      });
    } catch (e) {
      $("#inbox-status").textContent = "gagal: " + e.message;
      return;
    }
  }
  $("#inbox-note").value = "";
  $("#inbox-status").textContent = "ditambah ✓";
  loadInbox();
}

function inboxToTask(id) {
  S.da = S.da || {};
  S.da.attach = S.da.attach || [];
  if (!S.da.attach.includes(id)) S.da.attach.push(id);
  renderAttachChips();
  setTab("agency");
  const inp = $("#da-instr");
  if (!inp.value.trim()) inp.value = "Gunakan lampiran dalam inbox sebagai bahan kerja. ";
  inp.focus();
  toast("Lampiran dilekatkan pada tugasan baru", "ok");
}

async function addNoteOnly() {
  const note = ($("#inbox-note").value || "").trim();
  if (!note) return ($("#inbox-status").textContent = "tulis nota atau pilih fail");
  try {
    await api("/api/inbox", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: "nota.txt", note, content_b64: "" }),
    });
    $("#inbox-note").value = "";
    $("#inbox-status").textContent = "nota ditambah ✓";
    loadInbox();
  } catch (e) {
    $("#inbox-status").textContent = "gagal: " + e.message;
  }
}

async function inboxToRun(id) {
  const active = (S.pusat.live && S.pusat.live.runs) || [];
  const run = active[0] || (S.da && S.da.run && S.da.run.status === "running" ? S.da.run : null);
  if (!run) return toast("Tiada run aktif untuk dibetulkan", "bad");
  try {
    await api(`/api/agency/run/${encodeURIComponent(run.id)}/note`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "Lampiran baharu daripada pengguna — ambil kira dalam kerja seterusnya.", attachment_ids: [id] }),
    });
    toast(`Lampiran dihantar ke run ${run.id}`, "ok");
  } catch (e) {
    toast("gagal: " + e.message, "bad");
  }
}

function renderAttachChips() {
  const ids = (S.da && S.da.attach) || [];
  const el = $("#da-atts");
  if (!el) return;
  el.innerHTML = ids.length
    ? "Lampiran: " + ids.map((id) => `<span class="tag ok">${esc(id)}</span>
        <span class="tag" style="cursor:pointer" data-rm="${esc(id)}">✕</span>`).join(" ")
    : "";
  $$("#da-atts [data-rm]").forEach((x) =>
    x.addEventListener("click", () => {
      S.da.attach = ids.filter((i) => i !== x.dataset.rm);
      renderAttachChips();
    })
  );
}

async function loadReport() {
  try {
    const h = S.meta && S.meta.csrf ? { "X-Console-Token": S.meta.csrf } : {};
    const res = await fetch("/api/report/daily", { cache: "no-store", headers: h });
    const md = await res.text();
    $("#report-preview").textContent = md.slice(0, 2600);
    $("#report-meta").textContent = `${md.length} aksara · /api/report/daily`;
  } catch (e) {
    $("#report-preview").textContent = "gagal: " + e.message;
  }
}

async function reportTelegram() {
  $("#report-status").textContent = "menghantar…";
  try {
    const r = await api("/api/report/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channel: "telegram" }),
    });
    $("#report-status").textContent = `dihantar ✓ (msg ${r.message_id})`;
    toast("Laporan dihantar ke Telegram", "ok");
  } catch (e) {
    $("#report-status").textContent = "gagal";
    toast("gagal hantar: " + e.message, "bad");
  }
}

/* ---------------- peta ejen, bot, sejarah, drawer ---------------- */
function renderMap(runs) {
  const body = $("#map-body");
  if (!runs.length) {
    body.innerHTML = `<div class="empty">Tiada ejen berjalan. Peta akan hidup bila run bermula.</div>`;
    $("#map-meta").textContent = "0 ejen aktif";
    return;
  }
  const rows = [];
  let activeN = 0, cost = 0;
  runs.forEach((r) => {
    rows.push(`<tr><td colspan="6" style="padding:10px 8px 4px">
      <span class="tag ${r.status === "synthesizing" ? "warn" : "ok"}">${esc(r.status)}</span>
      <b class="mono" style="margin-left:6px">${esc(r.id)}</b>
      <span class="hint" style="margin-left:8px">gelombang ${r.wave}/${r.wave_total} · ${r.finished}/${r.total} ejen ·
      kos $${Number(r.cost_so_far || 0).toFixed(4)} · ${num(r.tokens_so_far)} tok</span></td></tr>`);
    cost += Number(r.cost_so_far || 0);
    (r.agents || []).forEach((a) => {
      if (a.state === "running") activeN++;
      rows.push(`<tr class="maprow" data-slug="${esc(a.slug)}">
        <td><span class="tag ${a.state === "running" ? "warn" : a.state === "done" ? "ok" : ""}">${esc(a.state)}</span></td>
        <td>${esc(a.emoji || "")} ${esc(a.nama || a.slug)}</td>
        <td class="loc">${esc(a.location || "–")}</td>
        <td class="n">${a.elapsed_s != null ? a.elapsed_s + "s" : "–"}</td>
        <td class="n">${a.tokens ? num(a.tokens) : "–"}</td>
        <td class="n">${a.cost != null ? "$" + Number(a.cost).toFixed(4) : "–"}</td></tr>`);
    });
  });
  body.innerHTML = table(
    ["Status", "Ejen", "Lokasi (sistem → divisi → ejen)", "Masa", "Token", "Kos"],
    rows
  );
  $("#map-meta").textContent = `${activeN} ejen aktif · kos setakat $${cost.toFixed(4)}`;
  $$("#map-body .maprow").forEach((tr) =>
    tr.addEventListener("click", () => openAgentDrawer(tr.dataset.slug))
  );
}

async function openAgentDrawer(slug) {
  closeDrawer();
  document.body.insertAdjacentHTML("beforeend",
    `<div class="drawer" id="drawer"><div class="drawer-box">
      <div class="drawer-head"><b class="mono">${esc(slug)}</b><span class="drawer-close" id="drawer-x">TUTUP ✕</span></div>
      <div class="drawer-body" id="drawer-body"><div class="empty">memuat…</div></div>
    </div></div>`);
  $("#drawer-x").addEventListener("click", closeDrawer);
  $("#drawer").addEventListener("click", (e) => { if (e.target.id === "drawer") closeDrawer(); });
  try {
    const a = await api(`/api/agent-live/${encodeURIComponent(slug)}`);
    const run = a.run || {};
    const out = a.output || {};
    const state = (a.active || {}).state || "tiada dalam run aktif";
    $("#drawer-body").innerHTML = `
      <div class="kv"><span class="k">Nama</span><span class="v">${esc(a.emoji || "")} ${esc(a.nama)}</span></div>
      <div class="kv"><span class="k">Lokasi</span><span class="v">${esc(a.location || "–")}</span></div>
      <div class="kv"><span class="k">Status</span><span class="v">${esc(state)}</span></div>
      <div class="kv"><span class="k">Masa</span><span class="v">${(a.active || {}).elapsed_s != null ? a.active.elapsed_s + "s" : "–"}</span></div>
      <div class="kv"><span class="k">Kos (run ini)</span><span class="v">${a.active && a.active.cost != null ? "$" + Number(a.active.cost).toFixed(4) : (run.cost ? "$" + Number(run.cost).toFixed(4) : "–")}</span></div>
      <div class="kv"><span class="k">Token</span><span class="v">${num(a.active && a.active.tokens ? a.active.tokens : run.tokens || 0)}</span></div>
      <div class="kv"><span class="k">Kos hari ini</span><span class="v">${a.today ? "$" + Number(a.today.cost).toFixed(4) + " · " + num(a.today.tokens) + " tok" : "–"}</span></div>
      <div class="kv"><span class="k">Run</span><span class="v">${esc(run.id || "–")} ${run.status ? "· " + esc(run.status) : ""}</span></div>
      <div class="kv"><span class="k">Gelombang</span><span class="v">${run.wave ? run.wave + "/" + run.wave_total : "–"}</span></div>
      <div class="kv"><span class="k">Tugasan</span><span class="v">${esc(run.instruction || "–")}</span></div>
      ${(run.attachments || []).length ? `<div class="hint" style="margin:12px 0 4px">Lampiran run (${run.attachments.length})</div>
        <div class="thumbs">${run.attachments.map((x) =>
          x.kind === "image"
            ? `<a href="/api/inbox/${esc(x.id)}/file" target="_blank"><img class="thumb" src="/api/inbox/${esc(x.id)}/file" alt="${esc(x.filename)}"></a>`
            : `<a class="tag blue" href="/api/inbox/${esc(x.id)}/file" target="_blank">📎 ${esc(x.filename)}</a>`
        ).join("")}</div>` : ""}
      <div class="hint" style="margin:12px 0 6px">Output ${out.status ? "· " + esc(out.status) : ""}</div>
      <div class="bodytext" style="max-height:38vh">${esc(out.text || "(tiada output lagi)")}</div>`;
  } catch (e) {
    $("#drawer-body").innerHTML = `<div class="empty">gagal: ${esc(e.message)}</div>`;
  }
}

function closeDrawer() {
  const d = $("#drawer");
  if (d) d.remove();
}

async function loadHistory() {
  try {
    const h = await api("/api/history?days=7");
    const days = h.days || [];
    if (!days.length) {
      $("#hist-body").innerHTML = `<div class="empty">Belum ada sampel. Rekod ditulis setiap 60 saat.</div>`;
      return;
    }
    const val = (d) => Number(d.console_cost || d.cost || 0);
    const maxC = Math.max(0.0001, ...days.map(val));
    $("#hist-body").innerHTML = `
      <div class="histbars">${days.map((d) => `
        <div class="hb" title="${esc(d.date)} · $${val(d).toFixed(4)} kos konsol · ${d.agents_peak} ejen puncak">
          <i style="height:${Math.max(3, Math.round((val(d) / maxC) * 100))}%"></i>
          <span>${esc(d.date.slice(5))}</span></div>`).join("")}</div>
      <div class="spark-axis"><span>kos harian (USD)</span><span>${days.length} hari</span></div>
      <div class="kv" style="margin-top:8px"><span class="k">Kos konsol 7 hari</span><span class="v">$${days.reduce((a, b) => a + val(b), 0).toFixed(4)}</span></div>
      <div class="kv"><span class="k">Puncak ejen</span><span class="v">${Math.max(...days.map((d) => d.agents_peak))}</span></div>
      <div class="kv"><span class="k">Sampel</span><span class="v">${h.samples} · ${esc(h.file)}</span></div>`;
    $("#hist-meta").textContent = `${days.length} hari`;
  } catch (e) {
    $("#hist-body").innerHTML = `<div class="empty">gagal: ${esc(e.message)}</div>`;
  }
}

function botLine(text, who) {
  const log = $("#bot-log");
  const div = document.createElement("div");
  div.className = `bot-line ${who}`;
  div.textContent = text;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

async function botSend() {
  const inp = $("#bot-cmd");
  const cmd = (inp.value || "").trim();
  if (!cmd) return;
  botLine("> " + cmd, "user");
  inp.value = "";
  try {
    const r = await api("/api/bot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd }),
    });
    botLine(r.reply, "bot");
  } catch (e) {
    botLine("RALAT: " + e.message, "sys");
  }
}

/* ---------------- WEB UI (dashboard 9119) ---------------- */
async function loadWeb() {
  const d = await api("/api/web");
  const chips = [
    `<span class="chip-live ${d.port_open ? "" : "bad"}">port 9119 <b>${d.port_open ? "BUKA" : "MATI"}</b></span>`,
    ...d.services.map((s) => {
      const cls = s.state === "run" ? "" : s.state === "ralat" ? "bad" : "warn";
      return `<span class="chip-live ${cls}">${esc(s.label || s.name)} <b>${esc(s.state)}</b></span>`;
    }),
  ];
  $("#web-chips").innerHTML = chips.join("");
  $("#web-url").textContent = d.url || "(URL belum ada — tunnel belum siap)";
  $("#web-updated").textContent = d.url_updated ? `dikemas kini ${d.url_updated}` : "";
  $("#web-lan").textContent = d.lan ? `http://${d.lan}:9119/` : "tiada WiFi";
  $("#web-user").textContent = d.user || "–";
  $("#web-secret").textContent = d.secret_file;
  $("#web-svc").innerHTML = d.services.map((s) => {
    const cls = s.state === "run" ? "ok" : "bad";
    return `<div class="svc-row">
      <div class="svc-main"><b>${esc(s.label || s.name)}</b>
        <span class="tag ${cls}">${esc(s.state)}</span>
        <div class="hint mono">${esc(s.name)}${s.raw ? " · " + esc(String(s.raw).slice(0, 70)) : ""}</div></div>
      <div class="svc-act">
        <button class="btn" data-wsvc="${esc(s.name)}" data-act="up">HIDUP</button>
        <button class="btn" data-wsvc="${esc(s.name)}" data-act="restart">MULA SEMULA</button>
        <button class="btn" data-wsvc="${esc(s.name)}" data-act="log">LOG</button>
      </div></div>`;
  }).join("");
  $$("#web-svc button[data-wsvc]").forEach((b) =>
    b.addEventListener("click", () => webSvc(b.dataset.wsvc, b.dataset.act)));
}

async function webSvc(name, act) {
  const msg = $("#web-msg");
  if (act === "log") {
    try {
      const r = await api(`/api/svc/${encodeURIComponent(name)}/log?lines=60`);
      $("#web-log").textContent = `${r.file} (${num(r.bytes)} bait)\n\n` + (r.lines || []).join("\n");
      $("#web-logmeta").textContent = name + " · log";
    } catch (e) { $("#web-log").textContent = "gagal: " + e.message; }
    return;
  }
  msg.textContent = `${act} ${name}…`;
  try {
    const r = await api(`/api/svc/${encodeURIComponent(name)}`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: act }), timeout: 40000,
    });
    msg.textContent = `${name}: ${act} ✓`;
    await loadWeb();
  } catch (e) { msg.textContent = "gagal: " + e.message; }
}

async function webVerify() {
  const msg = $("#web-msg"), log = $("#web-log");
  msg.textContent = "menguji…";
  log.textContent = "menjalankan ujian penuh (5 tanda)…";
  try {
    const r = await api("/api/web/verify", { method: "POST", timeout: 120000 });
    log.textContent = r.out || "(tiada output)";
    $("#web-logmeta").textContent = r.ok ? "LULUS ✓" : "GAGAL";
    msg.textContent = r.ok ? "lulus ✓" : "ada yang gagal — lihat log";
    await loadWeb();
  } catch (e) { log.textContent = "gagal: " + e.message; msg.textContent = "gagal"; }
}

/* ---------------- BUKA (lancar app) ---------------- */
async function loadBuka() {
  const d = await api("/api/buka");
  $("#buka-bin").textContent = d.exists ? d.bin : "skrip TIADA: " + d.bin;
  $("#buka-fixed").innerHTML = d.fixed.map((f) =>
    `<button class="btn" data-buka="${esc(f.t)}">${esc(f.n)}</button>`).join("");
  $("#buka-apps").innerHTML = d.apps.length
    ? d.apps.map((p) => `<button class="btn" data-buka="${esc(p)}">${esc(p.replace(/^[a-z]+\./, ""))}</button>`).join("")
    : `<span class="hint">tiada app pihak ketiga</span>`;
  $$("[data-buka]").forEach((b) => b.addEventListener("click", () => bukaRun(b.dataset.buka)));
}

async function bukaRun(target) {
  const log = $("#buka-log"), meta = $("#buka-meta");
  meta.textContent = "menjalankan: " + target;
  log.textContent = "…";
  try {
    const r = await api("/api/buka", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target }), timeout: 130000,
    });
    log.textContent = (r.ok ? "OK · " : "GAGAL · ") + "exit " + r.exit + "\n\n" + r.out;
    meta.textContent = r.ok ? "berjaya: " + target : "gagal: " + target;
  } catch (e) { log.textContent = "ralat: " + e.message; meta.textContent = "ralat"; }
}

async function bukaUrlGo() {
  const u = ($("#buka-url").value || "").trim();
  if (!u) return;
  const log = $("#buka-log"), meta = $("#buka-meta");
  meta.textContent = "membuka URL…";
  try {
    const r = await api("/api/buka", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: u }), timeout: 130000,
    });
    log.textContent = (r.ok ? "OK · " : "GAGAL · ") + "exit " + r.exit + "\n\n" + r.out;
    meta.textContent = r.ok ? "URL dibuka" : "gagal buka URL";
  } catch (e) { log.textContent = "ralat: " + e.message; }
}

/* ---------------- gudang (hantar ke telefon) ---------------- */
function gdSaiz(v) {
  const n = Number(v || 0);
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

function gdPilih() {
  const sel = $("#gd-calon");
  const it = ((S.gd && S.gd.calon) || []).find((x) => x.laluan === sel.value);
  $("#gd-pdf").disabled = !(it && /\.md$/i.test(it.laluan));
}

async function loadGudang() {
  const d = await api("/api/uim/state");
  S.gd = d;
  const calon = d.calon || [];
  const lama = $("#gd-calon").value;
  $("#gd-calon").innerHTML = calon.length
    ? calon
        .map((c) => `<option value="${esc(c.laluan)}">${esc(c.nama)} · ${gdSaiz(c.saiz)}</option>`)
        .join("")
    : `<option value="">tiada calon dalam ~/.hermes20/docs / workspaces/*/outbox</option>`;
  if (lama && calon.some((c) => c.laluan === lama)) $("#gd-calon").value = lama;
  gdPilih();

  const g = d.gudang || [];
  $("#gd-meta").textContent = d.akar || "Documents → UIM";
  $("#gd-ringkas").textContent = `${num((d.ringkasan || {}).fail || 0)} fail · ${gdSaiz((d.ringkasan || {}).saiz || 0)}`;
  $("#gd-senarai").textContent = g.length
    ? g.slice(0, 120).map((f) => `${f.kategori} / ${f.nama} · ${gdSaiz(f.saiz)} · ${dt(f.masa)}`).join("\n")
    : "gudang kosong — hantar fail pertama.";
  $("#gd-log").textContent = (d.log && d.log.length) ? d.log.join("\n") : "tiada log lagi.";
}

async function gdHantar(pdf) {
  const path = $("#gd-calon").value;
  if (!path) { $("#gd-msg").textContent = "pilih fail dahulu"; return; }
  const btn = pdf ? $("#gd-pdf") : $("#gd-hantar");
  const lain = pdf ? $("#gd-hantar") : $("#gd-pdf");
  btn.disabled = true;
  lain.disabled = true;
  $("#gd-msg").textContent = pdf ? "menjana PDF…" : "menyalin…";
  $("#gd-out").textContent = "menjalankan skrip…";
  try {
    const body = pdf
      ? { path }
      : { path, kategori: ($("#gd-kategori").value || "").trim() };
    const r = await api(pdf ? "/api/uim/pdf" : "/api/uim/hantar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      timeout: 130000,
    });
    $("#gd-out").textContent = r.output || "(tiada output)";
    if (r.ok) {
      $("#gd-msg").textContent = r.laluan ? `SIAP → ${r.laluan}` : "SIAP";
      $("#gd-out").textContent += `\n\nLALUAN PENUH: ${r.laluan || "–"}\n${r.arahan || "Buka app Files → Documents → UIM"}`;
      loadGudang().catch(() => {});
    } else {
      $("#gd-msg").textContent = `GAGAL (kod ${r.kod})`;
    }
  } catch (e) {
    $("#gd-msg").textContent = "RALAT: " + e.message;
    $("#gd-out").textContent = String(e.message || e);
  } finally {
    btn.disabled = false;
    lain.disabled = false;
    gdPilih();
  }
}

/* ---------------- sofia (PC) ---------------- */
function sfDur(s) {
  if (s == null) return "–";
  s = Math.max(0, Math.round(Number(s)));
  const d = Math.floor(s / 86400), j = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  if (d) return `${d}h ${j}j`;
  if (j) return `${j}j ${m}m`;
  return `${m}m`;
}
function sfAgo(s) {
  if (s == null) return "–";
  s = Math.max(0, Math.round(Number(s)));
  if (s < 60) return `${s}s lalu`;
  if (s < 3600) return `${Math.floor(s / 60)}m lalu`;
  if (s < 86400) return `${Math.floor(s / 3600)}j lalu`;
  return `${Math.floor(s / 86400)}h lalu`;
}

async function loadSofia() {
  const d = await api("/api/sofia").catch((e) => ({ ada: false, ralat: e.message }));
  const kosong = (t) => { const el = $("#sf-cards"); if (el) el.innerHTML = ""; return `<div class="empty">${esc(t)}</div>`; };
  if (!d.ada) {
    $("#sf-msg").textContent = d.ralat ? "RALAT" : "belum ada data";
    $("#sf-alerts").innerHTML = kosong(d.nota || d.ralat || "repo relay sofia-status belum wujud.");
    $("#sf-detail").innerHTML = `<div class="empty">folder dijangka: ${esc(d.folder || "–")}</div>`;
    $("#sf-log").textContent = "–";
    $("#sf-alert-meta").textContent = "–";
    $("#sf-detail-meta").textContent = "–";
    return;
  }
  const s = d.data || {}, h = s.hermes || {}, disk = (s.disks || [])[0] || {};
  $("#sf-msg").textContent = `data ${sfAgo(d.umur_s)}${d.basi ? " · BASI" : ""}`;
  $("#sf-cards").innerHTML = [
    card("PC", d.basi ? "BASI" : "HIDUP", s.host || "–", d.basi ? "bad" : ""),
    card("OS", "", s.os || "–"),
    card("HIDUP", sfDur(s.uptime_s), "sejak boot"),
    card("CPU", s.cpu_pct == null ? "–" : `${s.cpu_pct}%`, `${s.cores || "?"} teras`),
    card("RAM", s.ram_pct == null ? "–" : `${s.ram_pct}%`,
      `${s.ram_used_gb ?? "?"} / ${s.ram_total_gb ?? "?"} GB`, (s.ram_pct || 0) >= 92 ? "bad" : ""),
    card("CAKERA", disk.pct == null ? "–" : `${disk.pct}%`,
      disk.mount ? `${disk.mount} · ${disk.free_gb} GB bebas` : "–", (disk.pct || 0) >= 90 ? "bad" : ""),
    card("GATEWAY", h.gateway_alive === true ? "HIDUP" : h.gateway_alive === false ? "MATI" : "TIADA",
      h.version ? `v${h.version}` : "sofia", h.gateway_alive === false ? "bad" : ""),
    card("SESI HARI INI", num(h.sessions_today), `${num(h.messages_today)} mesej`),
  ].join("");

  const al = s.alerts || [];
  $("#sf-alert-meta").textContent = al.length ? `${al.length} amaran` : "tiada";
  $("#sf-alerts").innerHTML = al.length
    ? `<ul style="margin:0;padding-left:20px;line-height:1.8">${al.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>`
    : `<div class="empty">Tiada amaran. PC sihat.</div>`;

  const ls = h.last_session || {}, lc = h.last_cron || {};
  const kv = (k, v) => `<div class="kv"><span class="k">${esc(k)}</span><span class="v">${esc(v)}</span></div>`;
  $("#sf-detail").innerHTML = [
    kv("Home Hermes", h.home || "–"),
    kv("Sesi terakhir", ls.title ? `${ls.title} (${sfAgo(ls.ago_s)})` : "–"),
    kv("Kerja cron", h.cron_jobs == null ? "–" : `${h.cron_jobs} job`),
    kv("Cron terakhir", lc.ago_s == null ? "–" : `${lc.name || "?"} · ${sfAgo(lc.ago_s)}${lc.status ? " · " + lc.status : ""}`),
    kv("Masa tolak", s.ts || "–"),
    kv("Umur data", `${d.umur_s}s${d.basi ? " (basi — Sofia mungkin mati)" : ""}`),
  ].join("");
  $("#sf-detail-meta").textContent = (s.alerts || []).length ? "perlu tindakan" : "sihat";
  $("#sf-log").textContent = (d.log && d.log.length) ? d.log.join("\n") : "tiada log tarikan.";
}

/* ---------------- command palette (Ctrl/Cmd+K) ---------------- */
const TABS = [
  ["pusat", "PUSAT"], ["overview", "OVERVIEW"], ["work", "KERJA"], ["org", "ORGANISASI"],
  ["agency", "AGENCY"], ["ejen", "EJEN"], ["trading", "TRADING 19"],
 ["panduan", "PANDUAN"], ["system", "SISTEM"], ["gudang", "GUDANG"], ["buka", "BUKA"], ["sofia", "SOFIA · PC"],
 ["sandaran", "SANDARAN"],
];
let CMDK = { open: false, items: [], idx: 0 };

function openCmdk() {
  if (CMDK.open) return;
  CMDK.open = true;
  document.body.insertAdjacentHTML(
    "beforeend",
    `<div class="cmdk" id="cmdk"><div class="cmdk-box">
      <input id="cmdk-q" placeholder="Cari tab, ejen, atau tindakan…" autocomplete="off">
      <div class="cmdk-list" id="cmdk-list"></div>
      <div class="cmdk-foot">↑↓ pilih · Enter buka · Esc tutup · Ctrl/⌘K</div>
    </div></div>`
  );
  const q = $("#cmdk-q");
  const items = TABS.map(([tab, label], i) => ({
    key: String(i + 1), label: label, sub: "tab", run: () => setTab(tab),
  })).concat([
    { key: "R", label: "Muat semula data", sub: "aksi", run: () => loadTab() },
    { key: "W", label: "Buka imej alur kerja", sub: "imej", run: () => window.open("/static/img/workflow.png", "_blank") },
    { key: "A", label: "Dewan Arahan (AGENCY)", sub: "aksi", run: () => { setTab("agency"); $("#da-instr").focus(); } },
  ]);
  const top = (S.ag.data?.agents || []).slice(0, 12).map((a) => ({
    key: "ejen", label: `${a.emoji || ""} ${a.name}`, sub: a.division,
    run: () => { setTab("agency"); S.ag.sel = a.slug; openAgent(a.slug); },
  }));
  CMDK.items = items.concat(top);
  const render = () => {
    const term = (q.value || "").toLowerCase().trim();
    const list = CMDK.items.filter((it) => !term || (it.label + " " + it.sub).toLowerCase().includes(term));
    CMDK.filtered = list;
    CMDK.idx = Math.min(CMDK.idx, Math.max(0, list.length - 1));
    $("#cmdk-list").innerHTML =
      list.map((it, i) => `<div class="cmdk-item ${i === CMDK.idx ? "sel" : ""}" data-i="${i}">
        <span class="kk">${esc(it.key)}</span><span>${esc(it.label)}</span>
        <span class="sub">${esc(it.sub)}</span></div>`).join("") ||
      `<div class="cmdk-item">tiada padanan</div>`;
    $$("#cmdk-list .cmdk-item").forEach((el) =>
      el.addEventListener("click", () => {
        const it = CMDK.filtered[Number(el.dataset.i)];
        closeCmdk();
        it && it.run();
      })
    );
  };
  q.addEventListener("input", () => { CMDK.idx = 0; render(); });
  q.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { CMDK.idx = Math.min(CMDK.idx + 1, (CMDK.filtered || []).length - 1); render(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { CMDK.idx = Math.max(0, CMDK.idx - 1); render(); e.preventDefault(); }
    else if (e.key === "Enter") {
      const it = (CMDK.filtered || [])[CMDK.idx];
      closeCmdk();
      it && it.run();
    }
  });
  $("#cmdk").addEventListener("click", (e) => { if (e.target.id === "cmdk") closeCmdk(); });
  render();
  q.focus();
  if (!S.ag.data) api("/api/agency?limit=20").then((d) => { S.ag.data = d; }).catch(() => {});
}

function closeCmdk() {
  CMDK.open = false;
  const el = $("#cmdk");
  if (el) el.remove();
}

function bindKeys() {
  document.addEventListener("keydown", (e) => {
    const typing = ["INPUT", "TEXTAREA", "SELECT"].includes((document.activeElement || {}).tagName || "");
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); openCmdk(); return; }
    if (e.key === "Escape") { closeCmdk(); closeDrawer(); return; }
    if (typing || CMDK.open) return;
    const n = Number(e.key);
    if (n >= 1 && n <= TABS.length) setTab(TABS[n - 1][0]);
  });
}

function fmtSec(s) {
  if (s == null) return "–";
  if (s < 60) return Math.round(s) + "s";
  const m = Math.floor(s / 60), r = Math.round(s % 60);
  return m + "m " + r + "s";
}

async function loadWork() {
  const box = $("#ws-list");
  if (!box) return;
  try {
    const st = await api("/api/live/state");
    const runs = st.runs || [];
    $("#ws-meta").textContent = runs.length ? runs.length + " run aktif" : "tiada run";
    if (!runs.length) {
      box.innerHTML = `<div class="empty">Tiada tugasan berjalan. ${st.stats && st.stats.selesai ? "Selesai setakat ini: " + st.stats.selesai : ""}</div>`;
      return;
    }
    box.innerHTML = runs.map((r) => {
      const agents = r.agents || [];
      const rows = agents.map((a) => {
        const st2 = a.state || "queued";
        const cls = st2 === "running" ? "warn" : st2 === "done" ? "ok" : "";
        const cost = a.cost ? "$" + Number(a.cost).toFixed(4) : "–";
        return `<div class="svc-row" style="padding:8px 11px">
          <div class="svc-main"><b>${esc(a.name || a.slug)}</b>
            <span class="tag ${cls}">${esc(st2.toUpperCase())}</span>
            <div class="hint mono">${esc(a.model || "model lalai")} · ${fmtSec(a.elapsed_s)} · ${a.tokens || 0} tok · ${cost}</div>
          </div></div>`;
      }).join("");
      return `<div style="margin-bottom:14px">
        <div class="hint mono" style="margin-bottom:6px">${esc(r.id)} · ${esc(r.status || "")} · gelombang ${r.wave || 1}/${r.wave_total || 1} · ${r.finished || 0}/${r.total || 0} siap</div>
        <div style="font-size:13px;color:var(--ink2);margin-bottom:8px">${esc((r.instruction || "").slice(0, 160))}</div>
        <div class="workbar" style="margin-bottom:8px">
          <button class="btn" data-run="${esc(r.id)}" data-ra="stop">HENTIKAN</button>
          <button class="btn" data-run="${esc(r.id)}" data-ra="rerun">ULANG</button>
          <button class="btn" data-run="${esc(r.id)}" data-ra="delete">PADAM</button>
        </div>
        ${rows || '<div class="empty">tiada ejen</div>'}
      </div>`;
    }).join("");
    $$("[data-run]").forEach((b) =>
      b.addEventListener("click", () => runAct(b.dataset.run, b.dataset.ra)));
  } catch (e) {
    $("#ws-meta").textContent = "gagal: " + e.message;
  }
}

/* butang RESET GERBANG di tab PUSAT (dipasang sekali sahaja) */
function wireGwReset() {
  const b = $("#gw-reset");
  if (!b || b.dataset.wired) return;
  b.dataset.wired = "1";
  b.addEventListener("click", async () => {
    if (!confirm("Mula semula gerbang Telegram sekarang?")) return;
    const msg = $("#gw-reset-msg");
    const asal = b.textContent;
    b.disabled = true;
    b.textContent = "…";
    if (msg) msg.textContent = "menghantar arahan restart…";
    try {
      const r = await api("/api/svc/hermes-gateway", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "restart" }),
      });
      const st = (r.status && r.status.state) || "?";
      toast(`hermes-gateway: restart → ${st}`, r.ok ? "ok" : "bad");
      if (msg) {
        msg.textContent = `restart dihantar · status ${st} · ${new Date().toLocaleTimeString()}`;
      }
      loadFleet();
    } catch (e) {
      toast("gagal reset gerbang: " + e.message, "bad");
      if (msg) msg.textContent = "GAGAL: " + e.message;
    } finally {
      b.disabled = false;
      b.textContent = asal;
    }
  });
}

async function loadFleet() {
  wireGwReset();
  try {
    const d = await api("/api/fleet");
    $("#fl-meta").textContent = "dikemas kini " + d.now;
    $("#fl-gw").innerHTML = d.gateways.map((g) => {
      const cls = g.alive ? "ok" : "bad";
      const age = g.log_age_min == null ? "tiada log" : `${g.log_age_min} min lalu`;
      return `<div class="svc-row"><div class="svc-main"><b>${esc(g.name)}</b>
        <span class="tag ${cls}">${g.alive ? "HIDUP" : "MATI"}</span>
        <div class="hint mono">${esc(age)}</div></div></div>`;
    }).join("");
    const live = S.pusat.live || {};
    const active = (live.active_agents || []).length;
    const queued = (live.runs || []).reduce((n, r) =>
      n + (r.agents || []).filter((a) => a.state === "queued").length, 0);
    const total = (S.pusat.chart && S.pusat.chart.totals && S.pusat.chart.totals.agents) || 282;
    const rest = Math.max(0, total - active - queued);
    $("#fl-chips").innerHTML = [
      `<span class="chip-live">BEKERJA <b>${active}</b></span>`,
      `<span class="chip-live warn">BERFIKIR <b>${queued}</b></span>`,
      `<span class="chip-live">REHAT <b>${rest}</b></span>`,
    ].join("");
    $("#fl-skills").textContent = `hermes20 ${d.skills.hermes20} · hermes19 ${d.skills.hermes19}`;
    $("#fl-atc").textContent = d.atc.running ? "BERJALAN" : "tidak berjalan";
    $("#fl-mem").textContent = d.mem_mb.MemAvailable ? d.mem_mb.MemAvailable + " MB / " + d.mem_mb.MemTotal + " MB" : "–";
    $("#fl-disk").textContent = d.disk.free_gb ? d.disk.free_gb + " GB / " + d.disk.total_gb + " GB" : "–";
  } catch (e) {
    $("#fl-meta").textContent = "gagal: " + e.message;
  }
}

/* ---------------- dashboard 9119 dalam PUSAT ---------------- */
async function loadPusatWeb() {
  try {
    const d = await api("/api/web");
    $("#pw-url").textContent = d.url || "(tunnel belum siap)";
    $("#pw-meta").textContent = d.url_updated ? "dikemas kini " + d.url_updated : "";
    $("#pw-lan").textContent = d.lan ? "http://" + d.lan + ":9119/" : "tiada WiFi";
    $("#pw-user").textContent = d.user || "–";
    $("#pw-port").textContent = d.port_open ? "BUKA" : "MATI";
    $("#pw-svc").textContent = (d.services || []).map((s) => `${s.label || s.name}: ${s.state}`).join(" · ") || "–";
    $("#pw-secret").textContent = d.secret_file;
  } catch (e) {
    $("#pw-meta").textContent = "gagal: " + e.message;
  }
}

function initPusatWeb() {
  const o = $("#pw-open");
  if (o) o.addEventListener("click", () => {
    const u = ($("#pw-url").textContent || "").trim();
    if (u.startsWith("http")) window.open(u, "_blank", "noopener");
    else $("#pw-msg").textContent = "URL belum ada";
  });
  const c = $("#pw-copy");
  if (c) c.addEventListener("click", async () => {
    const u = ($("#pw-url").textContent || "").trim();
    try { await navigator.clipboard.writeText(u); $("#pw-msg").textContent = "disalin ✓"; }
    catch (_) { $("#pw-msg").textContent = "salin manual: " + u; }
  });
  loadPusatWeb();
  loadFleet();
  loadWork();
  setInterval(() => { loadPusatWeb(); loadFleet(); loadWork(); }, 60000);
}

/* ---------------- SKILL ---------------- */
let SK_CACHE = null;

function renderSkills(q) {
  if (!SK_CACHE) return;
  q = (q || "").toLowerCase();
  const rows = SK_CACHE.filter((s) =>
    !q || s.name.toLowerCase().includes(q) || (s.category || "").toLowerCase().includes(q) ||
    (s.desc || "").toLowerCase().includes(q));
  $("#sk-count").textContent = rows.length + " / " + SK_CACHE.length;
  $("#sk-list").innerHTML = rows.slice(0, 300).map((s) => `
    <div class="svc-row"><div class="svc-main">
      <b>${esc(s.name)}</b> <span class="tag">${esc(s.category || "—")}</span>
      <div class="hint">${esc(s.desc || "(tiada keterangan)")}</div>
    </div>
    <div class="svc-act"><button class="btn" data-skill="${esc(s.path)}">BUKA FAIL</button></div></div>`
  ).join("") || '<div class="empty">tiada padanan</div>';
  $$("[data-skill]").forEach((b) => b.addEventListener("click", () => bukaSkill(b.dataset.skill)));
}

async function bukaSkill(path) {
  const ov = document.getElementById("fileov");
  const body = document.getElementById("fileov-body");
  if (!ov) return;
  ov.style.display = "block";
  document.getElementById("fileov-name").textContent = path.split("/").slice(-2).join("/");
  body.textContent = "memuat…";
  try {
    const r = await api("/api/skill?path=" + encodeURIComponent(path));
    body.textContent = r.text || "(kosong)";
  } catch (e) {
    body.textContent = "gagal: " + e.message;
  }
}

async function loadSkills() {
  try {
    if (!SK_CACHE) {
      const d = await api("/api/skills");
      SK_CACHE = d.skills || [];
      $("#sk-meta").textContent = d.count + " skill";
    }
    renderSkills($("#sk-cari").value);
  } catch (e) {
    $("#sk-list").innerHTML = '<div class="empty">gagal: ' + esc(e.message) + "</div>";
  }
}

/* ---------------- TINDAKAN RUN ---------------- */
async function runAct(id, action) {
  if (action === "delete" && !confirm("Padam run " + id + "? (dipindah ke run-trash)")) return;
  try {
    const r = await api("/api/run/" + encodeURIComponent(id) + "/" + action, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: "{}", timeout: 120000,
    });
    $("#ws-meta").textContent = action + " ✓ " + id;
    await loadWork();
  } catch (e) {
    $("#ws-meta").textContent = "gagal " + action + ": " + e.message;
  }
}

/* ---------------- WATAK ---------------- */
let WT_CACHE = null;

function renderWatak(q) {
  if (!WT_CACHE) return;
  q = (q || "").toLowerCase();
  const rows = WT_CACHE.filter((a) =>
    !q || (a.name || "").toLowerCase().includes(q) || (a.slug || "").toLowerCase().includes(q) ||
    (a.division || "").toLowerCase().includes(q));
  $("#wt-count").textContent = rows.length + " / " + WT_CACHE.length;
  $("#wt-list").innerHTML = rows.slice(0, 300).map((a) => `
    <div class="svc-row"><div class="svc-main">
      <b>${esc((a.emoji || "") + " " + (a.name || a.slug))}</b>
      ${a.ketua ? '<span class="tag warn">KETUA</span>' : ""}
      <span class="tag ${a.active ? "ok" : ""}">${a.active ? "BEKERJA" : "REHAT"}</span>
      <span class="tag">${esc(a.division || "—")}${a.tier ? " · " + esc(a.tier) : ""}</span>
      <div class="hint mono">${esc(a.slug)}</div>
      <div class="workbar" style="margin-top:8px;gap:6px;flex-wrap:wrap">
        <button class="btn" data-wt-edit="${esc(a.slug)}">EDIT</button>
        <button class="btn" data-wt-ketua="${esc(a.slug)}">${a.ketua ? "BUKAN KETUA" : "JADIKAN KETUA"}</button>
        <button class="btn" data-wt-del="${esc(a.slug)}">PADAM</button>
      </div>
    </div></div>`).join("") || '<div class="empty">tiada padanan</div>';
}

/* --- borang tambah / edit watak --- */
let WT_EDIT = null;

function wtFormBuka(slug) {
  const f = $("#wt-form");
  WT_EDIT = slug || null;
  $("#wt-form-title").textContent = slug ? "EDIT WATAK · " + slug : "TAMBAH WATAK BAHARU";
  $("#wt-form-msg").textContent = "";
  if (slug) {
    const a = (WT_CACHE || []).find((x) => x.slug === slug) || {};
    $("#wtf-name").value = a.name || "";
    $("#wtf-emoji").value = a.emoji || "";
    $("#wtf-division").value = a.division || "";
    $("#wtf-tier").value = a.tier || "";
    $("#wtf-vibe").value = a.vibe || "";
    $("#wtf-desc").value = a.desc || "";
    $("#wtf-body").value = "";
    $("#wtf-ketua").checked = !!a.ketua;
  } else {
    ["wtf-name","wtf-emoji","wtf-division","wtf-tier","wtf-vibe","wtf-desc","wtf-body"].forEach((id) => { $("#" + id).value = ""; });
    $("#wtf-ketua").checked = false;
  }
  f.style.display = "block";
  f.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function wtSimpan() {
  const msg = $("#wt-form-msg");
  const name = ($("#wtf-name").value || "").trim();
  if (name.length < 2) { msg.textContent = "nama watak wajib (min 2 aksara)"; return; }
  const body = {
    name, emoji: $("#wtf-emoji").value.trim(), division: $("#wtf-division").value.trim(),
    tier: $("#wtf-tier").value.trim().toUpperCase(), vibe: $("#wtf-vibe").value.trim(),
    description: $("#wtf-desc").value.trim(), body: $("#wtf-body").value.trim(),
    ketua: $("#wtf-ketua").checked,
  };
  msg.textContent = "menyimpan…";
  try {
    const r = WT_EDIT
      ? await api("/api/watak/" + encodeURIComponent(WT_EDIT), { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      : await api("/api/watak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    msg.textContent = "tersimpan ✓ (" + (r.count || "?") + " watak)";
    WT_CACHE = null;
    $("#wt-form").style.display = "none";
    await loadWatak();
  } catch (e) {
    msg.textContent = "gagal: " + e.message;
  }
}

async function wtPadam(slug) {
  if (!confirm("Padam watak '" + slug + "'? (sandaran automatik dibuat)")) return;
  try {
    await api("/api/watak/" + encodeURIComponent(slug), { method: "DELETE" });
    WT_CACHE = null;
    await loadWatak();
  } catch (e) { alert("gagal padam: " + e.message); }
}

async function wtKetua(slug, jadi) {
  try {
    await api("/api/watak/" + encodeURIComponent(slug), { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ketua: jadi }) });
    WT_CACHE = null;
    await loadWatak();
  } catch (e) { alert("gagal: " + e.message); }
}

async function loadWatak() {
  try {
    if (!WT_CACHE) {
      const d = await api("/api/watak");
      WT_CACHE = d.agents || [];
      $("#wt-meta").textContent = d.count + " ejen dalam katalog";
    }
    renderWatak($("#wt-cari").value);
  } catch (e) {
    $("#wt-list").innerHTML = '<div class="empty">gagal: ' + esc(e.message) + "</div>";
  }
}

/* ---------------- TAMBAH KERJA ---------------- */
async function hantarKerja() {
  const instr = ($("#tk-instr").value || "").trim();
  const msg = $("#tk-msg");
  if (instr.length < 12) { msg.textContent = "arahan terlalu pendek (min 12 aksara)"; return; }
  msg.textContent = "menghantar…";
  const btn = $("#tk-hantar");
  btn.disabled = true;
  try {
    const r = await api("/api/task", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction: instr, max_agents: Number($("#tk-max").value || 3), start: true }),
      timeout: 180000,
    });
    msg.textContent = "lulus ✓ run " + (r.id || "") + " (" + ((r.plan && r.plan.ejen) || []).length + " ejen)";
    $("#tk-instr").value = "";
    if (typeof loadWork === "function") loadWork();
  } catch (e) {
    msg.textContent = "gagal: " + e.message;
  } finally {
    btn.disabled = false;
  }
}

/* ---------------- CRON TINDAKAN ---------------- */
async function cronAct(id, action) {
  try {
    const r = await api("/api/cron/" + encodeURIComponent(id), {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }), timeout: 100000,
    });
    $("#cr-meta").textContent = (r.ok ? "berjaya: " : "gagal: ") + action + " · " + id;
    await loadCron();
  } catch (e) {
    $("#cr-meta").textContent = "gagal: " + e.message;
  }
}

/* ---------------- CRON ---------------- */
async function loadCron() {
  try {
    const d = await api("/api/cron");
    $("#cr-meta").textContent = d.count + " kerja berjadual";
    $("#cr-list").innerHTML = d.jobs.map((j) => `
      <div class="svc-row"><div class="svc-main">
        <b>${esc(j.name || j.id)}</b>
        <span class="tag ${j.enabled ? "ok" : "bad"}">${j.enabled ? "AKTIF" : "MATI"}</span>
        <div class="hint mono">${esc(j.schedule)} · ${esc(j.script || "—")} · terakhir ${esc(j.last || "—")} · ${esc(j.status || "")}</div>
      </div>
      <div class="svc-act">
        <button class="btn" data-cron="${esc(j.id)}" data-act="run">JALAN</button>
        <button class="btn" data-cron="${esc(j.id)}" data-act="${j.enabled ? "pause" : "resume"}">${j.enabled ? "MATIKAN" : "HIDUPKAN"}</button>
      </div></div>`).join("") || '<div class="empty">tiada kerja</div>';
    $$("[data-cron]").forEach((b) =>
      b.addEventListener("click", () => cronAct(b.dataset.cron, b.dataset.act)));
  } catch (e) {
    $("#cr-list").innerHTML = '<div class="empty">gagal: ' + esc(e.message) + "</div>";
  }
}

/* ---------------- EMAIL ---------------- */
async function loadEmail() {
  try {
    const d = await api("/api/email");
    $("#em-meta").textContent = "dikemas kini " + d.updated;
    $("#em-inbox").textContent = d.inbox;
    $("#em-chips").innerHTML = Object.entries(d.counts || {}).map(([k, v]) =>
      `<span class="chip-live">${esc(k)} <b>${v}</b></span>`).join("");
    $("#em-log").textContent = (d.log || []).join("\n") || "(log kosong)";
  } catch (e) {
    $("#em-log").textContent = "gagal: " + e.message;
  }
}

/* ---------------- MCP ---------------- */
async function loadMcp() {
  try {
    const d = await api("/api/mcp");
    $("#mcp-meta").textContent = d.count + " pelayan · " + d.config;
    $("#mcp-list").innerHTML = (d.servers || []).map((s) => `
      <div class="svc-row">
        <div class="svc-main">
          <b>⚡ ${esc(s.name)}</b>
          <span class="tag ${s.enabled ? "ok" : "bad"}">${s.enabled ? "AKTIF" : "MATI"}</span>
          <span class="abadge">${esc(s.type)}</span>
          <div class="hint mono">${esc(s.url || (s.command + " " + (s.args || []).join(" ")))}</div>
        </div>
        <div class="acts" style="display:flex;gap:6px;flex-wrap:wrap">
          <button class="btn" data-mcp-test="${esc(s.name)}">UJI</button>
          <button class="btn" data-mcp-del="${esc(s.name)}">PADAM</button>
        </div>
      </div>`).join("") || '<div class="empty">Belum ada pelayan MCP. Tambah di atas.</div>';
    $$("#mcp-list button[data-mcp-test]").forEach((b) =>
      b.addEventListener("click", () => mcpTest(b.dataset.mcpTest)));
    $$("#mcp-list button[data-mcp-del]").forEach((b) =>
      b.addEventListener("click", () => mcpDel(b.dataset.mcpDel)));
  } catch (e) {
    $("#mcp-list").innerHTML = `<div class="empty">gagal: ${esc(e.message)}</div>`;
  }
}

async function mcpAdd() {
  const st = $("#mcp-status");
  const name = ($("#mcp-name").value || "").trim();
  const url = ($("#mcp-url").value || "").trim();
  const cmd = ($("#mcp-cmd").value || "").trim();
  const args = ($("#mcp-args").value || "").trim();
  if (!name) return (st.textContent = "nama wajib diisi");
  if (!url && !cmd) return (st.textContent = "isi URL atau command");
  st.textContent = "menambah…";
  try {
    const r = await api("/api/mcp", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, url, command: cmd, args }) });
    st.textContent = r.ok ? "ditambah ✓" : "gagal: " + (r.out || "").slice(-200);
    if (r.ok) { $("#mcp-name").value = ""; $("#mcp-url").value = ""; $("#mcp-cmd").value = ""; $("#mcp-args").value = ""; }
    await loadMcp();
  } catch (e) { st.textContent = "gagal: " + e.message; }
}

async function mcpTest(name) {
  const st = $("#mcp-status");
  st.textContent = "uji " + name + "…";
  try {
    const r = await api(`/api/mcp/${encodeURIComponent(name)}/test`, { method: "POST" });
    st.textContent = (r.ok ? "✓ " : "✗ ") + (r.out || "").slice(-260);
  } catch (e) { st.textContent = "gagal: " + e.message; }
}

async function mcpDel(name) {
  if (!confirm("Padam MCP " + name + "?")) return;
  const st = $("#mcp-status");
  st.textContent = "memadam…";
  try {
    const r = await api(`/api/mcp/${encodeURIComponent(name)}`, { method: "DELETE" });
    st.textContent = r.ok ? "dipadam ✓" : "gagal: " + (r.out || "").slice(-200);
    await loadMcp();
  } catch (e) { st.textContent = "gagal: " + e.message; }
}

/* ---------------- SATU PUSAT: sidebar + hud ---------------- */
async function loadHud() {
  try {
    const d = await api("/api/fleet");
    const [g1, g2] = d.gateways || [];
    const set = (id, txt, good) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.textContent = txt;
      const pill = el.closest(".pill");
      if (pill) pill.className = "pill " + (good ? "ok" : "bad");
    };
    if (g1) set("hud-gw1", g1.alive ? "HIDUP" : "MATI", g1.alive);
    if (g2) set("hud-gw2", g2.alive ? "HIDUP" : "MATI", g2.alive);
    const sk = document.getElementById("hud-sk");
    if (sk) sk.textContent = String(d.skills?.hermes20 ?? "–");
    const mem = document.getElementById("hud-mem");
    if (mem) mem.textContent = (d.mem_mb?.MemAvailable ?? "–") + " MB";
    const s = document.getElementById("side-svc");
    if (s) s.innerHTML = "skill " + (d.skills?.hermes20 ?? 0) + " · RAM bebas " + (d.mem_mb?.MemAvailable ?? 0) + " MB<br>" + (d.disk?.free_gb ?? "–") + " GB cakera";
  } catch (_) {}
}

function initSide() {
  document.querySelectorAll("#side button[data-go]").forEach((b) => {
    b.addEventListener("click", () => {
      document.querySelectorAll("#side button[data-go]").forEach((x) => x.classList.remove("on"));
      b.classList.add("on");
      if (typeof setTab === "function") setTab(b.dataset.go);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
  const THEMES = ["light","cream","blue","grey","mint","dark"];
  function applyTheme(name) {
    THEMES.forEach((x) => document.body.classList.remove("theme-" + x));
    document.body.classList.remove("light");
    if (name === "light" || name === "cream" || name === "blue" || name === "grey" || name === "mint") {
      document.body.classList.add("light");
    }
    if (name !== "light") document.body.classList.add("theme-" + name);
    try { localStorage.setItem("console_theme_v3", name); } catch (_) {}
  }
  const t = document.getElementById("hud-theme");
  if (t) {
    t.addEventListener("change", () => applyTheme(t.value));
    try {
      const saved = localStorage.getItem("console_theme_v3") || "light";
      t.value = saved;
      applyTheme(saved);
    } catch (_) { applyTheme("light"); }
  } else {
    try { applyTheme(localStorage.getItem("console_theme_v3") || "light"); } catch (_) { applyTheme("light"); }
  }
  loadHud();
  setInterval(loadHud, 30000);
  const sc = document.getElementById("sk-cari");
  if (sc) sc.addEventListener("input", () => renderSkills(sc.value));
  const wc = document.getElementById("wt-cari");
  if (wc) wc.addEventListener("input", () => renderWatak(wc.value));
  const wtAdd = document.getElementById("wt-tambah");
  if (wtAdd) wtAdd.addEventListener("click", () => wtFormBuka(null));
  const wtBatal = document.getElementById("wt-batal");
  if (wtBatal) wtBatal.addEventListener("click", () => { document.getElementById("wt-form").style.display = "none"; });
  const wtSim = document.getElementById("wt-simpan");
  if (wtSim) wtSim.addEventListener("click", wtSimpan);
  const wtList = document.getElementById("wt-list");
  if (wtList) wtList.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.wtEdit) wtFormBuka(b.dataset.wtEdit);
    else if (b.dataset.wtDel) wtPadam(b.dataset.wtDel);
    else if (b.dataset.wtKetua) {
      const a = (WT_CACHE || []).find((x) => x.slug === b.dataset.wtKetua);
      wtKetua(b.dataset.wtKetua, !(a && a.ketua));
    }
  });
  const tk = document.getElementById("tk-hantar");
  if (tk) tk.addEventListener("click", hantarKerja);
  const fc = document.getElementById("fileov-close");
  if (fc) fc.addEventListener("click", () => { document.getElementById("fileov").style.display = "none"; });
  const fo = document.getElementById("fileov");
  if (fo) fo.addEventListener("click", (e) => { if (e.target === fo) fo.style.display = "none"; });
}

/* ---------------- pusat pemantau ---------------- */
const OCS = { W: 1400, slot: 170, sysH: 54, divH: 54, divGap: 66 };

function esc3(s) { return esc(String(s ?? "")); }
function trunc(s, n) { s = String(s ?? ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; }

async function loadPusat() {
  try {
    const [chart, st] = await Promise.all([api("/api/orgchart"), api("/api/live/state")]);
    S.pusat.chart = chart;
    S.pusat.sig = (chart.active_agents || []).join(",");
    S.pusat.live = st;
    renderChart(chart);
    applyLive(st, true);
    renderMap(st.runs || []);
    loadHistory();
    loadInbox();
    loadReport();
    if (!S.pusat.webInit) { S.pusat.webInit = 1; initPusatWeb(); }
    startLive();
  } catch (e) {
    $("#oc-meta").textContent = "gagal: " + e.message;
  }
}

let OC_GEO = { systems: {}, divs: {}, H: 620 };

function renderChart(d) {
  const W = OCS.W;
  const systems = d.systems || [];
  const maxDiv = Math.max(1, ...systems.map((s) => s.divisions.length));
  const running = collectRunning();
  const bandH = running.length ? 86 : 0;
  const baseH = 186 + maxDiv * OCS.divGap + 10;
  const H = baseH + bandH;
  const svg = $(`#oc`);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const rootX = W / 2;
  const sysY = 96;
  const divY0 = 190;
  let out = [];
  OC_GEO = { systems: {}, divs: {}, H, W };

  // pautan root -> sistem
  systems.forEach((s, i) => {
    const cx = 20 + OCS.slot * i + OCS.slot / 2;
    out.push(`<path d="M${rootX} 66 V78 H${cx} V${sysY}" fill="none" style="stroke:var(--oc-link)" stroke-width="1.2"/>`);
  });

  // pautan sistem -> divisi
  systems.forEach((s, i) => {
    const cx = 20 + OCS.slot * i + OCS.slot / 2;
    if (!s.divisions.length) return;
    const yLast = divY0 + (s.divisions.length - 1) * OCS.divGap;
    out.push(`<path d="M${cx} ${sysY + OCS.sysH} V${yLast}" fill="none" style="stroke:var(--oc-link2)" stroke-width="1.2"/>`);
    s.divisions.forEach((v, j) => {
      const y = divY0 + j * OCS.divGap;
      out.push(`<path d="M${cx} ${y} H${cx}" style="stroke:var(--oc-link2)"/>`);
    });
  });

  // root
  out.push(`<g class="oc-node">
    <rect x="${rootX - 120}" y="18" width="240" height="48" rx="10" style="fill:var(--oc-root);stroke:var(--oc-root-stroke)" stroke-opacity=".55"/>
    <text x="${rootX}" y="40" text-anchor="middle" font-size="14" font-weight="700" style="fill:var(--oc-root-stroke)" letter-spacing="2">KETUA</text>
    <text x="${rootX}" y="56" text-anchor="middle" font-size="9" style="fill:var(--oc-dim)">Agent Factory · ${esc3(trunc((d.ketua || {}).model || "", 32))}</text>
  </g>`);

  // sistem
  systems.forEach((s, i) => {
    const cx = 20 + OCS.slot * i + OCS.slot / 2;
    const active = s.active > 0;
    out.push(`<g class="oc-node">
      <rect x="${cx - 79}" y="${sysY}" width="158" height="${OCS.sysH}" rx="8"
        style="fill:${active ? "var(--oc-node-active)" : "var(--oc-node)"};stroke:${active ? "var(--oc-accent)" : "var(--oc-link)"}" stroke-opacity="${active ? ".85" : "1"}"/>
      <text x="${cx}" y="${sysY + 20}" text-anchor="middle" font-size="10.5" font-weight="700" style="fill:${active ? "var(--oc-accent)" : "var(--oc-text)"}">${esc3(trunc(s.key, 19))}</text>
      <text x="${cx}" y="${sysY + 36}" text-anchor="middle" font-size="9" style="fill:var(--oc-dim)">${esc3(trunc(s.role || "", 26))}</text>
      <text x="${cx}" y="${sysY + 48}" text-anchor="middle" font-size="8.5" style="fill:var(--oc-dim2)">${s.count} ejen · ${s.divisions.length} divisi</text>
    </g>`);
    OC_GEO.systems[s.key] = { cx, y: sysY, w: 158, h: OCS.sysH };
  });

  // sistem tanpa divisi
  systems.forEach((s, i) => {
    if (s.divisions.length) return;
    const cx = 20 + OCS.slot * i + OCS.slot / 2;
    out.push(`<g class="oc-node">
      <rect x="${cx - 75}" y="${divY0}" width="150" height="40" rx="7" fill="none"
        style="stroke:var(--oc-link)" stroke-dasharray="4 4"/>
      <text x="${cx}" y="${divY0 + 25}" text-anchor="middle" font-size="9" style="fill:var(--oc-dim2)">modul memori · tiada divisi</text>
    </g>`);
  });

  // divisi
  systems.forEach((s, i) => {
    const cx = 20 + OCS.slot * i + OCS.slot / 2;
    s.divisions.forEach((v, j) => {
      const y = divY0 + j * OCS.divGap;
      const active = (v.active || []).length > 0;
      const col = v.color || "#5ee3a1";
      OC_GEO.divs[v.key] = { cx, y, w: 150, h: OCS.divH };
      out.push(`<g class="oc-div" data-div="${esc3(v.key)}" data-agents='${esc3(JSON.stringify(v.active || []))}'>
        ${active ? `<rect class="oc-pulse" x="${cx - 75}" y="${y}" width="150" height="${OCS.divH}" rx="7" fill="none" stroke="${col}" stroke-width="1.5"/>` : ""}
        <rect x="${cx - 75}" y="${y}" width="150" height="${OCS.divH}" rx="7"
          style="fill:${active ? "var(--oc-div-active)" : "var(--oc-div)"}" stroke="${col}" stroke-opacity="${active ? ".95" : ".35"}"
          stroke-width="${active ? "1.6" : "1"}"/>
        <text x="${cx}" y="${y + 20}" text-anchor="middle" font-size="10" font-weight="600" style="fill:var(--oc-text)">${esc3(trunc(v.label, 17))}</text>
        <text x="${cx}" y="${y + 35}" text-anchor="middle" font-size="8.5" style="fill:var(--oc-dim)">${v.count} ejen${v.used ? ` · ${v.used} dipakai` : ""}</text>
        ${active ? `<circle cx="${cx + 62}" cy="${y + 11}" r="7.5" fill="${col}" fill-opacity=".18" stroke="${col}"/>
          <text x="${cx + 62}" y="${y + 14.5}" text-anchor="middle" font-size="8.5" font-weight="700" fill="${col}">${v.active.length}</text>` : ""}
      </g>`);
    });
  });

  // jalur EJEN AKTIF di bawah carta (kad terapung + sambungan)
  if (running.length) {
    out.push(`<line x1="20" y1="${baseH - 2}" x2="${W - 20}" y2="${baseH - 2}" style="stroke:var(--oc-link2)"/>`);
    out.push(`<text x="24" y="${baseH + 16}" font-size="9" style="fill:var(--oc-dim2)" letter-spacing="2">EJEN AKTIF · ${running.length}</text>`);
    out = out.concat(floatCards(running, baseH, H, W));
  }
  svg.innerHTML = out.join("");
  $("#oc-meta").textContent =
    `${d.totals.systems} sistem · ${d.totals.divisions} divisi · ${d.totals.agents} ejen` +
    (d.totals.active ? ` · ${d.totals.active} AKTIF` : "");
  $$("#oc .oc-float").forEach((g) =>
    g.addEventListener("click", () => openAgentDrawer(g.dataset.slug))
  );
  $$("#oc .oc-div").forEach((g) =>
    g.addEventListener("click", () => {
      S.ag.div = g.dataset.div || "";
      S.ag.sel = null;
      setTab("agency");
    })
  );
}


function collectRunning() {
  const st = S.pusat.live;
  const out = [];
  if (!st || !st.runs) return out;
  st.runs.forEach((r) => (r.agents || []).forEach((a) => { if (a.state === "running") out.push(a); }));
  return out;
}

function floatCards(running, bandTop, H, W) {
  const parts = [];
  const cw = 248, ch = 56, gap = 10;
  const perRow = Math.max(1, Math.floor((W - 40 + gap) / (cw + gap)));
  running.forEach((a, i) => {
    const g = (OC_GEO.divs || {})[a.division];
    const row = Math.floor(i / perRow), col = i % perRow;
    const x = 20 + col * (cw + gap);
    const y = bandTop + 26 + row * (ch + 10);
    const col2 = "#f0b429";
    const el = a.elapsed_s != null ? `${Math.round(a.elapsed_s)}s` : "";
    const cost = a.cost != null ? `$${Number(a.cost).toFixed(4)}` : "kos selepas siap";
    if (g) {
      parts.push(`<path d="M${g.cx} ${g.y + 54} V${bandTop + 2} H${x + cw / 2} V${y}" fill="none"
        stroke="${col2}" stroke-opacity=".3" stroke-dasharray="3 4"/>`);
    }
    parts.push(`<g class="oc-float" data-slug="${esc3(a.slug)}">
      <rect x="${x}" y="${y}" width="${cw}" height="${ch}" rx="9" style="fill:var(--oc-float);stroke:${col2}" stroke-opacity=".85"/>
      <rect x="${x}" y="${y}" width="4" height="${ch}" rx="2" fill="${col2}"/>
      <text x="${x + 14}" y="${y + 21}" font-size="10.5" font-weight="700" style="fill:var(--oc-float-text)">${esc3(trunc(a.nama || a.slug, 21))}</text>
      <text x="${x + 14}" y="${y + 36}" font-size="8.5" style="fill:var(--oc-float-dim)">${esc3(trunc(a.location || a.slug, 34))}</text>
      <text x="${x + 14}" y="${y + 49}" font-size="8" fill="${col2}">● running · ${el} · ${cost}</text>
      <circle cx="${x + cw - 14}" cy="${y + 14}" r="4" fill="${col2}"><animate attributeName="opacity" values="1;.2;1" dur="1.5s" repeatCount="indefinite"/></circle>
    </g>`);
  });
  return parts;
}

function applyLive(st, initial) {
  S.pusat.live = st;
  const s = st.stats || {};
  const gw = st.gateway || {};
  const g = st.guard || {};
  const runs = st.runs || [];
  const active = st.active_agents || [];

  $("#hl-chips").innerHTML = [
    `<span class="chip-live ${gw.pid_alive === false ? "bad" : ""}">GATEWAY <b>${gw.pid_alive === true ? "HIDUP" : gw.pid_alive === false ? "MATI" : "TIADA"}</b></span>`,
    `<span class="chip-live">SESI AKTIF <b>${num(s.active_sessions)}</b></span>`,
    `<span class="chip-live">RUN <b>${runs.length}</b></span>`,
    `<span class="chip-live ${active.length ? "warn" : ""}">EJEN JALAN <b>${active.length}</b></span>`,
    `<span class="chip-live">TOOL HARI INI <b>${num(s.tools_today)}</b></span>`,
    `<span class="chip-live">TOKEN <b>${num(s.tokens_today)}</b></span>`,
    `<span class="chip-live warn">KOS <b>$${Number(s.cost_today || 0).toFixed(2)}</b></span>`,
    `<span class="chip-live">GUARD <b>${g.active && g.active.length ? "1 RUN" : g.starts_10min + "/" + g.max_runs_10min}</b></span>`,
  ].join("");

  // sedang jalan
  if (!runs.length) {
    $("#lv-runs").textContent = "tiada";
    $("#lv-active").innerHTML = `<div class="empty">Tiada run aktif. Mulakan di tab AGENCY → DEWAN ARAHAN.</div>`;
  } else {
    $("#lv-runs").textContent = `${runs.length} aktif`;
    $("#lv-active").innerHTML = runs
      .map((r) => {
        const pct = Math.round((r.finished / Math.max(1, r.total)) * 100);
        const rows = (r.agents || [])
          .map(
            (a) => `<div class="lv-ag ${a.state}"><span class="st"></span>
              <span class="nm">${esc3(a.nama || a.slug)}</span>
              <span class="dp">${esc3(a.state)}${(a.depends_on || []).length ? " · ↳" + esc3(a.depends_on.join(",")) : ""}</span></div>`
          )
          .join("");
        return `<div class="lv-run">
          <div class="meta"><span class="tag ${r.status === "synthesizing" ? "warn" : "ok"}">${esc3(r.status)}</span>
            <span>gelombang ${r.wave}/${r.wave_total}</span><span>${r.finished}/${r.total} ejen</span></div>
          <div class="t">${esc3(trunc(r.instruction, 130))}</div>
          <div class="minibar"><div class="track"><div class="fill" style="width:${pct}%"></div></div><span>${pct}%</span></div>
          ${rows}</div>`;
      })
      .join("");
  }

  renderMap(runs);

  // feed
  const feed = st.feed || [];
  $("#lv-feed").innerHTML =
    feed
      .map((f) => {
        const t = (f.ts || "").slice(11, 19);
        const tag = f.role === "tool" ? (f.tool || "tool").replace("agency_agents_", "agency:") : f.role;
        return `<div class="feed-item ${esc3(f.role)}"><span class="ft">${esc3(t)}</span>
          <span class="fr">${esc3(trunc(tag, 10))}</span>
          <span class="fs">${esc3(f.text)}</span></div>`;
      })
      .join("") || `<div class="empty">Tiada aktiviti.</div>`;

  // spark
  const series = s.series_60m || [];
  const maxS = Math.max(1, ...series);
  $("#lv-spark").innerHTML = series
    .map((v) => `<i style="height:${Math.max(2, Math.round((v / maxS) * 100))}%" title="${v} tool"></i>`)
    .join("");
  $("#lv-tools").textContent = `${num(series.reduce((a, b) => a + b, 0))} tool / 60m`;

  // radar info
  $("#lv-now").textContent = (st.now || "").replace("T", " ").slice(11, 19);
  $("#lv-radar").innerHTML = `
    <div class="kv"><span class="k">Sesi hari ini</span><span class="v">${num(s.sessions_today)}</span></div>
    <div class="kv"><span class="k">Sesi aktif (5m)</span><span class="v">${num(s.active_sessions)}</span></div>
    <div class="kv"><span class="k">Tool hari ini</span><span class="v">${num(s.tools_today)}</span></div>
    <div class="kv"><span class="k">Token hari ini</span><span class="v">${num(s.tokens_today)}</span></div>
    <div class="kv"><span class="k">Kos hari ini</span><span class="v">$${Number(s.cost_today || 0).toFixed(3)}</span></div>`;

  // carta: render semula hanya bila set ejen aktif berubah
  const sig = active.join(",");
  if (!initial && sig !== S.pusat.sig) {
    S.pusat.sig = sig;
    loadChartOnly();
  }

  // toast bila run selesai
  runs.forEach((r) => {
    const prev = S.pusat.seen[r.id];
    if (prev && prev !== r.status && (r.status === "done" || r.status === "failed")) {
      toast(`Run ${r.id} · ${r.status}`, r.status === "done" ? "ok" : "bad");
    }
    S.pusat.seen[r.id] = r.status;
  });
}

async function loadChartOnly() {
  try {
    const d = await api("/api/orgchart");
    S.pusat.chart = d;
    renderChart(d);
  } catch (e) {
    /* senyap: carta lama kekal */
  }
}

function startLive() {
  if (S.pusat.es || typeof EventSource === "undefined") return;
  try {
    const es = new EventSource("/api/live/stream");
    es.onmessage = (e) => {
      try {
        applyLive(JSON.parse(e.data));
      } catch (_) {}
    };
    es.onerror = () => {
      es.close();
      S.pusat.es = null;
      setTimeout(startLive, 8000);
    };
    S.pusat.es = es;
  } catch (_) {}
}

function toast(msg, kind = "") {
  let box = $("#toasts");
  if (!box) {
    document.body.insertAdjacentHTML("beforeend", `<div id="toasts" class="toasts"></div>`);
    box = $("#toasts");
  }
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = msg;
  box.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}

/* ---------------- agency ---------------- */
async function loadAgency() {
  const qs = `?division=${encodeURIComponent(S.ag.div)}&q=${encodeURIComponent(S.ag.q)}`;
  const d = await api(`/api/agency${qs}`);
  S.ag.data = d;
  const t = d.totals;
  $("#ag-hero").innerHTML = `<h1>THE AGENCY · ${num(t.agents)} EJEN</h1>
    <p>Roster <span class="mono">msitarzewski/agency-agents</span> yang sedia ada dalam hermes20 —
    ${t.divisions} divisi · katalog ${esc(d.source.catalog)} · korpus ${esc(d.source.corpus)}.</p>
    <p>Dipadankan ke 8 sistem Ketua: divisi → peranan → skill tempatan. Hermes19 pula simpan
    ${esc(d.hermes19.agents)} ejen (tapisan trading sahaja).</p>`;
  $("#ag-cards").innerHTML = [
    card("ROSTER", num(t.agents), `${t.divisions} divisi`),
    card("DIPAKAI", num(t.used_agents), `${t.unused_agents} belum dipakai`, "warn"),
    card("PANGGILAN TOOL", num(t.uses), `${t.sessions} sesi terlibat`),
    card("DRIFT", num((d.drift.missing_source || 0) + (d.drift.reported.body_diff || 0)), "path + badan berbeza", "bad"),
  ].join("");

  const chips = d.divisions
    .map(
      (v) => `<div class="divchip ${S.ag.div === v.key ? "on" : ""}" data-div="${esc(v.key)}" title="${esc(v.role)}">
        <span class="sw" style="background:${esc(v.color)}"></span>
        <span>${esc(v.label)}</span><span class="ct">${v.count}</span>
        ${v.role ? `<span class="rl">· ${esc(v.role)}</span>` : ""}
        ${(v.skills || []).length ? `<span class="abadge">skill:${v.skills.length}</span>` : `<span class="abadge">tiada skill</span>`}
      </div>`
    )
    .join("");
  $("#ag-divs").innerHTML =
    `<div class="divchip ${S.ag.div === "" ? "on" : ""}" data-div=""><span class="sw" style="background:#5ee3a1"></span><span>Semua</span><span class="ct">${t.agents}</span></div>` +
    chips;
  $$("#ag-divs .divchip").forEach((c) =>
    c.addEventListener("click", () => {
      S.ag.div = c.dataset.div || "";
      S.ag.sel = null;
      loadAgency();
      openAgent(null);
    })
  );

  $("#ag-count").textContent = `${t.filtered} ejen${S.ag.div ? " · " + S.ag.div : ""}`;
  $("#ag-list").innerHTML =
    d.agents
      .map(
        (a) => `<div class="acard ${S.ag.sel === a.slug ? "sel" : ""}" data-slug="${esc(a.slug)}">
          <div class="top"><span class="em">${esc(a.emoji || "•")}</span><span class="nm">${esc(a.name)}</span></div>
          <div class="vb">${esc(a.vibe || a.description || "")}</div>
          <div class="meta"><span class="abadge">${esc(a.division)}</span>
          ${a.uses ? `<span class="abadge" style="color:#f0b429;border-color:#4a3a12">dipakai ${a.uses}×</span>` : ""}
          ${a.has_source ? "" : `<span class="abadge" style="color:#ff6b6b">sumber hilang</span>`}</div>
        </div>`
      )
      .join("") || `<div class="empty">Tiada ejen sepadan.</div>`;
  $$("#ag-list .acard").forEach((el) =>
    el.addEventListener("click", () => openAgent(el.dataset.slug))
  );

  const g = d.git || {};
  $("#ag-githint").textContent = g.commit || "";
  $("#ag-src").innerHTML = `
    <div class="kv"><span class="k">Repo</span><span class="v">${esc(g.repo || "–")}</span></div>
    <div class="kv"><span class="k">Remote</span><span class="v">${esc(g.remote || "–")}</span></div>
    <div class="kv"><span class="k">Commit</span><span class="v">${esc(g.commit || "–")} · ${esc((g.date || "").slice(0, 10))}</span></div>
    <div class="kv"><span class="k">Cawangan</span><span class="v">${esc(g.branch || "–")} · ${g.dirty_files ? g.dirty_files + " fail berubah" : "bersih"}</span></div>
    <div class="kv"><span class="k">Subjek</span><span class="v">${esc((g.subject || "–").slice(0, 70))}</span></div>
    <div class="kv"><span class="k">Diklon ke</span><span class="v">${esc((g.path || "").replace("/data/data/com.termux/files/home", "~"))}</span></div>
    <div class="hint" style="margin-top:8px">Pemasangan asal guna brew tap/cask <span class="mono">msitarzewski/agency-agents/agency-agents</span>
    — brew tiada pada Termux/Android, jadi repo yang sama diklon terus ke hermes20 dan
    dikemas kini dengan <span class="mono">git -C ~/.hermes20/agency-agents pull</span>, kemudian
    <span class="mono">sync_agency_catalog.py</span> untuk bina semula katalog router.</div>`;

  $("#ag-ideas").innerHTML =
    (d.ideas || [])
      .map(
        (x) => `<div class="msg ${x.kind === "bad" ? "user" : x.kind === "warn" ? "assistant" : "tool"}" style="margin-bottom:11px">
          <div class="mh"><b>${x.kind === "bad" ? "KRITIKAL" : x.kind === "warn" ? "PERHATIAN" : "NOTA"}</b></div>
          <div style="font-size:12.5px;font-weight:600;margin-bottom:3px">${esc(x.title)}</div>
          <div style="font-size:12px;color:var(--dim);line-height:1.5">${esc(x.detail)}</div>
        </div>`
      )
      .join("") || `<div class="empty">Tiada cadangan.</div>`;

  const pl = d.pilots || [];
  $("#ag-pilots").innerHTML = pl.length
    ? `<div class="hint" style="margin:12px 0 7px">JURUTERBANG DICADANGKAN · 1 PER DIVISI · klik untuk buka</div>
       <div class="divchips">` +
      pl.map(
        (p) => `<button class="chip" data-slug="${esc(p.slug)}" title="${esc(p.reason)}"
          style="cursor:pointer;font-size:11px;padding:4px 8px">${esc(p.emoji || "•")} ${esc(p.name || p.slug)}
          <span style="opacity:.55">· ${esc(p.label)}</span></button>`
      ).join("") +
      `</div>`
    : "";
  $$("#ag-pilots .chip").forEach((el) =>
    el.addEventListener("click", () => openAgent(el.dataset.slug))
  );

  const dr = d.drift;
  $("#ag-drift").innerHTML = `
    <div class="kv"><span class="k">Roster katalog</span><span class="v">${num(dr.roster)} ejen</span></div>
    <div class="kv"><span class="k">Fail .md dalam korpus</span><span class="v">${num(dr.md_files_on_disk)}</span></div>
    <div class="kv"><span class="k">Sumber hilang (path)</span><span class="v">${num(dr.missing_source)} ${dr.missing_sample && dr.missing_sample.length ? "· " + esc(dr.missing_sample.slice(0, 3).join(", ")) : ""}</span></div>
    <div class="kv"><span class="k">Hanya dalam app</span><span class="v">${num(dr.reported.only_app ?? "–")}</span></div>
    <div class="kv"><span class="k">Hanya dalam aktif</span><span class="v">${num(dr.reported.only_active ?? "–")}</span></div>
    <div class="kv"><span class="k">Badan berbeza</span><span class="v">${num(dr.reported.body_diff ?? "–")}</span></div>
    <div class="kv"><span class="k">Beza susun atur</span><span class="v">${num(dr.reported.layout ?? 0)} · subfolder vs rata</span></div>
    <div class="kv"><span class="k">Laporan drift</span><span class="v">${dr.report ? esc(dr.report.file) + " · " + dt(dr.report.at) : "tiada"}</span></div>
    <div class="hint" style="margin-top:8px">Angka di atas dikira <b>langsung</b> daripada katalog + korpus app
    (${dr.live ? "mod live" : "mod laporan"}). Fail laporan hanya rujukan; ia tidak lagi menentukan angka.
    Beza susun atur bukan kehilangan fail — badan prompt tetap sama.</div>`;

  $("#ag-usecount").textContent = `${d.events.length} peristiwa terakhir`;
  $("#ag-usage").innerHTML =
    `<div class="kv"><span class="k">Panggilan mengikut tool</span><span class="v">${Object.entries(d.calls).map(([k, v]) => `${k.replace("agency_agents_", "")}:${v}`).join(" · ") || "–"}</span></div>` +
    table(
      ["Masa", "Tool", "Rujukan", "Sesi"],
      d.events.slice(0, 12).map(
        (e) => `<tr><td class="n">${esc((e.ts || "").replace("T", " ").slice(5, 19))}</td>
        <td><span class="tag blue">${esc((e.tool || "").replace("agency_agents_", ""))}</span></td>
        <td class="t">${esc(e.ref || "–")}</td>
        <td class="mono" style="font-size:10px">${esc((e.session || "").slice(0, 18))}</td></tr>`
      )
    );

  if (S.ag.sel) openAgent(S.ag.sel);
  loadKetuaRoster(false);
  if (!S.da.loaded) {
    S.da.loaded = true;
    loadArch();
    loadRuns();
    loadGuard();
  }
}

async function openAgent(slug) {
  S.ag.sel = slug;
  $$("#ag-list .acard").forEach((el) => el.classList.toggle("sel", el.dataset.slug === slug));
  if (!slug) {
    $("#ag-detail").innerHTML = `<div class="pbody"><div class="empty">Pilih satu ejen di kiri.</div></div>`;
    return;
  }
  $("#ag-detail").innerHTML = `<div class="pbody"><div class="empty">memuat ${esc(slug)}…</div></div>`;
  const a = await api(`/api/agency/agent/${encodeURIComponent(slug)}`);
  $("#ag-detail").innerHTML = `
    <div class="ph"><h2>${esc(a.emoji || "")} ${esc(a.name)}</h2>
      <span class="hint">${esc(a.division_label)}</span></div>
    <div class="pbody" style="border-bottom:1px solid var(--line)">
      <div class="kv"><span class="k">Slug</span><span class="v">${esc(a.slug)}</span></div>
      <div class="kv"><span class="k">Vibe</span><span class="v">${esc(a.vibe || "–")}</span></div>
      <div class="kv"><span class="k">Peranan dalam orkestra</span><span class="v">${esc(a.role_in_org || "–")}</span></div>
      <div class="kv"><span class="k">Digunakan</span><span class="v">${a.uses}× ${a.sessions.length ? "· " + esc(a.sessions.join(", ")) : ""}</span></div>
      <div class="kv"><span class="k">Sumber</span><span class="v">${esc(a.source_path || "–")} ${a.has_source ? "✓" : "✗"}</span></div>
      <div style="margin-top:9px"><div class="hint" style="margin-bottom:4px">Cara guna</div>
        <div class="copybox">${esc(a.load_hint)}</div></div>
    </div>
    <div class="pbody"><div class="hint" style="margin-bottom:6px">Prompt badan</div>
      <div class="bodytext">${esc(a.body || "(kosong)")}</div></div>`;
  $("#ag-detail").scrollTop = 0;
}


/* ---------------- dewan arahan ---------------- */
function daStep(n) {
  $$("#da-flow .st").forEach((el) => el.classList.toggle("on", Number(el.dataset.step) <= n));
}
function daStatus(text, cls = "") {
  const el = $("#da-status");
  el.textContent = text;
  el.className = `statuspill ${cls}`;
}

async function daPlan() {
  const instr = $("#da-instr").value.trim();
  if (instr.length < 12) return daStatus("arahan terlalu pendek (min 12 aksara)", "bad");
  const max = Number($("#da-max").value) || 3;
  daStatus("KETUA SELIDIK 282 EJEN…", "run");
  daStep(3);
  $("#da-run").disabled = true;
  $("#da-meta").textContent = "";
  const t0 = performance.now();
  try {
    const run = await api("/api/agency/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ instruction: instr, max_agents: max, attachment_ids: (S.da.attach || []) }),
    });
    S.da.run = run;
    saveRunId(run.id);
    renderPlan(run);
    daStatus("PELAN SIAP", "ok");
    daStep(4);
    $("#da-meta").textContent = `${run.model} · ${Math.round(performance.now() - t0)}ms`;
    $("#da-run").disabled = false;
    loadRuns();
  } catch (e) {
    daStatus("GAGAL: " + e.message, "bad");
  }
}

function renderPlan(run) {
  const p = run.plan || {};
  const box = $("#da-planpanel");
  box.style.display = "";
  $("#da-planid").textContent = `${run.id} · ${run.model || ""}`;
  const li = (arr, cls = "") => (arr || []).map((x) => `<li>${esc(x)}</li>`).join("");
  const cards = (p.ejen || [])
    .map((e) => {
      const deps = e.depends_on || [];
      return `<div class="one"><div class="nm">${esc(e.emoji || "")} ${esc(e.nama || e.slug)}</div>
      <div class="dv">${esc(e.division || "")} · ${esc(e.slug)}</div>
      <div class="why">${esc(e.sebab || "")}</div>
      <div class="sc"><b>Skop:</b> ${esc(e.skop || "")}<br><b>Hasil:</b> ${esc(e.hasil_dijangka || "–")}</div>
      <div class="sc"><b>Selepas:</b> ${deps.length ? deps.map((d) => `<span class="tag ok">${esc(d)}</span>`).join(" ") : `<span class="hint">mula sendiri (gelombang 1)</span>`}</div>
      </div>`;
    })
    .join("");
  const warn = (run.warnings || []).length
    ? `<div class="planbox" style="border-color:rgba(255,107,107,.45);background:rgba(255,107,107,.06)">
        <b style="color:#ff6b6b">AMARAN KESELAMATAN</b> — arahan mengandungi: ${esc((run.warnings || []).join("; "))}.
        Ia dilayan sebagai data, bukan arahan sistem; ejen tidak diberi akses kunci atau shell.</div>`
    : "";
  $("#da-planbody").innerHTML = warn + `
    <div class="planbox"><b>Faham:</b> ${esc(p.faham || "–")}<br>
      <b>Jenis:</b> ${esc(p.jenis_tugasan || "–")} · <b>Sistem:</b> ${esc((p.sistem_terlibat || []).join(" → ") || "–")}
      ${(p.andaian || []).length ? `<br><b>Andaian:</b> ${esc((p.andaian || []).join("; "))}` : ""}</div>
    <div class="hint" style="margin-bottom:6px">EJEN DIPILIH (${(p.ejen || []).length})</div>
    <div class="agsel">${cards || `<div class="empty">Tiada ejen.</div>`}</div>
    <div class="grid2">
      <div><div class="hint" style="margin-bottom:5px">LANGKAH ORKESTRASI</div><ol class="laws">${li(p.langkah)}</ol></div>
      <div><div class="hint" style="margin-bottom:5px">RISIKO / GATE</div><ol class="laws">${li(p.risiko)}</ol></div>
    </div>
    ${p.format_hasil ? `<div class="planbox" style="margin-top:10px"><b>Penilaian hasil:</b> ${esc(p.format_hasil)}</div>` : ""}`;
}

async function daRun() {
  if (!S.da.run) return;
  const id = S.da.run.id;
  daStatus("MULA EKSEKUSI…", "run");
  daStep(5);
  $("#da-run").disabled = true;
  try {
    await api(`/api/agency/run/${encodeURIComponent(id)}`, { method: "POST" });
    pollRun(id);
  } catch (e) {
    daStatus("GAGAL MULA: " + e.message, "bad");
  }
}

function pollRun(id) {
  clearTimeout(S.da.timer);
  const tick = async () => {
    try {
      const run = await api(`/api/agency/run/${encodeURIComponent(id)}`);
      S.da.run = run;
      renderRun(run);
      if (run.status === "running") {
        const done = (run.outputs || []).length;
        const total = (run.plan.ejen || []).length;
        daStatus(`EKSEKUSI ${done}/${total}`, "run");
        daStep(5);
        S.da.timer = setTimeout(tick, 2500);
      } else if (run.status === "synthesizing") {
        daStatus("SINTESIS KETUA…", "run");
        daStep(7);
        S.da.timer = setTimeout(tick, 2500);
      } else if (run.status === "done") {
        daStatus("SELESAI", "ok");
        daStep(8);
        $("#da-run").disabled = false;
        loadRuns();
      } else {
        daStatus("GAGAL: " + (run.error || run.status), "bad");
        $("#da-run").disabled = false;
      }
    } catch (e) {
      daStatus("RALAT POLL: " + e.message, "bad");
    }
  };
  tick();
}

function renderRun(run) {
  const box = $("#da-resultpanel");
  box.style.display = "";
  const total = (run.plan.ejen || []).length;
  const outs = run.outputs || [];
  const wv = run.wave_total ? ` · gelombang ${run.wave || 1}/${run.wave_total}` : "";
  $("#da-resultmeta").textContent = `${run.id} · ${run.status}${wv} · ${outs.length}/${total} ejen`;
  const blocks = outs
    .map(
      (o) => {
        const ag = ((run.plan || {}).ejen || []).find((x) => x.slug === o.slug) || {};
        const dep = (ag.depends_on || []).length ? ` · selepas ${esc((ag.depends_on || []).join(", "))}` : "";
        return `<details class="outblock"><summary>
        <span class="tag ${o.status === "done" ? "ok" : "bad"}">${esc(o.status)}</span>
        <b>${esc(o.nama || o.slug)}</b>
        <span class="hint">${esc(o.slug)}${dep} · ${o.ms || 0}ms</span></summary>
      <div class="ob">${esc(o.text || "")}</div></details>`;
      }
    )
    .join("");
  const running = total - outs.length;
  const pending = running > 0
    ? `<div class="minibar"><span>menunggu ${running} ejen</span><div class="track"><div class="fill" style="width:${Math.round((outs.length / Math.max(1, total)) * 100)}%"></div></div></div>`
    : "";
  $("#da-resultbody").innerHTML =
    pending +
    (blocks || `<div class="empty">Belum ada output ejen.</div>`) +
    (run.final
      ? `<div class="ph" style="border-top:1px solid var(--line);border-bottom:none;padding-left:0"><h2>KEPUTUSAN KETUA</h2></div>
         <div class="bodytext" style="max-height:none">${esc(run.final)}</div>`
      : `<div class="hint" style="margin-top:8px">Sintesis Ketua akan muncul selepas semua ejen selesai.</div>`);
}

function saveRunId(id) {
  try { localStorage.setItem("da_run", id); } catch (e) {}
}

async function loadArch() {
  try {
    const a = await api("/api/agency/analysis");
    const t = a.totals || {};
    $("#an-meta").textContent = `${t.agents} persona · ~${t.words_mean} perkataan`;
    const bars = (a.archetypes || [])
      .map(([k, v]) => {
        const pct = Math.round((v / Math.max(1, t.agents)) * 100);
        return `<div class="minibar"><span style="width:88px">${esc(k)}</span><div class="track"><div class="fill" style="width:${pct}%"></div></div><span>${v}</span></div>`;
      })
      .join("");
    const styles = (a.styles || []).map(([k, v]) => `<span class="chip">${esc(k)}: ${v}</span>`).join("");
    const divs = (a.by_division || [])
      .map((d) => `<tr><td>${esc(d.division)}</td><td class="n">${d.agents}</td><td class="n">${d.words_mean}w</td><td class="n">${d.lengkap}</td></tr>`)
      .join("");
    $("#an-body").innerHTML = `
      ${bars}
      <div class="chips" style="margin:9px 0">${styles}</div>
      <div class="hint" style="margin-bottom:5px">PER DIVISI (purata perkataan · archetype lengkap)</div>
      <div class="scrollx" style="max-height:260px;overflow:auto"><table class="tbl">
        <thead><tr><th>Divisi</th><th>Ejen</th><th>Panjang</th><th>Lengkap</th></tr></thead><tbody>${divs}</tbody></table></div>
      <div class="hint" style="margin-top:8px">Dijana ${esc((a.generated_at || "").replace("T", " ").slice(0, 19))} · ${esc(a.source || "")}</div>`;
  } catch (e) {
    $("#an-body").innerHTML = `<div class="empty">Analisis belum dijana: ${esc(e.message)}</div>`;
  }
}

async function loadGuard() {
  try {
    const g = await api("/api/agency/guard");
    $("#da-guard").textContent =
      `Keselamatan: token sesi aktif · ${g.active.length ? "1 run sedang jalan" : "tiada run aktif"} · ` +
      `${g.starts_10min}/${g.max_runs_10min} run dalam 10 minit · output disunting (kunci/rahsia)`;
  } catch (e) {
    $("#da-guard").textContent = "status keselamatan tidak tersedia: " + e.message;
  }
}

async function loadRuns() {
  try {
    const d = await api("/api/agency/runs");
    $("#da-rundir").textContent = d.dir;
    $("#da-runs").innerHTML = d.runs.length
      ? d.runs
          .map(
            (r) => `<div class="runitem" data-run="${esc(r.id)}">
              <span class="tag ${r.status === "done" ? "ok" : r.status === "failed" ? "bad" : "warn"}">${esc(r.status)}</span>
              <b class="mono">${esc(r.id)}</b>
              <span class="hint">${esc((r.agents || []).join(", "))}</span>
              <span class="t" style="flex:1;color:var(--dim)">${esc(r.instruction)}</span></div>`
          )
          .join("")
      : `<div class="empty">Belum ada run. Taip arahan di atas.</div>`;
    $$("#da-runs .runitem").forEach((el) =>
      el.addEventListener("click", async () => {
        const run = await api(`/api/agency/run/${encodeURIComponent(el.dataset.run)}`);
        S.da.run = run;
        $("#da-instr").value = run.instruction || "";
        renderPlan(run);
        renderRun(run);
        daStep(run.status === "done" ? 8 : run.status === "planned" ? 4 : 5);
        daStatus(run.status.toUpperCase(), run.status === "done" ? "ok" : run.status === "failed" ? "bad" : "run");
        $("#da-run").disabled = !(run.status === "planned" || run.status === "failed");
        if (run.status === "running" || run.status === "synthesizing") pollRun(run.id);
      })
    );
  } catch (e) {
    $("#da-runs").innerHTML = `<div class="empty">${esc(e.message)}</div>`;
  }
}

/* ---------------- trading ---------------- */
function renderPaperLive(pl) {
  const box = $("#tr-pl-strip");
  if (!box) return;
  const alive = !!pl.alive;
  const pid = (pl.procs || [])[0] || {};
  box.innerHTML = `
    <span class="tag ${alive ? "ok" : "bad"}">${alive ? "HIDUP" : "MATI"}</span>
    <span class="hint mono">pid ${pid.pid || "–"} · run_paper.py · selang 60s</span>
    <span class="abadge">${num(pl.rows_total || 0)} paper trade</span>
    <span class="abadge">${pl.csv_mtime ? esc(pl.csv_mtime.replace("T", " ")) : "tiada CSV"}</span>
    ${pl.feed && pl.feed.price ? `<span class="tag ${pl.feed.proxy ? "warn" : "ok"}">feed: ${esc(pl.feed.source)} ${esc(pl.feed.symbol || "")} ${Number(pl.feed.price).toFixed(2)}${pl.feed.proxy ? " (proksi)" : ""}</span>
      <span class="hint mono">${esc(String(pl.feed.last_time || "").slice(11, 19))}Z</span>` : ""}
    ${(pl.feed && pl.feed.errors || []).length ? `<span class="tag bad" title="${esc(JSON.stringify(pl.feed.errors))}">MetaAPI: belum deploy</span>` : ""}`;
  $("#tr-pl-meta").textContent = (pl.csv || "").replace(/^~/, "~");
  $("#tr-pl-events").innerHTML = (pl.events || []).length
    ? pl.events.map((e) => {
        const m = e.match(/^\[([^\]]+)\]\s*(.*)$/);
        const ts = m ? m[1].slice(11, 19) : "";
        const body = m ? m[2] : e;
        const cls = /NO_TRADE|VETO/.test(body) ? "warn" : "ok";
        return `<div class="feed-item"><span class="ft mono">${esc(ts)}</span>
          <span class="tag ${cls}">ATC</span><span class="fx">${esc(body)}</span></div>`;
      }).join("")
    : `<div class="empty">Belum ada kitaran paper. Jalankan: python3 run_paper.py -i 60</div>`;
}

async function loadTrading() {
  const d = await api("/api/trading");
  const last = d.decisions[0];
  $("#tr-hero").innerHTML = `<h1>${esc(d.identity || "HERMES19")}</h1>
    <p>Model ${esc(d.model)} · ${d.symbols.length} instrumen · ${d.decisions.length} keputusan ATC direkod · ${d.paper.length} paper trade.</p>`;
  $("#tr-symbols").innerHTML =
    `<thead><tr><th>Simbol</th><th>Kelas</th><th>Leverage</th><th>Sesi</th></tr></thead><tbody>` +
    d.symbols
      .map(
        (s) => `<tr><td class="mono">${esc(s.symbol)}</td><td>${esc(s.class)}</td>
        <td class="n"><span class="tag warn">${esc(s.leverage)}</span></td><td>${esc(s.session)}</td></tr>`
      )
      .join("") +
    `</tbody>`;
  $("#tr-doctrine").innerHTML = d.doctrine
    .map((l) => `<li><b>${esc(l.title)}</b> <span>${esc(l.text)}</span></li>`)
    .join("") || `<li>–</li>`;
  renderPaperLive(d.paper_live || {});
  const c = d.counts || {};
  $("#tr-counts").textContent = Object.entries(c).map(([k, v]) => `${k}:${v}`).join(" · ") || "tiada rekod";
  $("#tr-decisions").innerHTML =
    `<thead><tr><th>Masa (UTC)</th><th>Status</th><th>Simbol</th><th>Arah</th><th>Conf</th><th>Risk</th><th>Pasaran</th><th>Setuju</th></tr></thead><tbody>` +
    d.decisions
      .map((x) => {
        const cls = /APPROV|TRADE|ORDER/.test(x.status || "") ? "ok" : /VETO|REJECT|NO_TRADE/.test(x.status || "") ? "warn" : "";
        return `<tr><td class="n">${esc((x.ts || "").replace("T", " ").slice(0, 19))}</td>
        <td><span class="tag ${cls}">${esc(x.status)}</span></td>
        <td class="mono">${esc(x.symbol || "–")}</td><td>${esc(x.direction || "–")}</td>
        <td class="n">${x.confidence == null ? "–" : Number(x.confidence).toFixed(2)}</td>
        <td>${esc(x.risk_check || (x.risk_approved === true ? "PASS" : x.risk_approved === false ? "FAIL" : "–"))}</td>
        <td>${esc(x.data_quality || "–")}</td><td>${esc(x.agreement || "–")}</td></tr>`;
      })
      .join("") +
    `</tbody>`;
  $("#tr-paper").innerHTML = d.paper.length
    ? `<thead><tr>${Object.keys(d.paper[0]).map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead><tbody>` +
      d.paper
        .map((r) => `<tr>${Object.values(r).map((v) => `<td>${esc(String(v).slice(0, 60))}</td>`).join("")}</tr>`)
        .join("") +
      `</tbody>`
    : `<tbody><tr><td class="empty">Tiada paper trade direkod.</td></tr></tbody>`;
}

/* ---------------- system ---------------- */
async function loadSystem() {
  const d = await api("/api/health");
  // --- EJEN BERTUGAS: run agensi (siapa diarah buat apa) ---
  try {
    const ar = await api("/api/agency/runs");
    const runs = ar.runs || [];
    const warna = { done: "ok", running: "warn", queued: "", failed: "bad", error: "bad" };
    $("#sys-ejen").innerHTML = runs.length
      ? runs.map((x) => {
          const tag = `<span class="tag ${warna[x.status] || ""}">${esc((x.status || "–").toUpperCase())}</span>`;
          const ejen = (x.ejen_nama && x.ejen_nama.length ? x.ejen_nama : x.agents || [])
            .map((n) => `<span class="abadge" style="color:#6ab7ff;border-color:#6ab7ff55">${esc(n)}</span>`)
            .join(" ");
          return `<div class="panel" style="margin:0 0 8px">
            <div class="ph"><h2 style="font-size:13px">${esc(x.id)}</h2>${tag}</div>
            <div class="pbody">
              <div class="bodytext" style="margin-bottom:6px">${esc(x.instruction || "")}</div>
              <div style="display:flex;flex-wrap:wrap;gap:6px">${ejen || '<span class="hint">tiada ejen</span>'}</div>
              <div class="hint" style="margin-top:6px">${esc(x.created || "")} · ${x.bil_ejen || 0} ejen ·
                output ${x.outputs == null ? "–" : x.outputs}${x.error ? " · ralat: " + esc(x.error) : ""}</div>
            </div></div>`;
        }).join("")
      : `<div class="empty">Tiada ejen bertugas. Ketua belum hantar arahan kepada ejen.</div>`;
    $("#sys-ejen-masa").textContent = runs.length ? `terakhir ${runs[0].created || ""}` : "–";
  } catch (e) {
    $("#sys-ejen").innerHTML = `<div class="empty">Gagal baca senarai run: ${esc(e.message || e)}</div>`;
  }
  $("#sys-homes").innerHTML = d.homes
    .map((h) => {
      const g = h.gateway || {};
      const plat = Object.entries(g.platforms || {}).map(([k, v]) => `${k}:${v.state}`).join(" · ") || "–";
      return `<div class="panel"><div class="ph"><h2>${esc(h.label)}</h2>
        <span class="tag ${g.pid_alive === true ? "ok" : g.pid_alive === false ? "bad" : ""}">${g.pid_alive === true ? "HIDUP" : g.pid_alive === false ? "MATI" : "TIADA"}</span></div>
        <div class="pbody">
          <div class="kv"><span class="k">Laluan</span><span class="v">${esc(h.path)}</span></div>
          <div class="kv"><span class="k">Saiz</span><span class="v">${mb(h.home_mb)}</span></div>
          <div class="kv"><span class="k">DB</span><span class="v">${h.dbs.map((x) => `${x.name} ${kb(x.mb)}MB`).join(" · ") || "–"}</span></div>
          <div class="kv"><span class="k">Model</span><span class="v">${esc(h.model)}</span></div>
          <div class="kv"><span class="k">Gateway</span><span class="v">${esc(plat)}</span></div>
        </div></div>`;
    })
    .join("");
  const c = d.cron || {};
  $("#sys-cron").innerHTML = `
    <div class="kv"><span class="k">Ticker heartbeat</span><span class="v">${esc(c.heartbeat || "–")}</span></div>
    <div class="kv"><span class="k">Umur heartbeat</span><span class="v">${c.heartbeat_age_s == null ? "–" : c.heartbeat_age_s + "s"}</span></div>
    <div class="kv"><span class="k">Kali terakhir sukses</span><span class="v">${esc(c.last_success || "–")}</span></div>
    <div class="kv"><span class="k">Execution direkod</span><span class="v">${(c.executions || []).length}</span></div>`;
  $("#sys-procs").innerHTML = (d.processes || []).length
    ? d.processes.map((p) => `<div class="kv"><span class="k">${esc(p.name || p.id || "proc")}</span><span class="v">${esc(p.status || "")} pid ${esc(p.pid || "–")}</span></div>`).join("")
    : `<div class="empty">Tiada proses latar aktif.</div>`;
  $("#sys-logs").innerHTML = Object.entries(d.logs || {})
    .map(([k, lines]) => `<div class="hint" style="margin:4px 0 5px">${esc(k)}.log</div>
      <pre class="log">${esc((lines || []).slice(-14).join("\n") || "(kosong)")}</pre>`)
    .join("");
  try { await loadServis(); } catch (_) {}
}

/* ---------------- servis runit (hidup / mati / log) ---------------- */
async function loadServis() {
  try {
    const d = await api("/api/svc");
    const list = d.services || [];
    $("#svc-meta").textContent = `${list.length} servis · ${d.svdir || ""}`;
    $("#svc-list").innerHTML = list.map((s) => {
      const cls = s.state === "run" ? "ok" : s.state === "down" ? "warn" : "bad";
      const umur = s.seconds != null ? ` · ${s.seconds}s` : "";
      const pid = s.pid ? `pid ${s.pid}` : "tiada pid";
      const lg = s.log_bytes != null ? ` · log ${num(s.log_bytes)}b` : "";
      return `<div class="svc-row">
        <div class="svc-main">
          <div class="nm">${esc(s.label)}
            <span class="tag ${cls}">${esc((s.state || "?").toUpperCase())}</span></div>
          <div class="hint"><code>${esc(s.name)}</code> · ${esc(pid + umur + lg)}${s.has_down_file ? " · fail <b>down</b> ada" : ""}</div>
        </div>
        <div class="svc-act">
          <button class="btn" data-svc="${esc(s.name)}" data-act="up">HIDUP</button>
          <button class="btn" data-svc="${esc(s.name)}" data-act="restart">MULA SEMULA</button>
          <button class="btn" data-svc="${esc(s.name)}" data-act="down">MATI</button>
          <button class="btn" data-svc="${esc(s.name)}" data-act="log">LOG</button>
        </div></div>`;
    }).join("") || `<div class="empty">Tiada servis dalam senarai.</div>`;
    $$("#svc-list button[data-svc]").forEach((b) =>
      b.addEventListener("click", () => svcGo(b.dataset.svc, b.dataset.act, b)));
  } catch (e) {
    $("#svc-list").innerHTML = `<div class="empty">gagal baca servis: ${esc(e.message)}</div>`;
  }
}

async function svcGo(name, act, btn) {
  if (act === "log") {
    $("#svc-log").textContent = "memuat log…";
    try {
      const r = await api(`/api/svc/${encodeURIComponent(name)}/log?lines=80`);
      $("#svc-log").textContent = `${r.file} (${num(r.bytes)} bait)\n\n` +
        ((r.lines || []).join("\n") || "(kosong)");
    } catch (e) {
      $("#svc-log").textContent = "gagal: " + e.message;
    }
    return;
  }
  if (act === "down" && !confirm(`Matikan servis ${name}? Konsol 8787 akan berhenti serta-merta.`)) return;
  const asal = btn ? btn.textContent : "";
  if (btn) { btn.disabled = true; btn.textContent = "…"; }
  try {
    const r = await api(`/api/svc/${encodeURIComponent(name)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: act }),
    });
    const st = (r.status && r.status.state) || "?";
    toast(`${name}: ${act} → ${st}`, r.ok ? "ok" : "bad");
    $("#svc-log").textContent = `$ sv ${act} ${name}\n${r.out || "(tiada output)"}\n\nstatus: ${(r.status || {}).raw || ""}`;
  } catch (e) {
    toast("gagal: " + e.message, "bad");
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = asal; }
    loadServis();
  }
}

/* ---------------- Termux:Boot ---------------- */
async function loadBoot() {
  const b = await api("/api/device/boot");
  const ins = !!b.installed;
  $("#boot-status").innerHTML = `
    <span class="tag ${ins ? "ok" : "bad"}">Termux:Boot: ${ins ? "TERPASANG" : "BELUM"}</span>
    <span class="tag ${b.apk && b.apk.exists ? "ok" : "warn"}">APK: ${b.apk && b.apk.exists ? num(b.apk.bytes) + " bait" : "tiada"}</span>
    <span class="tag ${(b.boot_scripts || []).length ? "ok" : "warn"}">Skrip boot: ${(b.boot_scripts || []).length}</span>
    <span class="tag ${b.sumber_semakan === "pm" ? "" : "warn"}">semakan: ${esc(b.sumber_semakan || "–")}</span>`;
  $("#boot-msg").textContent = ins
    ? "terpasang ✓ — buka app Termux:Boot SEKALI sahaja, kemudian biarkan"
    : "";
  $("#boot-meta").textContent = `${b.apk && b.apk.path || ""} · ${b.boot_dir || ""}` +
    ((b.boot_scripts || []).length ? " · " + b.boot_scripts.join(", ") : "");
  $("#boot-go").textContent = ins ? "BUKA APL TERMUX:BOOT" : "BUKA PEMASANG APK";
  return b;
}

async function bootInstall() {
  const msg = $("#boot-msg");
  msg.textContent = "membuka…";
  try {
    const st = await api("/api/device/boot");
    if (st.installed) {
      const r = await api("/api/device/boot-open", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
      msg.textContent = r.ok ? "app Termux:Boot dibuka — tutup selepas nampak skrinnya" : "gagal buka app";
      return;
    }
    const r = await api("/api/device/boot-install", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    msg.textContent = "dialog Android dibuka — tekan PASANG di skrin telefon";
    const lg = $("#boot-log");
    lg.style.display = "block";
    lg.textContent = (r.log || []).map((x) => `${x.cara}: ${x.kod != null ? "exit " + x.kod : (x.ralat || x.skip || "")} ${x.out || ""}`).join("\n");
    loadBoot();
  } catch (e) {
    msg.textContent = "gagal: " + e.message;
  }
}

/* ---------------- boot ---------------- */

/* ======================================================================== */
/* PAPAN EJEN (mobile-first): pilih ejen → tugasan, data persona, prestasi   */
/* ======================================================================== */
const TIER_C = { A: "#5ee3a1", B: "#6ab7ff", C: "#8a8f98" };
const ST_C = { done: "#5ee3a1", error: "#ff6b6b", running: "#f0b429", queued: "#6f8a81", unknown: "#6f8a81" };

function tierPill(t, s, g) {
  const c = TIER_C[t] || "#8a8f98";
  const gred = g ? ` · ${g}` : "";
  return `<span class="abadge" style="color:${c};border-color:${c}55">TIER ${esc(t || "–")}` +
    `${s != null ? " · " + Math.round(s) : ""}${esc(gred)}</span>`;
}

function avHero(d) {
  const t = d.totals || {}, tier = t.tier || {};
  return `<h1>PAPAN EJEN</h1>
    <p>${num(t.ejen)} ejen · ${t.divisi} divisi · setiap satu ada <b>archetype</b>, <b>vibe</b>,
    <b>badan penuh</b>, dan <b>divisi</b>. Pilih ejen untuk lihat tugasan, data dan prestasi.</p>
    <div class="av-stats">
      <span><b>${num(t.ejen)}</b> ejen</span>
      <span><b>${num(tier.A)}</b> tier A</span>
      <span><b>${num(tier.B)}</b> tier B</span>
      <span><b>${num(t.kata_badan)}</b> perkataan badan</span>
    </div>`;
}

function avItems() {
  const d = S.av.data || { agents: [] };
  const q = (S.av.q || "").toLowerCase();
  let items = (d.agents || []).filter((a) => {
    if (S.av.arch && a.archetype !== S.av.arch) return false;
    if (!q) return true;
    return `${a.slug} ${a.nama} ${a.ringkas || ""} ${a.vibe || ""} ${(a.tag || []).join(" ")}`
      .toLowerCase().includes(q);
  });
  const s = S.av.sort;
  items.sort((a, b) =>
    s === "nama" ? String(a.nama).localeCompare(String(b.nama))
      : s === "badan" ? (b.badan_kata || 0) - (a.badan_kata || 0)
        : (b.skor || 0) - (a.skor || 0));
  return items;
}

function renderAvChips() {
  const d = S.av.data || {};
  const arch = d.archetypes || [];
  $("#av-chips").innerHTML =
    `<button class="av-chip ${S.av.arch === "" ? "on" : ""}" data-arch="">Semua <b>${num((d.totals || {}).ejen)}</b></button>` +
    arch.map((r) => `<button class="av-chip ${S.av.arch === r.key ? "on" : ""}" data-arch="${esc(r.key)}"
      title="${esc(r.maksud)}">${esc(r.label)} <b>${r.bilangan}</b></button>`).join("");
  $$("#av-chips .av-chip").forEach((b) =>
    b.addEventListener("click", () => { S.av.arch = b.dataset.arch; S.av.limit = 60; renderAvChips(); renderAvList(); }));
}

function renderAvList() {
  const items = avItems();
  const shown = items.slice(0, S.av.limit);
  $("#av-list").innerHTML = shown.map((a) => `
    <button class="avrow" data-slug="${esc(a.slug)}">
      <span class="av-em">${esc(a.emoji || "•")}</span>
      <span class="av-main">
        <span class="av-nm">${esc(a.nama)}</span>
        <span class="av-sub">${esc(a.archetype_label)} · ${esc(a.division)} · ${esc((a.tag || []).slice(0, 3).join(" · "))}</span>
        <span class="av-rk">${esc(a.ringkas || a.vibe || "")}</span>
      </span>
      <span class="av-score">${tierPill(a.tier, a.skor, a.gred)}</span>
    </button>`).join("") +
    (items.length > shown.length
      ? `<button class="btn av-more" id="av-more">Tunjuk lagi ${Math.min(60, items.length - shown.length)} · ${items.length - shown.length} baki</button>`
      : "") || `<div class="empty">Tiada ejen sepadan.</div>`;
  $$("#av-list .avrow").forEach((el) =>
    el.addEventListener("click", () => openAgentDash(el.dataset.slug)));
  const more = $("#av-more");
  if (more) more.addEventListener("click", () => { S.av.limit += 60; renderAvList(); });
}

async function renderAvHealth() {
  const box = $("#av-health");
  if (!box) return;
  box.innerHTML = `<div class="avh">menyemak kesihatan sistem…</div>`;
  try {
    const h = await api("/api/agency/health");
    const r = h.roster || {}, runs = h.runs || {}, p = h.penggunaan || {};
    const t = r.tier || {};
    box.innerHTML = `
      <div class="avh-grid">
        <div class="avh"><span class="avh-k">ROSTER</span><b>${num(r.ejen)}</b>
          <i>${num(r.divisi)} divisi · ${num(r.archetype)} archetype</i></div>
        <div class="avh"><span class="avh-k">TIER A/B/C</span><b>${num(t.A)}/${num(t.B)}/${num(t.C)}</b>
          <i>${num(r.kata_badan)} perkataan badan</i></div>
        <div class="avh"><span class="avh-k">RUN</span><b>${num(runs.selesai)}/${num(runs.jumlah)}</b>
          <i>${num(runs.aktif)} aktif · ${num(runs.gagal)} gagal</i></div>
        <div class="avh"><span class="avh-k">GUNA TOOL</span><b>${num(p.jumlah)}</b>
          <i>${num((p.terpakai || []).length)} ejen pernah dipanggil</i></div>
      </div>
      <div class="avh-actions">
        <button class="btn" id="av-uji">Uji 12 ejen rawak</button>
        <span class="hint" id="av-uji-hasil">semak API + masa tindak balas</span>
      </div>`;
    $("#av-uji").addEventListener("click", ujiEjenRawak);
  } catch (e) {
    box.innerHTML = `<div class="avh">RALAT kesihatan: ${esc(e.message)}</div>`;
  }
}

async function ujiEjenRawak() {
  const btn = $("#av-uji"), out = $("#av-uji-hasil");
  if (!btn) return;
  btn.disabled = true;
  out.textContent = "menguji…";
  const d = S.av.data || { agents: [] };
  const pick = [...(d.agents || [])].sort(() => Math.random() - 0.5).slice(0, 12);
  let ok = 0;
  const gagal = [], ms = [];
  await Promise.all(pick.map(async (a) => {
    const t0 = performance.now();
    try {
      await api(`/api/agent/${encodeURIComponent(a.slug)}/dashboard`);
      ok++;
      ms.push(performance.now() - t0);
    } catch (e) { gagal.push(a.slug); }
  }));
  ms.sort((x, y) => x - y);
  const med = Math.round(ms[ms.length >> 1] || 0);
  out.innerHTML = `<b style="color:#5ee3a1">${ok}/${pick.length} lulus</b> · median ${med}ms` +
    (gagal.length ? ` · gagal: ${esc(gagal.join(", "))}` : " · tiada ralat");
  btn.disabled = false;
}

async function loadEjen() {
  if (!S.av.data) {
    try {
      S.av.data = await api("/api/agency/ketua?limit=400");
    } catch (e) {
      $("#av-list").innerHTML = `<div class="empty">RALAT: ${esc(e.message)}</div>`;
      return;
    }
  }
  $("#av-picker").style.display = "";
  $("#av-hero").innerHTML = avHero(S.av.data);
  renderAvChips();
  renderAvList();
  renderAvHealth();
  if (S.av.slug) await openAgentDash(S.av.slug, true);
}

async function openAgentDash(slug, quiet) {
  S.av.slug = slug;
  $("#av-picker").style.display = "none";
  const box = $("#av-dash");
  box.style.display = "";
  if (!quiet) box.innerHTML = `<div class="empty">memuat papan ${esc(slug)}…</div>`;
  try {
    const d = await api(`/api/agent/${encodeURIComponent(slug)}/dashboard`);
    box.innerHTML = renderAgentDash(d);
    bindAgentDash(d);
  } catch (e) {
    box.innerHTML = `<div class="empty">RALAT: ${esc(e.message)}</div>`;
  }
  window.scrollTo({ top: 0, behavior: quiet ? "auto" : "smooth" });
}

function avBar(p) {
  const done = p.selesai || 0, bad = p.gagal || 0, act = p.aktif || 0;
  const rest = Math.max(0, (p.jumlah || 0) - done - bad - act);
  const seg = (n, c) => (n ? `<span style="flex:${n};background:${c}"></span>` : "");
  return `<div class="avbar">${seg(done, ST_C.done)}${seg(bad, ST_C.error)}${seg(act, ST_C.running)}${seg(rest, "#2a3a35")}</div>`;
}

function renderAgentDash(d) {
  const p = d.prestasi || {}, k = d.kualiti || {}, per = d.persona || {};
  const ms = (v) => (v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${v}ms`);
  const tasks = (d.tugasan || []).map((t) => `
    <div class="avtask">
      <div class="avtask-top">
        <span class="avdot" style="background:${ST_C[t.status] || ST_C.unknown}"></span>
        <b style="color:${ST_C[t.status] || ST_C.unknown}">${esc(t.status)}</b>
        <span class="mono">${esc(dt(t.created))}</span>
        <span class="mono">${t.ms ? ms(t.ms) : "–"}</span>
        <span class="mono">${t.tokens ? num(t.tokens) + " tok" : ""}</span>
      </div>
      <div class="avtask-instr">${esc(t.arahan || "–")}</div>
      ${t.skop ? `<div class="avtask-sub">skop: ${esc(t.skop)}</div>` : ""}
      ${t.verdict ? `<div class="avtask-verdict">${esc(t.verdict)}</div>` : ""}
    </div>`).join("");
  const secs = (per.seksyen || []).map((s) =>
    `<div class="avsec-row"><span>${esc(s.tajuk)}</span><span class="mono">${num(s.kata)}</span></div>`).join("");
  const hasil = (d.hasil || []).map((h) => `<li>${esc(h)}</li>`).join("");
  return `
  <div class="av-head">
    <button class="av-back" id="av-back">← Semua ejen</button>
    <div class="av-id">
      <div class="av-emoji">${esc(d.emoji || "•")}</div>
      <div>
        <h2>${esc(d.nama)}</h2>
        <div class="av-tags">
          <span class="abadge">${esc(d.division_label || d.division)}</span>
          <span class="abadge" style="color:#5ee3a1;border-color:#5ee3a155">${esc(d.archetype_label)}</span>
          ${d.archetype_kedua_label ? `<span class="abadge" style="color:#d8b74a;border-color:#d8b74a55">juga ${esc(d.archetype_kedua_label)}</span>` : ""}
          ${tierPill(k.tier, k.skor, k.gred)}
          ${k.pangkat != null ? `<span class="abadge">pangkat ${k.pangkat}%</span>` : ""}
        </div>
      </div>
    </div>
    <p class="av-vibe">${esc(d.vibe || d.ringkas || "")}</p>
    <p class="av-pilih"><b>Pilih bila:</b> ${esc(d.pilih_bila || "–")}</p>
  </div>

  <div class="av-kpi">
    <div class="avk"><span>TUGASAN</span><b>${num(p.jumlah)}</b><i>${num(p.selesai)} selesai · ${num(p.gagal)} gagal</i></div>
    <div class="avk"><span>KADAR SELESAI</span><b>${num(p.kadar_selesai)}%</b><i>${avBar(p)}</i></div>
    <div class="avk"><span>PURATA MASA</span><b>${p.purata_ms ? ms(p.purata_ms) : "–"}</b><i>setiap tugasan</i></div>
    <div class="avk"><span>KOS</span><b>$${Number(p.kos || 0).toFixed(3)}</b><i>${num(p.token)} token</i></div>
  </div>

  <div class="av-sec">
    <h3>TUGASAN <span class="hint">${(d.tugasan || []).length} rekod</span></h3>
    ${tasks || `<div class="empty">Belum ada tugasan. Mula di tab AGENCY → DEWAN ARAHAN.</div>`}
  </div>

  <div class="av-sec">
    <h3>DATA PERSONA</h3>
    <div class="av-facts">
      <span><b>${num(per.kata)}</b> perkataan</span>
      <span><b>${num((per.seksyen || []).length)}</b> seksyen</span>
      <span><b>${num(k.bullet)}</b> bullet</span>
      <span><b>${num(Math.round((k.originaliti || 0) * 100))}%</b> original</span>
    </div>
    ${hasil ? `<div class="hint" style="margin:10px 0 4px">HASIL / DELIVERABLE</div><ul class="av-hasil">${hasil}</ul>` : ""}
    <div class="hint" style="margin:10px 0 4px">SEKSYEN BADAN</div>
    <div class="avsec-list">${secs || `<div class="empty">–</div>`}</div>
    <div class="hint" style="margin:10px 0 4px">SUMBER</div>
    <div class="avsrc mono">${esc(per.sumber || "–")}</div>
  </div>

  <div class="av-sec">
    <h3>PRESTASI</h3>
    <div class="av-facts">
      <span><b>${num(d.penggunaan?.panggilan)}</b> panggilan tool</span>
      <span><b>${num(d.penggunaan?.sesi?.length)}</b> sesi</span>
      <span>terakhir <b>${d.penggunaan?.terakhir ? esc(ago(d.penggunaan.terakhir)) : "–"}</b></span>
    </div>
    <div class="avsec-list">
      <div class="avsec-row"><span>selesai</span><span class="mono">${num(p.selesai)}</span></div>
      <div class="avsec-row"><span>gagal</span><span class="mono">${num(p.gagal)}</span></div>
      <div class="avsec-row"><span>aktif / beratur</span><span class="mono">${num(p.aktif)}</span></div>
    </div>
  </div>

  <div class="av-sec">
    <h3>ARCHETYPE &amp; BUKTI</h3>
    <p class="av-pilih">${esc((S.av.data?.archetypes || []).find((r) => r.key === d.archetype)?.maksud || "")}</p>
    <div class="av-tags">
      ${(d.archetype_bukti || []).map((b) => `<span class="abadge">${esc(b)}</span>`).join("")}
      ${(d.tag || []).map((t) => `<span class="abadge" style="color:#6f8a81">#${esc(t)}</span>`).join("")}
    </div>
  </div>

  <div class="av-actions">
    <button class="btn primary" id="av-open-agency">Buka dalam AGENCY</button>
    <button class="btn" id="av-copy-tool">Salin arahan tool</button>
  </div>`;
}

function bindAgentDash(d) {
  $("#av-back").addEventListener("click", () => {
    S.av.slug = null;
    $("#av-dash").style.display = "none";
    $("#av-picker").style.display = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  $("#av-open-agency").addEventListener("click", () => {
    setTab("agency");
    S.ag.sel = d.slug;
    setTimeout(() => openAgent(d.slug), 400);
  });
  $("#av-copy-tool").addEventListener("click", async () => {
    const txt = d.persona?.tool || `agency_agents_load slug="${d.slug}"`;
    try { await navigator.clipboard.writeText(txt); } catch (e) {}
    $("#av-copy-tool").textContent = "Disalin ✓";
    setTimeout(() => ($("#av-copy-tool").textContent = "Salin arahan tool"), 1500);
  });
}

/* ---------------- ROSTER KETUA (dalam tab AGENCY) ---------------- */
async function loadKetuaRoster(force) {
  if (!S.kr.data || force) {
    try { S.kr.data = await api("/api/agency/ketua?limit=400"); }
    catch (e) { $("#kr-list").innerHTML = `<div class="empty">RALAT: ${esc(e.message)}</div>`; return; }
  }
  const d = S.kr.data, t = d.totals || {}, tier = t.tier || {};
  $("#kr-meta").textContent = `${num(t.ejen)} ejen · A ${num(tier.A)} · B ${num(tier.B)} · C ${num(tier.C)} · skor purata ${t.skor_purata}`;
  $("#kr-arch").innerHTML =
    `<button class="divchip ${S.kr.arch === "" ? "on" : ""}" data-arch=""><span class="sw" style="background:#5ee3a1"></span><span>Semua archetype</span><span class="ct">${num(t.ejen)}</span></button>` +
    (d.archetypes || []).map((r) => `<button class="divchip ${S.kr.arch === r.key ? "on" : ""}" data-arch="${esc(r.key)}" title="${esc(r.maksud)}">
      <span class="sw" style="background:#6ab7ff"></span><span>${esc(r.label)}</span><span class="ct">${r.bilangan}</span>
      <span class="rl">· A${r.tier_a}</span></button>`).join("");
  $$("#kr-arch .divchip").forEach((b) => b.addEventListener("click", () => {
    S.kr.arch = b.dataset.arch; loadKetuaRoster();
  }));
  renderKetuaList();
}

function renderKetuaList() {
  const d = S.kr.data || { agents: [] };
  const q = (S.kr.q || "").toLowerCase();
  let items = (d.agents || []).filter((a) => {
    if (S.kr.arch && a.archetype !== S.kr.arch) return false;
    if (S.kr.tier && a.tier !== S.kr.tier) return false;
    if (!q) return true;
    return `${a.slug} ${a.nama} ${a.ringkas || ""} ${(a.tag || []).join(" ")} ${(a.hasil || []).join(" ")}`
      .toLowerCase().includes(q);
  });
  $("#kr-list").innerHTML = items.slice(0, 80).map((a) => `
    <button class="krcard" data-slug="${esc(a.slug)}">
      <div class="krtop"><span class="krem">${esc(a.emoji || "•")}</span>
        <span class="krnm">${esc(a.nama)}</span>${tierPill(a.tier, a.skor, a.gred)}</div>
      <div class="krsub">${esc(a.archetype_label)} · ${esc(a.division)} · ${num(a.badan_kata)} perkataan</div>
      <div class="krring">${esc(a.ringkas || a.vibe || "")}</div>
      ${(a.hasil || []).length ? `<div class="krhasil">hasil: ${esc((a.hasil || [])[0])}</div>` : ""}
    </button>`).join("") ||
    `<div class="empty">Tiada ejen sepadan.</div>`;
  $$("#kr-list .krcard").forEach((el) => el.addEventListener("click", () => {
    setTab("ejen");
    S.av.slug = el.dataset.slug;
    setTimeout(() => openAgentDash(el.dataset.slug), 300);
  }));
}


async function boot() {
  if (new URLSearchParams(location.search).get("embed") === "1") {
    document.body.classList.add("embed");
  }
  S.meta = await api("/api/meta");
  S.home = S.pendingHome || S.meta.default_home || "hermes20";
  S.tab = S.pendingHome ? "pusat" : (S.meta.default_tab || "pusat");
  const qsTab = new URLSearchParams(location.search).get("tab") || (location.hash || "").replace("#", "");
  if (qsTab && TABS.some(([k]) => k === qsTab)) S.tab = qsTab;
  $("#ver").textContent = "v" + S.meta.version;
  if (S.meta.lan) {
    $(".clock").insertAdjacentHTML("afterbegin",
      `<span class="chip-live" style="margin-right:6px" title="Mod LAN: token diperlukan">LAN${S.meta.tls ? " · TLS" : ""}</span>`);
  }
  renderHomes();
  $$(".tab").forEach((t) => t.addEventListener("click", () => setTab(t.dataset.tab)));
  let t = null;
  $("#wq").addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => (S.tab === "work" ? loadWork() : null), 350);
  });
  $("#wlimit").addEventListener("change", loadWork);
  bindKeys();
  $("#inbox-file").addEventListener("change", (e) => inboxUpload(e.target.files));
  $("#inbox-send").addEventListener("click", () => {
    const f = $("#inbox-file").files;
    if (f && f.length) inboxUpload(f);
    else addNoteOnly();
  });
  const dz = $("#inbox-drop");
  ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("over"); }));
  dz.addEventListener("drop", (e) => inboxUpload(e.dataTransfer.files));
  const mcpAddBtn = $("#mcp-add");
  if (mcpAddBtn) mcpAddBtn.addEventListener("click", mcpAdd);
  const mcpCat = $("#mcp-catalog");
  if (mcpCat) mcpCat.addEventListener("click", () => {
    $("#mcp-status").textContent = "muat katalog…";
    api("/api/mcp/catalog").then((d) => {
      $("#mcp-status").textContent = (d.items || []).map((x) => x.name).join(" · ") || "katalog kosong";
    }).catch((e) => ($("#mcp-status").textContent = "gagal: " + e.message));
  });
  $("#report-dl").addEventListener("click", () => window.open("/api/report/daily", "_blank"));
  $("#report-tg").addEventListener("click", reportTelegram);
  $("#quick-adb").addEventListener("click", () => {
    setTab("system");
    const el = $("#adb-host");
    if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.focus(); }
  });
  $("#pd-send").addEventListener("click", panduanUpload);
  $("#pd-file").addEventListener("change", pdPreview);
  $("#pd-clear").addEventListener("click", pdClear);
  $("#pd-shot").addEventListener("click", pdShot);
  $("#boot-go").addEventListener("click", bootInstall);
  $("#boot-refresh").addEventListener("click", () => loadBoot().catch(() => {}));
  $("#adb-guide-go").addEventListener("click", () => {
    setTab("system");
    const el = $("#adb-host");
    if (el) { el.scrollIntoView({ behavior: "smooth", block: "center" }); el.focus(); }
  });
  $("#svc-refresh").addEventListener("click", () => loadServis().catch(() => {}));
  $("#up-file").addEventListener("change", upPick);
  $("#up-send").addEventListener("click", upSend);
  $("#up-clear").addEventListener("click", upClear);
  $("#adb-go").addEventListener("click", adbPairFromUI);
  $("#adb-code").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); adbPairFromUI(); } });
  $("#bot-send").addEventListener("click", botSend);
  $("#bot-cmd").addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); botSend(); }
  });
  $("#da-plan").addEventListener("click", daPlan);
  $("#da-run").addEventListener("click", daRun);
  $("#gd-refresh").addEventListener("click", () => loadGudang().catch(() => {}));
  $("#sf-refresh").addEventListener("click", () => loadSofia().catch(() => {}));
  $("#gd-calon").addEventListener("change", gdPilih);
  $("#gd-hantar").addEventListener("click", () => gdHantar(false));
  $("#gd-pdf").addEventListener("click", () => gdHantar(true));
  $("#da-instr").addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") daPlan();
  });
  let ta = null;
  const avq = $("#av-q");
  if (avq) avq.addEventListener("input", () => {
    clearTimeout(ta);
    ta = setTimeout(() => { S.av.q = avq.value.trim(); S.av.limit = 60; renderAvList(); }, 250);
  });
  const avs = $("#av-sort");
  if (avs) avs.addEventListener("change", () => { S.av.sort = avs.value; renderAvList(); });
  const krq = $("#kr-q");
  if (krq) krq.addEventListener("input", () => {
    clearTimeout(ta);
    ta = setTimeout(() => { S.kr.q = krq.value.trim(); renderKetuaList(); }, 250);
  });
  const krt = $("#kr-tier");
  if (krt) krt.addEventListener("change", () => { S.kr.tier = krt.value; renderKetuaList(); });
  $("#agq").addEventListener("input", () => {
    clearTimeout(ta);
    ta = setTimeout(() => {
      S.ag.q = $("#agq").value.trim();
      if (S.tab === "agency") loadAgency();
    }, 300);
  });
  setInterval(() => {
    $("#clock").textContent = new Date().toLocaleTimeString("en-GB");
  }, 1000);
  setInterval(() => {
    if (!S.auto) return;
    if (document.activeElement && ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
    loadTab();
  }, 15000);
  $("#live").addEventListener("click", () => {
    S.auto = !S.auto;
    $("#live").classList.toggle("off", !S.auto);
    $("#live").textContent = S.auto ? "LIVE" : "PAUSE";
    if (S.auto) loadTab();
  });
  const wv = $("#web-verify");
  if (wv) wv.addEventListener("click", webVerify);
  const wo = $("#web-open");
  if (wo) wo.addEventListener("click", () => {
    const u = ($("#web-url").textContent || "").trim();
    if (u.startsWith("http")) window.open(u, "_blank", "noopener");
  });
  const wc = $("#web-copy");
  if (wc) wc.addEventListener("click", async () => {
    const u = ($("#web-url").textContent || "").trim();
    try { await navigator.clipboard.writeText(u); $("#web-msg").textContent = "URL disalin ✓"; }
    catch (_) { $("#web-msg").textContent = "salin manual: " + u; }
  });

  const bugo = $("#buka-url-go");
  if (bugo) bugo.addEventListener("click", bukaUrlGo);

  initSide();
  setTab(S.tab);
}
boot().catch((e) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div style="padding:14px;color:#ff6b6b;font-family:monospace">RALAT: ${esc(e.message)}</div>`
  );
});

