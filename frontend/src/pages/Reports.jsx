import { useEffect, useState } from 'react';
import { api } from '../api/client.js';

export default function Reports() {
  const [historique, setHistorique] = useState([]);
  const [chargement, setChargement] = useState(true);
  const [erreur, setErreur] = useState('');

  useEffect(() => {
    api.get('/rapports/historique').then(setHistorique).catch((e) => setErreur(e.message)).finally(() => setChargement(false));
  }, []);

  async function exporter(type, filename = `${type}.csv`) {
    try {
      await api.download(`/rapports/${type}.csv`, filename);
      const h = await api.get('/rapports/historique');
      setHistorique(h);
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">Espace RH · Reporting</div>
          <h1 className="view-title">Rapports &amp; statistiques</h1>
          <p className="view-sub">Exports CSV (ouvrables dans Excel) — traçabilité des pointages, employés et télétravail.</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card__head"><div className="card__title">Exports</div></div>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <button className="btn btn--solid" onClick={() => exporter('pointages')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Pointages (.csv)
          </button>
          <button className="btn" onClick={() => exporter('employes')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Employés (.csv)
          </button>
          <button className="btn" onClick={() => exporter('teletravail')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Télétravail (.csv)
          </button>
          <button className="btn" onClick={() => exporter('absences', 'absences-par-jour.csv')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Absences par jour (.csv)
          </button>
          <button className="btn" onClick={() => exporter('absences-detail', 'rapport-absences.csv')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 1 1 1h14a1 1 0 0 0 1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Rapport Absences (.csv)
          </button>
          <button className="btn" onClick={() => exporter('retards-detail', 'rapport-retards.csv')}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 3v13m0 0-4-4m4 4 4-4M4 17v3a1 1 0 0 1 1 1h14a1 1 0 0 1-1-1v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/></svg>
            Rapport Retards (.csv)
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card__head"><div className="card__title">Historique des rapports générés</div></div>
        {chargement ? <div className="center-msg"><div className="spinner" /></div> : erreur ? (
          <p className="login-error">{erreur}</p>
        ) : (
          <div className="table-scroll">
            <table>
              <thead><tr><th>Type</th><th>Généré le</th><th>Par</th><th>Format</th></tr></thead>
              <tbody>
                {historique.map((r) => (
                  <tr key={r.id}>
                    <td style={{ textTransform: 'capitalize' }}>{r.type}</td>
                    <td className="mono">{new Date(r.date_generation).toLocaleString('fr-FR')}</td>
                    <td>{r.genere_par || '—'}</td>
                    <td>{r.format}</td>
                  </tr>
                ))}
                {historique.length === 0 && (
                  <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--muted)' }}>Aucun rapport généré pour le moment.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="foot-note">EMPREINTE · Suite RH — Pointage par reconnaissance faciale</div>
    </>
  );
}
