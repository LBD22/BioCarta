import React, { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './global.css'

// Types
interface User {
  email: string
  token: string
}

interface Biomarker {
  id: number
  code: string
  name_en: string
  name_ru: string
  category: string
  unit_std: string
  status?: string
  value?: number
  date?: string
  reference?: { low: number; high: number }
}

interface Upload {
  id: number
  file_path: string
  file_type: string
  status: string
  created_at: string
}

interface Suggestion {
  candidate_id: number
  upload_id?: number
  original_name: string
  value_raw: string
  unit_raw: string
  sample_datetime_raw: string
  suggested_biomarker_id: number | null
  suggested_biomarker_code: string | null
  suggested_biomarker_name: string | null
  confidence: string
}

interface UploadProgress {
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'complete' | 'error'
  uploadId?: number
}

// API Helper
const api = {
  async call(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token')
    const headers: any = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    
    const res = await fetch(endpoint, { ...options, headers: { ...headers, ...options.headers } })
    if (!res.ok) throw new Error(`Ошибка API: ${res.status}`)
    return res.json()
  },
  
  async upload(file: File, onProgress?: (progress: number) => void) {
    const token = localStorage.getItem('token')
    const formData = new FormData()
    formData.append('f', file)
    
    return new Promise<any>((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = (e.loaded / e.total) * 100
          onProgress(progress)
        }
      })
      
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch (e) {
            reject(new Error('Ошибка парсинга ответа'))
          }
        } else {
          reject(new Error(`Ошибка загрузки: ${xhr.status}`))
        }
      })
      
      xhr.addEventListener('error', () => reject(new Error('Ошибка сети')))
      xhr.addEventListener('abort', () => reject(new Error('Загрузка отменена')))
      
      xhr.open('POST', '/uploads')
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(formData)
    })
  }
}

// Modern styles
const styles = {
  loginContainer: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '20px',
    position: 'relative' as const,
    overflow: 'hidden'
  },
  loginBg: {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    opacity: 0.1,
    backgroundImage: 'radial-gradient(circle at 20% 50%, white 1px, transparent 1px), radial-gradient(circle at 80% 80%, white 1px, transparent 1px)',
    backgroundSize: '50px 50px'
  },
  loginCard: {
    background: 'rgba(255, 255, 255, 0.95)',
    backdropFilter: 'blur(20px)',
    borderRadius: '24px',
    padding: '48px',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    maxWidth: '440px',
    width: '100%',
    position: 'relative' as const,
    zIndex: 1,
    border: '1px solid rgba(255, 255, 255, 0.3)'
  },
  logoContainer: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    marginBottom: '32px'
  },
  logo: {
    width: '80px',
    height: '80px',
    marginBottom: '16px',
    filter: 'drop-shadow(0 4px 12px rgba(99, 102, 241, 0.3))'
  },
  appContainer: {
    minHeight: '100vh',
    background: 'linear-gradient(to bottom, #f9fafb 0%, #ffffff 100%)'
  },
  navbar: {
    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    padding: '16px 32px',
    boxShadow: '0 4px 20px rgba(99, 102, 241, 0.2)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    position: 'sticky' as const,
    top: 0,
    zIndex: 100
  },
  navBrand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    color: 'white',
    fontSize: '20px',
    fontWeight: '700'
  },
  navLogo: {
    width: '36px',
    height: '36px',
    filter: 'brightness(0) invert(1)'
  },
  navButtons: {
    display: 'flex',
    gap: '8px'
  },
  navButton: {
    background: 'rgba(255, 255, 255, 0.15)',
    color: 'white',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '12px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.2s',
    backdropFilter: 'blur(10px)'
  },
  navButtonActive: {
    background: 'white',
    color: '#6366f1',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
  },
  statCard: {
    background: 'white',
    borderRadius: '20px',
    padding: '28px',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.06)',
    border: '1px solid rgba(0, 0, 0, 0.04)',
    transition: 'all 0.3s'
  },
  statCardGradient: {
    background: 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
    color: 'white',
    borderRadius: '20px',
    padding: '28px',
    boxShadow: '0 8px 24px rgba(99, 102, 241, 0.25)',
    border: 'none'
  }
}

// Components
function LoginPage({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState('demo@biocarta.com')
  const [password, setPassword] = useState('demo123')
  const [isLogin, setIsLogin] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      const data = await api.call(isLogin ? '/auth/login' : '/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      
      localStorage.setItem('token', data.access_token)
      onLogin(data.access_token)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <div style={styles.loginContainer}>
      <div style={styles.loginBg} />
      <div style={styles.loginCard} className="animate-fade-in">
        <div style={styles.logoContainer}>
          <img src="/logo.png" alt="BioCarta" style={styles.logo} />
          <h1 className="gradient-text" style={{ fontSize: '32px', marginBottom: '8px', fontWeight: '800' }}>
            BioCarta
          </h1>
          <p style={{ color: '#6b7280', fontSize: '15px', textAlign: 'center' }}>
            Ваш персональный трекер здоровья
          </p>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className="input"
            required
          />
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="input"
            required
          />
          <button 
            type="submit" 
            disabled={loading}
            className="btn btn-primary"
            style={{ marginTop: '8px', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Загрузка...' : (isLogin ? 'Войти' : 'Зарегистрироваться')}
          </button>
          {error && <div style={{ color: '#ef4444', fontSize: '14px', textAlign: 'center', padding: '8px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '8px' }}>{error}</div>}
        </form>
        <div style={{ textAlign: 'center', marginTop: '24px' }}>
          <button 
            onClick={() => setIsLogin(!isLogin)} 
            style={{ background: 'none', border: 'none', color: '#6366f1', cursor: 'pointer', fontWeight: '600', fontSize: '14px' }}
          >
            {isLogin ? 'Создать аккаунт' : 'Уже есть аккаунт? Войти'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Dashboard() {
  const [summary, setSummary] = useState<any>(null)
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    loadData()
  }, [])
  
  const loadData = async () => {
    try {
      const [summaryData, overviewData] = await Promise.all([
        api.call('/dashboard/summary'),
        api.call('/dashboard/overview')
      ])
      setSummary(summaryData)
      setBiomarkers(overviewData.biomarkers || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center' }}>
        <div className="animate-pulse" style={{ fontSize: '18px', color: '#6b7280' }}>Загрузка...</div>
      </div>
    )
  }
  
  const statusColors: Record<string, string> = {
    'optimal': '#10b981',
    'borderline': '#f59e0b',
    'out_of_range': '#ef4444',
    'unknown': '#6b7280'
  }
  
  const statusLabels: Record<string, string> = {
    'optimal': 'Оптимально',
    'borderline': 'Пограничное',
    'out_of_range': 'Вне нормы',
    'unknown': 'Нет данных'
  }
  
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }} className="animate-fade-in">
      <h2 style={{ marginBottom: '32px', fontSize: '28px', fontWeight: '700', color: '#111827' }}>Дашборд</h2>
      
      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        <div style={styles.statCardGradient}>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px', fontWeight: '500' }}>Отслеживается</div>
          <div style={{ fontSize: '36px', fontWeight: '800' }}>{summary?.tracked || 0}</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '500' }}>Оптимально</div>
          <div style={{ fontSize: '36px', fontWeight: '800', color: '#10b981' }}>{summary?.optimal || 0}</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '500' }}>Пограничное</div>
          <div style={{ fontSize: '36px', fontWeight: '800', color: '#f59e0b' }}>{summary?.borderline || 0}</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px', fontWeight: '500' }}>Вне нормы</div>
          <div style={{ fontSize: '36px', fontWeight: '800', color: '#ef4444' }}>{summary?.out_of_range || 0}</div>
        </div>
      </div>
      
      {/* Biomarkers */}
      {biomarkers.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
          <h3 style={{ marginBottom: '8px', color: '#374151' }}>Нет данных</h3>
          <p style={{ color: '#6b7280' }}>Загрузите файлы с анализами на вкладке "Загрузка"</p>
        </div>
      ) : (
        <div className="card">
          <h3 style={{ marginBottom: '24px', fontSize: '20px', fontWeight: '700' }}>Последние показатели</h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            {biomarkers.slice(0, 10).map((b) => (
              <div key={b.id} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '16px',
                background: '#f9fafb',
                borderRadius: '12px',
                border: '1px solid #e5e7eb'
              }}>
                <div>
                  <div style={{ fontWeight: '600', color: '#111827', marginBottom: '4px' }}>{b.name_ru}</div>
                  <div style={{ fontSize: '13px', color: '#6b7280' }}>{b.code}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  {b.value && (
                    <div style={{ fontWeight: '700', fontSize: '18px', color: statusColors[b.status || 'unknown'] }}>
                      {b.value} {b.unit_std}
                    </div>
                  )}
                  {b.status && (
                    <span className={`badge badge-${b.status === 'optimal' ? 'success' : b.status === 'borderline' ? 'warning' : 'error'}`}>
                      {statusLabels[b.status]}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function BiomarkersPage() {
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  
  useEffect(() => {
    loadBiomarkers()
  }, [])
  
  const loadBiomarkers = async () => {
    try {
      const data = await api.call('/biomarkers')
      setBiomarkers(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  const filtered = biomarkers.filter(b => 
    b.name_ru.toLowerCase().includes(search.toLowerCase()) ||
    b.code.toLowerCase().includes(search.toLowerCase())
  )
  
  if (loading) return <div style={{ padding: '60px', textAlign: 'center' }} className="animate-pulse">Загрузка...</div>
  
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }} className="animate-fade-in">
      <h2 style={{ marginBottom: '24px', fontSize: '28px', fontWeight: '700' }}>Биомаркеры</h2>
      <div className="card">
        <input
          type="text"
          placeholder="Поиск биомаркеров..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="input"
          style={{ marginBottom: '24px' }}
        />
        <div style={{ display: 'grid', gap: '12px' }}>
          {filtered.map(b => (
            <div key={b.id} style={{ 
              padding: '16px',
              background: '#f9fafb',
              borderRadius: '12px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ fontWeight: '600', marginBottom: '4px' }}>{b.name_ru}</div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>{b.code} • {b.category}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function UploadsPage() {
  const [uploads, setUploads] = useState<UploadProgress[]>([])
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [loading, setLoading] = useState(false)
  
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return
    
    for (const file of files) {
      const uploadItem: UploadProgress = {
        filename: file.name,
        progress: 0,
        status: 'uploading'
      }
      
      setUploads(prev => [...prev, uploadItem])
      
      try {
        const result = await api.upload(file, (progress) => {
          setUploads(prev => prev.map(u => 
            u.filename === file.name ? { ...u, progress } : u
          ))
        })
        
        setUploads(prev => prev.map(u => 
          u.filename === file.name 
            ? { ...u, status: 'complete', uploadId: result.upload_id } 
            : u
        ))
        
        if (result.suggestions) {
          setSuggestions(prev => [...prev, ...result.suggestions])
        }
      } catch (err) {
        setUploads(prev => prev.map(u => 
          u.filename === file.name ? { ...u, status: 'error' } : u
        ))
      }
    }
  }
  
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }} className="animate-fade-in">
      <h2 style={{ marginBottom: '24px', fontSize: '28px', fontWeight: '700' }}>Загрузка</h2>
      
      <div className="card" style={{ marginBottom: '24px' }}>
        <label htmlFor="file-upload" className="btn btn-primary" style={{ cursor: 'pointer', display: 'inline-flex' }}>
          📁 Выбрать файлы
        </label>
        <input
          id="file-upload"
          type="file"
          multiple
          accept=".pdf,.csv,.xlsx,.xls,.txt,.xml,.zip"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <p style={{ marginTop: '16px', fontSize: '14px', color: '#6b7280' }}>
          Поддерживаемые форматы: PDF, CSV, Excel, TXT, XML, ZIP
        </p>
      </div>
      
      {uploads.length > 0 && (
        <div className="card">
          <h3 style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600' }}>Загруженные файлы</h3>
          <div style={{ display: 'grid', gap: '12px' }}>
            {uploads.map((u, i) => (
              <div key={i} style={{ padding: '16px', background: '#f9fafb', borderRadius: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <span style={{ fontWeight: '600' }}>{u.filename}</span>
                  <span className={`badge badge-${u.status === 'complete' ? 'success' : u.status === 'error' ? 'error' : 'info'}`}>
                    {u.status === 'complete' ? '✓ Готово' : u.status === 'error' ? '✗ Ошибка' : '⏳ Загрузка'}
                  </span>
                </div>
                {u.status === 'uploading' && (
                  <div className="progress">
                    <div className="progress-bar" style={{ width: `${u.progress}%` }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function TimelinePage() {
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }} className="animate-fade-in">
      <h2 style={{ marginBottom: '24px', fontSize: '28px', fontWeight: '700' }}>История</h2>
      <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📈</div>
        <h3 style={{ marginBottom: '8px' }}>Скоро здесь появится график</h3>
        <p style={{ color: '#6b7280' }}>Отслеживайте изменения показателей во времени</p>
      </div>
    </div>
  )
}

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [page, setPage] = useState<'dashboard' | 'biomarkers' | 'uploads' | 'timeline'>('dashboard')
  
  const handleLogin = (newToken: string) => {
    setToken(newToken)
  }
  
  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }
  
  if (!token) {
    return <LoginPage onLogin={handleLogin} />
  }
  
  return (
    <div style={styles.appContainer}>
      <nav style={styles.navbar} className="no-print">
        <div style={styles.navBrand}>
          <img src="/logo.png" alt="BioCarta" style={styles.navLogo} />
          <span>BioCarta</span>
        </div>
        <div style={styles.navButtons}>
          <button
            onClick={() => setPage('dashboard')}
            style={page === 'dashboard' ? { ...styles.navButton, ...styles.navButtonActive } : styles.navButton}
          >
            Дашборд
          </button>
          <button
            onClick={() => setPage('biomarkers')}
            style={page === 'biomarkers' ? { ...styles.navButton, ...styles.navButtonActive } : styles.navButton}
          >
            Биомаркеры
          </button>
          <button
            onClick={() => setPage('uploads')}
            style={page === 'uploads' ? { ...styles.navButton, ...styles.navButtonActive } : styles.navButton}
          >
            Загрузка
          </button>
          <button
            onClick={() => setPage('timeline')}
            style={page === 'timeline' ? { ...styles.navButton, ...styles.navButtonActive } : styles.navButton}
          >
            История
          </button>
          <button onClick={handleLogout} style={{ ...styles.navButton, background: 'rgba(239, 68, 68, 0.2)' }}>
            Выйти
          </button>
        </div>
      </nav>
      
      <main>
        {page === 'dashboard' && <Dashboard />}
        {page === 'biomarkers' && <BiomarkersPage />}
        {page === 'uploads' && <UploadsPage />}
        {page === 'timeline' && <TimelinePage />}
      </main>
    </div>
  )
}

const root = createRoot(document.getElementById('root')!)
root.render(<App />)
