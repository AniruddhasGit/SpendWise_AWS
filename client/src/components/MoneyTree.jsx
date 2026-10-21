import { useEffect, useRef } from 'react'
import { dollars } from '../lib/money.js'
import { prefersReducedMotion } from '../lib/motion.js'

/**
 * The money tree (SW-ADR-156): a poster-print bonsai whose leaves are banknotes.
 *
 * The tree is ONE still image (`/assets/tree/money-tree.webp`, provenance beside
 * it). Everything alive is drawn here: bills detach from the painted leaves and
 * flutter down to a frosted glass ground, where the roots fade out. On the
 * landing page a breeze passes now and then, mist drifts across the ground and
 * the poster's orbit lines circle the canopy.
 *
 * Interaction: brushing the pointer across the canopy shakes bills loose. A new
 * `dropRequest` (`{ id, label, paise }`) drops one bill carrying exactly that
 * label and amount; the dashboard sends one after the server confirms an
 * expense. The bills are canvas pixels, never DOM text, so no figure a test or a
 * screen reader reads is ever mid-animation. Reduced motion draws nothing.
 */

const TREE_SRC = '/assets/tree/money-tree.webp'

// The painted banknotes, located in the image (x, y as fractions of its box).
// Measured from the artwork, so a falling bill leaves from where a leaf is.
const LEAVES = [
  [0.579, 0.074], [0.508, 0.086], [0.635, 0.093], [0.573, 0.096], [0.617, 0.104], [0.679, 0.102],
  [0.479, 0.112], [0.517, 0.108], [0.731, 0.116], [0.378, 0.134], [0.447, 0.128], [0.55, 0.127],
  [0.594, 0.132], [0.662, 0.133], [0.507, 0.14], [0.722, 0.138], [0.393, 0.148], [0.43, 0.162],
  [0.47, 0.158], [0.565, 0.159], [0.687, 0.157], [0.371, 0.172], [0.511, 0.173], [0.628, 0.168],
  [0.775, 0.172], [0.72, 0.178], [0.792, 0.178], [0.341, 0.188], [0.41, 0.19], [0.618, 0.19],
  [0.677, 0.191], [0.489, 0.198], [0.536, 0.202], [0.714, 0.214], [0.764, 0.208], [0.804, 0.212],
  [0.253, 0.22], [0.275, 0.223], [0.312, 0.218], [0.382, 0.215], [0.421, 0.227], [0.458, 0.231],
  [0.672, 0.23], [0.843, 0.225], [0.362, 0.244], [0.744, 0.241], [0.828, 0.238], [0.493, 0.245],
  [0.782, 0.25], [0.868, 0.248], [0.262, 0.255], [0.324, 0.258], [0.412, 0.262], [0.506, 0.264],
  [0.619, 0.258], [0.652, 0.258], [0.39, 0.267], [0.467, 0.268], [0.709, 0.266], [0.722, 0.282],
  [0.825, 0.281], [0.362, 0.29], [0.438, 0.291], [0.557, 0.294], [0.622, 0.293], [0.786, 0.294],
  [0.88, 0.288], [0.272, 0.3], [0.859, 0.297], [0.253, 0.309], [0.309, 0.308], [0.58, 0.321],
  [0.734, 0.325], [0.808, 0.322], [0.361, 0.332], [0.401, 0.328], [0.478, 0.329], [0.701, 0.333],
  [0.572, 0.344], [0.766, 0.342], [0.246, 0.348], [0.286, 0.352], [0.333, 0.352], [0.392, 0.348],
  [0.652, 0.36], [0.845, 0.365], [0.879, 0.363], [0.822, 0.367], [0.138, 0.385], [0.182, 0.377],
  [0.266, 0.385], [0.758, 0.381], [0.226, 0.387], [0.686, 0.392], [0.738, 0.393], [0.792, 0.39],
  [0.159, 0.402], [0.361, 0.398], [0.486, 0.402], [0.822, 0.405], [0.922, 0.398], [0.854, 0.413],
  [0.138, 0.421], [0.208, 0.418], [0.532, 0.42], [0.907, 0.415], [0.252, 0.429], [0.463, 0.43],
  [0.298, 0.439], [0.445, 0.438], [0.883, 0.444], [0.174, 0.451], [0.849, 0.447], [0.588, 0.462],
  [0.729, 0.463], [0.206, 0.468], [0.905, 0.471], [0.118, 0.483], [0.26, 0.477], [0.826, 0.481],
  [0.872, 0.485], [0.926, 0.478], [0.139, 0.492], [0.08, 0.495], [0.232, 0.502], [0.514, 0.496],
  [0.768, 0.498], [0.164, 0.514], [0.198, 0.511], [0.847, 0.508], [0.77, 0.525], [0.099, 0.528],
  [0.14, 0.538], [0.199, 0.548], [0.051, 0.563], [0.109, 0.565], [0.098, 0.584],
]
const GROUND = 0.735        // where the trunk meets the roots, as a fraction of the image height
const CANOPY_BOTTOM = 0.6   // brushing below this does not shake bills

// Examples for the landing page, and for a dashboard with nothing logged yet.
// Illustrative spends, not claims about anyone's money.
export const EXAMPLE_BILLS = [
  { label: 'Pizza', paise: 1000 }, { label: 'Coffee', paise: 450 },
  { label: 'Taxi', paise: 1800 }, { label: 'Groceries', paise: 8600 },
  { label: 'Rent', paise: 145000 }, { label: 'Movie', paise: 1500 },
  { label: 'Gas', paise: 4000 }, { label: 'Books', paise: 2400 },
  { label: 'Electricity', paise: 9500 }, { label: 'Burrito', paise: 1200 },
  { label: 'Gym', paise: 3500 }, { label: 'Subway', paise: 290 },
]

/** `dollars()` is the only formatter; a bill just drops a zero fraction. */
function amountText(paise) {
  const s = dollars(paise)
  return s && s.endsWith('.00') ? s.slice(0, -3) : s
}

function readPalette(el) {
  const cs = getComputedStyle(el)
  const v = (name, fallback) => cs.getPropertyValue(name).trim() || fallback
  // The fallbacks only cover a stylesheet that has not loaded yet.
  return {
    ink: v('--sw-brand-vermilion', 'rgb(227 66 34)'),
    inkDeep: v('--sw-brand-vermilion-deep', 'rgb(179 48 26)'),
    leaf: v('--sw-brand-emerald', 'rgb(4 106 56)'),
    dust: v('--mt-dust', 'rgb(243 230 210)'),
    shadow: v('--mt-bill-shadow', 'rgb(11 42 28 / 0.18)'),
  }
}

// The bill itself is PRINTED, not drawn: one sprite rendered in the tree's
// risograph language (grain, guilloche, a halftone oval, the vermilion
// misregistration edge). Provenance beside the file. Canvas only writes the
// category and the amount, in vermilion, on its clear band.
// Every bill is the same paper and the same size as a leaf on the tree,
// whatever it says: the owner asked for no colour change mid-fall and no
// bigger bills (2026-10-20). A painted leaf is about 5.6% of the image's width.
const SPRITE_SRC = '/assets/tree/bill-front.webp'
const BILL_W = 62
const BILL_H = 32
const LEAF_W = 0.056
/** The bill's scale for a tree drawn `treeW` px wide: leaf-sized, never so
 *  small its amount cannot be read. */
const billScale = (treeW) => Math.min(1, Math.max(0.6, (treeW * LEAF_W) / BILL_W))

function loadSprite() {
  const im = new Image()
  im.decoding = 'async'
  im.src = SPRITE_SRC
  return im
}

function drawBill(ctx, b, pal, sprite, k) {
  const w = BILL_W * k
  const h = BILL_H * k
  ctx.save()
  ctx.globalAlpha = b.alpha
  ctx.translate(b.x, b.y)
  ctx.rotate(b.rot)
  // The paper fluttering: a cosine on one axis reads as a sheet tilting in the
  // air. It never turns over, so the face (and its writing) always shows, and
  // never gets thinner than 60%, so a bill never becomes a sliver.
  ctx.scale(1, 0.6 + 0.4 * Math.abs(Math.cos(b.phase)))

  ctx.shadowColor = pal.shadow
  ctx.shadowBlur = 7 * k
  ctx.shadowOffsetY = 2.5 * k
  if (sprite.complete && sprite.naturalWidth) ctx.drawImage(sprite, -w / 2, -h / 2, w, h)
  ctx.shadowColor = 'transparent'

  // the writing, in the clear band right of the oval: what, and how much
  const left = -w / 2 + w * 0.47
  const room = w * 0.47
  ctx.textBaseline = 'alphabetic'
  ctx.textAlign = 'left'
  ctx.fillStyle = pal.inkDeep
  ctx.font = `700 ${(8 * k).toFixed(1)}px Geist, system-ui, sans-serif`
  ctx.fillText(b.label, left, -h / 2 + h * 0.4, room)
  ctx.fillStyle = pal.ink
  ctx.font = `900 ${(14 * k).toFixed(1)}px "Big Shoulders Display", Geist, system-ui, sans-serif`
  ctx.fillText(b.amount, left, h / 2 - h * 0.2, room)
  ctx.restore()
}

/** The poster's four-point spark, for the burst where a new bill lands. */
function drawSpark(ctx, s, colour) {
  const r = s.r
  ctx.save()
  ctx.globalAlpha = s.alpha
  ctx.translate(s.x, s.y)
  ctx.rotate(s.rot)
  ctx.fillStyle = colour
  ctx.beginPath()
  ctx.moveTo(0, -r)
  ctx.lineTo(r * 0.18, -r * 0.18)
  ctx.lineTo(r, 0)
  ctx.lineTo(r * 0.18, r * 0.18)
  ctx.lineTo(0, r)
  ctx.lineTo(-r * 0.18, r * 0.18)
  ctx.lineTo(-r, 0)
  ctx.lineTo(-r * 0.18, -r * 0.18)
  ctx.closePath()
  ctx.fill()
  ctx.restore()
}

export default function MoneyTree({
  bills, variant = 'dashboard', atmosphere = false, orbits = atmosphere, mist = atmosphere,
  dust = false, ground = true, dropRequest = null, breeze = 0, alwaysMove = false, drops = true,
  alt = 'A bonsai tree whose leaves are banknotes', className = '',
}) {
  const rootRef = useRef(null)
  const imgRef = useRef(null)
  const canvasRef = useRef(null)
  const api = useRef(null)
  const feedRef = useRef(bills)
  feedRef.current = bills && bills.length ? bills : EXAMPLE_BILLS

  useEffect(() => {
    const root = rootRef.current
    const canvas = canvasRef.current
    const img = imgRef.current
    if (!root || !canvas || !img) return undefined
    const ctx = canvas.getContext('2d')
    if (!ctx) return undefined

    // `alwaysMove`: the signed-out scene animates whatever the motion
    // preference (the owner's ruling, SW-ADR-160)
    let reduced = alwaysMove ? false : prefersReducedMotion()
    let pal = readPalette(root)
    const sprite = loadSprite()
    const sparks = []
    let W = 0; let H = 0; let box = { x: 0, y: 0, w: 1, h: 1 }
    let raf = 0; let last = 0; let running = false; let visible = true
    let pageVisible = !document.hidden
    let spawnClock = 0; let feedIndex = 0
    // `breeze`: a steady wind in px/s (negative blows right to left) under the gusts
    let wind = breeze; let gust = null; let nextGust = 6 + Math.random() * 5
    const live = []
    // the air around the tree (landing only): specks of the poster's ink
    // drifting up through warm light, twinkling, pushed by the breeze
    const motes = []
    const MOTES = atmosphere ? 34 : 0
    const MAX = variant === 'landing' ? 30 : 18
    const every = variant === 'landing' ? 1.9 : 3.4

    const measure = () => {
      const r = root.getBoundingClientRect()
      const ir = img.getBoundingClientRect()
      W = Math.max(1, r.width); H = Math.max(1, r.height)
      box = { x: ir.left - r.left, y: ir.top - r.top, w: Math.max(1, ir.width), h: Math.max(1, ir.height) }
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = Math.round(W * dpr)
      canvas.height = Math.round(H * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }

    const nextItem = () => {
      const feed = feedRef.current
      const item = feed[feedIndex % feed.length]
      feedIndex += 1
      return item
    }

    const spawn = ({ x, y, item, featured = false, push = 0 }) => {
      if (live.length >= MAX && !featured) return
      live.push({
        x, y, featured,
        label: String(item.label || 'Uncategorised').slice(0, 18),
        amount: amountText(item.paise) || '',
        vx: breeze + push + (Math.random() - 0.5) * 14,
        vy: featured ? 4 : 8 + Math.random() * 10,
        rot: (Math.random() - 0.5) * 0.9,
        spin: (Math.random() - 0.5) * 0.6,
        phase: Math.random() * Math.PI * 2,
        flipRate: 1.6 + Math.random() * 2.2,
        swayAmp: 18 + Math.random() * 22,
        swayFreq: 1.1 + Math.random() * 1.3,
        t: 0, alpha: 0, settled: 0,
      })
    }

    const leafPoint = (near) => {
      let pick = LEAVES[Math.floor(Math.random() * LEAVES.length)]
      if (near) {
        let best = Infinity
        for (const p of LEAVES) {
          const dx = box.x + p[0] * box.w - near.x
          const dy = box.y + p[1] * box.h - near.y
          const d = dx * dx + dy * dy + Math.random() * 400
          if (d < best) { best = d; pick = p }
        }
      }
      return { x: box.x + pick[0] * box.w, y: box.y + pick[1] * box.h }
    }

    const groundY = () => box.y + GROUND * box.h

    const seedMote = (m = {}, anywhere = true) => {
      m.x = box.x + Math.random() * box.w
      m.y = anywhere ? box.y + Math.random() * box.h * 0.8 : box.y + box.h * (0.66 + Math.random() * 0.1)
      m.vy = -(5 + Math.random() * 9)
      m.wob = 8 + Math.random() * 16
      m.freq = 0.3 + Math.random() * 0.5
      m.t = Math.random() * 10
      m.r = 1.2 + Math.random() * 2.6
      m.star = Math.random() < 0.3
      m.green = !m.star && Math.random() < 0.4
      m.tw = 0.8 + Math.random() * 1.6
      m.rot = Math.random() * Math.PI
      return m
    }

    const step = (dt) => {
      // the breeze: a gust swells, peaks and dies away; it sways the tree and
      // carries loose bills sideways before they fall
      if (atmosphere) {
        nextGust -= dt
        if (!gust && nextGust <= 0) {
          gust = { t: 0, len: 2.6 + Math.random() * 1.4, peak: (breeze ? Math.sign(breeze) : (Math.random() < 0.5 ? -1 : 1)) * (70 + Math.random() * 50) }
          for (let i = 0; i < 3; i += 1) {
            const p = leafPoint()
            spawn({ ...p, item: nextItem(), push: gust.peak * 0.4 })
          }
        }
        if (gust) {
          gust.t += dt
          const k = gust.t / gust.len
          wind = breeze + gust.peak * Math.sin(Math.min(1, k) * Math.PI)
          if (k >= 1) { gust = null; wind = breeze; nextGust = 7 + Math.random() * 6 }
        }
        img.style.setProperty('--mt-sway', `${((wind - breeze) / 120) * 1.1}deg`)
      }

      if (MOTES) {
        while (motes.length < MOTES) motes.push(seedMote())
        for (const m of motes) {
          m.t += dt
          m.x += (Math.sin(m.t * m.freq) * m.wob + wind * 0.5) * dt
          m.y += m.vy * dt
          m.rot += dt * 0.6
          if (m.y < box.y - 10 || m.x < -20 || m.x > W + 20) seedMote(m, false)
        }
      }

      // `drops={false}`: no bills fall on their own (a new account's empty
      // ledger: example spends there could be mistaken for real ones)
      spawnClock += dt
      if (drops && spawnClock >= every) {
        spawnClock = 0
        spawn({ ...leafPoint(), item: nextItem() })
      }

      for (let i = sparks.length - 1; i >= 0; i -= 1) {
        const p = sparks[i]
        p.t += dt
        p.x += p.vx * dt
        p.y += p.vy * dt
        p.vy += 60 * dt
        p.rot += dt * 2
        p.alpha = Math.max(0, 1 - p.t / 0.9)
        if (p.alpha <= 0) sparks.splice(i, 1)
      }

      const floor = groundY()
      for (let i = live.length - 1; i >= 0; i -= 1) {
        const b = live[i]
        b.t += dt
        if (b.settled) {
          b.settled += dt
          b.alpha = Math.max(0, Math.min(1, 1 - (b.settled - (b.featured ? 2.2 : 0.4)) / 0.9))
          if (b.alpha <= 0) live.splice(i, 1)
          continue
        }
        b.alpha = Math.min(1, b.alpha + dt * 4)
        b.vy = Math.min(b.featured ? 38 : 52, b.vy + 40 * dt)
        b.vx += (wind - b.vx) * 1.4 * dt
        b.x += (b.vx + Math.sin(b.t * b.swayFreq) * b.swayAmp) * dt
        b.y += b.vy * dt
        b.rot += b.spin * dt + Math.sin(b.t * b.swayFreq) * 0.4 * dt
        b.phase += b.flipRate * dt
        if (b.y >= floor - 6) {
          b.y = floor - 6
          b.settled = 0.0001
          b.phase = 0
          b.rot *= 0.4
          if (b.featured) {
            // the landing of a just-logged expense: a burst of poster sparks
            for (let k = 0; k < 7; k += 1) {
              const a = (k / 7) * Math.PI * 2 + Math.random() * 0.4
              sparks.push({ x: b.x, y: b.y, vx: Math.cos(a) * (60 + Math.random() * 60),
                            vy: Math.sin(a) * (40 + Math.random() * 40) - 30,
                            r: 5 + Math.random() * 6, rot: Math.random(), t: 0, alpha: 1 })
            }
          }
        }
        if (b.x < -80 || b.x > W + 80) live.splice(i, 1)
      }
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H)
      for (const m of motes) {
        // fade in from the ground, out toward the top, and twinkle
        const k = (m.y - box.y) / (box.h * 0.8)
        const a = Math.max(0, Math.min(1, k * 3, (1 - k) * 4 + 0.6)) * (0.45 + 0.55 * Math.abs(Math.sin(m.t * m.tw)))
        if (m.star && !dust) {
          drawSpark(ctx, { x: m.x, y: m.y, r: m.r * 2.4, rot: m.rot, alpha: a * 0.85 }, pal.ink)
        } else {
          ctx.globalAlpha = a * 0.7
          ctx.fillStyle = dust ? pal.dust : m.green ? pal.leaf : pal.ink
          ctx.beginPath()
          ctx.arc(m.x, m.y, m.r, 0, Math.PI * 2)
          ctx.fill()
          ctx.globalAlpha = 1
        }
      }
      const k = billScale(box.w)
      for (const b of live) {
        // a bill blown toward the edge of the canvas fades out rather than
        // being cut in half by it
        const edge = Math.max(0, Math.min(1, (Math.min(b.x, W - b.x) - 18) / 50))
        if (edge <= 0) continue
        const a = b.alpha
        b.alpha = a * edge
        drawBill(ctx, b, pal, sprite, k)
        b.alpha = a
      }
      for (const p of sparks) drawSpark(ctx, p, pal.ink)
    }

    const frame = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000 || 0)
      last = now
      step(dt)
      draw()
      raf = requestAnimationFrame(frame)
    }

    const start = () => {
      if (running || reduced || !visible || !pageVisible) return
      running = true
      last = performance.now()
      raf = requestAnimationFrame(frame)
    }
    const stop = () => {
      running = false
      cancelAnimationFrame(raf)
    }

    measure()
    const ro = new ResizeObserver(() => { measure(); if (!running) draw() })
    ro.observe(root)
    img.addEventListener('load', measure)

    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      if (visible) start(); else stop()
    })
    io.observe(root)

    const onVis = () => { pageVisible = !document.hidden; if (pageVisible) start(); else stop() }
    document.addEventListener('visibilitychange', onVis)

    // Theme and motion preferences can change while the tree is on screen.
    const motionMq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const onMotion = () => {
      reduced = alwaysMove ? false : prefersReducedMotion()
      if (reduced) { stop(); live.length = 0; motes.length = 0; ctx.clearRect(0, 0, W, H) } else start()
    }
    motionMq.addEventListener?.('change', onMotion)
    const themeMo = new MutationObserver(() => { pal = readPalette(root) })
    themeMo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    const schemeMq = window.matchMedia('(prefers-color-scheme: dark)')
    const onScheme = () => { pal = readPalette(root) }
    schemeMq.addEventListener?.('change', onScheme)

    // Brushing the canopy shakes bills loose, from the leaves nearest the pointer.
    let lastPt = null; let travelled = 0
    const onMove = (e) => {
      if (reduced) return
      const r = root.getBoundingClientRect()
      const pt = { x: e.clientX - r.left, y: e.clientY - r.top }
      const inCanopy = pt.x >= box.x && pt.x <= box.x + box.w
        && pt.y >= box.y && pt.y <= box.y + CANOPY_BOTTOM * box.h
      if (lastPt && inCanopy) {
        const dx = pt.x - lastPt.x
        travelled += Math.hypot(dx, pt.y - lastPt.y)
        if (travelled > 60) {
          travelled = 0
          spawn({ ...leafPoint(pt), item: nextItem(), push: Math.max(-60, Math.min(60, dx * 3)) })
        }
      }
      lastPt = pt
    }
    const onLeave = () => { lastPt = null; travelled = 0 }
    root.addEventListener('pointermove', onMove)
    root.addEventListener('pointerleave', onLeave)

    // Fonts first, or the first bills are written in the fallback face.
    document.fonts?.ready.then(() => { if (!running) draw() })

    api.current = {
      drop(item) {
        if (reduced) return
        const p = leafPoint({ x: box.x + box.w * 0.5, y: box.y })
        spawn({ ...p, item, featured: true })
        start()
      },
    }
    start()

    return () => {
      stop()
      ro.disconnect()
      io.disconnect()
      themeMo.disconnect()
      img.removeEventListener('load', measure)
      document.removeEventListener('visibilitychange', onVis)
      motionMq.removeEventListener?.('change', onMotion)
      schemeMq.removeEventListener?.('change', onScheme)
      root.removeEventListener('pointermove', onMove)
      root.removeEventListener('pointerleave', onLeave)
      api.current = null
    }
  }, [variant, atmosphere, dust, breeze, alwaysMove, drops])

  // A drop request is played once, even if it arrived before the tree mounted.
  const played = useRef(null)
  useEffect(() => {
    if (!dropRequest || played.current === dropRequest.id) return
    played.current = dropRequest.id
    // after the mount effect has set the canvas up
    const id = requestAnimationFrame(() => api.current?.drop(dropRequest))
    return () => cancelAnimationFrame(id)
  }, [dropRequest])

  return (
    <div ref={rootRef} className={`mt mt-${variant}${atmosphere ? ' mt-atmos' : ''} ${className}`.trim()}>
      {orbits && (
        <svg className="mt-orbits" viewBox="0 0 1000 1000" aria-hidden="true" focusable="false">
          <g className="mt-orbit mt-orbit-a">
            <ellipse cx="500" cy="380" rx="470" ry="150" />
          </g>
          <g className="mt-orbit mt-orbit-b">
            <ellipse cx="500" cy="380" rx="430" ry="210" strokeDasharray="2 10" />
          </g>
          <g className="mt-orbit mt-orbit-c">
            <ellipse cx="500" cy="380" rx="490" ry="96" strokeDasharray="1 7" />
          </g>
          {[[150, 230, 0], [830, 250, 1], [740, 110, 2], [230, 540, 3], [905, 470, 4], [400, 70, 5]].map(([x, y, i]) => (
            <path key={i} className={`mt-spark mt-spark-${i}`}
                  d={`M${x} ${y - 22}L${x + 4} ${y - 4}L${x + 22} ${y}L${x + 4} ${y + 4}L${x} ${y + 22}L${x - 4} ${y + 4}L${x - 22} ${y}L${x - 4} ${y - 4}Z`} />
          ))}
        </svg>
      )}
      <div className="mt-stage">
        <img ref={imgRef} className="mt-tree" src={TREE_SRC} alt={alt}
             width="1200" height="1200" decoding="async"
             fetchPriority={variant === 'landing' ? 'high' : 'auto'} draggable="false" />
        {ground && <div className="mt-ground" aria-hidden="true" />}
        {mist && (
          <div className="mt-mist" aria-hidden="true">
            <span className="mt-mist-a" /><span className="mt-mist-b" /><span className="mt-mist-c" />
          </div>
        )}
      </div>
      <canvas ref={canvasRef} className="mt-bills" aria-hidden="true" />
    </div>
  )
}
