import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { boot } from './lib/theme.js'

// Tokens FIRST, then components — the cascade is order-dependent and the
// components reference the custom properties the tokens define.
import './styles/tokens.css'
import './styles/app.css'

// BEFORE the first render. Applying the theme in an effect means the first
// paint uses the media query and then flips — a white flash on every load for
// anyone who chose dark while their system is light (`SW-ADR-147 B`).
boot()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
