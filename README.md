# 🧬 BioCarta - Персональный трекер здоровья

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

BioCarta — современное веб-приложение для отслеживания биомаркеров здоровья, анализа генетических данных и расчета биологического возраста.

![BioCarta Dashboard](https://via.placeholder.com/800x400/6366f1/ffffff?text=BioCarta+Dashboard)

## ✨ Основные возможности

### 📊 Импорт данных
- **InBody PDF** - автоматический парсинг отчетов InBody (вес, BMI, жир, мышцы)
- **Apple Health** - импорт из iPhone/Apple Watch (пульс, HRV, давление, SpO2, глюкоза)
- **CSV/Excel** - загрузка анализов в табличном формате
- **WHOOP** - интеграция с WHOOP браслетом (OAuth 2.0)
- **Oura Ring** - интеграция с Oura Ring (OAuth 2.0)

### 🧬 Генетический анализ
- Импорт данных **23andMe**, **AncestryDNA**, **Promethease**
- Анализ 10+ важных SNP:
  - MTHFR (метаболизм фолатов)
  - APOE (риск Альцгеймера)
  - FTO (предрасположенность к ожирению)
  - COMT, BDNF, ACE, ACTN3, CYP1A2, LCT, ALDH2
- Интерпретация результатов на русском языке

### 🕐 Биологический возраст
- **PhenoAge** (Levine 2018, Yale) - научно валидированный алгоритм
- **Simplified BioAge** - упрощенная версия для доступных биомаркеров
- Сравнение с хронологическим возрастом
- Рекомендации по улучшению показателей

### 📈 Визуализация и аналитика
- Дашборд с ключевыми метриками
- История изменений биомаркеров
- Статусы: оптимально / пограничное / вне нормы
- Экспорт данных в PDF

## 🚀 Быстрый старт

### Локальная разработка

```bash
# Клонируйте репозиторий
git clone https://github.com/LBD22/BioCarta.git
cd BioCarta

# Backend
cd backend
pip install -r requirements.txt
python migrate_db.py
python seeds/load_all.py
uvicorn main:app --reload --port 8080

# Frontend (в другом терминале)
cd frontend
pnpm install
pnpm dev
```

Откройте http://localhost:5173

### Production деплой на Render

1. Форкните репозиторий на GitHub
2. Зайдите на [Render.com](https://render.com)
3. New → Web Service → Connect GitHub
4. Render автоматически обнаружит `render.yaml`
5. Нажмите "Create Web Service"

Готово! Ваше приложение будет доступно по адресу `https://your-app.onrender.com`

## 📚 Документация

- [**Системная документация**](SYSTEM_DOCUMENTATION.md) - полная техническая документация
- [**Quick Start**](QUICK_START.md) - быстрый старт и troubleshooting
- [**Новые функции**](NEW_FEATURES.md) - описание всех возможностей
- [**История изменений**](CHANGELOG.md) - changelog

## 🏗️ Архитектура

### Backend (FastAPI)
```
backend/
├── api/          # FastAPI роутеры (auth, uploads, biomarkers, genetics, bioage)
├── core/         # Конфигурация, БД, безопасность
├── models/       # SQLAlchemy модели
├── domain/       # Бизнес-логика (парсинг, интеграции, расчеты)
├── seeds/        # Seed данные (50+ биомаркеров)
└── schemas/      # Pydantic схемы
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── main.tsx              # Главный компонент
│   ├── global.css            # Стили (Inter font, градиенты)
│   ├── bioage_page.tsx       # Биологический возраст
│   ├── genetics_page.tsx     # Генетика
│   └── integrations_page.tsx # WHOOP/Oura
└── vite.config.ts
```

## 🛠️ Технологии

**Backend:**
- FastAPI 0.104 - современный Python веб-фреймворк
- SQLAlchemy 2.0 - ORM для работы с БД
- Pydantic 2.5 - валидация данных
- pdfplumber - парсинг PDF
- pandas - обработка табличных данных

**Frontend:**
- React 18.2 - UI библиотека
- TypeScript 5.4 - типизация
- Vite 5.0 - сборщик
- Inter font - современный шрифт с кириллицей

**Deployment:**
- Docker - контейнеризация
- Render.com - хостинг
- SQLite / PostgreSQL - база данных

## 📊 API Endpoints

### Auth
- `POST /auth/register` - регистрация
- `POST /auth/login` - вход

### Uploads
- `POST /uploads` - загрузка файла
- `GET /uploads/suggestions` - кандидаты на парсинг
- `POST /uploads/confirm` - подтверждение

### Biomarkers
- `GET /biomarkers` - список биомаркеров
- `GET /biomarkers/{id}` - детали

### Genetics
- `POST /genetics/upload` - загрузка генетических данных
- `GET /genetics/report` - отчет

### BioAge
- `POST /bioage/calculate` - расчет биологического возраста

### Integrations
- `GET /integrations/whoop/auth` - WHOOP OAuth
- `POST /integrations/whoop/sync` - синхронизация WHOOP
- `GET /integrations/oura/auth` - Oura OAuth
- `POST /integrations/oura/sync` - синхронизация Oura

Полная документация API: `/docs` (Swagger UI)

## 🎨 Дизайн

- **Шрифт:** Inter (Google Fonts) с поддержкой кириллицы
- **Цветовая схема:** Indigo (#6366f1) → Purple (#a855f7) градиенты
- **Анимации:** Плавные CSS transitions и keyframes
- **Адаптивность:** Responsive design для всех устройств

## 🔒 Безопасность

- JWT токены для аутентификации
- Bcrypt для хеширования паролей
- CORS настроен для production
- OAuth 2.0 для сторонних интеграций

## 📝 Лицензия

MIT License - свободное использование для личных и коммерческих целей.

## 🤝 Вклад в проект

Приветствуются pull requests! Для крупных изменений сначала откройте issue для обсуждения.

## 📧 Контакты

- **GitHub:** [@LBD22](https://github.com/LBD22)
- **Email:** lbd22@biocarta.app
- **Production:** [biocarta-7wy5.onrender.com](https://biocarta-7wy5.onrender.com)

## 🙏 Благодарности

- [FastAPI](https://fastapi.tiangolo.com/) - отличный веб-фреймворк
- [React](https://reactjs.org/) - мощная UI библиотека
- [Inter](https://rsms.me/inter/) - красивый шрифт
- [Render](https://render.com/) - простой деплой

---

**Создано с ❤️ для здоровья и долголетия**
