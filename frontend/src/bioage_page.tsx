import React, { useState, useEffect } from 'react'

interface BioAgeResult {
  phenoage?: {
    phenoage: number
    chronological_age: number
    age_delta: number
    mortality_score: number
    interpretation: string
  }
  simple_bioage?: {
    bioage: number
    chronological_age: number
    age_delta: number
    aging_score: number
    biomarkers_used: number
    interpretation: string
  }
  average?: {
    age_delta: number
    interpretation: string
  }
}

const BioAgePage: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [result, setResult] = useState<BioAgeResult | null>(null)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    loadBioAge()
  }, [])

  const loadBioAge = async () => {
    setLoading(true)
    setError('')
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/bioage/all', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      
      if (!res.ok) {
        throw new Error('Недостаточно данных для расчета биологического возраста')
      }
      
      const data = await res.json()
      setResult(data)
    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  const getAgeDeltaColor = (delta: number) => {
    if (delta < -3) return '#28a745'
    if (delta < -1) return '#5cb85c'
    if (delta < 1) return '#ffc107'
    if (delta < 3) return '#fd7e14'
    return '#dc3545'
  }

  const getAgeDeltaEmoji = (delta: number) => {
    if (delta < -3) return '🌟'
    if (delta < -1) return '😊'
    if (delta < 1) return '😐'
    if (delta < 3) return '😕'
    return '⚠️'
  }

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>⏳</div>
        <p style={{ color: '#666' }}>Расчет биологического возраста...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '40px', maxWidth: '700px', margin: '0 auto' }}>
        <div style={{
          background: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '12px',
          padding: '30px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '15px' }}>
            Недостаточно данных
          </h2>
          <p style={{ color: '#666', marginBottom: '20px' }}>
            {error}
          </p>
          <p style={{ color: '#666', fontSize: '14px' }}>
            Загрузите результаты анализов крови для расчета биологического возраста
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>
        Биологический возраст
      </h1>
      <p style={{ color: '#666', marginBottom: '40px' }}>
        Оценка скорости старения на основе биомаркеров крови
      </p>

      <div style={{ display: 'grid', gap: '30px' }}>
        {/* Simple BioAge Card */}
        {result?.simple_bioage && (
          <div style={{
            background: 'white',
            border: '1px solid #e0e0e0',
            borderRadius: '12px',
            padding: '30px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '30px' }}>
              <div>
                <h2 style={{ fontSize: '18px', color: '#666', marginBottom: '10px' }}>
                  Биологический возраст
                </h2>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}>
                  <span style={{ fontSize: '48px', fontWeight: 'bold' }}>
                    {result.simple_bioage.bioage.toFixed(1)}
                  </span>
                  <span style={{ fontSize: '24px', color: '#666' }}>лет</span>
                </div>
              </div>
              <div style={{
                fontSize: '64px',
                opacity: 0.3
              }}>
                {getAgeDeltaEmoji(result.simple_bioage.age_delta)}
              </div>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '20px',
              marginBottom: '30px'
            }}>
              <div style={{
                padding: '20px',
                background: '#f8f9fa',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>
                  Хронологический возраст
                </div>
                <div style={{ fontSize: '28px', fontWeight: 'bold' }}>
                  {result.simple_bioage.chronological_age.toFixed(1)}
                </div>
              </div>

              <div style={{
                padding: '20px',
                background: '#f8f9fa',
                borderRadius: '8px'
              }}>
                <div style={{ fontSize: '14px', color: '#666', marginBottom: '5px' }}>
                  Разница
                </div>
                <div style={{
                  fontSize: '28px',
                  fontWeight: 'bold',
                  color: getAgeDeltaColor(result.simple_bioage.age_delta)
                }}>
                  {result.simple_bioage.age_delta > 0 ? '+' : ''}
                  {result.simple_bioage.age_delta.toFixed(1)} лет
                </div>
              </div>
            </div>

            <div style={{
              padding: '20px',
              background: '#f8f9fa',
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <div style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                Интерпретация
              </div>
              <p style={{ lineHeight: '1.6', margin: 0 }}>
                {result.simple_bioage.interpretation}
              </p>
            </div>

            <div style={{ fontSize: '12px', color: '#999' }}>
              Использовано биомаркеров: {result.simple_bioage.biomarkers_used}
            </div>
          </div>
        )}

        {/* PhenoAge Card */}
        {result?.phenoage && (
          <div style={{
            background: 'white',
            border: '1px solid #e0e0e0',
            borderRadius: '12px',
            padding: '30px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '20px'
            }}>
              <h2 style={{ fontSize: '24px', fontWeight: 'bold' }}>PhenoAge</h2>
              <span style={{
                padding: '4px 8px',
                background: '#e3f2fd',
                color: '#1976d2',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: '600'
              }}>
                Научный метод
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '10px', marginBottom: '30px' }}>
              <span style={{ fontSize: '48px', fontWeight: 'bold' }}>
                {result.phenoage.phenoage.toFixed(1)}
              </span>
              <span style={{ fontSize: '24px', color: '#666' }}>лет</span>
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: '15px',
              marginBottom: '30px'
            }}>
              <div style={{
                padding: '15px',
                background: '#f8f9fa',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                  Хрон. возраст
                </div>
                <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                  {result.phenoage.chronological_age.toFixed(1)}
                </div>
              </div>

              <div style={{
                padding: '15px',
                background: '#f8f9fa',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                  Разница
                </div>
                <div style={{
                  fontSize: '20px',
                  fontWeight: 'bold',
                  color: getAgeDeltaColor(result.phenoage.age_delta)
                }}>
                  {result.phenoage.age_delta > 0 ? '+' : ''}
                  {result.phenoage.age_delta.toFixed(1)}
                </div>
              </div>

              <div style={{
                padding: '15px',
                background: '#f8f9fa',
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '5px' }}>
                  Риск смертности
                </div>
                <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                  {result.phenoage.mortality_score.toFixed(2)}%
                </div>
              </div>
            </div>

            <div style={{
              padding: '20px',
              background: '#f8f9fa',
              borderRadius: '8px'
            }}>
              <p style={{ lineHeight: '1.6', margin: 0 }}>
                {result.phenoage.interpretation}
              </p>
            </div>

            <div style={{
              marginTop: '20px',
              padding: '15px',
              background: '#e3f2fd',
              borderRadius: '8px',
              fontSize: '13px',
              color: '#1976d2'
            }}>
              <strong>PhenoAge</strong> — научно валидированный алгоритм расчета биологического возраста,
              разработанный Morgan Levine (Yale University, 2018). Основан на 9 биомаркерах крови.
            </div>
          </div>
        )}

        {/* Info Card */}
        <div style={{
          padding: '25px',
          background: '#f8f9fa',
          borderRadius: '12px',
          border: '1px solid #e0e0e0'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '15px' }}>
            ℹ️ Как улучшить биологический возраст?
          </h3>
          <ul style={{ color: '#666', lineHeight: '1.8', paddingLeft: '20px', margin: 0 }}>
            <li>Регулярные физические нагрузки (150+ минут в неделю)</li>
            <li>Сбалансированное питание (средиземноморская диета)</li>
            <li>Качественный сон (7-9 часов)</li>
            <li>Управление стрессом (медитация, йога)</li>
            <li>Отказ от курения и умеренное потребление алкоголя</li>
            <li>Регулярный мониторинг биомаркеров</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default BioAgePage
