import { useEffect, useRef } from 'react'
import { useFinePointer, usePrefersReducedMotion } from '../lib/motion.js'

/**
 * A surface that tilts toward the pointer in 3D, with a specular glare that
 * follows the cursor. Decorative, so it is gated hard:
 *
 *   - only a real hovering pointer (mouse / pen): `(hover: hover) and
 *     (pointer: fine)`. Touch never tilts; a tap must not leave a card askew.
 *   - never under reduced motion.
 *   - never from the keyboard: focus does not tilt, and nothing about layout,
 *     focus order or the accessible tree changes. The glare is aria-hidden.
 *
 * Feel: while the pointer moves, `transform` follows on a 180ms ease-out
 * TRANSITION, so each move retargets from wherever the card is (interruptible).
 * On leave it returns on `--sw-spring` (a computed damped spring, 650ms).
 * Writes go straight to the element's `style.transform`, at most once per
 * frame — never through a custom property on a parent.
 *
 *   <TiltCard className="card card-hero" data-testid="headline">…</TiltCard>
 *   <TiltCard as="section" className="gate-card" max={4}>…</TiltCard>
 *
 * Props
 *   as        element type, default 'div'
 *   max       maximum tilt in degrees, default 6 (the system's ceiling)
 *   glare     draw the specular highlight, default true
 *   lift      scale while hovered, default 1.01
 *   className, children, and any other prop (data-testid, aria-*, id, role…)
 *             are passed to the element unchanged.
 *
 * The element gets `.sw-tilt` and `position: relative`. It becomes a stacking
 * context while tilted, so do not put a `position: fixed` child inside one.
 */
export default function TiltCard({
  as: Tag = 'div',
  max = 6,
  glare = true,
  lift = 1.01,
  className = '',
  children,
  ...rest
}) {
  const ref = useRef(null)
  const glareRef = useRef(null)
  const fine = useFinePointer()
  const reduced = usePrefersReducedMotion()
  const enabled = fine && !reduced

  useEffect(() => {
    const el = ref.current
    if (!el || !enabled) return undefined

    let frame = 0
    let pending = null
    let rect = null
    let half = 0          // half the glare's width, measured with the rect
    const measure = () => {
      rect = el.getBoundingClientRect()
      half = (glareRef.current?.offsetWidth ?? 0) / 2
    }

    const paint = () => {
      frame = 0
      if (!pending || !rect) return
      const { x, y } = pending
      const px = (x - rect.left) / rect.width    // 0..1
      const py = (y - rect.top) / rect.height
      const ry = (px - 0.5) * 2 * max            // left/right -> rotateY
      const rx = (0.5 - py) * 2 * max            // up/down    -> rotateX
      el.style.transform =
        `perspective(1000px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) scale(${lift})`
      const g = glareRef.current
      if (g) {
        g.style.transform =
          `translate(${(x - rect.left - half).toFixed(1)}px, ${(y - rect.top - half).toFixed(1)}px)`
      }
    }

    const onEnter = (e) => {
      if (e.pointerType === 'touch') return
      measure()
      el.setAttribute('data-tilting', '')
    }
    const onMove = (e) => {
      if (e.pointerType === 'touch') return
      if (!rect) measure()
      if (!el.hasAttribute('data-tilting')) el.setAttribute('data-tilting', '')
      pending = { x: e.clientX, y: e.clientY }
      if (!frame) frame = requestAnimationFrame(paint)
    }
    const reset = () => {
      if (frame) cancelAnimationFrame(frame)
      frame = 0
      pending = null
      rect = null
      el.removeAttribute('data-tilting')   // switches the transition to the spring
      el.style.transform = ''
    }
    // The rect goes stale on scroll or resize; re-measure on the next move.
    const stale = () => { rect = null }

    el.addEventListener('pointerenter', onEnter)
    el.addEventListener('pointermove', onMove)
    el.addEventListener('pointerleave', reset)
    el.addEventListener('pointercancel', reset)
    window.addEventListener('scroll', stale, { passive: true, capture: true })
    window.addEventListener('resize', stale)
    return () => {
      el.removeEventListener('pointerenter', onEnter)
      el.removeEventListener('pointermove', onMove)
      el.removeEventListener('pointerleave', reset)
      el.removeEventListener('pointercancel', reset)
      window.removeEventListener('scroll', stale, { capture: true })
      window.removeEventListener('resize', stale)
      reset()
    }
  }, [enabled, max, lift])

  return (
    <Tag ref={ref} className={`sw-tilt ${className}`.trim()} {...rest}>
      {children}
      {glare && enabled && (
        <span className="sw-tilt-glare" aria-hidden="true">
          <span ref={glareRef} />
        </span>
      )}
    </Tag>
  )
}

/** The contactless mark: four arcs, stroke = currentColor. Decorative. */
function Contactless() {
  return (
    <svg className="sw-bankcard-contactless" viewBox="0 0 24 24" aria-hidden="true" focusable="false"
      fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M7.5 8.5a5 5 0 0 1 0 7" />
      <path d="M11 6.2a8.4 8.4 0 0 1 0 11.6" />
      <path d="M14.5 4a11.8 11.8 0 0 1 0 16" />
      <path d="M4.2 10.6a2 2 0 0 1 0 2.8" />
    </svg>
  )
}

/**
 * The SpendWise card: a bank card made of glass (or of dark emerald metal),
 * with a gold chip, a contactless mark, a guilloché rosette and a gold-foil
 * edge, tilting in 3D under the pointer with a metallic specular.
 *
 *   Login hero (decorative, translucent, over the orb):
 *     <BankCard decorative holder="Your name here" last4="2026" meta="Since 2026" />
 *
 *   Dashboard total (real figures, OPAQUE face):
 *     <BankCard variant="solid" label="Spent this month"
 *       value={<CountUp value={total} data-testid="total" />}
 *       holder={person.name} meta="1–31 Aug" data-testid="headline" />
 *
 * Props
 *   variant     'glass' (default; translucent, CHROME tier) | 'solid' (opaque
 *               deep-emerald face; use whenever real money is shown on it)
 *   label       small muted line above `value`
 *   value       the big figure (a node: <CountUp>, <Odometer>, <Money>)
 *   children    extra body content, under value
 *   number      the masked number line; default from `last4`
 *   last4       default '2026' -> "•••• •••• •••• 2026"
 *   holder      bottom-left (the person's name, or a placeholder)
 *   meta        bottom-right small text
 *   brand       wordmark, default 'SPENDWISE'
 *   chip        draw the EMV chip; default: only when there is no `value`
 *               (a total needs the room the chip takes)
 *   decorative  aria-hidden on the whole card (use when it repeats nothing
 *               a reader needs — the login hero). Default false.
 *   tilt        pointer tilt + glare, default true (TiltCard's own gating
 *               still applies: fine pointer only, never reduced motion)
 *   max         tilt ceiling in degrees, default 6
 *   as, className, and any other prop -> the root element.
 */
export function BankCard({
  variant = 'glass',
  label,
  value,
  children,
  number,
  last4 = '2026',
  holder,
  meta,
  brand = 'SPENDWISE',
  chip,
  decorative = false,
  tilt = true,
  max = 6,
  className = '',
  ...rest
}) {
  const cls = `sw-bankcard${variant === 'solid' ? ' sw-bankcard-solid' : ''} ${className}`.trim()
  const masked = number ?? `•••• •••• •••• ${last4}`
  const inner = (
    <>
      <span className="sw-bankcard-guilloche" aria-hidden="true" />
      <span className="sw-bankcard-foil" aria-hidden="true" />
      <div className="sw-bankcard-top">
        <span className="sw-bankcard-brand">{brand}</span>
        <Contactless />
      </div>
      <div className="sw-bankcard-body">
        {(chip ?? value == null) && <span className="sw-bankcard-chip" aria-hidden="true" />}
        {label != null && <span className="sw-bankcard-label">{label}</span>}
        {value != null && <span className="sw-bankcard-value">{value}</span>}
        {children}
      </div>
      <div className="sw-bankcard-bottom">
        <div>
          {value == null && <div className="sw-bankcard-number">{masked}</div>}
          {holder != null && <div className="sw-bankcard-holder">{holder}</div>}
        </div>
        {meta != null && <span className="sw-bankcard-meta">{meta}</span>}
      </div>
    </>
  )
  const a11y = decorative ? { 'aria-hidden': 'true' } : {}
  if (!tilt) {
    const Tag = rest.as || 'div'
    delete rest.as
    return <Tag className={cls} {...a11y} {...rest}>{inner}</Tag>
  }
  return (
    <TiltCard className={cls} max={max} lift={1.015} {...a11y} {...rest}>
      {inner}
    </TiltCard>
  )
}
