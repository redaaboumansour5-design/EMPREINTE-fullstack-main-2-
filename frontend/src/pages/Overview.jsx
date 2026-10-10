import { useEffect, useState } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';
import { StatCard } from '../components/ui.jsx';

const TOOLTIP_STYLE = {
  background: '#FFFFFF', border: '1px solid #DDE2EA', borderRadius: 8,
  fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, color: '#2C3E50',
                  boxShadow: '0 4px 12px rgba(15,23,42,.08), 0 1px 3px rgba(0,0,0,.05)',
};

export default function Overview() {
  const { utilisateur, role } = useAuth();

  const [vue, setVue] = useState(null); // vue-ensemble (globale)
  const [vueMensuel, setVueMensuel] = useState(null); // vue/mois
  const [tendance, setTendance] = useState([]);
  const [departements, setDepartements] = useState([]);
  const [joursAffiches, setJoursAffiches] = useState(10);
  const [seriesActives, setSeriesActives] = useState({
    presentiel: true,
    teletravail: true,
    absence: true,
  });

  const [erreur, setErreur] = useState('');
  const [chargement, setChargement] = useState(true);

  useEffect(() => {
    let annule = false;
    setChargement(true);

    Promise.all([
      api.get('/dashboard/vue-ensemble'),
      api.get('/dashboard/mois'),
      api.get(`/dashboard/tendance?jours=${joursAffiches}`),
      api.get('/dashboard/par-departement'),
    ])
      .then(([v, m, t, d]) => {
        if (annule) return;
        setVue(v);
        setVueMensuel(m);
        setTendance(
          t.map((j) => ({
            ...j,
            dateLabel: new Date(j.date).toLocaleDateString('fr-FR', {
              weekday: 'short', day: '2-digit', month: '2-digit',
            }),
          }))
        );
        setDepartements(d);
      })
      .catch((err) => !annule && setErreur(err.message))
      .finally(() => !annule && setChargement(false));

    return () => { annule = true; };
  }, [joursAffiches]);

  const nomAffiche = utilisateur?.prenom || utilisateur?.nom_complet?.split(' ')[0] || utilisateur?.identifiant_admin || '';
  const roleLabel = role === 'administrateur' ? 'Espace Administration' : role === 'rh' ? 'Espace RH' : role === 'manager' ? 'Espace Manager' : 'Espace Employé';
  const sousTitre = role === 'employe'
    ? 'Votre suivi de présence du mois, basé sur les données réelles de pointage et sur les demandes approuvées.'
    : role === 'manager'
      ? 'Vue de votre service, construite à partir des statuts de présence et des validations enregistrées.'
      : 'Vue globale de l’organisation, issue des données de présence et des indications de validation en base.';

  const toggleSerie = (key) => {
    setSeriesActives((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const seriesOptions = [
    { key: 'presentiel', label: 'Présentiel', color: '#2D6A4F' },
    { key: 'teletravail', label: 'Télétravail', color: '#92580F' },
    { key: 'absence', label: 'Absence', color: '#9B2335' },
  ];

  if (chargement) return <div className="center-msg"><div className="spinner" /></div>;
  if (erreur) return <div className="center-msg">Erreur : {erreur}</div>;

  return (
    <>
      <div className="view-head anim-fade-in-up">
        <div>
          <div className="eyebrow">{roleLabel}</div>
          <h1 className="view-title">Bonjour, {nomAffiche}</h1>
          <p className="view-sub">{sousTitre}</p>
        </div>
      </div>

      <div className="stat-row">
        {role === 'employe' && vueMensuel && (
          <>
            <div className="anim-fade-in-up anim-delay-1" style={{gridRow:1,gridColumn:1}}><StatCard
              label="Jours présentiel (mois)"
              value={vueMensuel.jours_presentiel}
              accent="cyan"
              delta={`${vueMensuel.jours_teletravail} jours télétravail`}
              deltaType="up"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M8 7V3m8 4V3M6 21h12a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-2"><StatCard
              label="Retards (mois)"
              value={vueMensuel.retards}
              accent="violet"
              delta="heure limite 08:30"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/><path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-3"><StatCard
              label="Absences (mois)"
              value={vueMensuel.absences}
              accent="coral"
              delta={`${vueMensuel.conges ?? 0} j. congé · ${vueMensuel.feries ?? 0} j. férié`}
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-4"><StatCard
              label="Ponctualité (30j)"
              value={vueMensuel.taux_ponctualite_30j}
              suffix="%"
              accent="amber"
              delta="avant 08:30"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" stroke="currentColor" strokeWidth="2"/></svg>}
            /></div>
          </>
        )}

        {role !== 'employe' && vue && (
          <>
            <div className="anim-fade-in-up anim-delay-1"><StatCard
              label="Présents aujourd'hui" value={vue.presents} suffix={`/ ${vue.effectif_total}`}
              accent="cyan" delta={`${vue.taux_presence} % de l'effectif${vue.en_attente_validation ? ` · ${vue.en_attente_validation} à valider` : ''}`} deltaType="up"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M4 12.5l5 5L20 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-2"><StatCard
              label="Télétravail" value={vue.teletravail} accent="amber" delta="présentiel + télétravail = présents"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><rect x="3" y="5" width="18" height="11" rx="1.4" stroke="currentColor" strokeWidth="2"/><path d="M8 20h8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-3"><StatCard
              label="Retards" value={vue.retards} accent="violet" delta="arrivées après 08:30"
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" strokeWidth="2"/><path d="M12 8v4l2.5 1.8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>}
            /></div>
            <div className="anim-fade-in-up anim-delay-4"><StatCard
              label="Absences" value={vue.absences} accent="coral"
              delta={vue.jours_ouvre === false ? 'jour non ouvré' : `${vue.conges ?? 0} en congé · ${vue.feries ?? 0} férié`}
              icon={<svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>}
            /></div>
          </>
        )}
      </div>

      <div className="grid-2">
        <div className="card anim-fade-in-up anim-delay-5" style={{ gridColumn: '1 / -1' }}>
          <div className="card__head">
            <div className="card__title">Tendance de présence — {joursAffiches} derniers jours ouvrés</div>
            <div className="card__hint">Sélectionnez les courbes à afficher</div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
            <select
              value={joursAffiches}
              onChange={(e) => setJoursAffiches(Number(e.target.value))}
              style={{ border: '1px solid #DDE2EA', borderRadius: 8, padding: '8px 10px', background: '#fff' }}
            >
              <option value={7}>7 jours</option>
              <option value={10}>10 jours</option>
              <option value={15}>15 jours</option>
              <option value={30}>30 jours</option>
            </select>
            {seriesOptions.map((serie) => (
              <button
                key={serie.key}
                type="button"
                onClick={() => toggleSerie(serie.key)}
                style={{
                  border: `1px solid ${serie.color}`,
                  borderRadius: 999,
                  padding: '6px 10px',
                  background: seriesActives[serie.key] ? `${serie.color}15` : '#fff',
                  color: seriesActives[serie.key] ? serie.color : '#4B5563',
                  cursor: 'pointer',
                  fontSize: 12,
                }}
              >
                {seriesActives[serie.key] ? '●' : '○'} {serie.label}
              </button>
            ))}
          </div>
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={360}>
              <AreaChart data={tendance}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,.06)" vertical={false} />
                <XAxis dataKey="dateLabel" tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: 12, color: '#4B5563' }} />
                {seriesActives.presentiel && <Area type="monotone" dataKey="presentiel" name="Présentiel" stackId="1" stroke="#2D6A4F" fill="rgba(45,106,79,.12)" strokeWidth={1.8} />}
                {seriesActives.teletravail && <Area type="monotone" dataKey="teletravail" name="Télétravail" stackId="1" stroke="#92580F" fill="rgba(146,88,15,.10)" strokeWidth={1.8} />}
                {seriesActives.absence && <Area type="monotone" dataKey="absence" name="Absence" stackId="1" stroke="#9B2335" fill="rgba(155,35,53,.10)" strokeWidth={1.8} />}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {role !== 'employe' && (
          <div className="card anim-fade-in-up anim-delay-6">
            <div className="card__head">
              <div className="card__title">{role === 'manager'
                ? `Taux de présence — ${utilisateur?.departement?.nom || 'Service'}`
                : 'Taux de présence par service'}</div>
            </div>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={departements} layout="vertical" margin={{ left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,.06)" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} unit="%" />
                  <YAxis type="category" dataKey="departement" width={120} tick={{ fill: '#2C3E50', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`, 'Présence']} />
                  <Bar dataKey="taux_presence" fill="var(--primary)" radius={[0, 6, 6, 0]} maxBarSize={26} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      
    </>
  );
}

