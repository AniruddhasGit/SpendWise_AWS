/**
 * COINFALL — the money-themed loading experience (SW-ADR-156).
 *
 * A short cinematic intro (a gold ₹ coin falls into a pool of light, the
 * SpendWise mark rises) then an interactive playground: ₹ coins rain and you
 * fling them into your eight category vaults — a live donut fills and a total
 * counts up — until the real app is ready, when it hands off.
 *
 * Props
 *   progress  0..100   real load progress for the rail (honest; no faking)
 *   ready     bool      the app behind it is ready to show
 *   onEnter   fn        dismiss and reveal the app
 *   replay    bool      on-demand replay: no auto-advance, a Close button
 *
 * framer-motion `m.*` only (LazyMotion strict). Reduced motion: no falling
 * coins, straight to a composed frame + Enter (coinfall.css handles the rest).
 */
import { useEffect, useMemo, useRef, useState } from 'react'
import { m } from 'framer-motion'
import { rupees } from '../lib/money.js'
import { usePrefersReducedMotion } from '../lib/motion.js'
import { spring, springSoft } from '../lib/anim.js'

const CATEGORIES = [
  ['Groceries', '#4a7c59'],
  ['Food', '#b5543b'],
  ['Transport', '#3e6b8f'],
  ['Rent', '#9c7a2f'],
  ['Health', '#2e7d8a'],
  ['Fun', '#7b4b94'],
  ['Shopping', '#a04c72'],
  ['Other', '#7d8471'],
]

const INTRO_MS = 2000
const MIN_SHOWN_MS = 1800
const SPAWN_MS = 620
const MAX_COINS = 7
const rand = (a, b) => a + Math.random() * (b - a)
const pick = (arr) => arr[Math.floor(Math.random() * arr.length)]
// A plausible ₹ amount for a coin, in paise.
const coinValue = () => Math.round(rand(40, 2400)) * 100

let COIN_SEQ = 0

export default function Coinfall({ progress = 0, ready = false, onEnter, replay = false }) {
  const reduced = usePrefersReducedMotion()
  const [phase, setPhase] = useState(reduced ? 'play' : 'intro')
  const [coins, setCoins] = useState([])
  const [totals, setTotals] = useState(() => CATEGORIES.map(() => 0))
  const stageRef = useRef(null)
  const vaultRefs = useRef([])
  const mountedAt = useRef(Date.now())
  const enteredRef = useRef(false)

  const totalPaise = totals.reduce((a, b) => a + b, 0)

  // intro → play
  useEffect(() => {
    if (phase !== 'intro') return undefined
    const t = setTimeout(() => setPhase('play'), INTRO_MS)
    return () => clearTimeout(t)
  }, [phase])

  // rain coins during play (capped); not under reduced motion
  useEffect(() => {
    if (phase !== 'play' || reduced) return undefined
    const spawn = () => {
      setCoins((cur) => {
        if (cur.length >= MAX_COINS) return cur
        const [, tint] = pick(CATEGORIES)
        return [...cur, {
          id: ++COIN_SEQ,
          x: rand(8, 92),               // vw-ish percent across the stage
          tint,
          value: coinValue(),
          drift: rand(-3, 3),
        }]
      })
    }
    spawn()
    const iv = setInterval(spawn, SPAWN_MS)
    return () => clearInterval(iv)
  }, [phase, reduced])

  // auto-advance once the app is ready (not in replay); Skip can beat it
  useEffect(() => {
    if (replay || enteredRef.current) return undefined
    if (!ready) return undefined
    const wait = Math.max(0, MIN_SHOWN_MS - (Date.now() - mountedAt.current))
    const t = setTimeout(() => enter(), wait + 400)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, replay])

  const enter = () => {
    if (enteredRef.current) return
    enteredRef.current = true
    onEnter?.()
  }

  // a coin was released — collect it into the vault under its x, else drop it
  const onCoinEnd = (coin) => (_e, info) => {
    const stage = stageRef.current
    if (!stage) return
    const pointX = info.point.x
    let hit = -1
    vaultRefs.current.forEach((el, i) => {
      if (!el) return
      const r = el.getBoundingClientRect()
      if (pointX >= r.left - 6 && pointX <= r.right + 6) hit = i
    })
    if (hit >= 0) {
      setTotals((t) => t.map((v, i) => (i === hit ? v + coin.value : v)))
      setCoins((cur) => cur.filter((c) => c.id !== coin.id))
    } else {
      // tap-to-sort fallback: a quick tap (tiny drag) sorts to a matching vault
      const moved = Math.abs(info.offset.x) + Math.abs(info.offset.y)
      if (moved < 6) {
        const idx = CATEGORIES.findIndex(([, c]) => c === coin.tint)
        setTotals((t) => t.map((v, i) => (i === idx ? v + coin.value : v)))
        setCoins((cur) => cur.filter((c) => c.id !== coin.id))
      }
    }
  }

  const removeCoin = (id) => setCoins((cur) => cur.filter((c) => c.id !== id))

  const donut = useMemo(() => buildDonut(totals), [totals])
  const pct = Math.max(0, Math.min(100, Math.round(progress)))

  return (
    <m.div
      className="coinfall"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, transition: { duration: 0.5 } }}
      role="dialog"
      aria-label="SpendWise is loading"
    >
      <div className="coinfall-stage" ref={stageRef}>
        {phase === 'play' && (
          <m.div className="coinfall-readout"
            initial={{ y: -14, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={spring}>
            <Donut data={donut} />
            <span className="coinfall-total">{rupees(totalPaise)}</span>
          </m.div>
        )}

        {/* intro */}
        {phase === 'intro' && !reduced && (
          <>
            <m.div className="coin coin--hero" aria-hidden="true"
              initial={{ y: '-60vh', rotate: -40 }}
              animate={{ y: 0, rotate: 0 }}
              transition={{ ...springSoft, delay: 0.1 }}>₹</m.div>
            {[0, 1, 2].map((i) => (
              <m.div key={i} className="coinfall-ripple" aria-hidden="true"
                initial={{ scale: 0, opacity: 0.5 }}
                animate={{ scale: 6 + i * 2, opacity: 0 }}
                transition={{ duration: 1.1, delay: 0.75 + i * 0.12, ease: 'easeOut' }} />
            ))}
          </>
        )}

        <m.div className="coinfall-hero"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: phase === 'intro' ? 1 : 0, y: phase === 'intro' ? 0 : -16 }}
          transition={{ ...spring, delay: phase === 'intro' ? 0.9 : 0 }}>
          <div className="coinfall-mark">SpendWise</div>
          <div className="coinfall-tag">Where did it all go?</div>
        </m.div>

        {/* falling coins (play) */}
        {phase === 'play' && coins.map((c) => (
          <m.div key={c.id} className="coin coin--tagged" aria-hidden="true"
            style={{ left: `${c.x}%`, top: 0, '--tint': c.tint }}
            initial={{ y: -80, opacity: 0 }}
            animate={{ y: ['-6vh', '72vh'], x: [0, c.drift * 10], opacity: [0, 1, 1] }}
            transition={{ duration: rand(3.4, 4.6), ease: 'linear' }}
            onAnimationComplete={() => removeCoin(c.id)}
            drag
            dragSnapToOrigin={false}
            dragElastic={0.6}
            whileDrag={{ scale: 1.12, zIndex: 20 }}
            onDragEnd={onCoinEnd(c)}>₹</m.div>
        ))}
      </div>

      {/* vaults */}
      {phase === 'play' && (
        <m.div className="coinfall-vaults"
          initial="hidden" animate="show"
          variants={{ show: { transition: { staggerChildren: 0.05 } }, hidden: {} }}>
          {CATEGORIES.map(([name, tint], i) => {
            const share = totalPaise ? totals[i] / totalPaise : 0
            return (
              <m.div key={name} className="vault" ref={(el) => (vaultRefs.current[i] = el)}
                style={{ '--tint': tint, '--fill': `${Math.min(92, share * 160)}%` }}
                variants={{ hidden: { y: 18, opacity: 0 }, show: { y: 0, opacity: 1, transition: spring } }}>
                <span className="vault-cap" style={{ background: tint }} />
                <span className="vault-name">{name}</span>
              </m.div>
            )
          })}
        </m.div>
      )}

      <div className="coinfall-foot">
        <div className="coinfall-hint">
          <span>{phase === 'play' ? 'Fling the coins into a vault →' : 'Loading your money…'}</span>
          <span>{ready ? 'Ready' : `${pct}%`}</span>
        </div>
        <div className="coinfall-rail" aria-hidden="true">
          <m.span animate={{ width: `${ready ? 100 : pct}%` }} transition={spring} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          {replay ? (
            <button type="button" className="coinfall-skip" onClick={enter}>Close</button>
          ) : ready ? (
            <button type="button" className="coinfall-enter" onClick={enter}>Enter SpendWise →</button>
          ) : (
            <button type="button" className="coinfall-skip" onClick={enter}>Skip</button>
          )}
        </div>
      </div>
    </m.div>
  )
}

// ── a tiny donut from the per-category totals ─────────────────────────────────
function buildDonut(totals) {
  const sum = totals.reduce((a, b) => a + b, 0)
  if (!sum) return []
  const R = 15.9155        // circumference 100 for easy dash maths
  let offset = 0
  const out = []
  totals.forEach((v, i) => {
    if (!v) return
    const len = (v / sum) * 100
    out.push({ i, tint: CATEGORIES[i][1], len, offset, R })
    offset += len
  })
  return out
}

function Donut({ data }) {
  return (
    <svg className="coinfall-donut" viewBox="0 0 36 36" aria-hidden="true">
      <circle cx="18" cy="18" r="15.9155" fill="none" stroke="rgba(255,255,255,.12)" strokeWidth="4" />
      {data.map((s) => (
        <circle key={s.i} cx="18" cy="18" r={s.R} fill="none" stroke={s.tint} strokeWidth="4"
          strokeDasharray={`${s.len} ${100 - s.len}`} strokeDashoffset={-s.offset}
          transform="rotate(-90 18 18)" strokeLinecap="butt" />
      ))}
    </svg>
  )
}
