import { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client.js';

const validators = {
  matricule: /^[A-Z0-9]{3,10}$/,
  nom: /^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$/u,
  prenom: /^[A-Za-zÀ-ÖØ-öø-ÿ]+(?:[ '-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$/u,
  email: /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d\s]).{8,}$/,
  poste: /^[A-Za-z0-9À-ÖØ-öø-ÿ]+(?:[ '-][A-Za-z0-9À-ÖØ-öø-ÿ]+)*$/u,
};

const validationMessages = {
  matricule: '3 à 10 lettres majuscules ou chiffres.',
  nom: 'Lettres, accents, espaces, apostrophes ou tirets uniquement.',
  prenom: 'Lettres, accents, espaces, apostrophes ou tirets uniquement.',
  email: 'Format attendu : utilisateur@domaine.com.',
  password: '8 caractères minimum, avec majuscule, minuscule, chiffre et caractère spécial.',
  poste: 'Lettres, chiffres, accents, espaces, apostrophes ou tirets uniquement.',
};
import { useAuth } from '../context/AuthContext.jsx';
import CameraCapture from '../components/CameraCapture.jsx';

const DEPT_COLORS = {
  Direction: '#48E8C9', 'Ressources Humaines': '#9C8CFF', Finance: '#F4B740',
  IT: '#5B9DF4', Commercial: '#E36BD9', Production: '#4ADE80',
};

function initiales(u) {
  return ((u.prenom?.[0] || '') + (u.nom?.[0] || '')).toUpperCase();
}

export default function Employees() {
  const { role } = useAuth();
  const [employes, setEmployes] = useState([]);
  const [departements, setDepartements] = useState([]);
  const [deptActif, setDeptActif] = useState('all');
  const [recherche, setRecherche] = useState('');
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');
  const [modalOuvert, setModalOuvert] = useState(false);
  const [empreinteCible, setEmpreinteCible] = useState(null); // employé en cours d'enrôlement

  const peutGerer = ['rh', 'administrateur'].includes(role);


  const charger = useCallback(() => {
    setChargement(true);
    // Pour un manager : le backend doit déjà filtrer sur son département.
    // On garde la liste des départements pour l'UI (création), mais l'annuaire sera filtré côté API.
    Promise.all([
      api.get('/employes'),
      api.get('/employes/departements'),
    ])
      .then(([e, d]) => { setEmployes(e); setDepartements(d); })
      .catch((err) => setErreur(err.message))
      .finally(() => setChargement(false));
  }, []);


  useEffect(charger, [charger]);

  const filtres = employes.filter((e) => {
    if (deptActif !== 'all' && e.departement?.id !== Number(deptActif)) return false;
    if (recherche) {
      const hay = `${e.prenom} ${e.nom} ${e.poste || ''} ${e.matricule}`.toLowerCase();
      if (!hay.includes(recherche.toLowerCase())) return false;
    }
    return true;
  });

  if (chargement) return <div className="center-msg"><div className="spinner" /></div>;

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">Espace RH</div>
          <h1 className="view-title">Gestion des employés</h1>
          <p className="view-sub">Annuaire, rôles et enrôlement biométrique (empreinte de référence).</p>
        </div>
        {peutGerer && (
          <button className="btn btn--solid" onClick={() => setModalOuvert(true)}>+ Nouvel employé</button>
        )}
      </div>

      {erreur && <div className="login-error" style={{ marginBottom: 16 }}>{erreur}</div>}

      <div className="toolbar">
        <input className="search" placeholder="Rechercher un employé, un poste, un matricule…" value={recherche} onChange={(e) => setRecherche(e.target.value)} />
      </div>

      {/* Masquer la barre de filtres par département uniquement pour les managers */}
      {!['manager'].includes(role) && (
        <div className="chips" style={{ marginBottom: 6 }}>
          <button className={`chip${deptActif === 'all' ? ' active' : ''}`} onClick={() => setDeptActif('all')}>Tous</button>
          {departements.map((d) => (
            <button key={d.id} className={`chip${deptActif === String(d.id) ? ' active' : ''}`} onClick={() => setDeptActif(String(d.id))}>{d.nom}</button>
          ))}
        </div>
      )}

      <p className="sample-note">{filtres.length} employé{filtres.length > 1 ? 's' : ''} affiché{filtres.length > 1 ? 's' : ''}</p>


      <div className="emp-grid">
        {filtres.map((e) => (
          <div key={e.id} className="emp-card">
            <div className="avatar reticle-sm" style={{ width: 40, height: 40 }}>{initiales(e)}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="emp-name">{e.prenom} {e.nom}</div>
              <div className="emp-role">{e.role.toUpperCase()} · {e.matricule}</div>
              <div className="emp-dept">
                <span className="dept-dot" style={{ background: DEPT_COLORS[e.departement?.nom] || '#7C8CA3' }} />
                {e.departement?.nom || '—'} · {e.poste || '—'}
              </div>
              <div className="emp-foot">
                <span className="emp-time">{e.a_empreinte_enregistree ? '✓ Empreinte enregistrée' : 'Aucune empreinte'}</span>
                {peutGerer && (
                  <button className="btn btn--sm" onClick={() => setEmpreinteCible(e)}>
                    {e.a_empreinte_enregistree ? 'Réenrôler' : 'Enrôler'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {modalOuvert && (
        <NouvelEmployeModal
          departements={departements}
          onClose={() => setModalOuvert(false)}
          onCreated={() => { setModalOuvert(false); charger(); }}
        />
      )}

      {empreinteCible && (
        <EnrolementModal
          employe={empreinteCible}
          onClose={() => setEmpreinteCible(null)}
          onDone={() => { setEmpreinteCible(null); charger(); }}
        />
      )}
    </>
  );
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(4,6,9,.65)', zIndex: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 440, width: '100%', maxHeight: '90vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
        <div className="card__head">
          <div className="card__title">{title}</div>
          <button className="btn btn--sm btn--ghost" onClick={onClose}>Fermer</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function NouvelEmployeModal({ departements, onClose, onCreated }) {
  const [form, setForm] = useState({ matricule: '', nom: '', prenom: '', email: '', password: '', role: 'employe', poste: '', departement_id: departements[0]?.id || '' });
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    const valeurs = Object.fromEntries(Object.entries(form).map(([champ, valeur]) => [champ, typeof valeur === 'string' ? valeur.trim().normalize('NFC') : valeur]));
    const champInvalide = ['matricule', 'nom', 'prenom', 'email', 'password', 'poste'].find((champ) => valeurs[champ] && !validators[champ].test(valeurs[champ]));
    if (champInvalide) {
      setErreur(`${champInvalide === 'password' ? 'Mot de passe' : champInvalide.charAt(0).toUpperCase() + champInvalide.slice(1)} : ${validationMessages[champInvalide]}`);
      return;
    }
    setEnvoi(true); setErreur('');
    try {
      await api.post('/employes', { ...valeurs, departement_id: Number(valeurs.departement_id) || null });
      onCreated();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Modal title="Nouvel employé" onClose={onClose}>
      <form onSubmit={onSubmit}>
        {['matricule', 'nom', 'prenom', 'email', 'password', 'poste'].map((champ) => (
          <div className="login-field" key={champ}>
            <label>{champ === 'password' ? 'Mot de passe' : champ.charAt(0).toUpperCase() + champ.slice(1)}</label>
            <input
              type={champ === 'password' ? 'password' : 'text'}
              value={form[champ]}
              onChange={(e) => setForm({ ...form, [champ]: e.target.value })}
              required={champ !== 'poste'}
              pattern={validators[champ].source}
              minLength={champ === 'password' ? 8 : undefined}
              maxLength={champ === 'matricule' ? 10 : undefined}
              title={validationMessages[champ]}
            />
          </div>
        ))}
        <div className="login-field">
          <label>Rôle</label>
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} style={{ width: '100%', background: 'var(--panel-2)', border: '1px solid var(--line)', borderRadius: 9, padding: '11px 14px', color: 'var(--text)' }}>
            <option value="employe">Employé</option>
            <option value="manager">Manager</option>
            <option value="rh">RH</option>
          </select>
        </div>
        <div className="login-field">
          <label>Département</label>
          <select value={form.departement_id} onChange={(e) => setForm({ ...form, departement_id: e.target.value })} style={{ width: '100%', background: 'var(--panel-2)', border: '1px solid var(--line)', borderRadius: 9, padding: '11px 14px', color: 'var(--text)' }}>
            {departements.map((d) => <option key={d.id} value={d.id}>{d.nom}</option>)}
          </select>
        </div>
        {erreur && <div className="login-error">{erreur}</div>}
        <button type="submit" className="btn btn--solid" style={{ width: '100%', justifyContent: 'center', marginTop: 18 }} disabled={envoi}>
          {envoi ? 'Création…' : 'Créer l\'employé'}
        </button>
      </form>
    </Modal>
  );
}

function EnrolementModal({ employe, onClose, onDone }) {
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);
  const [succes, setSucces] = useState(false);

  async function onCapture(dataUrl) {
    setEnvoi(true); setErreur('');
    try {
      await api.post(`/employes/${employe.id}/empreinte`, { photo: dataUrl });
      setSucces(true);
      setTimeout(onDone, 900);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <Modal title={`Enrôlement biométrique — ${employe.prenom} ${employe.nom}`} onClose={onClose}>
      <p className="view-sub" style={{ marginBottom: 16 }}>
        Capturez une photo de référence nette et bien éclairée. Elle sera convertie en
        empreinte FaceNet (vecteur d'embedding) et servira de base à tous les futurs pointages.
      </p>
      <CameraCapture onCapture={onCapture} label={envoi ? 'Envoi…' : 'Capturer la référence'} disabled={envoi} />
      {erreur && <div className="login-error" style={{ marginTop: 14 }}>{erreur}</div>}
      {succes && <div className="login-error" style={{ marginTop: 14, background: 'var(--cyan-dim)', color: 'var(--cyan)' }}>✓ Empreinte enregistrée avec succès.</div>}
    </Modal>
  );
}
