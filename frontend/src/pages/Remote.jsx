import { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';
import { StatutTag } from '../components/ui.jsx';

export default function Remote() {
  const { role } = useAuth();
  const [demandes, setDemandes] = useState([]);
  const [resume, setResume] = useState({ en_attente: 0, approuvees_ce_mois: 0, rejetees_ce_mois: 0 });
  const [chargement, setChargement] = useState(true);
  const [formOuvert, setFormOuvert] = useState(false);

  const peutValider = ['manager', 'rh', 'administrateur'].includes(role);

  const charger = useCallback(() => {
    setChargement(true);
    Promise.all([api.get('/teletravail/demandes'), api.get('/teletravail/resume')])
      .then(([d, r]) => { setDemandes(d); setResume(r); })
      .finally(() => setChargement(false));
  }, []);

  useEffect(charger, [charger]);

  async function decider(id, statut) {
    try {
      await api.patch(`/teletravail/demandes/${id}/decider`, { statut });
      charger();
    } catch (err) {
      alert(err.message);
    }
  }

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">Espace Manager</div>
          <h1 className="view-title">Télétravail</h1>
          <p className="view-sub">{peutValider ? 'Validez les demandes soumises par votre équipe.' : 'Déclarez vos périodes de télétravail.'}</p>
        </div>
        <button className="btn btn--solid" onClick={() => setFormOuvert(true)}>+ Nouvelle demande</button>
      </div>

      <div className="rt-summary">
        <div className="rt-chip reticle-sm rc-amber"><div className="num" style={{ color: 'var(--amber)' }}>{resume.en_attente}</div><div className="lbl">En attente de décision</div></div>
        <div className="rt-chip"><div className="num" style={{ color: 'var(--cyan)' }}>{resume.approuvees_ce_mois}</div><div className="lbl">Approuvées ce mois</div></div>
        <div className="rt-chip"><div className="num" style={{ color: 'var(--coral)' }}>{resume.rejetees_ce_mois}</div><div className="lbl">Rejetées ce mois</div></div>
      </div>

      {chargement ? (
        <div className="center-msg"><div className="spinner" /></div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Employé</th><th>Département</th><th>Période</th><th>Motif</th><th>Statut</th>
                {peutValider && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={d.id}>
                  <td><div className="cell-name">{d.employe.nom_complet}</div><div className="cell-sub">{d.employe.matricule}</div></td>
                  <td>{d.employe.departement || '—'}</td>
                  <td className="mono">{d.date_debut} → {d.date_fin}</td>
                  <td>{d.motif}</td>
                  <td><StatutTag statut={d.statut} /></td>
                  {peutValider && (
                    <td>
                      {d.statut === 'SOUMISE' ? (
                        <div className="row-actions">
                          <button className="btn btn--sm btn--solid" onClick={() => decider(d.id, 'APPROUVE')}>Valider</button>
                          <button className="btn btn--sm" onClick={() => decider(d.id, 'REJETE')}>Refuser</button>
                        </div>
                      ) : (
                        <span className="card__hint">Traité</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr><td colSpan={peutValider ? 6 : 5} style={{ textAlign: 'center', color: 'var(--muted)' }}>Aucune demande.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {formOuvert && <NouvelleDemandeModal onClose={() => setFormOuvert(false)} onCreated={() => { setFormOuvert(false); charger(); }} />}
    </>
  );
}

function NouvelleDemandeModal({ onClose, onCreated }) {
  const [dateDebut, setDateDebut] = useState('');
  const [dateFin, setDateFin] = useState('');
  const [motif, setMotif] = useState('');
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setEnvoi(true); setErreur('');
    try {
      await api.post('/teletravail/demandes', { date_debut: dateDebut, date_fin: dateFin, motif });
      onCreated();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(4,6,9,.65)', zIndex: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }} onClick={onClose}>
      <div className="card" style={{ maxWidth: 420, width: '100%' }} onClick={(e) => e.stopPropagation()}>
        <div className="card__head">
          <div className="card__title">Déclarer une période de télétravail</div>
          <button className="btn btn--sm btn--ghost" onClick={onClose}>Fermer</button>
        </div>
        <form onSubmit={onSubmit}>
          <div className="login-field">
            <label>Date de début</label>
            <input type="date" value={dateDebut} onChange={(e) => setDateDebut(e.target.value)} required />
          </div>
          <div className="login-field">
            <label>Date de fin</label>
            <input type="date" value={dateFin} onChange={(e) => setDateFin(e.target.value)} required />
          </div>
          <div className="login-field">
            <label>Motif</label>
            <input type="text" value={motif} onChange={(e) => setMotif(e.target.value)} placeholder="Garde d'enfant, rendez-vous…" />
          </div>
          {erreur && <div className="login-error">{erreur}</div>}
          <button type="submit" className="btn btn--solid" style={{ width: '100%', justifyContent: 'center', marginTop: 18 }} disabled={envoi}>
            {envoi ? 'Envoi…' : 'Envoyer la demande'}
          </button>
        </form>
      </div>
    </div>
  );
}
