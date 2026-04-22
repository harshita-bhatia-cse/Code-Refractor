import { Navigate, Route, Routes } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { ReposPage } from './pages/ReposPage.jsx'
import { FilesPage } from './pages/FilesPage.jsx'
import { CodePage } from './pages/CodePage.jsx'
import { RequireAuth } from './components/RequireAuth.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LoginPage />} />

      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <DashboardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/repos"
        element={
          <RequireAuth>
            <ReposPage />
          </RequireAuth>
        }
      />
      <Route
        path="/files"
        element={
          <RequireAuth>
            <FilesPage />
          </RequireAuth>
        }
      />
      <Route
        path="/code"
        element={
          <RequireAuth>
            <CodePage />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
