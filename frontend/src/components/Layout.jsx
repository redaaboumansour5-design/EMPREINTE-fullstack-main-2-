import { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { api } from '../api/client.js';
import AppLogo from './AppLogo.jsx';
import BackToLandingButton from './BackToLandingButton.jsx';

const NAV_ITEMS = [
  { to: '/app', label: "Vue d'ensemble", icon: 'overview', end: true, roles: null },
  { to: '/app/employes', label: 'Employés', icon: 'employees', roles: ['rh', 'administrateur', 'manager'] },

  { to: '/app/pointages', label: 'Pointages', icon: 'pointages', roles: null },
  { to: '/app/demandes', label: 'Demandes', icon: 'requests', roles: ['rh', 'employe', 'administrateur', 'manager'] },

  { to: '/app/reconnaissance', label: 'Reconnaissance IA', icon: 'ai', roles: ['administrateur'] },
  { to: '/app/rapports', label: 'Rapports', icon: 'reports', roles: ['rh', 'administrateur'] },
];

const ICONS = {
  overview: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M3 13h4v7H3zM10 8h4v12h-4zM17 3h4v17h-4z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/></svg>,
  employees: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><circle cx="9" cy="8" r="3.2" stroke="currentColor" strokeWidth="1.7"/><path d="M3.5 20c.8-3.6 3-5.5 5.5-5.5s4.7 1.9 5.5 5.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/><circle cx="17" cy="8" r="2.6" stroke="currentColor" strokeWidth="1.7"/><path d="M15.5 14.8c2.2.2 3.8 2 4.4 4.7" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
  pointages: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8.3" stroke="currentColor" strokeWidth="1.7"/><path d="M12 7.5V12l3 2.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  requests: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><rect x="4" y="3.5" width="16" height="17" rx="2" stroke="currentColor" strokeWidth="1.7"/><path d="M8 8h8M8 12h8M8 16h5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
  ai: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><rect x="3.5" y="3.5" width="17" height="17" rx="3" stroke="currentColor" strokeWidth="1.7"/><circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.7"/><path d="M12 3.5V6M12 18v2.5M3.5 12H6M18 12h2.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
  reports: <svg width="17" height="17" viewBox="0 0 24 24" fill="none"><path d="M6 3.5h9l4.5 4.5V20a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/><path d="M9 13.5h6M9 17h4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round"/></svg>,
};

const ESPACES = {
  employe: 'Espace Employé',
  manager: 'Espace Manager',
  rh: 'Espace RH',
  administrateur: 'Espace Administration',
};

function useHorloge() {
  const [maintenant, setMaintenant] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setMaintenant(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return maintenant;
}

export default function Layout() {
  const { utilisateur, role, logout } = useAuth();
  const navigate = useNavigate();
  const [drawerOuvert, setDrawerOuvert] = useState(false);
  const [enAttenteDemandes, setEnAttenteDemandes] = useState(0);
  const maintenant = useHorloge();

  useEffect(() => {
    if (['manager', 'rh', 'administrateur'].includes(role)) {
      api.get('/demandes/resume').then((r) => setEnAttenteDemandes(r.en_attente)).catch(() => {});
    }
  }, [role]);

  const initiales = utilisateur
    ? ((utilisateur.prenom?.[0] || '') + (utilisateur.nom?.[0] || utilisateur.identifiant_admin?.[0] || '')).toUpperCase()
    : '--';
  const nomAffiche = utilisateur?.prenom
    ? `${utilisateur.prenom} ${utilisateur.nom}`
    : utilisateur?.nom_complet || utilisateur?.identifiant_admin || 'Utilisateur';

  const itemsVisibles = NAV_ITEMS.filter((item) => !item.roles || item.roles.includes(role));

  const fermerDrawer = () => setDrawerOuvert(false);

  return (
    <div className="app">
      <div className={`backdrop${drawerOuvert ? ' show' : ''}`} onClick={fermerDrawer} />
      <aside className={`side${drawerOuvert ? ' open' : ''}`}>
        <div className="side__brand">
          <div className="bg-gray-100 rounded-lg p-1 flex items-center justify-center">
            <AppLogo size={40} />
          </div>
          <span className="font-bold text-lg tracking-tight text-slate-900"></span>
        </div>

        <nav className="side__nav">
          <div className="nav-divider">
            <BackToLandingButton variant="sidebar" />
          </div>
          {itemsVisibles.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={fermerDrawer}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              {ICONS[item.icon]}
              {item.label}
              {item.to === '/app/demandes' && enAttenteDemandes > 0 && (
                <span className="nav-badge">{enAttenteDemandes}</span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="side__spacer" />
        <div className="side__role">
          <div className="role-chip">
            <div className="role-avatar reticle-sm">{initiales}</div>
            <div>
              <div className="role-name">{nomAffiche}</div>
              <div className="role-space">{ESPACES[role] || 'Espace'}</div>
            </div>
          </div>
          <button className="btn btn--logout" onClick={() => { logout(); navigate('/login'); }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Déconnexion
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button className="burger" onClick={() => setDrawerOuvert((v) => !v)} aria-label="Ouvrir le menu">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
          <BackToLandingButton variant="topbar" />
          <div className="topbar__date">
            Aujourd'hui · <strong>{maintenant.toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</strong>
          </div>
          <div className="topbar__spacer" />
          <div className="topbar__clock">
            <span className="live-dot" />
            <span>{maintenant.toLocaleTimeString('fr-FR', { timeZone: 'Africa/Casablanca' })}</span>
          </div>
        </header>

        <main className="views">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

