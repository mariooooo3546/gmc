# 🚀 Merchant Center Monitor

Aplikacja webowa monitorująca status produktów w Google Merchant Center z automatycznymi alertami e-mailowymi. Aplikacja sprawdza co 30 minut liczbę produktów odrzuconych/zawieszonych i wysyła alerty gdy przekroczone zostaną określone progi.

## ✨ Funkcje

- **Automatyczne monitorowanie** - sprawdzanie statusu produktów co 30 minut
- **Inteligentne alerty** - powiadomienia e-mailowe przy przekroczeniu progów
- **Dashboard webowy** - wizualizacja danych i trendów
- **API REST** - pełne API do integracji z innymi systemami
- **Historia alertów** - śledzenie wszystkich wysłanych powiadomień
- **Elastyczna konfiguracja** - dostosowanie progów i ustawień

## 🏗️ Architektura

- **Backend**: Python 3.12 + FastAPI
- **Baza danych**: Google Cloud Firestore
- **Autoryzacja**: Google Service Account OAuth 2.0
- **E-mail**: SendGrid API
- **Hosting**: Google Cloud Run / Vercel
- **Harmonogram**: Cloud Scheduler / Vercel Cron

## 🚀 Szybki start

### 1. Wymagania

- Python 3.12+
- Konto Google Cloud Platform
- Konto Google Merchant Center
- Konto SendGrid (lub inny dostawca SMTP)

### 2. Konfiguracja Google Cloud

#### Włączenie Merchant API

1. Przejdź do [Google Cloud Console](https://console.cloud.google.com/)
2. Wybierz swój projekt
3. Włącz API:
   - Google Merchant API
   - Cloud Firestore API
   - Cloud Scheduler API (jeśli używasz Cloud Run)

#### Utworzenie Service Account

1. W Google Cloud Console przejdź do **IAM & Admin > Service Accounts**
2. Kliknij **Create Service Account**
3. Wprowadź nazwę: `merchant-monitor`
4. Dodaj role:
   - `Firestore User`
   - `Service Account Token Creator`
5. Utwórz klucz JSON i pobierz plik

#### Konfiguracja Merchant Center

1. Przejdź do [Google Merchant Center](https://merchants.google.com/)
2. W **Settings > Users** dodaj e-mail Service Account jako użytkownika
3. Nadaj rolę **Standard** lub wyższą
4. Zapisz ID konta Merchant Center

### 3. Konfiguracja SendGrid

1. Zarejestruj się na [SendGrid](https://sendgrid.com/)
2. Utwórz API Key z uprawnieniami **Mail Send**
3. Skonfiguruj domenę nadawcy (lub użyj weryfikacji pojedynczego nadawcy)

### 4. Instalacja lokalna

```bash
# Klonowanie repozytorium
git clone <repository-url>
cd merchant-monitor

# Instalacja zależności
pip install -r requirements.txt

# Konfiguracja zmiennych środowiskowych
cp env.example .env
# Edytuj .env z własnymi wartościami

# Uruchomienie aplikacji
python -m app.main
```

### 5. Konfiguracja zmiennych środowiskowych

Skopiuj `env.example` do `.env` i uzupełnij:

```bash
# Google Cloud Configuration
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_SERVICE_ACCOUNT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
GOOGLE_SERVICE_ACCOUNT_KEY=path/to/service-account-key.json
MERCHANT_ACCOUNT_ID=your-merchant-account-id

# Alert Configuration
ALERT_THRESHOLD_ABS=25
ALERT_THRESHOLD_DELTA=10
ALERT_COUNTRY=PL
ALERT_REPORTING_CONTEXT=SHOPPING_ADS

# Email Configuration
MAIL_FROM=alerts@yourdomain.com
MAIL_TO=admin@yourdomain.com
SENDGRID_API_KEY=your-sendgrid-api-key

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🌐 Wdrożenie

### Google Cloud Run

1. **Przygotowanie obrazu Docker**:
```bash
# Budowanie obrazu
docker build -t gcr.io/YOUR_PROJECT_ID/merchant-monitor .

# Wypchnięcie do Container Registry
docker push gcr.io/YOUR_PROJECT_ID/merchant-monitor
```

2. **Wdrożenie na Cloud Run**:
```bash
gcloud run deploy merchant-monitor \
  --image gcr.io/YOUR_PROJECT_ID/merchant-monitor \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars ENVIRONMENT=production
```

3. **Konfiguracja Cloud Scheduler**:
```bash
gcloud scheduler jobs create http merchant-monitor-cron \
  --schedule "*/30 * * * *" \
  --uri "https://merchant-monitor-REGION-PROJECT_ID.a.run.app/tasks/run" \
  --http-method POST \
  --headers Content-Type=application/json \
  --time-zone UTC
```

### Vercel

1. **Instalacja Vercel CLI**:
```bash
npm i -g vercel
```

2. **Wdrożenie**:
```bash
vercel --prod
```

3. **Konfiguracja zmiennych środowiskowych** w Vercel Dashboard

4. **Cron job** jest automatycznie skonfigurowany w `vercel.json`

## 📊 API Endpoints

### `GET /health`
Sprawdzenie stanu aplikacji.

**Odpowiedź**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-16T13:00:00Z",
  "version": "1.0.0"
}
```

### `POST /tasks/run`
Uruchomienie pojedynczego sprawdzenia statusu produktów.

**Odpowiedź**:
```json
{
  "checked_at": "2025-01-16T13:00:00Z",
  "country": "PL",
  "reporting_context": "SHOPPING_ADS",
  "totals": {
    "approved": 12345,
    "disapproved": 78,
    "limited": 12,
    "pending": 34
  },
  "delta": {"disapproved": 9},
  "alert_sent": true,
  "top_issues": [
    {
      "code": "MISSING_GTIN",
      "description": "Product is missing a GTIN",
      "count": 25
    }
  ]
}
```

### `GET /status`
Pobranie aktualnego statusu i ostatnich metryk.

### `GET /alerts/history`
Historia wysłanych alertów.

### `GET /dashboard`
Dashboard webowy z wizualizacją danych.

## 🔧 Konfiguracja alertów

### Progi alertów

- **`ALERT_THRESHOLD_ABS`** - bezwzględny próg (domyślnie 25)
  - Alert gdy disapproved + limited + suspended > próg
- **`ALERT_THRESHOLD_DELTA`** - próg zmiany (domyślnie 10)
  - Alert gdy wzrost disapproved >= próg względem poprzedniego sprawdzenia

### Przykład konfiguracji

```bash
# Alert gdy więcej niż 50 produktów ma problemy
ALERT_THRESHOLD_ABS=50

# Alert gdy wzrost disapproved o 15 lub więcej
ALERT_THRESHOLD_DELTA=15

# Monitorowanie tylko Polski
ALERT_COUNTRY=PL

# Tylko Shopping Ads
ALERT_REPORTING_CONTEXT=SHOPPING_ADS
```

## 📧 Format alertów e-mailowych

Alerty zawierają:

- **Podsumowanie statusu** - liczba produktów w każdym stanie
- **Trendy** - zmiana względem poprzedniego sprawdzenia
- **Top 5 problemów** - najczęstsze kody błędów z opisami
- **Linki** - bezpośrednie linki do Merchant Center
- **Kontekst** - kraj, reporting context, czas sprawdzenia

## 🗄️ Struktura bazy danych

### Kolekcja `checks`
Snapshoty statusów produktów:
```json
{
  "timestamp": "2025-01-16T13:00:00Z",
  "country": "PL",
  "reporting_context": "SHOPPING_ADS",
  "totals": {...},
  "delta_disapproved": 9,
  "alert_sent": true,
  "top_issues": [...]
}
```

### Kolekcja `email_alerts`
Historia wysłanych e-maili:
```json
{
  "to": "admin@example.com",
  "subject": "🚨 Merchant Center Alert",
  "body": "<html>...</html>",
  "sent_at": "2025-01-16T13:00:00Z"
}
```

### Kolekcja `settings`
Konfiguracja aplikacji:
```json
{
  "alert_threshold_abs": 25,
  "alert_threshold_delta": 10,
  "alert_country": "PL",
  "alert_reporting_context": "SHOPPING_ADS",
  "mail_to": "admin@example.com"
}
```

## 🧪 Testowanie

### Testy jednostkowe

```bash
# Uruchomienie testów
pytest

# Z pokryciem kodu
pytest --cov=app
```

### Test integracyjny

```bash
# Test z mockowanym API
pytest tests/test_integration.py -v
```

### Test ręczny

```bash
# Uruchomienie pojedynczego sprawdzenia
curl -X POST http://localhost:8080/tasks/run

# Sprawdzenie statusu
curl http://localhost:8080/status
```

## 🔍 Monitorowanie i logi

### Logi aplikacji

Aplikacja loguje:
- Sprawdzenia statusu produktów
- Wysłane alerty
- Błędy API
- Operacje bazy danych

### Metryki

- Czas odpowiedzi API
- Liczba sprawdzeń
- Liczba wysłanych alertów
- Błędy autoryzacji

### Health checks

Endpoint `/health` zwraca status aplikacji dla monitoringu zewnętrznego.

## 🚨 Rozwiązywanie problemów

### Częste problemy

1. **Błąd autoryzacji Google**
   - Sprawdź poprawność Service Account
   - Upewnij się, że SA ma dostęp do Merchant Center
   - Zweryfikuj scope OAuth

2. **Brak danych w API**
   - Sprawdź ID konta Merchant Center
   - Upewnij się, że produkty są w odpowiednim kraju/kontekście
   - Sprawdź filtry w zapytaniu API

3. **E-maile nie są wysyłane**
   - Zweryfikuj klucz API SendGrid
   - Sprawdź domenę nadawcy
   - Sprawdź logi aplikacji

4. **Błędy bazy danych**
   - Sprawdź uprawnienia Firestore
   - Zweryfikuj strukturę kolekcji
   - Sprawdź indeksy Firestore

### Debugowanie

```bash
# Uruchomienie z debugowaniem
LOG_LEVEL=DEBUG python -m app.main

# Sprawdzenie konfiguracji
python -c "from app.config import settings; print(settings.dict())"
```

## 🔄 Migracja z Content API

Jeśli używasz starego Content API for Shopping:

1. **Aktualizacja autoryzacji**:
   - Scope zmienia się z `https://www.googleapis.com/auth/content` na `https://www.googleapis.com/auth/content`
   - Endpoint API: `https://merchantapi.googleapis.com/` zamiast `https://shoppingcontent.googleapis.com/`

2. **Aktualizacja zapytań**:
   - Nowe endpointy w Merchant API
   - Inne formaty odpowiedzi
   - Nowe filtry i parametry

3. **Testowanie**:
   - Uruchom testy z nowym API
   - Porównaj wyniki ze starym systemem
   - Zweryfikuj alerty

## 📈 Rozszerzenia

### Możliwe ulepszenia

1. **Dodatkowe progi**:
   - Procentowy próg (np. 5% disapproved)
   - Próg dla konkretnych kategorii produktów
   - Próg dla nowych problemów

2. **Więcej kanałów alertów**:
   - Slack notifications
   - SMS alerts
   - Webhook notifications

3. **Zaawansowana analityka**:
   - Wykresy trendów
   - Predykcje problemów
   - Analiza sezonowości

4. **Integracje**:
   - Google Analytics
   - Google Ads
   - Inne systemy e-commerce

## 📄 Licencja

MIT License - zobacz plik LICENSE dla szczegółów.

## 🤝 Wsparcie

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Dokumentacja**: [Wiki](https://github.com/your-repo/wiki)
- **Discord**: [Community Server](https://discord.gg/your-server)

## 🙏 Podziękowania

- Google Merchant API team
- FastAPI community
- SendGrid team
- Wszystkim kontrybutorom

---

**Uwaga**: Ta aplikacja używa nowego Google Merchant API, które zastępuje Content API for Shopping (wycofywane 18.08.2026).
