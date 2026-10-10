import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import AppLogo from '../components/AppLogo.jsx';

/* ───── Fingerprint SVG icon (inline, no external assets) ───── */
function FingerprintIcon({ size = 64 }) {
  return (
    <svg
      viewBox="0 0 100 100"
      style={{ width: size, height: size }}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* concentric fingerprint ridges */}
      <g stroke="var(--primary-mid)" strokeWidth="1.8" strokeLinecap="round" opacity={0.9}>
        <path d="M50 60 C44 60 40 54 40 48 C40 42 44 36 50 36 C56 36 60 42 60 48 C60 54 56 60 50 60Z" />
        <path d="M50 68 C38 68 30 58 30 48 C30 38 38 28 50 28 C62 28 70 38 70 48 C70 58 62 68 50 68Z" opacity={0.85} />
        <path d="M50 78 C34 78 20 64 20 48 C20 32 34 18 50 18 C66 18 80 32 80 48 C80 64 66 78 50 78Z" opacity={0.7} />
        <path d="M50 86 C30 86 12 70 12 48 C12 28 28 12 50 12 C72 12 88 28 88 48 C88 68 72 84 50 86Z" opacity={0.5} strokeWidth="1.2" />
      </g>
      {/* core dot */}
      <circle cx="50" cy="48" r="3" fill="var(--primary-mid)" opacity={0.8} />
      {/* blue accent arc */}
      <path d="M50 42 C56 42 60 46 60 52" stroke="var(--primary)" strokeWidth="2.2" strokeLinecap="round" opacity={0.9} />
      {/* ridge minutiae breaks */}
      <path d="M34 38 L36 42" stroke="var(--primary-mid)" strokeWidth="1.4" strokeLinecap="round" opacity={0.5} />
      <path d="M66 54 L68 58" stroke="var(--primary-mid)" strokeWidth="1.4" strokeLinecap="round" opacity={0.5} />
      <path d="M40 68 L44 70" stroke="var(--primary-mid)" strokeWidth="1.2" strokeLinecap="round" opacity={0.35} />
      <path d="M56 26 L58 30" stroke="var(--primary-mid)" strokeWidth="1.2" strokeLinecap="round" opacity={0.35} />
    </svg>
  );
}

export default function Login() {
  const { login, estConnecte, pret } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [espace, setEspace] = useState('employe');
  const [modeDemande, setModeDemande] = useState('presentiel');
  const [erreur, setErreur] = useState('');
  const [enCours, setEnCours] = useState(false);

  if (pret && estConnecte) return <Navigate to="/app" replace />;

  async function onSubmit(e) {
    e.preventDefault();
    setErreur('');
    setEnCours(true);
    try {
      await login(email, password, { espace, mode_demande: modeDemande });
      if (espace === 'employe') {
        navigate(modeDemande === 'teletravail' ? '/teletravail' : '/pointages');
      } else {
        navigate('/');
      }
    } catch (err) {
      setErreur(err.message || 'Connexion impossible.');
    } finally {
      setEnCours(false);
    }
  }

  return (
    <div className="login-wrap" style={{ background: 'linear-gradient(135deg, #f0f4ff 0%, #e8edf5 100%)' }}>
      <div className="login-card" style={{ textAlign: 'center', padding: '40px 32px' }}>
        {/* ─── brand ─── */}
        <div className="empreinte-login__brand" style={{ justifyContent: 'center', marginBottom: 4 }}>
          <div className="bg-gray-100 rounded-lg p-1 flex items-center justify-center">
            <AppLogo size={32} />
          </div>
          <span className="font-bold text-lg tracking-tight" style={{ color: 'var(--primary)' }}>SmartPointage</span>
        </div>
        <p className="view-sub" style={{ marginBottom: 28, color: '#6B7280' }}>Suite RH · Pointage biométrique</p>

        {/* ─── form ─── */}
        <form onSubmit={onSubmit}>
          {/* espace toggle */}
          <div className="login-field" style={{ textAlign: 'left' }}>
            <label>Espace</label>
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                type="button"
                className={espace === 'admin' ? 'btn btn--solid' : 'btn'}
                onClick={() => setEspace('admin')}
                style={{ flex: 1, justifyContent: 'center' }}
              >
                Admin
              </button>
              <button
                type="button"
                className={espace === 'employe' ? 'btn btn--solid' : 'btn'}
                onClick={() => setEspace('employe')}
                style={{ flex: 1, justifyContent: 'center' }}
              >
                Employé
              </button>
            </div>
          </div>

          {/* mode conditionnel */}
          {espace === 'employe' && (
            <div className="login-field" style={{ textAlign: 'left' }}>
              <label>Mode</label>
              <div style={{ display: 'flex', gap: 12 }}>
                <button
                  type="button"
                  className={modeDemande === 'presentiel' ? 'btn btn--solid' : 'btn'}
                  onClick={() => setModeDemande('presentiel')}
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  Présentiel
                </button>
                <button
                  type="button"
                  className={modeDemande === 'teletravail' ? 'btn btn--solid' : 'btn'}
                  onClick={() => setModeDemande('teletravail')}
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  Télétravail
                </button>
              </div>
            </div>
          )}

          <div className="login-field" style={{ textAlign: 'left' }}>
            <label htmlFor="email">Email</label>
            <input
              id="email" type="text" autoComplete="username" value={email}
              onChange={e => setEmail(e.target.value)} required
              placeholder="prenom.nom@entreprise.ma"
            />
          </div>

          <div className="login-field" style={{ textAlign: 'left' }}>
            <label htmlFor="password">Mot de passe</label>
            <input
              id="password" type="password" autoComplete="current-password" value={password}
              onChange={e => setPassword(e.target.value)} required placeholder="••••••••"
            />
          </div>

          {erreur && <div className="login-error">{erreur}</div>}

          <button
            type="submit"
            className="btn btn--solid"
            style={{ width: '100%', justifyContent: 'center', marginTop: 20 }}
            disabled={enCours}
          >
            {enCours ? (
              <span className="spinner" />
            ) : (
              <>
                Se connecter
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
              </>
            )}
          </button>
        </form>

        <p className="login-hint" style={{ marginTop: 20 }}>
          Les employés se connectent avec leur email. L'administrateur utilise son identifiant système.
        </p>
      </div>
    </div>
  );
}

