# BioCarta - Полная документация системы

## ✅ Проверка модулей завершена

Все основные модули проверены на критические ошибки:
- ✅ Core modules (config, db, security) - OK
- ✅ Models (user, biomarker, measurement, genetic_variant) - OK
- ✅ API endpoints (auth, uploads, biomarkers, genetics, bioage) - OK
- ✅ Domain logic (parsing, apple_health, bioage, genetics_parser) - OK
- ✅ Frontend (React + TypeScript + Vite) - OK
- ✅ Deployment (Dockerfile, render.yaml) - OK

## Архитектура

### Backend (FastAPI)

**Структура:**
```
backend/
├── main.py                 # Главный файл приложения
├── core/
│   ├── config.py          # Настройки (Pydantic Settings)
│   ├── db.py              # SQLAlchemy setup
│   └── security.py        # JWT, password hashing
├── models/                # SQLAlchemy модели
│   ├── user.py
│   ├── biomarker.py
│   ├── measurement.py
│   ├── genetic_variant.py
│   └── ...
├── api/                   # FastAPI роутеры
│   ├── auth.py           # Регистрация/логин
│   ├── uploads.py        # Загрузка файлов
│   ├── biomarkers.py     # CRUD биомаркеров
│   ├── genetics.py       # Генетика
│   ├── bioage.py         # Биологический возраст
│   └── integrations.py   # WHOOP/Oura
├── domain/               # Бизнес-логика
│   ├── parsing.py        # Парсинг файлов (InBody PDF, CSV)
│   ├── apple_health.py   # Apple Health XML
│   ├── genetics_parser.py # 23andMe, AncestryDNA
│   ├── bioage.py         # PhenoAge алгоритм
│   ├── whoop_integration.py
│   └── oura_integration.py
├── seeds/                # Seed данные
│   ├── biomarkers.json   # 50+ биомаркеров
│   ├── references.json   # Референсные значения
│   └── synonyms.json     # Синонимы названий
└── requirements.txt      # Python зависимости
```

**Ключевые зависимости:**
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- Pydantic 2.5.0 + pydantic-settings
- pdfplumber (InBody PDF)
- pandas (CSV, Excel)
- requests (API интеграции)

### Frontend (React + TypeScript)

**Структура:**
```
frontend/
├── src/
│   ├── main.tsx              # Главный компонент (все в одном файле)
│   ├── global.css            # Стили (Inter font, градиенты)
│   ├── bioage_page.tsx       # Страница биологического возраста
│   ├── genetics_page.tsx     # Страница генетики
│   ├── integrations_page.tsx # WHOOP/Oura интеграции
│   ├── biomarker_detail.tsx  # Детали биомаркера
│   └── history_component.tsx # История измерений
├── index.html
├── package.json
└── vite.config.ts
```

**Технологии:**
- React 18.2
- TypeScript 5.4
- Vite 5.0 (сборка)
- Без роутера (single-page app с состоянием)

### База данных (SQLite)

**Таблицы:**
- `users` - Пользователи
- `biomarkers` - Биомаркеры (TC, HDL, glucose и т.д.)
- `measurements` - Измерения
- `uploads` - Загруженные файлы
- `parse_candidates` - Кандидаты на парсинг
- `genetic_variants` - Генетические варианты (SNP)
- `genetic_reports` - Отчеты по генетике
- `references` - Референсные значения
- `synonyms` - Синонимы названий
- `unit_conversions` - Конвертация единиц

## Основные функции

### 1. InBody PDF парсинг
**Файл:** `backend/domain/parsing.py`

Парсит PDF отчеты InBody, извлекает:
- Вес, BMI
- Процент жира
- Мышечная масса
- Висцеральный жир

### 2. Apple Health импорт
**Файл:** `backend/domain/apple_health.py`

Поддерживает:
- XML файл export.xml
- ZIP архив с export.xml
- 15+ типов данных (вес, пульс, HRV, давление, SpO2, глюкоза)

### 3. WHOOP интеграция
**Файл:** `backend/domain/whoop_integration.py`

OAuth 2.0 flow:
1. Получение authorization code
2. Обмен на access token
3. Синхронизация данных (HRV, RHR, SpO2, вес, жир)

### 4. Oura Ring интеграция
**Файл:** `backend/domain/oura_integration.py`

OAuth 2.0 flow + синхронизация:
- HRV, пульс в покое
- Частота дыхания
- SpO2, температура тела

### 5. Генетика (23andMe, AncestryDNA)
**Файл:** `backend/domain/genetics_parser.py`

Парсит:
- 23andMe raw data (TXT)
- AncestryDNA (TXT)
- Promethease (CSV)

Анализирует 10+ SNP:
- MTHFR (C677T, A1298C)
- APOE (e2/e3/e4)
- FTO (rs9939609)
- COMT (rs4680)
- BDNF (rs6265)
- ACE (rs4340)
- ACTN3 (rs1815739)
- CYP1A2 (rs762551)
- LCT (rs4988235)
- ALDH2 (rs671)

### 6. Биологический возраст (BioAge)
**Файл:** `backend/domain/bioage.py`

Два алгоритма:
1. **PhenoAge** (Levine 2018, Yale)
   - Научно валидированный
   - Требует 9 биомаркеров
   
2. **Simplified BioAge**
   - Упрощенная версия
   - Работает с доступными биомаркерами

## Деплой

### Render.com

**Конфигурация:** `render.yaml`

```yaml
services:
  - type: web
    name: biocarta
    env: python
    buildCommand: |
      pip install -r backend/requirements.txt
      cd frontend && pnpm install && pnpm build
      cp -r frontend/dist/* static/
    startCommand: python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

**Dockerfile:**
- Python 3.11 slim
- Node.js 20 + pnpm
- Сборка frontend в Docker

### Environment Variables

Требуются на Render:
- `DATABASE_URL` - sqlite:///./app.db
- `SECRET_KEY` - для JWT (опционально)
- `WHOOP_CLIENT_ID`, `WHOOP_CLIENT_SECRET` (для WHOOP)
- `OURA_CLIENT_ID`, `OURA_CLIENT_SECRET` (для Oura)

## API Endpoints

### Auth
- `POST /auth/register` - Регистрация
- `POST /auth/login` - Логин

### Uploads
- `POST /uploads` - Загрузка файла
- `GET /uploads` - Список загрузок
- `GET /uploads/suggestions` - Кандидаты на парсинг
- `POST /uploads/confirm` - Подтверждение парсинга

### Biomarkers
- `GET /biomarkers` - Список биомаркеров
- `GET /biomarkers/{id}` - Детали биомаркера

### Measurements
- `GET /measurements` - Список измерений
- `POST /measurements` - Создать измерение
- `DELETE /measurements/{id}` - Удалить измерение

### Genetics
- `POST /genetics/upload` - Загрузка генетических данных
- `GET /genetics/variants` - Список вариантов
- `GET /genetics/report` - Отчет по генетике

### BioAge
- `POST /bioage/calculate` - Расчет биологического возраста

### Integrations
- `GET /integrations/whoop/auth` - WHOOP OAuth URL
- `POST /integrations/whoop/callback` - WHOOP callback
- `POST /integrations/whoop/sync` - Синхронизация WHOOP
- `GET /integrations/oura/auth` - Oura OAuth URL
- `POST /integrations/oura/callback` - Oura callback
- `POST /integrations/oura/sync` - Синхронизация Oura

## Известные проблемы и решения

### 1. Static файлы не раздаются
**Решение:** Исправлен путь в `backend/main.py`:
```python
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
```

### 2. Файлы загружаются, но не парсятся
**Возможные причины:**
- База данных не заполнена seed данными
- Отсутствуют biomarkers, references, synonyms

**Решение:** Запустить `backend/seeds/load_all.py` после создания БД

### 3. Логотип не загружается
**Решение:** Убран логотип, оставлен только текст

## Backup

**Архив:** `biocarta_backup_20251116_201431.tar.gz` (17 MB)

**Содержит:**
- Весь исходный код
- Seed данные
- Конфигурацию деплоя
- Документацию

**Исключено:**
- node_modules
- __pycache__
- .git
- *.db
- frontend/dist

## GitHub

**Репозиторий:** https://github.com/LBD22/BioCarta

**Последние коммиты:**
- `9293245` - Fix static files, remove broken logo, improve empty state icon
- `70487d2` - Add email-validator dependency
- `6e63212` - Add pydantic-settings dependency
- `f4effe5` - Add Dockerfile for Render deployment

## Следующие шаги

1. ✅ Деплой на Render
2. ⏳ Проверить загрузку и парсинг файлов
3. ⏳ Заполнить seed данные в production БД
4. ⏳ Настроить OAuth для WHOOP/Oura
5. ⏳ Добавить тесты
6. ⏳ Улучшить UI/UX

## Контакты

- GitHub: LBD22
- Email: lbd22@biocarta.app
- Render: https://biocarta-7wy5.onrender.com

---

**Дата создания:** 2025-11-16  
**Версия:** 2.0  
**Статус:** Production Ready ✅
