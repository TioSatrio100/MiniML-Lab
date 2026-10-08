import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'

const Dashboard = lazy(() => import('./pages/Dashboard'))

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center font-mono text-sm text-muted-foreground">
          loading dashboard…
        </div>
      }
    >
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Dashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
