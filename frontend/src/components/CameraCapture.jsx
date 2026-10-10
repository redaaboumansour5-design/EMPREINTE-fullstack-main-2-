import { useRef, useState, useEffect, useCallback } from 'react';

/**
 * Capture caméra via WebRTC (getUserMedia), conforme à stack.jpeg :
 * "Capture Vidéo — WebRTC — Accès à la webcam du navigateur pour capturer
 * la frame photo en temps réel."
 *
 * Props :
 *   onCapture(dataUrl: string)  — appelé avec l'image capturée (JPEG base64)
 *   label (string)              — texte du bouton de capture
 *   disabled (bool)
 */
export default function CameraCapture({ onCapture, label = 'Capturer', disabled = false }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [statut, setStatut] = useState('inactif'); // inactif | demande | actif | refuse | absent
  const [dernierApercu, setDernierApercu] = useState(null);

  const demarrer = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setStatut('absent');
      return;
    }
    setStatut('demande');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 480 }, height: { ideal: 360 }, facingMode: 'user' },
        audio: false,
      });
      // Un démontage rapide (StrictMode en dev, navigation rapide) peut survenir
      // pendant l'attente de getUserMedia : le <video> n'existe alors plus, on
      // arrête le flux immédiatement plutôt que de l'attacher dans le vide.
      if (!videoRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      try {
        await videoRef.current.play();
      } catch (playErr) {
        // AbortError : une requête play() plus récente a interrompu celle-ci —
        // bénin (typique de StrictMode en dev), on ignore silencieusement.
        if (playErr.name !== 'AbortError') throw playErr;
      }
      setStatut('actif');
    } catch (err) {
      console.error('Accès caméra refusé :', err);
      setStatut('refuse');
    }
  }, []);

  useEffect(() => {
    demarrer();
    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      if (videoRef.current) videoRef.current.srcObject = null;
    };
  }, [demarrer]);

  function capturer() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || statut !== 'actif') return;
    const w = video.videoWidth;
    const h = video.videoHeight;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext('2d');
    // Flip horizontal pour corriger l'effet miroir (selfie) de la caméra avant
    ctx.translate(w, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, w, h);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
    setDernierApercu(dataUrl);
    onCapture(dataUrl);
  }

  return (
    <div>
      <div className="cam-frame">
        {statut === 'actif' && (
          <div className="reticle-corners">
            <span /><span /><span /><span />
          </div>
        )}
        <video ref={videoRef} muted playsInline style={{ display: statut === 'actif' ? 'block' : 'none', transform: 'scaleX(-1)' }} />
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        {statut !== 'actif' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 10, color: 'var(--muted)', fontSize: '.82rem', textAlign: 'center', padding: 16 }}>
            {statut === 'demande' && <><div className="spinner" /><span>Demande d'accès à la caméra…</span></>}
            {statut === 'refuse' && <span>Accès caméra refusé. Autorisez la caméra dans les paramètres du navigateur puis réessayez.</span>}
            {statut === 'absent' && <span>Aucune caméra détectée sur cet appareil.</span>}
            {statut === 'inactif' && <span>Caméra inactive.</span>}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 14 }}>
        {statut === 'actif' ? (
          <button type="button" className="btn btn--solid" onClick={capturer} disabled={disabled}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="13" r="4" stroke="currentColor" strokeWidth="1.8"/><path d="M4 8.5a1.5 1.5 0 0 1 1.5-1.5H8l1-2h6l1 2h2.5A1.5 1.5 0 0 1 20 8.5V18a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 18V8.5Z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/></svg>
            {label}
          </button>
        ) : (
          <button type="button" className="btn" onClick={demarrer}>Réessayer l'accès caméra</button>
        )}
      </div>

      {dernierApercu && (
        <p className="cam-status">✓ Dernière capture prête à être envoyée.</p>
      )}
    </div>
  );
}
