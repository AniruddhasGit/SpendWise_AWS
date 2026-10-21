import { useEffect, useState } from 'react'

/**
 * Controls shared by the two pages of the signed-out scene (SW-ADR-160).
 */

/** One switch, sun or moon: the scene's light and dark. Dark by default. */
export function ThemeSwitch({ theme, onTheme, className = '' }) {
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <button type="button" className={`icon-btn scene-theme ${className}`.trim()}
            data-testid="scene-theme" aria-label={`Switch to ${next} mode`}
            onClick={(e) => onTheme(next, e)}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
           strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        {theme === 'dark'
          // a moon: dark now, press for light
          ? <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
          // a sun: light now, press for dark
          : <>
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4" />
            </>}
      </svg>
    </button>
  )
}

/**
 * The countdown while the server wakes up ("Render time", 60 seconds, with a
 * note saying why). It counts down from an estimate,
 * opens the moment the server answers (early or late), and past zero says
 * "Almost there" rather than going negative. Shown only after a beat, so a
 * server that is already awake never flashes it.
 */
const ESTIMATE_S = 60
const SHOW_AFTER_MS = 350

export function Countdown({ since }) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 250)
    return () => clearInterval(t)
  }, [])
  const waited = now - since
  if (waited < SHOW_AFTER_MS) return null
  const left = Math.max(0, Math.ceil(ESTIMATE_S - waited / 1000))
  const mm = String(Math.floor(left / 60)).padStart(2, '0')
  const ss = String(left % 60).padStart(2, '0')
  return (
    <div className="scene-countdown" role="status" aria-live="polite" data-testid="countdown">
      <span className="scene-countdown-label">{left > 0 ? 'Render time' : 'Almost there'}</span>
      <span className="scene-countdown-time" aria-hidden={left === 0 ? 'true' : undefined}>
        {left > 0 ? `${mm}:${ss}` : '…'}
      </span>
      <span className="scene-countdown-bar" aria-hidden="true">
        <span style={{ '--p': Math.min(1, waited / (ESTIMATE_S * 1000)) }} />
      </span>
      {/* something to read while waiting (owner, 2026-10-21) */}
      <p className="scene-countdown-note">
        SpendWise runs on Render's free plan, which puts the server to sleep when nobody has
        visited for a while. It is waking up now, which takes about a minute and only happens
        for the first visitor. The page opens by itself the moment it is ready.
      </p>
    </div>
  )
}
