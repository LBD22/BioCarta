import React, { useState, useEffect } from 'react'

interface IntegrationStatus {
  whoop: { connected: boolean; name: string }
  oura: { connected: boolean; name: string }
}

const IntegrationsPage: React.FC = () => {
  const [status, setStatus] = useState<IntegrationStatus | null>(null)
  const [syncing, setSyncing] = useState<string | null>(null)
  const [message, setMessage] = useState<string>('')

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/integrations/status', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setStatus(data)
    } catch (err) {
      console.error('Failed to load integration status', err)
    }
  }

  const connectWhoop = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/integrations/whoop/auth', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      window.location.href = data.auth_url
    } catch (err) {
      setMessage('Ошибка подключения WHOOP')
    }
  }

  const connectOura = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/integrations/oura/auth', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      window.location.href = data.auth_url
    } catch (err) {
      setMessage('Ошибка подключения Oura')
    }
  }

  const syncWhoop = async () => {
    setSyncing('whoop')
    setMessage('')
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/integrations/whoop/sync?days_back=30', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setMessage(`✓ ${data.message}`)
    } catch (err) {
      setMessage('Ошибка синхронизации WHOOP')
    } finally {
      setSyncing(null)
    }
  }

  const syncOura = async () => {
    setSyncing('oura')
    setMessage('')
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/integrations/oura/sync?days_back=30', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setMessage(`✓ ${data.message}`)
    } catch (err) {
      setMessage('Ошибка синхронизации Oura')
    } finally {
      setSyncing(null)
    }
  }

  const disconnectWhoop = async () => {
    if (!confirm('Отключить WHOOP?')) return
    try {
      const token = localStorage.getItem('token')
      await fetch('/integrations/whoop/disconnect', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      loadStatus()
      setMessage('WHOOP отключен')
    } catch (err) {
      setMessage('Ошибка отключения WHOOP')
    }
  }

  const disconnectOura = async () => {
    if (!confirm('Отключить Oura?')) return
    try {
      const token = localStorage.getItem('token')
      await fetch('/integrations/oura/disconnect', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      loadStatus()
      setMessage('Oura отключен')
    } catch (err) {
      setMessage('Ошибка отключения Oura')
    }
  }

  if (!status) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Загрузка...</div>
  }

  return (
    <div style={{ padding: '40px', maxWidth: '900px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Интеграции</h1>
      <p style={{ color: '#666', marginBottom: '40px' }}>
        Подключите носимые устройства для автоматической синхронизации данных
      </p>

      {message && (
        <div style={{
          padding: '15px',
          marginBottom: '30px',
          background: message.startsWith('✓') ? '#d4edda' : '#f8d7da',
          border: `1px solid ${message.startsWith('✓') ? '#c3e6cb' : '#f5c6cb'}`,
          borderRadius: '8px',
          color: message.startsWith('✓') ? '#155724' : '#721c24'
        }}>
          {message}
        </div>
      )}

      <div style={{ display: 'grid', gap: '30px' }}>
        {/* WHOOP Card */}
        <div style={{
          background: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          padding: '30px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(135deg, #000 0%, #333 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '24px',
                fontWeight: 'bold'
              }}>W</div>
              <div>
                <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>WHOOP</h2>
                <p style={{ color: '#666', fontSize: '14px' }}>
                  {status.whoop.connected ? '✓ Подключено' : 'Не подключено'}
                </p>
              </div>
            </div>
            <div style={{
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              background: status.whoop.connected ? '#d4edda' : '#f8f9fa',
              color: status.whoop.connected ? '#155724' : '#666'
            }}>
              {status.whoop.connected ? 'Активно' : 'Неактивно'}
            </div>
          </div>

          <p style={{ color: '#666', marginBottom: '20px', lineHeight: '1.6' }}>
            Синхронизация данных: HRV, пульс в покое, частота дыхания, SpO2, вес, процент жира
          </p>

          <div style={{ display: 'flex', gap: '10px' }}>
            {!status.whoop.connected ? (
              <button
                onClick={connectWhoop}
                style={{
                  padding: '12px 24px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Подключить WHOOP
              </button>
            ) : (
              <>
                <button
                  onClick={syncWhoop}
                  disabled={syncing === 'whoop'}
                  style={{
                    padding: '12px 24px',
                    background: syncing === 'whoop' ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: syncing === 'whoop' ? 'not-allowed' : 'pointer'
                  }}
                >
                  {syncing === 'whoop' ? 'Синхронизация...' : 'Синхронизировать'}
                </button>
                <button
                  onClick={disconnectWhoop}
                  style={{
                    padding: '12px 24px',
                    background: 'white',
                    color: '#dc3545',
                    border: '1px solid #dc3545',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Отключить
                </button>
              </>
            )}
          </div>
        </div>

        {/* Oura Card */}
        <div style={{
          background: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          padding: '30px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              <div style={{
                width: '60px',
                height: '60px',
                background: 'linear-gradient(135deg, #4A90E2 0%, #357ABD 100%)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '24px',
                fontWeight: 'bold'
              }}>O</div>
              <div>
                <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '5px' }}>Oura Ring</h2>
                <p style={{ color: '#666', fontSize: '14px' }}>
                  {status.oura.connected ? '✓ Подключено' : 'Не подключено'}
                </p>
              </div>
            </div>
            <div style={{
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              background: status.oura.connected ? '#d4edda' : '#f8f9fa',
              color: status.oura.connected ? '#155724' : '#666'
            }}>
              {status.oura.connected ? 'Активно' : 'Неактивно'}
            </div>
          </div>

          <p style={{ color: '#666', marginBottom: '20px', lineHeight: '1.6' }}>
            Синхронизация данных: HRV, пульс в покое, частота дыхания, SpO2, температура тела
          </p>

          <div style={{ display: 'flex', gap: '10px' }}>
            {!status.oura.connected ? (
              <button
                onClick={connectOura}
                style={{
                  padding: '12px 24px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer'
                }}
              >
                Подключить Oura
              </button>
            ) : (
              <>
                <button
                  onClick={syncOura}
                  disabled={syncing === 'oura'}
                  style={{
                    padding: '12px 24px',
                    background: syncing === 'oura' ? '#ccc' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: syncing === 'oura' ? 'not-allowed' : 'pointer'
                  }}
                >
                  {syncing === 'oura' ? 'Синхронизация...' : 'Синхронизировать'}
                </button>
                <button
                  onClick={disconnectOura}
                  style={{
                    padding: '12px 24px',
                    background: 'white',
                    color: '#dc3545',
                    border: '1px solid #dc3545',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  Отключить
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      <div style={{
        marginTop: '40px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '10px' }}>ℹ️ Информация</h3>
        <ul style={{ color: '#666', lineHeight: '1.8', paddingLeft: '20px' }}>
          <li>Синхронизация импортирует данные за последние 30 дней</li>
          <li>Данные автоматически сопоставляются с биомаркерами BioCarta</li>
          <li>Вы можете отключить интеграцию в любой момент</li>
          <li>Для подключения требуется аккаунт WHOOP или Oura</li>
        </ul>
      </div>
    </div>
  )
}

export default IntegrationsPage
