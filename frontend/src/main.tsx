import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { Providers } from '@/app/providers'
import { router } from '@/app/router'
import { initSentry } from '@/lib/telemetry/sentry'
import './index.css'

// G-08: Inicializa telemetria do Sentry se configurado no ambiente
initSentry()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <RouterProvider router={router} />
      <SpeedInsights />
    </Providers>
  </StrictMode>,
)
