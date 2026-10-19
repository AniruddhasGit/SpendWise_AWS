import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { LazyMotion, domMax, MotionConfig } from 'framer-motion'
import App from './App.jsx'
import { boot } from './lib/theme.js'

// Tokens FIRST — every stylesheet below reads the custom properties they define.
import './styles/tokens.css'
// The system: base reset, surfaces and primitives, then motion utilities.
import './styles/glass.css'
import './styles/motion.css'
import './styles/coinfall.css'
// Screen sheets, LAST. Each is owned by one screen and only refines geometry
// and screen-specific detail on top of the system.
import './styles/screens/shell.css'
import './styles/screens/dashboard.css'
import './styles/screens/charts.css'
import './styles/screens/expenses.css'
import './styles/screens/settings-admin.css'

// BEFORE the first render. Applying the theme in an effect means the first
// paint uses the media query and then flips — a white flash on every load for
// anyone who chose dark while their system is light (`SW-ADR-147 B`).
boot()

// framer-motion (SW-ADR-156), bundle-lean: LazyMotion loads the DOM feature
// set once (m.* components stay tiny), `strict` forbids the heavy motion.*
// import, and MotionConfig makes every animation obey the OS reduce-motion
// setting — the same signal tokens.css already honours.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <LazyMotion features={domMax} strict>
      <MotionConfig reducedMotion="user">
        <App />
      </MotionConfig>
    </LazyMotion>
  </StrictMode>,
)
