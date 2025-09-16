# 🚀 Quick Start Guide

Szybki przewodnik uruchomienia aplikacji Merchant Center Monitor.

## ⚡ Szybkie uruchomienie (5 minut)

### 1. Przygotowanie środowiska

```bash
# Klonowanie i przejście do katalogu
cd merchant-monitor

# Instalacja zależności
pip install -r requirements.txt

# Konfiguracja zmiennych środowiskowych
cp env.example .env
```

### 2. Konfiguracja .env

Edytuj plik `.env` z podstawowymi ustawieniami:

```bash
# Minimalna konfiguracja do testów
GOOGLE_PROJECT_ID=your-project-id
MERCHANT_ACCOUNT_ID=your-merchant-account-id
MAIL_FROM=test@example.com
MAIL_TO=admin@example.com
SENDGRID_API_KEY=your-sendgrid-key

# Progi alertów (nisko dla testów)
ALERT_THRESHOLD_ABS=5
ALERT_THRESHOLD_DELTA=2
```

### 3. Uruchomienie aplikacji

```bash
# Uruchomienie serwera deweloperskiego
python run.py

# Aplikacja będzie dostępna na http://localhost:8080
```

### 4. Testowanie

```bash
# Sprawdzenie zdrowia aplikacji
curl http://localhost:8080/health

# Uruchomienie ręcznego sprawdzenia
curl -X POST http://localhost:8080/tasks/run

# Sprawdzenie statusu
curl http://localhost:8080/status

# Otwarcie dashboardu w przeglądarce
open http://localhost:8080/dashboard
```

## 🔧 Konfiguracja Google Cloud

### Service Account

1. **Utworzenie Service Account**:
```bash
gcloud iam service-accounts create merchant-monitor \
    --display-name="Merchant Center Monitor"
```

2. **Nadanie uprawnień**:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:merchant-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

3. **Utworzenie klucza**:
```bash
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=merchant-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Merchant Center

1. Przejdź do [Google Merchant Center](https://merchants.google.com/)
2. **Settings > Users**
3. Dodaj e-mail Service Account: `merchant-monitor@YOUR_PROJECT_ID.iam.gserviceaccount.com`
4. Nadaj rolę **Standard**
5. Skopiuj **Account ID** z URL lub ustawień

## 📧 Konfiguracja SendGrid

### 1. Utworzenie konta SendGrid

1. Zarejestruj się na [SendGrid](https://sendgrid.com/)
2. Zweryfikuj domenę nadawcy
3. Utwórz API Key z uprawnieniami **Mail Send**

### 2. Test e-maila

```bash
# Test wysłania e-maila
curl -X POST http://localhost:8080/tasks/run
# Sprawdź czy otrzymałeś e-mail alert
```

## 🧪 Testowanie z przykładowymi danymi

### Symulacja alertu

```bash
# Ustaw niskie progi w .env
ALERT_THRESHOLD_ABS=1
ALERT_THRESHOLD_DELTA=1

# Uruchom sprawdzenie
curl -X POST http://localhost:8080/tasks/run
```

### Sprawdzenie logów

```bash
# Logi aplikacji
tail -f app.log

# Logi z debugowaniem
LOG_LEVEL=DEBUG python run.py
```

## 🌐 Wdrożenie

### Google Cloud Run

```bash
# Użyj skryptu wdrożeniowego
./scripts/deploy.sh

# Lub ręcznie:
gcloud run deploy merchant-monitor \
    --source . \
    --region us-central1 \
    --allow-unauthenticated
```

### Vercel

```bash
# Instalacja Vercel CLI
npm i -g vercel

# Wdrożenie
vercel --prod
```

## 🔍 Rozwiązywanie problemów

### Częste błędy

1. **"Authentication failed"**
   - Sprawdź poprawność Service Account
   - Upewnij się, że SA ma dostęp do Merchant Center

2. **"No data returned"**
   - Sprawdź ID konta Merchant Center
   - Zweryfikuj filtry kraju i kontekstu

3. **"Email not sent"**
   - Sprawdź klucz API SendGrid
   - Zweryfikuj domenę nadawcy

### Debugowanie

```bash
# Uruchomienie z debugowaniem
LOG_LEVEL=DEBUG python run.py

# Sprawdzenie konfiguracji
python -c "from app.config import settings; print(settings.dict())"

# Test połączenia z API
python -c "from app.merchant_api import merchant_api; print(merchant_api.get_aggregate_product_statuses())"
```

## 📊 Monitorowanie

### Health checks

```bash
# Sprawdzenie statusu
curl http://localhost:8080/health

# Szczegółowy status
curl http://localhost:8080/status
```

### Logi

```bash
# Logi aplikacji
tail -f app.log

# Logi z filtrowaniem
grep "ERROR" app.log
grep "ALERT" app.log
```

## 🎯 Następne kroki

1. **Konfiguracja harmonogramu** - ustaw Cloud Scheduler lub Vercel Cron
2. **Dostosowanie progów** - ustaw odpowiednie wartości dla swojego biznesu
3. **Monitoring** - skonfiguruj alerty dla samej aplikacji
4. **Rozszerzenia** - dodaj dodatkowe kanały powiadomień (Slack, SMS)

## 📞 Wsparcie

- **Dokumentacja**: [README.md](README.md)
- **Przykłady**: [examples/](examples/)
- **Testy**: `pytest tests/ -v`

---

**Gotowe!** 🎉 Twoja aplikacja monitorująca Merchant Center jest uruchomiona i gotowa do pracy.
