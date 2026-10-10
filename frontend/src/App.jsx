import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext.jsx';
import Landing from './pages/Landing.jsx';
import Layout from './components/Layout.jsx';
import Login from './pages/Login.jsx';
import Overview from './pages/Overview.jsx';
import Employees from './pages/Employees.jsx';
import Pointages from './pages/Pointages.jsx';
import Demandes from './pages/Demandes.jsx';
import AI from './pages/AI.jsx';
import Reports from './pages/Reports.jsx';

function ProtectedRoute({ children }) {
  const { estConnecte, pret } = useAuth();
  if (!pret) {
    return <div className="center-msg"><div className="spinner" /></div>;
  }
  if (!estConnecte) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Overview />} />
        <Route path="employes" element={<Employees />} />
        <Route path="pointages" element={<Pointages />} />
        <Route path="demandes" element={<Demandes />} />
        <Route path="teletravail" element={<Navigate to="/app/demandes" replace />} />
        <Route path="reconnaissance" element={<AI />} />
        <Route path="rapports" element={<Reports />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

