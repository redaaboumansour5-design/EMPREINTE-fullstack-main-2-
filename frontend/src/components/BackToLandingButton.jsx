import { useNavigate } from 'react-router-dom';

/**
 * BackToLandingButton — Bouton réutilisable de retour vers la Landing Page.
 *
 * Props :
 *   variant  : 'sidebar' | 'topbar' | 'icon-only'  (style d'affichage)
 *   label    : string personnalisable (défaut : "Accueil")
 */
export default function BackToLandingButton({
  variant = 'sidebar',
  label = 'Accueil',
}) {
  const navigate = useNavigate();

  const handleClick = (e) => {
    e.preventDefault();
    navigate('/');
  };

  // ─── Variante topbar : petit bouton icône + texte ───
  if (variant === 'topbar') {
    return (
      <button
        type="button"
        className="btn btn--back-topbar"
        onClick={handleClick}
        title="Retour à la page d'accueil"
        aria-label="Retour à l'accueil"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
        <span>{label}</span>
      </button>
    );
  }

  // ─── Variante icon-only : uniquement l'icône ───
  if (variant === 'icon-only') {
    return (
      <button
        type="button"
        className="btn btn--back-icon"
        onClick={handleClick}
        title={label || "Retour à l'accueil"}
        aria-label={label || "Retour à l'accueil"}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
          <polyline points="9 22 9 12 15 12 15 22" />
        </svg>
      </button>
    );
  }

  // ─── Variante sidebar (défaut) : nav-item complet ───
  return (
    <button
      type="button"
      className="nav-item nav-item--back"
      onClick={handleClick}
      title="Retour à la page d'accueil"
      aria-label="Retour à l'accueil"
    >
      <svg
        width="17"
        height="17"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
        <polyline points="9 22 9 12 15 12 15 22" />
      </svg>
      <span>{label}</span>
      <svg
        className="nav-item__arrow"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M19 12H5m7-7-7 7 7 7" />
      </svg>
    </button>
  );
}

