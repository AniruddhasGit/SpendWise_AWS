import { useEffect, useRef } from 'react'

/**
 * Ground fog for the landing scene (SW-ADR-159).
 *
 * The owner's sketch and reference (2026-10-21): fog that starts where the
 * trunk meets the ground and carries on, a sea of it, down to the bottom of
 * the first screen, so the scene reads as a 3D world seen from a raised
 * camera. A bright, dense band lies along the ground line with smoke curling
 * up off its top; below it the fog is dimmer and softer. A steady wind blows
 * right to left.
 *
 * The fog is one real texture (`/assets/fog/ground-fog.jpg`, made with Runway;
 * provenance beside it), grey on black. It is tinted once into the dusk fog
 * ink with its brightness as alpha, then tiled across the screen, every other
 * tile mirrored so the joins never show. Two layers drift at different speeds
 * for depth. Positions move by sub-pixel amounts on a time base, never
 * stepped, so the drift is smooth. It pauses off screen and in hidden tabs,
 * and the scene clips it to the first screen. It moves whatever the motion
 * preference: the owner's ruling for the signed-out scene (SW-ADR-160).
 *
 * `layer`: 'front' (over the tree, thinned over the trunk) or 'back' (behind
 * the tree, so the trunk rises out of the fog). `floor` and `stage` are
 * selectors: the band sits on the floor's top edge, and its size follows the
 * tree's height (a sixth of it).
 */
const SRC = '/assets/fog/ground-fog.jpg'
// where the fog surface starts in the texture (its soft far edge), as a
// fraction of the texture's height; below that it fills to the bottom
const FAR_EDGE = 0.22

function tint(img, colour) {
  const c = document.createElement('canvas')
  c.width = img.naturalWidth
  c.height = img.naturalHeight
  const g = c.getContext('2d')
  g.drawImage(img, 0, 0)
  const data = g.getImageData(0, 0, c.width, c.height)
  const px = data.data
  const [r, gr, b] = colour.split(/\s+/).map(Number)
  const w = c.width; const h = c.height
  // its top and sides of the far edge fade to nothing, so no layer ends on a
  // straight line; the bottom stays full, the nearest fog is the densest
  const ramp = (y) => {
    const top = Math.min(1, Math.max(0, (y - h * (FAR_EDGE - 0.12)) / (h * 0.2)))
    const bottom = 1
    const v = Math.min(top, bottom)
    return v * v * (3 - 2 * v)
  }
  for (let i = 0; i < px.length; i += 4) {
    const lum = (px[i] / 255) * ramp(Math.floor(i / 4 / w))
    px[i] = r; px[i + 1] = gr; px[i + 2] = b
    px[i + 3] = Math.round(255 * Math.min(1, lum * 1.15))
  }
  g.putImageData(data, 0, 0)
  // a mirrored copy, so tiles can alternate and the joins match
  const m = document.createElement('canvas')
  m.width = c.width
  m.height = c.height
  const mg = m.getContext('2d')
  mg.translate(c.width, 0)
  mg.scale(-1, 1)
  mg.drawImage(c, 0, 0)
  return [c, m]
}

export default function Fog({ ground: groundDefault = 0.72, floor = null, stage = null,
                              layer = 'front', scene = 'dark', pool = false, className = '' }) {
  const ref = useRef(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return undefined
    const ctx = canvas.getContext('2d')
    if (!ctx) return undefined
    let colour = getComputedStyle(canvas).getPropertyValue('--sw-dusk-fog').trim() || '220 228 220'
    const SCALE = 0.6
    let W = 1; let H = 1
    let ground = groundDefault
    let span = 60
    let trunkX = 0.5; let stageW = 600
    let tiles = null
    let raf = 0; let last = 0; let t = 0; let running = false; let visible = true
    let pageVisible = !document.hidden
    let fadeIn = 0

    const measure = () => {
      const r = canvas.getBoundingClientRect()
      W = Math.max(1, r.width); H = Math.max(1, r.height)
      // a selector may name the canvas's own parent (the sign-in page's tree box)
      const find = (sel) => {
        const p = canvas.parentElement
        return sel && p ? (p.matches(sel) ? p : p.querySelector(sel)) : null
      }
      const el = find(floor)
      if (el) ground = Math.min(0.95, Math.max(0.3, (el.getBoundingClientRect().top - r.top) / H))
      trunkX = W / 2
      const st = find(stage)
      if (st) {
        const sr = st.getBoundingClientRect()
        span = Math.max(16, (el ? el.getBoundingClientRect().top - sr.top : sr.height * 0.715) / 6)
        trunkX = sr.left - r.left + sr.width / 2
        stageW = sr.width
        // no floor element (the sign-in page): the tree picture's own ground
        // line, 71.5% down its box (MoneyTree's GROUND)
        if (!el) ground = Math.min(0.95, Math.max(0.1, (sr.top - r.top + sr.height * 0.715) / H))
      } else {
        span = H * 0.08
      }
      canvas.width = Math.round(W * SCALE)
      canvas.height = Math.round(H * SCALE)
      ctx.setTransform(SCALE, 0, 0, SCALE, 0, 0)
      strips.clear()
    }

    // A strip of mirrored tiles, joined ONCE on an offscreen canvas at whole
    // pixels (no gap, no overlap: on see-through fog either shows as a line),
    // then slid as one image by fractional amounts, so the drift stays smooth.
    // Built per size and kept until the next resize.
    const strips = new Map()
    const buildStrip = (sx, sw, dh) => {
      const key = `${sx}|${sw}|${Math.round(dh)}`
      if (strips.has(key)) return strips.get(key)
      const [a, b] = tiles
      const tilePx = Math.max(1, Math.round(dh * (sw / a.height) * SCALE))
      const hPx = Math.max(1, Math.round(dh * SCALE))
      const count = Math.ceil((W * SCALE) / tilePx) + 3
      const c = document.createElement('canvas')
      c.width = tilePx * (count + (count % 2))
      c.height = hPx
      const g = c.getContext('2d')
      for (let i = 0; i * tilePx < c.width; i += 1) {
        g.drawImage(i % 2 ? b : a, i % 2 ? a.width - sx - sw : sx, 0, sw, a.height, i * tilePx, 0, tilePx, hPx)
      }
      const made = { c, period: (tilePx * 2) / SCALE }
      strips.set(key, made)
      return made
    }
    const strip = (sx, sw, dy, dh, offset, alpha) => {
      const { c, period } = buildStrip(sx, sw, dh)
      ctx.globalAlpha = alpha
      ctx.drawImage(c, -(offset % period), dy, c.width / SCALE, dh)
    }

    // `pool`: on the sign-in page the fog gathers round the tree's base only,
    // an oval that fades out at its edges
    const poolMask = (gy) => {
      if (!pool) return
      // A soft cloud, never a shape: the oval is sized to fit well inside the
      // canvas on every side, and its density falls to nothing long before
      // its rim, so no edge (and no canvas border) can ever show.
      const cy = Math.min(gy + span * 0.3, H * 0.62)
      const rx = Math.max(40, Math.min(stageW * 0.95, trunkX * 0.96, (W - trunkX) * 0.96))
      const ry = Math.max(24, Math.min(span * 3.6, cy * 0.95, (H - cy) * 0.95))
      ctx.save()
      ctx.globalAlpha = 1
      ctx.globalCompositeOperation = 'destination-in'
      ctx.translate(trunkX, cy)
      ctx.scale(1, ry / rx)
      const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rx)
      // a long, bell-shaped falloff: the fog thins out gradually and is all
      // but gone well before the rim, so it dissipates instead of ending
      for (let k = 0; k <= 12; k += 1) {
        const r = k / 12
        g.addColorStop(r, `rgb(0 0 0 / ${Math.exp(-4.2 * r * r) * (1 - r)})`)
      }
      ctx.fillStyle = g
      // clear everything outside the oval too (destination-in keeps only
      // what the fill covers)
      ctx.fillRect(-W * 4, -H * 4 * (rx / ry), W * 8, H * 8 * (rx / ry))
      ctx.restore()
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H)
      if (!tiles) return
      const [a] = tiles
      const iw = a.width; const ih = a.height
      const gy = H * ground
      const k = Math.min(1, fadeIn)
      // the fog is a surface lying on the ground: its soft far edge a little
      // above the line where the trunk meets the ground, its densest part at
      // the bottom of the screen. No band, no line (owner, 2026-10-21).
      const farY = gy - span * 0.8
      const hImg = (H - farY) / (1 - FAR_EDGE)
      const top = H - hImg
      const speed = (stageW / 600) * 12 // px a second
      // trim a few columns off each side: the texture's own edge columns are
      // a touch lighter, and would show as seams where the tiles meet
      const sx = Math.round(iw * 0.006); const sw = iw - sx * 2
      if (layer === 'back') {
        strip(sx, sw, top, hImg, t * speed, 0.8 * k)
        ctx.globalAlpha = 1
        poolMask(gy)
        return
      }
      // two passes of the same surface for depth: a fainter, larger one that
      // moves faster (nearer), under the main one
      strip(sx, sw, top + hImg * 0.08, hImg * 1.15, t * speed * 1.6 + 500, 0.35 * k)
      strip(sx, sw, top, hImg, t * speed, 0.9 * k)
      // thinner in front of the trunk, so the tree stays readable
      ctx.globalAlpha = 1
      ctx.globalCompositeOperation = 'destination-out'
      const rx = Math.max(40, stageW * 0.12)
      const g = ctx.createRadialGradient(trunkX, gy - span * 0.3, 0, trunkX, gy - span * 0.3, rx)
      g.addColorStop(0, 'rgb(0 0 0 / 0.5)')
      g.addColorStop(1, 'rgb(0 0 0 / 0)')
      ctx.fillStyle = g
      ctx.fillRect(trunkX - rx, gy - span * 0.3 - rx, rx * 2, rx * 2)
      ctx.globalCompositeOperation = 'source-over'
      poolMask(gy)
    }

    const frame = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000 || 0)
      last = now
      t += dt
      if (fadeIn < 1) fadeIn += dt / 1.2
      draw()
      raf = requestAnimationFrame(frame)
    }
    const start = () => {
      if (running || !visible || !pageVisible || !tiles) return
      running = true
      last = performance.now()
      raf = requestAnimationFrame(frame)
    }
    const stop = () => { running = false; cancelAnimationFrame(raf) }

    measure()
    const img = new Image()
    img.decoding = 'async'
    img.onload = () => {
      tiles = tint(img, colour)
      draw()
      start()
    }
    img.src = SRC
    // the app's theme can change under the dashboard's fog: re-tint it
    const themeMo = new MutationObserver(() => {
      const next = getComputedStyle(canvas).getPropertyValue('--sw-dusk-fog').trim() || '220 228 220'
      if (next === colour || !img.complete) return
      colour = next
      tiles = tint(img, colour)
      strips.clear()
      draw()
    })
    themeMo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    const ro = new ResizeObserver(() => { measure(); draw() })
    ro.observe(canvas)
    const io = new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible) start(); else stop() })
    io.observe(canvas)
    const onVis = () => { pageVisible = !document.hidden; if (pageVisible) start(); else stop() }
    document.addEventListener('visibilitychange', onVis)
    return () => {
      stop()
      img.onload = null
      themeMo.disconnect()
      ro.disconnect()
      io.disconnect()
      document.removeEventListener('visibilitychange', onVis)
    }
  }, [groundDefault, floor, stage, layer, scene, pool])

  return <canvas ref={ref} className={`fog ${className}`.trim()} aria-hidden="true" />
}
