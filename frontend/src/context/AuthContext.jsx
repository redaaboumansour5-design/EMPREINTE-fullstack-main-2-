import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { api, setToken } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [utilisateur, setUtilisateur] = useState(null);
  const [role, setRole] = useState(null);
  const [pret, setPret] = useState(false); // évite un flash "non connecté" au premier rendu

  useEffect(() => {
    const token = localStorage.getItem('empreinte_token');
    const roleSauvegarde = localStorage.getItem('empreinte_role');
    if (!token) {
      setPret(true);
      return;
    }
    api.get('/auth/moi')
      .then((data) => {
        setUtilisateur(data);
        setRole(roleSauvegarde || data.role);
      })
      .catch(() => {
        setToken(null);
        localStorage.removeItem('empreinte_role');
      })
      .finally(() => setPret(true));
  }, []);

  const login = useCallback(async (email, password, { espace, mode_demande } = {}) => {
    const data = await api.post('/auth/login', { email, password, espace, mode_demande });

    setToken(data.access_token);
    localStorage.setItem('empreinte_role', data.role);
    setUtilisateur(data.utilisateur);
    setRole(data.role);
    return data;
  }, []);

  const logout = useCallback(() => {
    api.post('/auth/logout').catch(() => {});
    setToken(null);
    localStorage.removeItem('empreinte_role');
    setUtilisateur(null);
    setRole(null);
  }, []);

  const value = { utilisateur, role, pret, estConnecte: !!utilisateur, login, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth doit être utilisé sous <AuthProvider>');
  return ctx;
}
