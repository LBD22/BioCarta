# BioCarta - Quick Start Guide

## 🚀 Быстрый старт

### Локальная разработка

#### 1. Установка зависимостей

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
pnpm install
```

#### 2. Инициализация базы данных

```bash
cd backend
python migrate_db.py
python seeds/load_all.py
```

#### 3. Запуск

**Backend (терминал 1):**
```bash
cd backend
uvicorn main:app --reload --port 8080
```

**Frontend (терминал 2):**
```bash
cd frontend
pnpm dev
```

Откройте http://localhost:5173

### Production деплой на Render

#### 1. Создайте репозиторий на GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/BioCarta.git
git push -u origin main
```

#### 2. Подключите к Render
1. Зайдите на https://dashboard.render.com
2. New → Web Service
3. Connect GitHub repository
4. Render автоматически обнаружит `render.yaml`
5. Нажмите "Create Web Service"

#### 3. Настройте переменные окружения
В Render Dashboard → Environment:
- `DATABASE_URL` = `sqlite:///./app.db`
- `SECRET_KEY` = (сгенерируйте случайную строку)

#### 4. Деплой
Render автоматически:
- Установит зависимости
- Соберет frontend
- Запустит backend
- Выдаст URL: `https://your-app.onrender.com`

## 📝 Первый вход

**Демо-аккаунт:**
- Email: `demo@biocarta.com`
- Пароль: `demo123`

Или создайте новый аккаунт через "Создать аккаунт"

## 📤 Загрузка данных

### InBody PDF
1. Перейдите на вкладку "Загрузка"
2. Выберите PDF файл InBody
3. Система автоматически распознает:
   - Вес, BMI
   - Процент жира
   - Мышечную массу
   - Висцеральный жир

### Apple Health
1. На iPhone: Health app → Профиль → Экспорт данных
2. Получите `export.zip`
3. Загрузите в BioCarta
4. Система импортирует все доступные данные

### CSV/Excel
1. Подготовьте файл с колонками:
   - Название биомаркера
   - Значение
   - Единица измерения
   - Дата
2. Загрузите файл
3. Подтвердите распознанные данные

### Генетика (23andMe, AncestryDNA)
1. Скачайте raw data с сайта провайдера
2. Загрузите TXT файл в BioCarta
3. Система проанализирует важные SNP

## 🔗 Интеграции

### WHOOP
1. Зарегистрируйте приложение на https://developer.whoop.com
2. Получите `CLIENT_ID` и `CLIENT_SECRET`
3. Добавьте в Environment Variables на Render
4. В BioCarta: Интеграции → WHOOP → Подключить

### Oura Ring
1. Зарегистрируйте приложение на https://cloud.ouraring.com/oauth/applications
2. Получите `CLIENT_ID` и `CLIENT_SECRET`
3. Добавьте в Environment Variables
4. В BioCarta: Интеграции → Oura → Подключить

## 🧬 Биологический возраст

Для расчета PhenoAge нужны биомаркеры:
- Альбумин (Albumin)
- Креатинин (Creatinine)
- Глюкоза (Glucose)
- C-реактивный белок (CRP)
- Лимфоциты (Lymphocytes %)
- Средний объем эритроцитов (MCV)
- Ширина распределения эритроцитов (RDW)
- Щелочная фосфатаза (ALP)
- Лейкоциты (WBC)

Если не все биомаркеры доступны, система использует упрощенный алгоритм.

## 📊 Дашборд

**Статусы биомаркеров:**
- 🟢 **Оптимально** - в пределах нормы
- 🟡 **Пограничное** - близко к границе
- 🔴 **Вне нормы** - требует внимания
- ⚪ **Нет данных** - нет референсных значений

## 🛠️ Troubleshooting

### Файлы не парсятся
1. Проверьте, что seed данные загружены:
   ```bash
   python backend/seeds/load_all.py
   ```
2. Проверьте формат файла (PDF, CSV, XML)
3. Посмотрите логи в консоли backend

### OAuth не работает
1. Проверьте `CLIENT_ID` и `CLIENT_SECRET`
2. Убедитесь, что Redirect URI совпадает:
   - WHOOP: `https://your-app.onrender.com/integrations/whoop/callback`
   - Oura: `https://your-app.onrender.com/integrations/oura/callback`

### Static файлы не загружаются
1. Проверьте, что frontend собран:
   ```bash
   cd frontend && pnpm build
   ```
2. Проверьте, что файлы скопированы в `static/`:
   ```bash
   cp -r frontend/dist/* static/
   ```

## 📚 Дополнительная документация

- `SYSTEM_DOCUMENTATION.md` - Полная техническая документация
- `NEW_FEATURES.md` - Описание всех функций
- `CHANGELOG.md` - История изменений
- `API_DOCS.md` - API документация (автоматически на `/docs`)

## 🆘 Поддержка

- GitHub Issues: https://github.com/LBD22/BioCarta/issues
- Email: lbd22@biocarta.app

## 📄 Лицензия

MIT License - свободное использование для личных и коммерческих целей.
