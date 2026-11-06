import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import Archive from './Archive'
import './archive.css'

const client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: 15_000 } } })

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter><Archive /></BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
