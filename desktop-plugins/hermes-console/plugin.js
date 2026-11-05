/**
 * Hermes Console — plugin DESKTOP (runtime, pintu rasmi `desktop-plugins/`).
 *
 * Tujuan: paparan console yang SAMA (127.0.0.1:8787) muncul dalam app Hermes
 * Desktop sebagai halaman `/console` + baris nav sidebar + command palette.
 *
 * Kenapa plugin dan bukan patch core:
 *   - tiada suntingan pada apps/desktop (selamat naik taraf Hermes)
 *   - loader runtime menguruskan nyahmuat/ulangmuat automatik
 *   - console kekal satu sumber kebenaran; plugin hanya membingkaikannya
 *
 * Fail ini ESM tulen dengan panggilan jsx() — format yang loader desktop
 * jangka (rujuk apps/desktop/src/plugins/hello-runtime/plugin.runtime.js).
 */

import { PALETTE_AREA, ROUTES_AREA, SIDEBAR_NAV_AREA, host } from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useCallback, useEffect, useState } from 'react'

const DEFAULT_BASE = 'http://127.0.0.1:8787'
const BASE_KEY = 'base'
const baseOf = ctx => {
  const saved = ctx?.storage?.get?.(BASE_KEY, DEFAULT_BASE)
  return String(saved || DEFAULT_BASE).replace(/\/+$/, '')
}
const embedUrl = base => `${base}/?embed=1`
const MONO = 'ui-monospace, SFMono-Regular, Menlo, monospace'
const C = {
  bg: '#070a09',
  panel: '#0f1614',
  line: '#1c2a26',
  ink: '#d7e4df',
  dim: '#6f8a81',
  acc: '#5ee3a1',
  gold: '#f0b429',
  red: '#ff6b6b'
}

function usePing(base) {
  const [state, setState] = useState('checking')

  useEffect(() => {
    let alive = true
    const probe = async () => {
      try {
        const r = await fetch(`${base}/api/ping`, { cache: 'no-store' })
        if (!alive) return
        setState(r.ok ? 'ok' : 'down')
      } catch {
        if (alive) setState('down')
      }
    }
    probe()
    const t = setInterval(probe, 10000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [base])

  return state
}

function btnStyle(primary) {
  return {
    background: primary ? C.acc : '#0e1715',
    color: primary ? '#06110d' : C.ink,
    border: `1px solid ${primary ? 'transparent' : C.line}`,
    borderRadius: 6,
    padding: '4px 9px',
    fontSize: 11,
    fontFamily: MONO,
    cursor: 'pointer',
    letterSpacing: '0.04em'
  }
}

function Btn({ children, onClick, primary }) {
  return jsx('button', { type: 'button', onClick, style: btnStyle(primary), children })
}

function DownPane({ os, base }) {
  const cmd = '~/hermes-console/run.sh'
  const [copied, setCopied] = useState(false)
  const copy = useCallback(async () => {
    const ok = await os?.writeClipboard?.(cmd)
    setCopied(Boolean(ok))
    setTimeout(() => setCopied(false), 1500)
  }, [os])

  return jsxs('div', {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      padding: 24,
      textAlign: 'center'
    },
    children: [
      jsx('div', { style: { fontSize: 34, lineHeight: 1 }, children: '⚪' }),
      jsx('div', { style: { fontSize: 14, fontWeight: 600 }, children: 'Pelayan console tidak berjalan' }),
      jsx('div', {
        style: { fontSize: 12, color: C.dim, maxWidth: 420, lineHeight: 1.6 },
        children:
          'Hermes Desktop membingkaikan console pada 127.0.0.1:8787. Mulakan pelayan sekali, kemudian tekan Muat semula — paparan akan sama seperti di pelayar.'
      }),
      jsxs('div', {
        style: {
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          marginTop: 4,
          background: '#0b1311',
          border: `1px dashed ${C.line}`,
          borderRadius: 6,
          padding: '7px 10px'
        },
        children: [
          jsx('code', { style: { fontFamily: MONO, fontSize: 11.5, color: C.gold }, children: cmd }),
          jsx(Btn, { onClick: copy, children: copied ? 'disalin' : 'salin' })
        ]
      }),
      jsx(Btn, {
        primary: true,
        onClick: () => os?.openExternal?.(embedUrl(base)),
        children: 'Buka dalam pelayar'
      })
    ]
  })
}

function ConsolePage({ os, base }) {
  const ping = usePing(base)
  const [nonce, setNonce] = useState(0)
  const reload = useCallback(() => setNonce(v => v + 1), [])

  const dotColor = ping === 'ok' ? C.acc : ping === 'down' ? C.red : C.gold
  const hostLabel = String(base || '').replace(/^https?:\/\//, '')
  const statusText =
    ping === 'ok' ? `${hostLabel} · tersambung` : ping === 'down' ? 'pelayan tidak berjalan' : 'menyemak…'

  return jsxs('div', {
    style: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      minHeight: 0,
      background: C.bg,
      color: C.ink
    },
    children: [
      jsxs('div', {
        style: {
          display: 'flex',
          alignItems: 'center',
          gap: 9,
          padding: '7px 11px',
          borderBottom: `1px solid ${C.line}`,
          background: C.panel,
          flexShrink: 0
        },
        children: [
          jsx('span', {
            style: {
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: dotColor,
              boxShadow: `0 0 8px ${dotColor}`
            }
          }),
          jsx('span', {
            style: { fontFamily: MONO, fontSize: 11.5, letterSpacing: '0.14em', color: C.acc },
            children: 'HERMES CONSOLE'
          }),
          jsx('span', { style: { fontFamily: MONO, fontSize: 10.5, color: C.dim }, children: statusText }),
          jsx('span', { style: { flex: 1 } }),
          jsx(Btn, { onClick: reload, children: 'Muat semula' }),
          jsx(Btn, { onClick: () => os?.openExternal?.(embedUrl(base)), children: 'Pelayar' })
        ]
      }),
      ping === 'down'
        ? jsx(DownPane, { os, base })
        : jsx('iframe', {
            key: nonce,
            src: embedUrl(base),
            title: 'Hermes Console',
            style: { flex: 1, width: '100%', border: 0, background: C.bg }
          })
    ]
  })
}

function ConsolePill({ base }) {
  const ping = usePing(base)
  const color = ping === 'ok' ? C.acc : ping === 'down' ? C.red : C.gold

  return jsxs('span', {
    title: ping === 'ok' ? 'Console aktif di 127.0.0.1:8787' : 'Console tidak dapat dihubungi',
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 5,
      padding: '0 6px',
      height: '100%',
      fontSize: 11,
      color: C.dim,
      cursor: 'pointer'
    },
    onClick: () => host.navigate('/console'),
    children: [
      jsx('span', { style: { width: 7, height: 7, borderRadius: '50%', background: color }, children: '' }),
      jsx('span', { children: 'console' })
    ]
  })
}

let STORE = null
const readBase = () => baseOf(STORE)

export default {
  id: 'hermes-console',
  name: 'Hermes Console',
  defaultEnabled: true,
  register(ctx) {
    const os = ctx.os
    STORE = ctx.storage

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        title: 'Console',
        data: { path: '/console' },
        render: () => jsx(ConsolePage, { os, base: readBase() })
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 60,
        data: { codicon: 'pulse', label: 'Console', path: '/console' }
      },
      {
        id: 'pill',
        area: 'statusBar.right',
        order: 90,
        render: () => jsx(ConsolePill, { base: readBase() })
      },
      {
        id: 'open',
        area: PALETTE_AREA,
        data: {
          id: 'hermes-console.open',
          label: 'Console: Buka papan pemantau',
          keywords: ['console', 'monitor', 'ejen', 'agency', 'kerja', 'sessions'],
          run: () => host.navigate('/console')
        }
      },
      {
        id: 'set-url',
        area: PALETTE_AREA,
        data: {
          id: 'hermes-console.set-url',
          label: 'Console: Tetapkan URL pelayan',
          keywords: ['console', 'url', 'pelayan', 'server', 'remote'],
          run: () => {
            if (typeof window === 'undefined' || !window.prompt) return
            const next = window.prompt(
              'URL pelayan console (127.0.0.1:8787, atau IP peranti untuk akses jauh)',
              readBase()
            )
            if (!next) return
            STORE?.set?.(BASE_KEY, String(next).trim().replace(/\/+$/, ''))
            host.navigate('/console')
            window.location.reload()
          }
        }
      }
    ])
  }
}
