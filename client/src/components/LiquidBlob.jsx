import { useEffect, useRef, useState } from 'react'

/**
 * One slow, organic orb of liquid metal — molten emerald with gold where the
 * light catches it — whose surface ripples like water.
 * The system's ONE hand-written shader (SW-ADR-016 allows one). WebGL 1, a
 * single full-screen triangle, no textures, no library.
 *
 *   <LiquidBlob />                          fixed behind the whole page
 *   <LiquidBlob x={0.5} y={0.42} size={0.9} />
 *   <LiquidBlob contained />                fills its nearest positioned parent
 *
 * Props
 *   x, y        the blob's centre as a fraction of the layer (default 0.5, 0.45)
 *   size        radius as a fraction of half the layer's shorter side (default 0.85)
 *   contained   absolute inside the parent instead of fixed to the viewport
 *   ripple      pointer moves drop a ripple into the surface (default true;
 *               fine pointers only, never under reduced motion)
 *   className   extra classes on the wrapper
 *
 * Contrast safety (DESIGN-SYSTEM.md §2.4). Every pixel the shader writes is a
 * CONVEX mix of the three orb tokens (--sw-orb-deep, --sw-orb-emerald,
 * --sw-orb-gold), at alpha <= 1, and the wrapper's CSS opacity is
 * --sw-orb-opacity. Luminance over that hull is extremal at the
 * pure stops (checked), and those stops at that opacity are exactly what the
 * worst-case contrast table composites under the glass. The one exception —
 * a white specular glint — is drawn ONLY when the theme is light, where a
 * lighter ground can only raise the contrast of dark ink.
 *
 * Cost. Drawn at 3/4 resolution inside a hero stage, half resolution when
 * fixed behind a page (capped at 960px on the long side), at 30fps,
 * and NOT drawn at all while: the tab is hidden, the layer is off screen, or
 * the person prefers reduced motion (then exactly one still frame is drawn).
 * Colours are read from the tokens, and re-read when the theme changes.
 * Placement: put ONE <LiquidBlob contained /> inside a positioned wrapper
 * directly behind the bank card (login hero, dashboard hero), or one fixed
 * <LiquidBlob /> per page. Never two running at once.
 * No WebGL, or a lost context: a still CSS blob from the same tokens.
 */
const VERT = `
attribute vec2 a;
void main() { gl_Position = vec4(a, 0.0, 1.0); }
`

/* NO unbounded time reaches the GPU. On GPUs that really run mediump as fp16
   (many phones), a clock in the hundreds of seconds turns sin(x - t*k) and the
   noise offsets into steps within minutes. So JS (in doubles) hands over:
     uPhase  four wave phases, already wrapped to [0, 2pi)
     uDrift  two noise offsets moving slowly round circles of radius 3
             (periodic, so nothing ever wraps or jumps)
     uWob    the outline's offset, the same way
   and highp is used wherever the fragment stage has it. */
const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec2 uRes;
uniform vec4 uPhase;
uniform vec4 uDrift;
uniform vec2 uWob;
uniform vec3 uC1;
uniform vec3 uC2;
uniform vec3 uC3;
uniform float uSpec;
uniform vec2 uCenter;
uniform float uScale;
uniform vec3 uDrop0;
uniform vec3 uDrop1;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
             mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 4; i++) { v += a * noise(p); p *= 2.03; a *= 0.5; }
  return v;
}

/* The metal ramp: deep emerald in shadow, emerald in the body, gold on the
   faces that catch the light. Always a convex mix of two adjacent stops. */
vec3 metal(float t) {
  t = clamp(t, 0.0, 1.0);
  if (t < 0.6) return mix(uC1, uC2, smoothstep(0.0, 0.6, t));
  return mix(uC2, uC3, smoothstep(0.6, 1.0, t));
}

/* One pointer drop: a ring that travels out and decays on its own clock. */
float drop(vec3 dr, vec2 p) {
  float age = dr.z;
  if (age >= 4.0) return 0.0;
  float d = length(p - dr.xy);
  return sin(d * 28.0 - age * 8.0) * exp(-age * 1.1) * exp(-d * 2.6) * 1.1;
}

/* The water surface: a height field of slow swells plus the pointer drops. */
float height(vec2 q, vec2 p) {
  float h = sin(length(q) * 16.0 - uPhase.x) * 0.45;
  h += sin(dot(q, vec2(0.8, 0.6)) * 10.0 + uPhase.y) * 0.30;
  h += sin(dot(q, vec2(-0.5, 0.9)) * 13.0 - uPhase.z) * 0.20;
  return h + drop(uDrop0, p) + drop(uDrop1, p);
}

void main() {
  float unit = min(uRes.x, uRes.y) * 0.5 * uScale;
  vec2 p = (gl_FragCoord.xy - uCenter * uRes) / unit;

  /* slow domain warp: the organic drift */
  vec2 w = vec2(fbm(p * 0.9 + uDrift.xy), fbm(p * 0.9 + uDrift.zw + 3.1)) - 0.5;
  vec2 q = p + w * 0.38;

  /* the outline: a circle whose radius wobbles with angle */
  float ang = atan(q.y, q.x);
  float wob = fbm(vec2(cos(ang), sin(ang)) * 1.4 + uWob) - 0.5;
  float d = length(q) - (0.70 + 0.22 * wob);
  float alpha = 1.0 - smoothstep(-0.20, 0.02, d);
  if (alpha <= 0.002) { gl_FragColor = vec4(0.0); return; }

  /* surface normal by central differences on the height field */
  float e = 0.01;
  float hx = height(q + vec2(e, 0.0), p) - height(q - vec2(e, 0.0), p);
  float hy = height(q + vec2(0.0, e), p) - height(q - vec2(0.0, e), p);
  vec3 n = normalize(vec3(-hx * 0.9, -hy * 0.9, 2.0 * e * 8.0));

  /* molten metal: lit faces and the fresnel rim go to gold, the core and the
     shadow side stay deep emerald. A slow flow term keeps it alive. */
  vec3 L = normalize(vec3(-0.45, 0.6, 0.66));
  float rim = pow(clamp(length(q) / 0.92, 0.0, 1.0), 3.0);
  float lit = 0.5 + 0.5 * dot(n, L);
  float flow = 0.08 * sin(uPhase.w + w.y * 6.0);
  /* The floor of the ramp is lifted off the deepest stop, so the shadow side
     reads as dark metal rather than a hole in it. */
  vec3 col = metal(0.20 + 0.56 * lit * lit + 0.36 * rim + flow);

  /* a glint, light theme only (see the contrast note in the JSX) */
  vec3 R = reflect(-L, n);
  float s = pow(max(R.z, 0.0), 28.0) * uSpec;
  col = mix(col, vec3(1.0), clamp(s * 0.55, 0.0, 0.55));

  gl_FragColor = vec4(col * alpha, alpha);
}
`

function readColour(name) {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  const hex = raw.replace('#', '')
  if (/^[0-9a-f]{6}$/i.test(hex)) {
    return [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  }
  const m = raw.match(/[\d.]+/g)
  return m ? m.slice(0, 3).map((v) => Number(v) / 255) : [0.17, 0.83, 0.6]
}

/** Light or dark, decided by the paper token itself — no second theme switch. */
function isLightTheme() {
  const [r, g, b] = readColour('--sw-paper')
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.5
}

function compile(gl, type, src) {
  const s = gl.createShader(type)
  gl.shaderSource(s, src)
  gl.compileShader(s)
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(s)
    gl.deleteShader(s)
    throw new Error(log || 'shader compile failed')
  }
  return s
}

export default function LiquidBlob({
  x = 0.5,
  y = 0.45,
  size = 0.85,
  contained = false,
  ripple = true,
  className = '',
}) {
  const wrapRef = useRef(null)
  const canvasRef = useRef(null)
  const [isStatic, setStatic] = useState(false)

  useEffect(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return undefined

    const gl = canvas.getContext('webgl', {
      alpha: true, premultipliedAlpha: true, antialias: false, depth: false,
      stencil: false, preserveDrawingBuffer: false, powerPreference: 'low-power',
    })
    if (!gl) { setStatic(true); return undefined }

    let program
    try {
      program = gl.createProgram()
      gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, VERT))
      gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, FRAG))
      gl.linkProgram(program)
      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error('link failed')
    } catch {
      setStatic(true)
      return undefined
    }
    gl.useProgram(program)

    // One triangle that covers the viewport.
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    const loc = gl.getAttribLocation(program, 'a')
    gl.enableVertexAttribArray(loc)
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)

    const U = {}
    for (const n of ['uRes', 'uPhase', 'uDrift', 'uWob', 'uC1', 'uC2', 'uC3', 'uSpec',
                     'uCenter', 'uScale', 'uDrop0', 'uDrop1']) {
      U[n] = gl.getUniformLocation(program, n)
    }

    const reducedMq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const fineMq = window.matchMedia('(hover: hover) and (pointer: fine)')
    const darkMq = window.matchMedia('(prefers-color-scheme: dark)')

    const applyColours = () => {
      gl.uniform3fv(U.uC1, readColour('--sw-orb-deep'))
      gl.uniform3fv(U.uC2, readColour('--sw-orb-emerald'))
      gl.uniform3fv(U.uC3, readColour('--sw-orb-gold'))
      gl.uniform1f(U.uSpec, isLightTheme() ? 1 : 0)
    }

    // A contained orb is a few hundred pixels: drawn closer to full size it
    // reads as metal, not as a smudge upscaled 2x. The page-wide one stays at half.
    const SCALE = contained ? 0.75 : 0.5
    const MAX_SIDE = 960
    // Orb geometry in CSS px: the centre as a fraction of the layer, and the
    // shader's `unit` (one unit of p). Props by default; on a hero stage the
    // screen sheet's --orb-r / --orb-dx / --orb-dy win (glass.css §15).
    // EDGE: the outline's mean radius in units (0.70 + the 0.02 smoothstep
    // tail). EXTENT: how far the wobble (±0.11) and the domain warp can push
    // it in the worst case (~1.0). The radius is capped so the full extent
    // fits the layer, so the canvas edge never cuts the orb.
    const EDGE = 0.72
    const EXTENT = 1.0
    const geom = { cx: x, cy: y, unit: 1 }
    const measureGeom = (W, H) => {
      const cs = getComputedStyle(wrap)
      const want = parseFloat(cs.getPropertyValue('--orb-r'))
      if (contained && Number.isFinite(want) && want > 0) {
        const dx = parseFloat(cs.getPropertyValue('--orb-dx')) || 0
        const dy = parseFloat(cs.getPropertyValue('--orb-dy')) || 0
        const fit = Math.min((W / 2 - Math.abs(dx)), (H / 2 - Math.abs(dy))) * EDGE / EXTENT
        const R = Math.max(1, Math.min(want, fit))
        geom.cx = (W / 2 + dx) / Math.max(W, 1)
        geom.cy = (H / 2 + dy) / Math.max(H, 1)
        geom.unit = R / EDGE
      } else {
        geom.cx = x
        geom.cy = y
        geom.unit = Math.max(1, Math.min(W, H) * 0.5 * size)
      }
    }
    const resize = () => {
      const r = wrap.getBoundingClientRect()
      const k = Math.min(SCALE, MAX_SIDE / Math.max(r.width, r.height, 1))
      const w = Math.max(1, Math.round(r.width * k))
      const h = Math.max(1, Math.round(r.height * k))
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w
        canvas.height = h
        gl.viewport(0, 0, w, h)
      }
      gl.uniform2f(U.uRes, w, h)
      measureGeom(r.width, r.height)
      gl.uniform2f(U.uCenter, geom.cx, 1 - geom.cy)   // GL's y grows upward
      // The shader's unit is min(res)*0.5*uScale, in canvas pixels.
      gl.uniform1f(U.uScale, (geom.unit * (w / Math.max(r.width, 1))) / (Math.min(w, h) * 0.5))
    }

    gl.uniform3f(U.uDrop0, 0, 0, 99)
    gl.uniform3f(U.uDrop1, 0, 0, 99)
    applyColours()
    resize()

    // Start somewhere along the loop, so a reload is not the same frame.
    const epoch = performance.now() - Math.random() * 20000
    // Two drop slots, used in turn, so a new ring never cuts off the last one.
    const drops = [{ x: 0, y: 0, at: -1e9 }, { x: 0, y: 0, at: -1e9 }]
    let slot = 0
    let frame = 0
    let last = 0
    let visible = true
    let lost = false

    const TAU = Math.PI * 2
    const draw = (now) => {
      const t = (now - epoch) / 1000   // a double: wrapped here, never on the GPU
      gl.uniform4f(U.uPhase, (t * 1.3) % TAU, (t * 0.9) % TAU, (t * 1.1) % TAU, (t * 0.21) % TAU)
      // Radius 3, so these move at ~0.030, ~0.027 and ~0.045 units/s: the
      // speeds the original linear drift had, on paths that never run out.
      const a = t * 0.010
      const b = t * 0.009 + 1.0
      const c = t * 0.015 + 2.0
      gl.uniform4f(U.uDrift, 3 * Math.cos(a), 3 * Math.sin(a), 3 * Math.cos(b), 3 * Math.sin(b))
      gl.uniform2f(U.uWob, 3 * Math.cos(c), 3 * Math.sin(c))
      for (const [i, d] of drops.entries()) {
        gl.uniform3f(i ? U.uDrop1 : U.uDrop0, d.x, d.y, Math.min((now - d.at) / 1000, 99))
      }
      gl.clearColor(0, 0, 0, 0)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.drawArrays(gl.TRIANGLES, 0, 3)
    }

    const running = () => visible && !document.hidden && !reducedMq.matches && !lost

    // 30fps, paced against the IDEAL schedule rather than the last frame. On
    // a 60Hz display rAF stamps jitter around 16.67ms; a strict `>= 33.33`
    // test skips the frame that lands at 33.2ms and leaves a 50ms gap, so
    // the spacing wobbles between 33 and 50ms. A 4ms tolerance plus advancing
    // `last` by whole intervals keeps every gap at two refreshes.
    const IV = 1000 / 30
    const loop = (now) => {
      frame = 0
      if (!running()) return
      const since = now - last
      if (since >= IV - 4) {
        last = since > IV * 2 ? now : last + IV
        draw(now)
      }
      frame = requestAnimationFrame(loop)
    }
    const kick = () => {
      if (lost) return
      if (running()) { if (!frame) frame = requestAnimationFrame(loop) }
      else if (reducedMq.matches) draw(epoch + 6000)   // one still frame
    }

    const io = new IntersectionObserver((entries) => {
      visible = entries.some((e) => e.isIntersecting)
      kick()
    })
    io.observe(wrap)

    const ro = new ResizeObserver(() => { resize(); if (!running()) kick() })
    ro.observe(wrap)

    const onTheme = () => { applyColours(); resize(); if (!running()) kick() }
    const mo = new MutationObserver(onTheme)
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    darkMq.addEventListener('change', onTheme)
    reducedMq.addEventListener('change', kick)
    document.addEventListener('visibilitychange', kick)

    // A pointer move drops a ripple, fine pointers only. Two slots in turn,
    // at most one new drop every 1.1s, so a slot is reused only after 2.2s,
    // when its ring is down to ~9% (exp(-2.2 * 1.1)) and fades out instead of
    // vanishing mid-wave.
    const onPointer = (e) => {
      if (!ripple || !fineMq.matches || reducedMq.matches || e.pointerType === 'touch') return
      const now = performance.now()
      if (now - drops[slot ^ 1].at < 1100) return
      const r = wrap.getBoundingClientRect()
      drops[slot] = {
        x: (e.clientX - r.left - geom.cx * r.width) / geom.unit,
        y: -((e.clientY - r.top) - geom.cy * r.height) / geom.unit,
        at: now,
      }
      slot ^= 1
    }
    window.addEventListener('pointermove', onPointer, { passive: true })

    const onLost = (e) => { e.preventDefault(); lost = true; setStatic(true) }
    canvas.addEventListener('webglcontextlost', onLost)

    kick()

    return () => {
      if (frame) cancelAnimationFrame(frame)
      io.disconnect()
      ro.disconnect()
      mo.disconnect()
      darkMq.removeEventListener('change', onTheme)
      reducedMq.removeEventListener('change', kick)
      document.removeEventListener('visibilitychange', kick)
      window.removeEventListener('pointermove', onPointer)
      canvas.removeEventListener('webglcontextlost', onLost)
      gl.deleteBuffer(buf)
      gl.deleteProgram(program)
    }
  }, [x, y, size, ripple, contained])

  return (
    <div
      ref={wrapRef}
      className={`sw-blob ${className}`.trim()}
      aria-hidden="true"
      data-contained={contained ? '' : undefined}
      data-static={isStatic ? '' : undefined}
      // Contained, the orb is measured from its own (square) box; fixed, from the viewport.
      style={{ '--blob-x': x, '--blob-y': y, '--blob-r': contained ? `${size * 50}%` : `${size * 50}vmin` }}
    >
      {!isStatic && <canvas ref={canvasRef} />}
    </div>
  )
}
