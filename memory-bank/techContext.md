# Tech Context

Stack
- Frontend: React 18, React Router, React Query, axios, react-toastify
- Styles: saf CSS modülleri, sayfa bazlı stylesheet’ler
- Backend: FastAPI, SQLAlchemy, Pydantic, Uvicorn, Redis (opsiyonel)
- PDF/İmza: pyHanko, pikepdf
- DB: SQL Server
- Deployment: Docker, Docker Compose, Nginx (frontend)

Geliştirme
- `frontend/` Vite dev server; `index.css` global kurallar
- `--vh` custom birimi için `main.jsx`’te resize listener
- API base path: `/api/*`

Kısıtlar
- Multi-company güvenliği: `company_id` ve rol kontrolleri zorunlu
- Pydantic validasyonları (EmailStr, enum UserRole)
- Büyük tablolar mobilde kart formatına dönüşmeli
