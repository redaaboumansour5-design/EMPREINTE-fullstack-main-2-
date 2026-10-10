import { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';
import { StatutTag } from '../components/ui.jsx';

/**
 * Demandes — Page unifiée Congés + Télétravail.
 *
 * Onglets : Toutes | Congé | Télétravail
 * Stats combinées + tableau unifié + modal création avec sélecteur de type.
 */
export default function Demandes() {
  const { role } = useAuth();
  const [demandes, setDemandes] = useState([]);
  const [resume, setResume] = useState({
    en_attente: 0,
    approuvees_ce_mois: 0,
    rejetees_ce_mois: 0,
  });
  const [chargement, setChargement] = useState(true);
  const [formOuvert, setFormOuvert] = useState(false);
  const [filtreType, setFiltreType] = useState('');

  const peutValider = ['manager', 'rh', 'administrateur'].includes(role);

  const charger = useCallback(() => {
    setChargement(true);
    const params = filtreType ? `?type=${filtreType}` : '';
    Promise.all([
      api.get(`/demandes${params}`),
      api.get('/demandes/resume'),
    ])
      .then(([d, r]) => {
        setDemandes(d);
        setResume(r);
      })
      .catch(() => {})
      .finally(() => setChargement(false));
  }, [filtreType]);

  useEffect(charger, [charger]);

  async function decider(id, statut) {
    try {
      await api.patch(`/demandes/${id}/decider`, { statut });
      charger();
    } catch (err) {
      alert(err.message);
    }
  }

  function TypeBadge({ type }) {
    const isConge = type === 'conge';
    return (
      <span
        className={`tag ${isConge ? 'tag-amber' : 'tag-cyan'}`}
        style={{ textTransform: 'capitalize' }}
      >
        {isConge ? 'Congé' : 'Télétravail'}
      </span>
    );
  }

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">
            {role === 'employe' ? 'Mes demandes' : 'Gestion des demandes'}
          </div>
          <h1 className="view-title">Demandes</h1>
          <p className="view-sub">
            {peutValider
              ? 'Gérez les demandes de congé et télétravail de votre équipe.'
              : 'Consultez et créez vos demandes de congé et télétravail.'}
          </p>
        </div>
        <button
          className="btn btn--solid"
          onClick={() => setFormOuvert(true)}
        >
          + Nouvelle demande
        </button>
      </div>

      {/* Stats combinées */}
      <div className="rt-summary">
        <div className="rt-chip reticle-sm rc-amber">
          <div className="num" style={{ color: 'var(--amber)' }}>
            {resume.en_attente}
          </div>
          <div className="lbl">En attente de décision</div>
        </div>
        <div className="rt-chip">
          <div className="num" style={{ color: 'var(--cyan)' }}>
            {resume.approuvees_ce_mois}
          </div>
          <div className="lbl">Approuvées ce mois</div>
        </div>
        <div className="rt-chip">
          <div className="num" style={{ color: 'var(--coral)' }}>
            {resume.rejetees_ce_mois}
          </div>
          <div className="lbl">Rejetées ce mois</div>
        </div>
      </div>

      {/* Onglets de filtre */}
      <div className="chips demandes-tabs" style={{ marginBottom: 16 }}>
        {[
          { value: '', label: 'Toutes' },
          { value: 'conge', label: 'Congé' },
          { value: 'teletravail', label: 'Télétravail' },
        ].map((tab) => (
          <button
            key={tab.value}
            className={`chip ${filtreType === tab.value ? 'active' : ''}`}
            onClick={() => setFiltreType(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tableau des demandes */}
      {chargement ? (
        <div className="center-msg">
          <div className="spinner" />
        </div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Employé</th>
                <th>Département</th>
                <th>Période</th>
                <th>Motif</th>
                <th>Statut</th>
                {peutValider && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {demandes.map((d) => (
                <tr key={`${d.type_demande}-${d.id}`}>
                  <td>
                    <TypeBadge type={d.type_demande} />
                  </td>
                  <td>
                    <div className="cell-name">{d.employe.nom_complet}</div>
                    <div className="cell-sub">{d.employe.matricule}</div>
                  </td>
                  <td>{d.employe.departement || '—'}</td>
                  <td className="mono">
                    {d.date_debut} → {d.date_fin}
                  </td>
                  <td>{d.motif || '—'}</td>
                  <td>
                    <StatutTag statut={d.statut} />
                  </td>
                  {peutValider && (
                    <td>
                      {d.statut === 'SOUMISE' ? (
                        <div className="row-actions">
                          <button
                            className="btn btn--sm btn--solid"
                            onClick={() => decider(d.id, 'APPROUVE')}
                          >
                            Valider
                          </button>
                          <button
                            className="btn btn--sm"
                            onClick={() => decider(d.id, 'REJETE')}
                          >
                            Refuser
                          </button>
                        </div>
                      ) : (
                        <span className="card__hint">Traité</span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {demandes.length === 0 && (
                <tr>
                  <td
                    colSpan={peutValider ? 7 : 6}
                    style={{ textAlign: 'center', color: 'var(--muted)' }}
                  >
                    Aucune demande.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {formOuvert && (
        <NouvelleDemandeModal
          onClose={() => setFormOuvert(false)}
          onCreated={() => {
            setFormOuvert(false);
            charger();
          }}
        />
      )}
    </>
  );
}

/* ==========================================================================
   Modal de création de demande (unifié : Congé / Télétravail)
   ========================================================================== */
function NouvelleDemandeModal({ onClose, onCreated }) {
  const [typeDemande, setTypeDemande] = useState('conge');
  const [dateDebut, setDateDebut] = useState('');
  const [dateFin, setDateFin] = useState('');
  const [motif, setMotif] = useState('');
  const [typeConge, setTypeConge] = useState('paye');
  const [recurrence, setRecurrence] = useState('ponctuel');
  const [lieuTeletravail, setLieuTeletravail] = useState('domicile');
  const [justificatif, setJustificatif] = useState('');
  const [erreur, setErreur] = useState('');
  const [envoi, setEnvoi] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setEnvoi(true);
    setErreur('');
    try {
      const payload = {
        type_demande: typeDemande,
        date_debut: dateDebut,
        date_fin: dateFin,
        motif,
      };

      if (typeDemande === 'conge') {
        payload.type_conge = typeConge;
        if (justificatif) payload.justificatif = justificatif;
      } else {
        payload.recurrence = recurrence;
        payload.lieu_teletravail = lieuTeletravail;
      }

      await api.post('/demandes', payload);
      onCreated();
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(4,6,9,.65)',
        zIndex: 80,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 20,
      }}
      onClick={onClose}
    >
      <div
        className="card"
        style={{ maxWidth: 440, width: '100%' }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="card__head">
          <div className="card__title">Nouvelle demande</div>
          <button className="btn btn--sm btn--ghost" onClick={onClose}>
            Fermer
          </button>
        </div>

        <form onSubmit={onSubmit}>
          {/* Sélecteur du type de demande */}
          <div className="login-field">
            <label>Type de demande</label>
            <div className="empreinte-toggle" style={{ marginTop: 4 }}>
              <button
                type="button"
                className={`empreinte-toggle__btn ${typeDemande === 'conge' ? 'active' : ''}`}
                onClick={() => setTypeDemande('conge')}
              >
                Congé
              </button>
              <button
                type="button"
                className={`empreinte-toggle__btn ${typeDemande === 'teletravail' ? 'active' : ''}`}
                onClick={() => setTypeDemande('teletravail')}
              >
                Télétravail
              </button>
            </div>
          </div>

          {typeDemande === 'conge' ? (
            <>
              <div className="login-field">
                <label>Type de congé</label>
                <select value={typeConge} onChange={(e) => setTypeConge(e.target.value)}>
                  <option value="paye">Payé</option>
                  <option value="maladie">Maladie</option>
                  <option value="exceptionnel">Exceptionnel</option>
                </select>
              </div>
              <div className="login-field">
                <label>Justificatif</label>
                <input
                  type="text"
                  value={justificatif}
                  onChange={(e) => setJustificatif(e.target.value)}
                  placeholder="Référence, certificat, etc."
                />
              </div>
            </>
          ) : (
            <>
              <div className="login-field">
                <label>Récurrence</label>
                <select value={recurrence} onChange={(e) => setRecurrence(e.target.value)}>
                  <option value="ponctuel">Ponctuel</option>
                  <option value="recurrent">Récurrent</option>
                </select>
              </div>
              <div className="login-field">
                <label>Lieu de télétravail</label>
                <select value={lieuTeletravail} onChange={(e) => setLieuTeletravail(e.target.value)}>
                  <option value="domicile">Domicile</option>
                  <option value="bureau">Bureau</option>
                  <option value="hybride">Hybride</option>
                </select>
              </div>
            </>
          )}

          <div className="login-field">
            <label>Date de début</label>
            <input
              type="date"
              value={dateDebut}
              onChange={(e) => setDateDebut(e.target.value)}
              required
            />
          </div>
          <div className="login-field">
            <label>Date de fin</label>
            <input
              type="date"
              value={dateFin}
              onChange={(e) => setDateFin(e.target.value)}
              required
            />
          </div>
          <div className="login-field">
            <label>Motif</label>
            <input
              type="text"
              value={motif}
              onChange={(e) => setMotif(e.target.value)}
              placeholder={
                typeDemande === 'conge'
                  ? 'Congé personnel, maladie...'
                  : 'Garde d\'enfant, rendez-vous...'
              }
            />
          </div>

          {erreur && <div className="login-error">{erreur}</div>}

          <button
            type="submit"
            className="btn btn--solid"
            style={{ width: '100%', justifyContent: 'center', marginTop: 18 }}
            disabled={envoi}
          >
            {envoi ? 'Envoi…' : 'Envoyer la demande'}
          </button>
        </form>
      </div>
    </div>
  );
}
