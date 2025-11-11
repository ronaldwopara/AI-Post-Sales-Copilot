import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import App from './App' // This will be our layout
import DashboardPage from './pages/DashboardPage.'
import ContractsPage from './pages/ContractsPage'
import './index.css'

// Create a client
const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* We'll nest all pages inside App.jsx soon */}
          <Route path="/" element={<DashboardPage />} />
          <Route path="/contracts" element={<ContractsPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)