# Frontend Build Debug

## Detaylı Log İçin:

```bash
cd /opt/emutabakat
docker-compose build --no-cache --progress=plain frontend 2>&1 | tail -100
```

## Muhtemel Sorunlar:

### 1. Memory Yetersizliği
Frontend build işlemi çok RAM tüketebilir. Eğer "JavaScript heap out of memory" hatası varsa:

**Çözüm:** Build memory limitini artır

### 2. Package Uyumsuzluğu  
Node.js versiyonu veya package uyumsuzluğu

### 3. Terser Minification Hatası
Vite terser ile minify ederken hata verebilir

## Hızlı Çözüm:

Vite config'i basitleştirerek tekrar dene:
```

Ancak ben şimdilik **daha basit bir frontend build yapılandırması** hazırlayayım:

