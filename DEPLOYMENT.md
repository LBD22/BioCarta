# BioCarta Deployment Guide

## Railway Deployment

### Prerequisites
- GitHub account connected to Railway
- Railway account (free tier available)

### Environment Variables

Set these in Railway dashboard:

```bash
# Database (automatically provided by Railway PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Application
SECRET_KEY=your-secret-key-here-min-32-chars
STORAGE_DIR=/app/storage

# Optional
ALLOWED_ORIGINS=https://your-domain.railway.app
```

### Deployment Steps

1. **Connect GitHub Repository**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose BioCarta repository

2. **Add PostgreSQL Database**
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set DATABASE_URL

3. **Configure Environment Variables**
   - Go to project settings
   - Add SECRET_KEY (generate with: `openssl rand -hex 32`)
   - Add STORAGE_DIR=/app/storage

4. **Deploy**
   - Railway will automatically build and deploy
   - Wait for deployment to complete (~5-10 minutes)

5. **Verify**
   - Open the provided Railway URL
   - Test registration and file upload

### Database Migrations

Seed data is automatically loaded on first startup.

### Monitoring

- View logs in Railway dashboard
- Set up alerts for errors
- Monitor resource usage

### Scaling

Free tier limits:
- 500 hours/month
- 512MB RAM
- 1GB storage

For production:
- Upgrade to Hobby plan ($5/month)
- Add more resources as needed

### Backup

Railway automatically backs up PostgreSQL database.

For manual backup:
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

### Troubleshooting

**Build fails:**
- Check Dockerfile syntax
- Verify all dependencies in requirements.txt

**Database connection error:**
- Verify DATABASE_URL is set
- Check PostgreSQL service is running

**File upload fails:**
- Ensure STORAGE_DIR exists
- Check file permissions

### Custom Domain

1. Go to project settings
2. Click "Domains"
3. Add custom domain
4. Update DNS records as instructed
