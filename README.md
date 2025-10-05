# Guia Completo — Backend + Frontend (Local e Deploy)
**Autor(a): Camilly Cunha da Silva**  
**RU: 3607375**

Este documento consolida o passo‑a‑passo para subir **backend (Django + DRF)** e **frontend (React + Vite)** localmente, além de um roteiro de deploy simples em VM Linux.

---

## 1) Backend — instalação local
### 1.1 Ambiente
```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 1.2 `settings.py` essenciais
- `INSTALLED_APPS`: `rest_framework`, `corsheaders`, `rest_framework_simplejwt.token_blacklist` (opcional), `accounts`, `learning`, `courses`, `quizzes`
- `MIDDLEWARE`: inclua `corsheaders.middleware.CorsMiddleware`
- `AUTH_USER_MODEL = "accounts.User"`
- `REST_FRAMEWORK` com JWT + Session
- `SIMPLE_JWT` para **UUID**:
```python
from datetime import timedelta
SIMPLE_JWT = {
  "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
  "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
  "AUTH_HEADER_TYPES": ("Bearer",),
  "USER_ID_FIELD": "uuid",
  "USER_ID_CLAIM": "user_id",
}
```
- **CORS (dev)**: `CORS_ALLOW_ALL_ORIGINS = True`
- **E-mail (dev)**: `EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"`
- **Media**: `MEDIA_URL = "/media/"`, `MEDIA_ROOT = <pasta media>`

### 1.3 URLs do projeto
```python
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
  path("accounts/", include("accounts.urls")),
  path("learning/", include("learning.urls")),
  path("courses/", include("courses.urls")),
  path("quizzes/", include("quizzes.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 1.4 Migrações e admin
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --email admin@local.test
python manage.py runserver 8000
```

### 1.5 Endpoints principais
- **Auth**: `POST /accounts/auth/login/`, `POST /accounts/auth/refresh/`, `POST /accounts/auth/logout/`
- **Users**: `POST /accounts/users/register/`, `PATCH /accounts/users/update-user/<uuid>/`
- **Learning**: CRUD cursos/módulos/aulas/vídeos, `POST /learning/courses/<id>/enroll/`, `POST /learning/progress/tick/`
- **Quizzes**: CRUD quizzes/questions/options, tentativas em `/quizzes/attempts/`

---

## 2) Frontend — instalação local
### 2.1 Setup
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios react-router-dom
```
Crie `.env`:
```
VITE_API_BASE=http://localhost:8000
```

### 2.2 Cliente Axios com refresh
Vide `src/api.ts`:
```ts
import axios from "axios";
const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE });
api.interceptors.request.use((c)=>{ const a=localStorage.getItem("access"); if(a) c.headers.Authorization=`Bearer ${a}`; return c; });
let refreshing=false;
api.interceptors.response.use(r=>r, async (e)=>{
  const o=e.config;
  if(e.response?.status===401 && !o._retry){
    if(refreshing) return Promise.reject(e);
    o._retry=true; refreshing=true;
    try{
      const refresh=localStorage.getItem("refresh"); if(!refresh) throw new Error();
      const {data}=await axios.post(`${import.meta.env.VITE_API_BASE}/accounts/auth/refresh/`,{refresh});
      localStorage.setItem("access", data.access); refreshing=false; o.headers.Authorization=`Bearer ${data.access}`; return api(o);
    }catch{ refreshing=false; localStorage.removeItem("access"); localStorage.removeItem("refresh"); window.location.href="/login";}
  }
  return Promise.reject(e);
});
export default api;
```

### 2.3 Rotas e Login
- Proteção via `Protected.tsx` e tela `Login.tsx` chamando `POST /accounts/auth/login/`.
- Exemplo de consumo: `GET /learning/courses/` no `Dashboard`.

### 2.4 Rodar
```bash
npm run dev
```
Acesse `http://localhost:5173`.

---

## 3) Troubleshooting rápido
- **404 no login**: use `/accounts/auth/login/` (ou adicione compat `/accounts/login/` e `/api/...` no backend).
- **500 no login**: adicione `SIMPLE_JWT["USER_ID_FIELD"]="uuid"`.
- **CORS no navegador**: `CORS_ALLOW_ALL_ORIGINS=True` no backend (somente dev).
- **401 recorrente**: confira `VITE_API_BASE` e reinicie o Vite após alterar `.env`.
- **CSRF 403**: não use `withCredentials` nos requests JWT.

---

## 4) Deploy simples em VM (Ubuntu)
1. **Pacotes**: `sudo apt install -y python3-venv nginx git`
2. **App user**: `sudo adduser app && sudo su - app`
3. **Código**: `git clone <repo> apprepo && cd apprepo`
4. **Venv**: `python3 -m venv .venv && source .venv/bin/activate`
5. **Dependências**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
6. **Gunicorn (systemd)** em `127.0.0.1:8001`
7. **Nginx** proxy + `client_max_body_size 200M` (para vídeos)
8. **HTTPS**: `certbot --nginx -d SEU_DOMINIO`
9. **Frontend**: `npm run build` e sirva o **build estático** pelo Nginx (ou deploy separado).

Exemplo de bloco Nginx para o front:
```
location / {
  root /var/www/frontend/dist;
  try_files $uri /index.html;
}
```

---

## 5) Checklist final
- [ ] `AUTH_USER_MODEL=accounts.User`
- [ ] `SIMPLE_JWT.USER_ID_FIELD="uuid"`
- [ ] `CORS_ALLOW_ALL_ORIGINS=True` (dev)
- [ ] URLs: `accounts/`, `learning/`, `courses/`, `quizzes/`
- [ ] Migrations ok e admin criado
- [ ] Front `.env` com `VITE_API_BASE`
- [ ] Login/refresh funcionando (tokens em localStorage)

---

**Camilly Cunha da Silva — RU 3607375**
