import { useEffect, useState, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { api } from '../api/client.js';
import { useAuth } from '../context/AuthContext.jsx';
import { StatCard } from '../components/ui.jsx';

const TOOLTIP_STYLE = {
  background: '#1A222C', border: '1px solid #232D38', borderRadius: 8,
  fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, color: '#F2F5F7',
};

function couleurBin(mid, seuilMin, seuilMax) {
  if (mid < seuilMin) return '#F1596B';
  if (mid < seuilMax) return '#F4B740';
  return '#48E8C9';
}

export default function AI() {
  const { role } = useAuth();
  const [stats, setStats] = useState(null);
  const [config, setConfig] = useState(null);
  const [brouillon, setBrouillon] = useState({ seuil_min: 0.45, seuil_max: 0.75, seuil_distance: 1.0 });
  const [enregistrement, setEnregistrement] = useState(false);
  const [message, setMessage] = useState('');

  const estAdmin = role === 'administrateur';

  const charger = useCallback(() => {
    Promise.all([api.get('/dashboard/reconnaissance'), api.get('/configuration')]).then(([s, c]) => {
      setStats(s);
      setConfig(c);
      setBrouillon({ seuil_min: c.seuil_min, seuil_max: c.seuil_max, seuil_distance: c.seuil_distance });
    });
  }, []);

  useEffect(charger, [charger]);

  async function enregistrerSeuils() {
    setEnregistrement(true); setMessage('');
    try {
      const c = await api.patch('/configuration', brouillon);
      setConfig(c);
      setMessage('✓ Seuils mis à jour.');
    } catch (err) {
      setMessage(`Erreur : ${err.message}`);
    } finally {
      setEnregistrement(false);
    }
  }

  if (!stats || !config) return <div className="center-msg"><div className="spinner" /></div>;

  const histo = stats.histogramme.map((b) => ({
    label: `${b.min.toFixed(2)}–${b.max.toFixed(2)}`,
    count: b.count,
    mid: (b.min + b.max) / 2,
  }));

  return (
    <>
      <div className="view-head">
        <div>
          <div className="eyebrow">Fonctions communes</div>
          <h1 className="view-title">Moteur de reconnaissance faciale</h1>
          <p className="view-sub">DeepFace (FaceNet) — vecteurs d'embeddings, score de similarité et seuils de décision.</p>
        </div>
      </div>

      <div className="stat-row">
        <StatCard label="Taux de réussite" value={stats.taux_reussite ?? '—'} suffix={stats.taux_reussite != null ? '%' : ''} />
        <StatCard label="Scans aujourd'hui" value={stats.scans_aujourd_hui} />
        <StatCard label="Vérifications RH" value={stats.en_attente} accent="amber" />
        <StatCard label="Rejetés" value={stats.rejete} accent="coral" />
      </div>

      <div className="config-panel">
        <div className="config-head">
          <h3 className="card__title">Configuration système — Seuils de reconnaissance</h3>
          <span className="config-badge">Configuration</span>
        </div>
        <p className="card__hint" style={{ marginTop: 2 }}>
          Réglage global (classe <em>Configuration</em>) appliqué à tous les pointages.
          {!estAdmin && ' Lecture seule — seul un administrateur peut modifier ces valeurs.'}
        </p>

        <div className="slider-row">
          <div className="slider-top">
            <span className="slider-name">Seuil minimum — en dessous : rejeté</span>
            <span className="slider-val sv-min">{brouillon.seuil_min.toFixed(2)}</span>
          </div>
          <input
            type="range" min="0.20" max="0.70" step="0.01" value={brouillon.seuil_min} disabled={!estAdmin}
            onChange={(e) => setBrouillon((b) => ({ ...b, seuil_min: Math.min(parseFloat(e.target.value), b.seuil_max - 0.05) }))}
          />
        </div>
        <div className="slider-row">
          <div className="slider-top">
            <span className="slider-name">Seuil maximum — au-dessus : validé auto</span>
            <span className="slider-val sv-max">{brouillon.seuil_max.toFixed(2)}</span>
          </div>
          <input
            type="range" min="0.50" max="0.98" step="0.01" value={brouillon.seuil_max} disabled={!estAdmin}
            onChange={(e) => setBrouillon((b) => ({ ...b, seuil_max: Math.max(parseFloat(e.target.value), b.seuil_min + 0.05) }))}
          />
        </div>

        <div className="slider-row">
          <div className="slider-top">
            <span className="slider-name">Seuil distance euclidienne — au-dessus : rejeté (dissimilarité)</span>
            <span className="slider-val sv-dist">{brouillon.seuil_distance.toFixed(2)}</span>
          </div>
          <input
            type="range" min="0.10" max="3.00" step="0.05" value={brouillon.seuil_distance} disabled={!estAdmin}
            onChange={(e) => setBrouillon((b) => ({ ...b, seuil_distance: parseFloat(e.target.value) }))}
          />
        </div>

        <div className="zone-bar">
          <span style={{ background: 'var(--coral)', width: `${brouillon.seuil_min * 100}%` }} />
          <span style={{ background: 'var(--amber)', width: `${(brouillon.seuil_max - brouillon.seuil_min) * 100}%` }} />
          <span style={{ background: 'var(--cyan)', width: `${(1 - brouillon.seuil_max) * 100}%` }} />
        </div>
        <div className="legend">
          <div className="legend-item"><span className="legend-dot" style={{ background: 'var(--coral)' }} />Rejeté</div>
          <div className="legend-item"><span className="legend-dot" style={{ background: 'var(--amber)' }} />En attente RH</div>
          <div className="legend-item"><span className="legend-dot" style={{ background: 'var(--cyan)' }} />Validé automatiquement</div>
        </div>

        {estAdmin && (
          <button className="btn btn--solid" style={{ marginTop: 18 }} onClick={enregistrerSeuils} disabled={enregistrement}>
            {enregistrement ? 'Enregistrement…' : 'Enregistrer les seuils'}
          </button>
        )}
        {message && <p className="card__hint" style={{ marginTop: 10 }}>{message}</p>}
      </div>

      <div className="card">
        <div className="card__head">
          <div className="card__title">Distribution des scores de similarité</div>
          <div className="card__hint">{stats.scans_aujourd_hui} scans · aujourd'hui</div>
        </div>
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={histo}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.06)" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: '#8996A6', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8996A6', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v} scans`, '']} />
              <Bar dataKey="count" radius={[5, 5, 0, 0]}>
                {histo.map((b, i) => <Cell key={i} fill={couleurBin(b.mid, config.seuil_min, config.seuil_max)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
}
