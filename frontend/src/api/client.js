const BASE_URL = import.meta.env.VITE_API_URL || ''; // '' -> utilise le proxy vite en dev

function getToken() {
  return localStorage.getItem('empreinte_token');
}

export function setToken(token) {
  if (token) localStorage.setItem('empreinte_token', token);
  else localStorage.removeItem('empreinte_token');
}

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const token = getToken();
  const finalHeaders = { ...headers };
  if (body !== undefined) finalHeaders['Content-Type'] = 'application/json';
  if (token) finalHeaders['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}/api${path}`, {
    method,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  const contentType = res.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await res.json() : await res.blob();

  if (!res.ok) {
    const message = (data && data.erreur) || `Erreur ${res.status}`;
    throw new ApiError(message, res.status, data);
  }
  return data;
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
  put: (path, body) => request(path, { method: 'PUT', body }),
  patch: (path, body) => request(path, { method: 'PATCH', body }),
  delete: (path) => request(path, { method: 'DELETE' }),

  /** Télécharge un export CSV et déclenche le téléchargement navigateur. */
  async download(path, filename) {
    const token = getToken();
    const res = await fetch(`${BASE_URL}/api${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new ApiError(data.erreur || `Erreur ${res.status}`, res.status, data);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 800);
  },
};

export { ApiError };
