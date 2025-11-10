// This will be inserted into main.tsx before App component

function HistoryPage() {
  const [timeline, setTimeline] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedBiomarker, setSelectedBiomarker] = useState<number | null>(null)
  const [biomarkerHistory, setBiomarkerHistory] = useState<any>(null)
  
  useEffect(() => {
    loadTimeline()
    loadStats()
  }, [])
  
  const loadTimeline = async () => {
    try {
      const data = await api.call('/timeline')
      setTimeline(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  const loadStats = async () => {
    try {
      const data = await api.call('/timeline/stats')
      setStats(data)
    } catch (err) {
      console.error(err)
    }
  }
  
  const loadBiomarkerHistory = async (biomarkerId: number) => {
    try {
      const data = await api.call(`/measurements/stats/${biomarkerId}`)
      setBiomarkerHistory(data)
      setSelectedBiomarker(biomarkerId)
    } catch (err) {
      console.error(err)
    }
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
  
  if (loading) return <div style={{ padding: '60px', textAlign: 'center', fontSize: '18px', color: '#6c757d' }}>Загрузка...</div>
  
  if (selectedBiomarker && biomarkerHistory) {
    return (
      <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
        <button
          onClick={() => { setSelectedBiomarker(null); setBiomarkerHistory(null); }}
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '10px',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '24px',
            transition: 'all 0.3s'
          }}
        >
          ← Назад к истории
        </button>
        
        <h1 style={{ marginBottom: '16px', fontSize: '32px', fontWeight: '700', color: '#1f2937' }}>
          {biomarkerHistory.biomarker.name_ru}
        </h1>
        <p style={{ marginBottom: '32px', fontSize: '16px', color: '#6b7280' }}>
          {biomarkerHistory.biomarker.code} • {biomarkerHistory.count} измерений
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '40px' }}>
          <div style={{ ...styles.card, borderLeft: '4px solid #667eea' }}>
            <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Последнее значение</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#1f2937' }}>
              {biomarkerHistory.latest_value?.toFixed(2)} {biomarkerHistory.biomarker.unit_std}
            </div>
            <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '8px' }}>
              {new Date(biomarkerHistory.latest_date).toLocaleDateString('ru-RU')}
            </div>
          </div>
          
          <div style={{ ...styles.card, borderLeft: `4px solid ${statusColors[biomarkerHistory.status]}` }}>
            <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Статус</div>
            <div style={{ fontSize: '24px', fontWeight: '700', color: statusColors[biomarkerHistory.status] }}>
              {statusLabels[biomarkerHistory.status]}
            </div>
            {biomarkerHistory.reference && (
              <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '8px' }}>
                Норма: {biomarkerHistory.reference.low} - {biomarkerHistory.reference.high} {biomarkerHistory.reference.unit}
              </div>
            )}
          </div>
        </div>
        
        <div style={styles.card}>
          <h2 style={{ fontSize: '22px', marginBottom: '20px', fontWeight: '600', color: '#1f2937' }}>История измерений</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>Дата</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>Значение</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>Единица</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>Статус</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontSize: '13px', fontWeight: '600', color: '#6b7280' }}>Источник</th>
                </tr>
              </thead>
              <tbody>
                {biomarkerHistory.history.map((h: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '12px', fontSize: '14px' }}>
                      {new Date(h.date).toLocaleDateString('ru-RU')}
                    </td>
                    <td style={{ padding: '12px', fontSize: '14px', fontWeight: '600' }}>
                      {h.value.toFixed(2)}
                    </td>
                    <td style={{ padding: '12px', fontSize: '14px', color: '#6b7280' }}>
                      {h.unit}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        background: statusColors[h.status],
                        color: 'white',
                        padding: '4px 10px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {statusLabels[h.status]}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '14px', color: '#6b7280' }}>
                      {h.source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '32px', fontSize: '32px', fontWeight: '700', color: '#1f2937' }}>История анализов</h1>
      
      {stats && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '40px' }}>
          <div style={{ ...styles.statCard }}>
            <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '8px', fontWeight: '500' }}>Всего измерений</div>
            <div style={{ fontSize: '40px', fontWeight: '700' }}>{stats.total_measurements}</div>
          </div>
          <div style={{ ...styles.card, borderLeft: '4px solid #10b981' }}>
            <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Уникальных биомаркеров</div>
            <div style={{ fontSize: '32px', fontWeight: '700', color: '#10b981' }}>{stats.unique_biomarkers}</div>
          </div>
          <div style={{ ...styles.card, borderLeft: '4px solid #667eea' }}>
            <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Период</div>
            <div style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937' }}>
              {stats.first_date && new Date(stats.first_date).toLocaleDateString('ru-RU')}
              {' - '}
              {stats.last_date && new Date(stats.last_date).toLocaleDateString('ru-RU')}
            </div>
          </div>
        </div>
      )}
      
      {timeline.length === 0 ? (
        <div style={{ ...styles.card, textAlign: 'center', padding: '60px' }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
          <div style={{ fontSize: '18px', color: '#6b7280' }}>Нет данных</div>
          <div style={{ fontSize: '14px', color: '#9ca3af', marginTop: '8px' }}>
            Загрузите файлы с анализами на вкладке "Загрузка"
          </div>
        </div>
      ) : (
        timeline.map(day => (
          <div key={day.date} style={{ ...styles.card, marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '16px', borderBottom: '2px solid #f3f4f6' }}>
              <h2 style={{ fontSize: '22px', fontWeight: '600', color: '#1f2937', margin: 0 }}>
                {new Date(day.date).toLocaleDateString('ru-RU', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </h2>
              <span style={{ fontSize: '14px', color: '#6b7280', fontWeight: '600' }}>
                {day.count} измерений
              </span>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {day.measurements.map((m: any) => (
                <div
                  key={m.id}
                  onClick={() => loadBiomarkerHistory(m.id)}
                  style={{
                    padding: '16px',
                    background: '#f9fafb',
                    borderRadius: '10px',
                    borderLeft: `4px solid ${statusColors[m.status]}`,
                    cursor: 'pointer',
                    transition: 'all 0.3s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)'
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                  }}
                >
                  <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>{m.biomarker_code}</div>
                  <div style={{ fontSize: '16px', fontWeight: '600', color: '#1f2937', marginBottom: '8px' }}>
                    {m.biomarker_name}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: '20px', fontWeight: '700', color: statusColors[m.status] }}>
                      {m.value.toFixed(2)} {m.unit}
                    </div>
                    <span style={{
                      background: statusColors[m.status],
                      color: 'white',
                      padding: '4px 8px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: '600'
                    }}>
                      {statusLabels[m.status]}
                    </span>
                  </div>
                  {m.reference && (
                    <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '8px' }}>
                      Норма: {m.reference.low} - {m.reference.high}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  )
}
