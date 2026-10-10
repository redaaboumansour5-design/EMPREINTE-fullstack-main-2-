export function StatCard({ label, value, suffix, icon, accent, delta, deltaType = 'flat' }) {
  return (
    <div className={`stat-card reticle${accent ? ` rc-${accent}` : ''}`} data-accent={accent || 'cyan'}>
      <div className="stat-top">
        <span className="stat-label">{label}</span>
        {icon && (
          <span
            className="stat-icon"
            style={{
              background: `var(--${accent || 'cyan'}-dim)`,
              color: `var(--${accent || 'cyan'})`,
            }}
          >
            {icon}
          </span>
        )}
      </div>
      <div className="stat-value">
        {value}
        {suffix && <small>{suffix}</small>}
      </div>
      {delta && <div className={`stat-delta delta-${deltaType}`}>{delta}</div>}
    </div>
  );
}

const TAG_CLASSES = {
  VALIDE: 'tag-cyan',
  APPROUVE: 'tag-cyan',
  'À l\'heure': 'tag-cyan',
  EN_ATTENTE: 'tag-amber',
  SOUMISE: 'tag-amber',
  Retard: 'tag-violet',
  REJETE: 'tag-coral',
  Absence: 'tag-coral',
};

const TAG_LABELS = {
  VALIDE: 'Validé',
  EN_ATTENTE: 'En attente RH',
  REJETE: 'Rejeté',
  APPROUVE: 'Approuvée',
  SOUMISE: 'Soumise',
};

export function StatutTag({ statut }) {
  const cls = TAG_CLASSES[statut] || 'tag-slate';
  const label = TAG_LABELS[statut] || statut;
  return <span className={`tag ${cls}`}>{label}</span>;
}

const TYPE_CLASSES = { ENTREE: 'tag-cyan', SORTIE: 'tag-violet' };
const TYPE_ICONS = {
  ENTREE: (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" style={{ marginRight: 3 }}>
      <path d="M5 12h14m-7-7 7 7-7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  SORTIE: (
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" style={{ marginRight: 3 }}>
      <path d="M19 12H5m7-7-7 7 7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
};
export function TypeTag({ type }) {
  const cls = TYPE_CLASSES[type] || 'tag-slate';
  const label = type === 'ENTREE' ? 'Entrée' : type === 'SORTIE' ? 'Sortie' : type;
  return <span className={`tag ${cls}`} style={{ display: 'inline-flex', alignItems: 'center' }}>{TYPE_ICONS[type]}{label}</span>;
}
