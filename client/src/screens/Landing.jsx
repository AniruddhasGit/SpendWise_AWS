import { useLayoutEffect, useRef } from 'react'
import { gsap } from 'gsap'
import { SplitText } from 'gsap/SplitText'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import Fog from '../components/Fog.jsx'
import MoneyTree from '../components/MoneyTree.jsx'
import { Countdown, ThemeSwitch } from '../components/SceneControls.jsx'

gsap.registerPlugin(SplitText, ScrollTrigger)

/**
 * The front door (SW-ADR-156; the scene SW-ADR-159; the arrival and the
 * carry-over SW-ADR-160): what a signed-out visitor sees first.
 *
 * The tree and its fog are on screen at once. On the always-on front the
 * server may still be asleep, so the rest of the page waits behind a
 * countdown, and the moment the server answers it all arrives with style: the
 * bar slides down, the headline's letters rise into place one after another,
 * the line follows, the button springs in. Further down the details rise as
 * they are scrolled to.
 *
 * Leaving for the sign-in page (`leave`), the words scatter and lift away
 * before App carries the tree across (lib/scene.js). The falling bills are
 * illustrative spends (MoneyTree's EXAMPLE_BILLS), never anyone's money.
 */
const TREE_SRC = '/assets/tree/money-tree.webp'

const DETAILS = [
  ['Log it in seconds.', 'An amount, a date, a category if you like. Done before the coffee cools.'],
  ['See where it went.', 'By category, by day, by weekday, and against last month, as soon as you look.'],
  ['Yours alone.', 'Every row is locked to your account in the database itself. Not even an administrator can see your amounts.'],
  ['Exact to the cent.', 'Money is kept as whole cents, never as rounded decimals, so every total adds up.'],
]

export default function Landing({ ready, since, theme, onTheme, onSignIn, onRegister }) {
  const rootRef = useRef(null)
  const split = useRef(null)
  const leaving = useRef(false)

  // Before the server answers: everything but the tree and the fog waits,
  // hidden, so nothing flashes before its entrance.
  useLayoutEffect(() => {
    const ctx = gsap.context(() => {
      gsap.set('.scene-in', { autoAlpha: 0 })
    }, rootRef)
    return () => ctx.revert()
  }, [])

  // The arrival, once the server is awake.
  useLayoutEffect(() => {
    if (!ready) return undefined
    const ctx = gsap.context(() => {
      split.current = SplitText.create('.landing-title', { type: 'chars,words', aria: 'auto' })
      const tl = gsap.timeline({ defaults: { ease: 'power4.out' } })
      tl.to('.scene-countdown', { autoAlpha: 0, y: -12, duration: 0.35, ease: 'power2.in' }, 0)
        .fromTo('.landing-bar', { autoAlpha: 0, y: -64 }, { autoAlpha: 1, y: 0, duration: 0.9 }, 0.15)
        .set('.landing-title', { autoAlpha: 1 }, 0.3)
        .from(split.current.chars, {
          yPercent: 120, rotateX: -80, autoAlpha: 0, filter: 'blur(6px)',
          duration: 0.9, stagger: 0.028, transformOrigin: '50% 100%',
        }, 0.3)
        .fromTo('.landing-line', { autoAlpha: 0, y: 24, filter: 'blur(8px)' },
          { autoAlpha: 1, y: 0, filter: 'blur(0px)', duration: 0.8 }, 0.75)
        .fromTo('.landing-start', { autoAlpha: 0, scale: 0.6, y: 18 },
          { autoAlpha: 1, scale: 1, y: 0, duration: 0.8, ease: 'back.out(2)' }, 0.95)
        .fromTo('.landing-cue', { autoAlpha: 0, y: -10 }, { autoAlpha: 1, y: 0, duration: 0.6 }, 1.2)

      // below the fold: each detail rises and sharpens as it is scrolled to
      gsap.set('.landing-reveal', { autoAlpha: 1 })
      ScrollTrigger.batch('.landing-reveal', {
        start: 'top 88%',
        once: true,
        onEnter: (els) => gsap.fromTo(els,
          { autoAlpha: 0, y: 70, filter: 'blur(10px)' },
          { autoAlpha: 1, y: 0, filter: 'blur(0px)', duration: 1, stagger: 0.12, ease: 'power3.out' }),
      })
    }, rootRef)
    return () => { split.current?.revert(); split.current = null; ctx.revert() }
  }, [ready])

  /** The words leave dramatically, then `next` runs (App carries the tree). */
  const leave = (next) => () => {
    if (leaving.current) return
    leaving.current = true
    const root = rootRef.current
    const chars = split.current?.chars || []
    gsap.timeline({ onComplete: next })
      .to(chars, {
        y: () => gsap.utils.random(-140, 140), x: () => gsap.utils.random(-90, 30),
        rotate: () => gsap.utils.random(-70, 70), autoAlpha: 0, filter: 'blur(6px)',
        duration: 0.6, ease: 'power3.in', stagger: { each: 0.008, from: 'random' },
      }, 0)
      .to(root.querySelector('.landing-side'), { x: 120, autoAlpha: 0, duration: 0.5, ease: 'power3.in' }, 0)
      .to(root.querySelector('.landing-bar'), { y: -80, autoAlpha: 0, duration: 0.5, ease: 'power3.in' }, 0.05)
      .to(root.querySelectorAll('.landing-cue, .landing-details, .landing-final'),
        { autoAlpha: 0, duration: 0.3 }, 0)
  }

  return (
    <div className="landing scene" data-scene={theme} ref={rootRef}>
      <header className="landing-bar scene-in">
        <span className="wordmark landing-brand">SpendWise</span>
        <div className="landing-bar-actions">
          <ThemeSwitch theme={theme} onTheme={onTheme} />
          <button type="button" className="btn landing-signin"
                  data-testid="landing-sign-in" onClick={leave(onSignIn)}>
            Sign in
          </button>
        </div>
      </header>

      <main>
        <section className="landing-scene" aria-labelledby="landing-title">
          <h1 className="landing-title sw-extruded scene-in" id="landing-title">
            Know where every dollar goes.
          </h1>

          <div className="landing-stage">
            {/* the glass floor, seen from a raised camera: a slab with a lit
                rim and a front edge, the tree's reflection inside it */}
            <div className="landing-floor" aria-hidden="true">
              <div className="landing-floor-glass">
                <img className="landing-reflection" src={TREE_SRC} alt="" decoding="async" />
              </div>
            </div>
            <MoneyTree variant="landing" atmosphere orbits mist={false} dust ground={false}
                       breeze={-34} alwaysMove
                       alt="A bonsai tree whose leaves are banknotes, standing on a glass floor in mist, with bills drifting down from it" />
          </div>

          <div className="landing-side">
            <p className="landing-line scene-in">
              Log a spend in seconds. Visible to you alone.
            </p>
            <button type="button" className="btn btn-lg landing-start scene-in"
                    data-testid="landing-start" onClick={leave(onRegister)}>
              Create your account
            </button>
          </div>

          <Fog className="landing-fog landing-fog-back" layer="back" scene={theme}
               floor=".landing-floor" stage=".landing-stage" />
          <Fog className="landing-fog landing-fog-front" scene={theme}
               floor=".landing-floor" stage=".landing-stage" />
          {!ready && <Countdown since={since} />}
          <span className="landing-cue scene-in" aria-hidden="true">Scroll</span>
        </section>

        <section className="landing-details" aria-label="What it does">
          {DETAILS.map(([title, body], i) => (
            <article key={title} className="landing-detail landing-reveal scene-in">
              <span className="landing-detail-n" aria-hidden="true">{String(i + 1).padStart(2, '0')}</span>
              <h2 className="landing-detail-title">{title}</h2>
              <p className="landing-detail-body">{body}</p>
            </article>
          ))}
        </section>

        <section className="landing-final landing-reveal scene-in" aria-labelledby="landing-final-title">
          <h2 className="landing-final-title sw-extruded" id="landing-final-title">
            Start with one expense.
          </h2>
          <div className="landing-final-actions">
            <button type="button" className="btn btn-lg" onClick={leave(onRegister)}>Create your account</button>
            <button type="button" className="btn btn-quiet btn-lg landing-final-signin" onClick={leave(onSignIn)}>
              Sign in
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
