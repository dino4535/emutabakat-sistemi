# System Patterns

Mimari
- Frontend: React + React Router + React Query, Nginx ile servis
- Backend: FastAPI + SQLAlchemy + Pydantic, Redis cache (opsiyonel)
- DB: SQL Server (çok şirketli veri modeli)
- Deployment: Docker Compose (frontend, backend)

Ana Kalıplar
- Multi-Company: tüm sorgularda `company_id` filtreleri ve rol kontrolü
- KVKK: `kvkk_consents`, `kvkk_consent_deletion_logs` ile yasal kayıt ve snapshot
- Güvenlik: `FailedLoginTracker` ile deneme sayacı, kilitleme, IP/ISP kaydı
- Mutabakat: lazy PDF üretimi, bayi detaylarının ayrı tabloya yazılması
- Public Onay: token bazlı işlem, IP loglama, ActivityLogger

UI Kalıpları
- Tablolar için `.table-wrap` + `responsive-table` + `data-label` (mobil)
- 100vh iOS düzeltmesi: `--vh` custom birimi ve resize listener
- Mobilde header gizleme, hızlı işlemler sidebar’da
