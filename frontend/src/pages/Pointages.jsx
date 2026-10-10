import { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';
import { StatutTag, TypeTag } from '../components/ui.jsx';
import CameraCapture from '../components/CameraCapture.jsx';

const FUSEAU_MAROC = 'Africa/Casablanca';

function formaterHeureMaroc(valeur) {
  return new Date(valeur).toLocaleTimeString('fr-FR', {
    timeZone: FUSEAU_MAROC,
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formaterDateHeureMaroc(valeur) {
  return new Date(valeur).toLocaleString('fr-FR', {
    timeZone: FUSEAU_MAROC,
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function CountdownTimer({ tempsRestantSecondes, heureAutorisee }) {
  const [temps, setTemps] = useState(tempsRestantSecondes);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (temps <= 0) return;
    intervalRef.current = setInterval(() => {
      setTemps((prev) => {
        if (prev <= 1) {
          clearInterval(intervalRef.current);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(intervalRef.current);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const h = Math.floor(temps / 3600);
  const m = Math.floor((temps % 3600) / 60);
  const s = temps % 60;

  const format = (n) => String(n).padStart(2, '0');

  return (
    <div className="countdown-wrap">
      <div className="countdown-ring">
        <div className="countdown-value">{format(h)}<small>h</small> {format(m)}<small>m</small> {format(s)}<small>s</small></div>
      </div>
      <p className="countdown-label">Temps restant avant autorisation de sortie</p>
    </div>
  );
}

export default function Pointages() {
  const { role } = useAuth();
  const [pointages, setPointages] = useState([]);
  const [filtreMethode, setFiltreMethode] = useState('all');
  const [chargement, setChargement] = useState(true);
  const [afficherScan, setAfficherScan] = useState(false);
  const [resultatScan, setResultatScan] = useState(null);
  const [erreurScan, setErreurScan] = useState('');
  const [enCoursScan, setEnCoursScan] = useState(false);
  const [blocageSortie, setBlocageSortie] = useState(null);

  const charger = useCallback(() => {
    setChargement(true);
    const q = filtreMethode === 'all' ? '' : `?methode=${encodeURIComponent(filtreMethode)}`;
    api.get(`/pointage${q}`).then(setPointages).finally(() => setChargement(false));
  }, [filtreMethode]);

  useEffect(charger, [charger]);

  async function onCapture(dataUrl) {
    setEnCoursScan(true); setErreurScan(''); setResultatScan(null); setBlocageSortie(null);
    try {
      const res = await api.post('/pointage/scan', { photo: dataUrl });
      setResultatScan(res);
      charger();
    } catch (err) {
      // Vérifier si c'est un blocage SORTIE (code JSON)
      if (err.data?.code === 'SORTIE_BLOQUEE') {
        setBlocageSortie(err.data);
      } else {
        setErreurScan(err.message);
      }
    } finally {
      setEnCoursScan(false);
    }
  }

  async function exporter() {
    try {
      await api.download('/rapports/pointages.csv', 'pointages.csv');
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">Espace Employé</div>
          <h1 className="view-title">Pointages</h1>
          <p className="view-sub">Pointez via la caméra et consultez l'historique de vos pointages (ou de votre équipe).</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          {['rh', 'administrateur'].includes(role) && (
            <button className="btn" onClick={exporter}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
              Exporter (.csv)
            </button>
          )}
          <button className="btn btn--solid" onClick={() => { setAfficherScan((v) => !v); setResultatScan(null); setErreurScan(''); }}>
            {afficherScan ? 'Fermer la caméra' : 'Pointer maintenant'}
          </button>
        </div>
      </div>

      {afficherScan && (
        <div className="card" style={{ marginBottom: 20, alignItems: 'center' }}>
          <CameraCapture onCapture={onCapture} label={enCoursScan ? 'Analyse…' : 'Pointer'} disabled={enCoursScan} />
          {blocageSortie && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <CountdownTimer tempsRestantSecondes={blocageSortie.temps_restant_secondes} heureAutorisee={blocageSortie.heure_autorisee} />
              <p className="card__hint" style={{ marginTop: 8, maxWidth: 340 }}>
                Entrée enregistrée à {formaterHeureMaroc(blocageSortie.heure_entree)}.
                Vous pourrez pointer votre sortie après {blocageSortie.duree_minimum_heures}h de travail.
              </p>
            </div>
          )}
          {!blocageSortie && erreurScan && <div className="login-error" style={{ marginTop: 16, maxWidth: 400 }}>{erreurScan}</div>}
          {resultatScan && (
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <span className="chip active" style={{ marginBottom: 8 }}>{resultatScan.type}</span>
              <StatutTag statut={resultatScan.statut} />
              <p className="view-sub" style={{ marginTop: 8 }}>{resultatScan.message}</p>
              <p className="card__hint" style={{ marginTop: 4 }}>
                Mode : {resultatScan.mode} · Score : {resultatScan.score}
              </p>
            </div>
          )}
        </div>
      )}

      <div className="chips" style={{ marginBottom: 16 }}>
        {[['all', 'Tous'], ['Présentiel', 'Présentiel'], ['Télétravail', 'Télétravail']].map(([key, lbl]) => (
          <button key={key} className={`chip${filtreMethode === key ? ' active' : ''}`} onClick={() => setFiltreMethode(key)}>{lbl}</button>
        ))}
      </div>

      {chargement ? (
        <div className="center-msg"><div className="spinner" /></div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr><th>Heure</th><th>Employé</th><th>Département</th><th>Type</th><th>Méthode</th><th>Score</th><th>Statut</th></tr>
            </thead>
            <tbody>
              {pointages.map((p) => (
                <tr key={p.id}>
                  <td className="mono">{formaterDateHeureMaroc(p.date_heure)}</td>
                  <td>
                    <div className="cell-name">{p.utilisateur?.nom_complet || '—'}</div>
                    <div className="cell-sub">{p.utilisateur?.matricule}</div>
                  </td>
                  <td>{p.utilisateur?.departement || '—'}</td>
                  <td><TypeTag type={p.type} /></td>
                  <td>{p.mode}</td>
                  <td className="mono">{p.score_confiance ?? '—'}</td>
                  <td><StatutTag statut={p.statut} /></td>
                </tr>
              ))}
              {pointages.length === 0 && (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--muted)' }}>Aucun pointage pour le moment.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
