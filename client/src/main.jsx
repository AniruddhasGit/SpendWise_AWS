import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { boot } from './lib/theme.js'

// Tokens FIRST — every stylesheet below reads the custom properties they define.
import './styles/tokens.css'
// Lenis's base rules (smooth scroll everywhere, SW-ADR-160)
import 'lenis/dist/lenis.css'
// The system: base reset, surfaces and primitives, then motion utilities.
import './styles/glass.css'
import './styles/motion.css'
// Screen sheets, LAST. Each is owned by one screen and only refines geometry
// and screen-specific detail on top of the system.
import './styles/screens/shell.css'
import './styles/screens/dashboard.css'
import './styles/screens/charts.css'
import './styles/screens/expenses.css'
import './styles/screens/settings-admin.css'
import './styles/screens/money-tree.css'
import './styles/screens/landing.css'

// BEFORE the first render. Applying the theme in an effect means the first
// paint uses the media query and then flips — a white flash on every load for
// anyone who chose dark while their system is light (`SW-ADR-147 B`).
boot()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
