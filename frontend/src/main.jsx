// auth/authFetch must load before App: it hooks axios.create, and services create their clients on import.
import { installAuthFetch } from './auth/authFetch'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

installAuthFetch()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
