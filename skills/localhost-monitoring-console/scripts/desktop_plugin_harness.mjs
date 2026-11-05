/**
 * Desktop plugin harness — run a Hermes Desktop runtime plugin through the same
 * pipeline the app uses (rewrite specifiers -> import -> register(ctx) -> render),
 * but with stub SDK/react modules. Proves registration and page output without
 * building Electron (which does not exist for Android/Termux).
 *
 * Usage: node desktop_plugin_harness.mjs [path/to/plugin.js]
 * Default: ~/.hermes20/desktop-plugins/hermes-console/plugin.js
 */
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const HOME = os.homedir()
const pluginPath =
  process.argv[2] || path.join(HOME, '.hermes20/desktop-plugins/hermes-console/plugin.js')

// Termux: os.tmpdir() is $PREFIX/tmp (writable); fall back to the plugin's dir.
let tmp
try {
  tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'dp-'))
} catch {
  tmp = fs.mkdtempSync(path.join(path.dirname(pluginPath), '.dp-'))
}

const stub = (name, body) => {
  const f = path.join(tmp, `${name}.mjs`)
  fs.writeFileSync(f, body)
  return pathToFileURL(f).href
}

const sdkUrl = stub(
  'sdk',
  `export const ROUTES_AREA='routes'
   export const SIDEBAR_NAV_AREA='sidebar.nav'
   export const PALETTE_AREA='palette'
   export const STATUSBAR_AREAS={left:'statusBar.left',right:'statusBar.right'}
   export const host={navigate:(p)=>{globalThis.__nav=(globalThis.__nav||[]).concat(p)}}
   export const cn=(...a)=>a.filter(Boolean).join(' ')
   export const Codicon=()=>null
   export const Tip=()=>null
   export const useValue=()=>null
   export const useQuery=()=>({data:null})`
)
const reactUrl = stub(
  'react',
  `export const useState=(v)=>[v,()=>{}]
   export const useEffect=()=>{}
   export const useCallback=(f)=>f
   export const useMemo=(f)=>f()
   export const useRef=(v)=>({current:v})`
)
const jsxUrl = stub(
  'jsx',
  `const mk=(type,props)=>({type,props:props||{}})
   export const jsx=mk
   export const jsxs=mk
   export const Fragment='Fragment'`
)

const map = {
  '@hermes/plugin-sdk': sdkUrl,
  react: reactUrl,
  'react/jsx-runtime': jsxUrl,
  'react/jsx-dev-runtime': jsxUrl
}
const src = fs.readFileSync(pluginPath, 'utf8')
const rewritten = src.replace(
  /(from\s*|import\s*\(\s*|import\s+)(['"])([^'"]+)\2/g,
  (whole, pre, q, spec) => (map[spec] ? `${pre}${q}${map[spec]}${q}` : whole)
)
const entry = path.join(tmp, 'plugin.mjs')
fs.writeFileSync(entry, rewritten)

let failures = 0
const check = (cond, msg) => {
  console.log(`${cond ? 'OK   ' : 'GAGAL '}${msg}`)
  if (!cond) failures++
}

const mod = await import(pathToFileURL(entry).href)
const plugin = mod.default

check(Boolean(plugin), 'default export wujud')
check(typeof plugin.id === 'string' && plugin.id.length > 0, `id plugin: ${plugin.id}`)
check(typeof plugin.register === 'function', 'register(ctx) boleh dipanggil')

const got = []
const ctx = {
  source: `plugin:${plugin.id}`,
  register: c => {
    got.push(c)
    return () => {}
  },
  registerMany: cs => {
    cs.forEach(c => got.push(c))
    return () => {}
  },
  onDispose: () => {},
  storage: { get: (_k, d) => d, set: () => {}, remove: () => {} },
  os: { notify: () => {}, openExternal: async () => true, revealPath: async () => false, writeClipboard: async () => true }
}
plugin.register(ctx)

check(got.length > 0, `kontribusi didaftarkan: ${got.length} (${got.map(c => c.area).join(', ')})`)

const route = got.find(c => c.area === 'routes')
check(Boolean(route), 'ada kontribusi area routes')
check(Boolean(route?.data?.path?.startsWith('/')), `laluan halaman: ${route?.data?.path}`)
check(typeof route?.render === 'function', 'halaman ada fungsi render')

const nav = got.find(c => c.area === 'sidebar.nav')
check(!nav || (nav.data?.path && nav.data?.codicon), `nav sidebar: ${nav?.data?.label}`)

if (route?.render) {
  const renderTree = node => {
    if (node == null || typeof node !== 'object') return node
    if (Array.isArray(node)) return node.map(renderTree)
    if (typeof node.type === 'function') return renderTree(node.type(node.props || {}))
    const props = { ...(node.props || {}) }
    if (props.children !== undefined) props.children = renderTree(props.children)
    return { type: node.type, props }
  }
  const flat = []
  const walk = n => {
    if (!n || typeof n !== 'object') return
    if (Array.isArray(n)) return n.forEach(walk)
    flat.push(n)
    walk(n.props?.children)
  }
  walk(renderTree(route.render()))

  const iframe = flat.find(n => n.type === 'iframe')
  check(Boolean(iframe), 'halaman render mengandungi iframe')
  if (iframe) console.log(`       iframe src: ${iframe.props?.src}`)
  check(flat.some(n => n.type === 'button'), 'ada butang kawalan')
}

for (const c of got.filter(x => typeof x.render === 'function' && x.id !== 'page')) {
  let ok = true
  try {
    c.render()
  } catch (e) {
    ok = false
    console.log(`       ${c.area}: ${e.message}`)
  }
  check(ok, `render ${c.id} tanpa ralat`)
}

fs.rmSync(tmp, { recursive: true, force: true })
console.log(failures === 0 ? '\nLULUS — plugin berdaftar & halaman dirender' : `\nGAGAL — ${failures} semakan`)
process.exit(failures === 0 ? 0 : 1)
