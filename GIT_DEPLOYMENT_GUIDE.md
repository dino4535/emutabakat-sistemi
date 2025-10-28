# 🚀 GIT İLE DEPLOYMENT REHBERİ

## ✨ AVANTAJLAR

- ✅ Tek komutla tüm dosyaları sunucuya çek
- ✅ Versiyon kontrolü ve rollback imkanı
- ✅ Güncellemeler `git pull` ile saniyeler içinde
- ✅ Merge conflict yönetimi
- ✅ Team collaboration ready

---

## 📋 ADIM ADIM KURULUM

### **ADIM 1: Yerel Repository Hazırlığı** (2 dakika)

```bash
# Proje dizinine git
cd C:\Users\Oguz\.cursor\Proje1

# Git reposunu başlat (eğer başlatılmamışsa)
git init

# Tüm dosyaları stage'e ekle
git add .

# İlk commit
git commit -m "Initial commit - E-Mutabakat Sistemi v1.0"
```

---

### **ADIM 2: GitHub/GitLab'a Push** (3 dakika)

#### **Seçenek A: GitHub (Önerilen)**

1. **GitHub'da yeni repo oluştur:**
   - https://github.com/new adresine git
   - Repository name: `emutabakat-sistemi`
   - Visibility: **Private** (güvenlik için!)
   - README, .gitignore ekleme (zaten var)

2. **Remote ekle ve push et:**
```bash
# Remote ekle (REPO_URL'i kendi repo adresinle değiştir)
git remote add origin https://github.com/YOUR_USERNAME/emutabakat-sistemi.git

# Default branch adını main yap
git branch -M main

# Push et
git push -u origin main
```

#### **Seçenek B: GitLab**

```bash
# GitLab'da yeni proje oluştur (Private)
# Remote ekle
git remote add origin https://gitlab.com/YOUR_USERNAME/emutabakat-sistemi.git
git branch -M main
git push -u origin main
```

#### **Seçenek C: Kendi Git Sunucunuz (Gelişmiş)**

```bash
# Sunucunuzda bare repository oluşturun
ssh root@85.209.120.101
mkdir -p /opt/git/emutabakat-sistemi.git
cd /opt/git/emutabakat-sistemi.git
git init --bare
exit

# Yerel bilgisayardan push edin
git remote add origin root@85.209.120.101:/opt/git/emutabakat-sistemi.git
git push -u origin main
```

---

### **ADIM 3: Sunucuda Clone ve Deploy** (5 dakika)

#### **3.1. Git Kurulumu (Eğer yoksa)**
```bash
ssh root@85.209.120.101

# Git kurulu mu kontrol et
git --version

# Kurulu değilse:
apt-get update
apt-get install -y git

# veya CentOS/RHEL:
# yum install -y git
```

#### **3.2. Repository'yi Clone Et**

**Private repo için SSH key yapılandırması (Önerilen):**

```bash
# Sunucuda SSH key oluştur
ssh-keygen -t ed25519 -C "emutabakat@server"
# Enter tuşuna bas (default location)
# Passphrase opsiyonel

# Public key'i kopyala
cat ~/.ssh/id_ed25519.pub
```

GitHub/GitLab'da:
- Settings → SSH Keys
- Yukarıdaki key'i yapıştır

**Clone işlemi:**
```bash
# Uygulama dizinine git
cd /opt

# Repository'yi clone et (SSH kullanarak)
git clone git@github.com:YOUR_USERNAME/emutabakat-sistemi.git emutabakat

# veya HTTPS ile (her seferinde şifre soracak):
# git clone https://github.com/YOUR_USERNAME/emutabakat-sistemi.git emutabakat

cd emutabakat
```

#### **3.3. Environment Dosyasını Oluştur**

```bash
# .env dosyası oluştur (bu dosya git'te yok, güvenlik için)
cp env.production.example .env

# SECRET_KEY üret
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# .env dosyasını düzenle
nano .env
```

**.env dosyasına yapıştırın:**
```bash
DATABASE_URL=mssql+pyodbc://mutabakat_user:PASSWORD@85.209.120.57:1433/Mutabakat?driver=ODBC+Driver+17+for+SQL+Server
SECRET_KEY=<yukarıda-üretilen-key>
REDIS_PASSWORD=emutabakat2025
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@emutabakat.com
FLOWER_USER=admin
FLOWER_PASSWORD=admin2025
```

**Kaydet:** CTRL+X → Y → Enter

```bash
# İzinleri kısıtla
chmod 600 .env

# Gerekli dizinleri oluştur
mkdir -p fonts certificates uploads pdfs
```

---

### **ADIM 4: Portainer'da Deploy** (2 dakika)

1. **Portainer'a git:** https://85.209.120.101:9443
2. **Stacks** → **+ Add stack**
3. **Name:** `emutabakat`
4. **Build method:** Repository
   - **Repository URL:** `https://github.com/YOUR_USERNAME/emutabakat-sistemi` (veya SSH)
   - **Repository reference:** `refs/heads/main`
   - **Compose path:** `docker-compose.yml`
   - **Authentication:** Private repo ise gerekli
   
   **VEYA daha basit:**
   - **Build method:** Web editor
   - `/opt/emutabakat/docker-compose.yml` içeriğini yapıştır

5. **Environment variables:**
   - "Advanced mode" açın
   - `.env` dosyanızın içeriğini yapıştırın

6. **Deploy the stack**

---

## 🔄 GÜNCELLEME SÜRECİ (30 saniye!)

### **Yerel Değişikliklerden Sonra:**

```bash
# Yerel bilgisayarda
cd C:\Users\Oguz\.cursor\Proje1

# Değişiklikleri commit et
git add .
git commit -m "Feature: Added new functionality"

# Push et
git push origin main
```

### **Sunucuda Güncelleme:**

```bash
# Sunucuya SSH ile bağlan
ssh root@85.209.120.101
cd /opt/emutabakat

# Son değişiklikleri çek
git pull origin main

# Docker konteynerları yeniden başlat (sadece değişenler rebuild olur)
docker-compose down
docker-compose up -d --build
```

### **Portainer'da Güncelleme:**

1. **Stacks** → **emutabakat** → **Editor**
2. **Pull and redeploy** butonuna tıkla
3. Veya terminal'den:
```bash
docker-compose pull
docker-compose up -d
```

---

## 🎯 GİT WORKFLOW

### **Günlük Geliştirme:**

```bash
# 1. Yeni feature branch oluştur
git checkout -b feature/new-feature

# 2. Değişiklikleri yap
# ... kod değişiklikleri ...

# 3. Commit et
git add .
git commit -m "Add: New feature description"

# 4. Main'e merge et
git checkout main
git merge feature/new-feature

# 5. Push et
git push origin main

# 6. Sunucuda güncelle
ssh root@85.209.120.101
cd /opt/emutabakat && git pull && docker-compose up -d --build
```

### **Rollback (Geri Alma):**

```bash
# Son commit'i geri al
git revert HEAD
git push origin main

# Belirli bir commit'e geri dön
git log  # commit hash'lerini gör
git checkout <commit-hash>
git push origin main

# Sunucuda:
cd /opt/emutabakat
git pull
docker-compose up -d --build
```

---

## 🔒 GÜVENLİK BEST PRACTICES

### **1. .gitignore Kontrolü**
Hassas dosyalar git'e GİTMEMELİ:
```
✅ .env
✅ .env.production
✅ certificates/*.pfx
✅ certificates/*.key
✅ uploads/*
✅ *.log
```

### **2. Private Repository**
- Repository'yi **PRIVATE** yapın!
- Public yaparsanız API key'ler vs açığa çıkar

### **3. Secrets Management**
```bash
# Sunucuda .env dosyası için backup
cp .env .env.backup
chmod 600 .env.backup

# Git'te tutmayın, sadece example dosya:
git add env.production.example
```

### **4. Deploy Keys (GitHub/GitLab)**
- Personal access token yerine deploy key kullanın
- Read-only yeterli (sunucu sadece clone/pull yapacak)

---

## 🚀 OTOMATİK DEPLOYMENT (İleri Seviye)

### **GitHub Actions (CI/CD)**

`.github/workflows/deploy.yml` oluşturun:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /opt/emutabakat
            git pull origin main
            docker-compose up -d --build
```

**GitHub Secrets ekleyin:**
- `SERVER_HOST`: 85.209.120.101
- `SERVER_USER`: root
- `SERVER_SSH_KEY`: Sunucu SSH private key

### **GitLab CI/CD**

`.gitlab-ci.yml` oluşturun:

```yaml
deploy:
  stage: deploy
  only:
    - main
  script:
    - ssh root@85.209.120.101 "cd /opt/emutabakat && git pull && docker-compose up -d --build"
```

### **Webhook ile Otomatik Deploy**

Sunucuda webhook listener kurun:
```bash
# webhook paketi kur
apt-get install -y webhook

# /opt/webhook/deploy.sh oluştur
#!/bin/bash
cd /opt/emutabakat
git pull origin main
docker-compose up -d --build
```

GitHub/GitLab'da webhook ekle:
- URL: http://85.209.120.101:9000/hooks/deploy
- Events: Push

---

## 📊 BRANCH STRATEJİSİ

### **Basit Strateji (Küçük Ekip):**
```
main (production)
  ├── feature/new-feature
  ├── fix/bug-fix
  └── hotfix/critical-bug
```

### **Gelişmiş Strateji (Büyük Ekip):**
```
main (production)
  └── develop (staging)
        ├── feature/new-feature
        ├── fix/bug-fix
        └── release/v1.1
```

---

## 🆘 SORUN GİDERME

### **Git clone başarısız (Authentication)**

```bash
# SSH key'i kontrol et
ssh -T git@github.com

# HTTPS kullanıyorsan token oluştur:
# GitHub → Settings → Developer settings → Personal access tokens
# Repo access yetkisi ver

# Token ile clone:
git clone https://<TOKEN>@github.com/YOUR_USERNAME/emutabakat-sistemi.git
```

### **Git pull conflict (Merge hatası)**

```bash
# Sunucudaki local değişiklikleri kaybet, remote'u al
cd /opt/emutabakat
git fetch origin
git reset --hard origin/main

# veya local değişiklikleri sakla:
git stash
git pull
git stash pop
```

### **Permission denied**

```bash
# Git dizin sahipliğini düzelt
chown -R root:root /opt/emutabakat

# veya git user oluştur:
useradd -m git
chown -R git:git /opt/emutabakat
```

---

## ✅ KONTROL LİSTESİ

### **Git Setup:**
- [ ] Git init yapıldı
- [ ] .gitignore kontrol edildi
- [ ] İlk commit yapıldı
- [ ] GitHub/GitLab'da private repo oluşturuldu
- [ ] Remote eklendi ve push edildi

### **Sunucu Setup:**
- [ ] Git kurulu
- [ ] SSH key oluşturuldu ve eklendi
- [ ] Repository clone edildi
- [ ] .env dosyası oluşturuldu ve yapılandırıldı
- [ ] Gerekli dizinler oluşturuldu

### **Deploy:**
- [ ] Portainer'da stack oluşturuldu
- [ ] Konteynerlar çalışıyor
- [ ] Sistem erişilebilir

---

## 🎉 SONUÇ

**Git ile deployment çok daha profesyonel!**

### **Avantajlar:**
- ✅ Tek komutla deployment: `git pull && docker-compose up -d --build`
- ✅ Versiyon kontrolü ve history
- ✅ Rollback imkanı
- ✅ Team collaboration ready
- ✅ CI/CD entegrasyonu kolay

### **Sonraki Adımlar:**
1. Git repo'yu push edin
2. Sunucuda clone edin
3. Portainer'da deploy edin
4. CI/CD pipeline kurun (opsiyonel)

---

**Başarılar! 🚀**

_Sorularınız için: support@example.com_

