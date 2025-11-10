import React, { useState, useEffect } from 'react'

interface GeneticVariant {
  id: number
  rsid: string
  gene: string
  genotype: string
  interpretation: string
  risk_score: number
  clinical_significance: string
}

interface GeneticSummary {
  total_variants: number
  high_risk: GeneticVariant[]
  moderate_risk: GeneticVariant[]
  genes_tested: string[]
}

const GeneticsPage: React.FC = () => {
  const [summary, setSummary] = useState<GeneticSummary | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadSummary()
  }, [])

  const loadSummary = async () => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch('/genetics/summary', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      setSummary(data)
    } catch (err) {
      console.error('Failed to load genetics summary', err)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    setMessage('')

    try {
      const token = localStorage.getItem('token')
      const formData = new FormData()
      formData.append('file', file)

      const res = await fetch('/genetics/upload?file_type=auto', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (!res.ok) throw new Error('Upload failed')

      const data = await res.json()
      setMessage(`✓ ${data.message}`)
      loadSummary()
    } catch (err) {
      setMessage('Ошибка загрузки файла')
    } finally {
      setUploading(false)
    }
  }

  const getRiskColor = (score: number) => {
    if (score >= 0.9) return '#dc3545'
    if (score >= 0.4) return '#ffc107'
    return '#28a745'
  }

  const getRiskLabel = (score: number) => {
    if (score >= 0.9) return 'Высокий риск'
    if (score >= 0.4) return 'Умеренный риск'
    return 'Низкий риск'
  }

  if (!summary || summary.total_variants === 0) {
    return (
      <div style={{ padding: '40px', maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Генетика</h1>
        <p style={{ color: '#666', marginBottom: '40px' }}>
          Анализ генетических данных из 23andMe, AncestryDNA
        </p>

        <div style={{
          background: 'white',
          border: '2px dashed #e0e0e0',
          borderRadius: '12px',
          padding: '60px 40px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '20px' }}>🧬</div>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '15px' }}>
            Загрузите генетические данные
          </h2>
          <p style={{ color: '#666', marginBottom: '30px', lineHeight: '1.6' }}>
            Поддерживаются файлы от 23andMe, AncestryDNA, Promethease<br />
            Форматы: TXT, JSON
          </p>

          <label style={{
            display: 'inline-block',
            padding: '15px 30px',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white',
            borderRadius: '8px',
            fontWeight: '600',
            cursor: uploading ? 'not-allowed' : 'pointer',
            opacity: uploading ? 0.6 : 1
          }}>
            {uploading ? 'Загрузка...' : 'Выбрать файл'}
            <input
              type="file"
              accept=".txt,.json"
              onChange={handleFileUpload}
              disabled={uploading}
              style={{ display: 'none' }}
            />
          </label>

          {message && (
            <div style={{
              marginTop: '20px',
              padding: '15px',
              background: message.startsWith('✓') ? '#d4edda' : '#f8d7da',
              border: `1px solid ${message.startsWith('✓') ? '#c3e6cb' : '#f5c6cb'}`,
              borderRadius: '8px',
              color: message.startsWith('✓') ? '#155724' : '#721c24'
            }}>
              {message}
            </div>
          )}
        </div>

        <div style={{
          marginTop: '40px',
          padding: '25px',
          background: '#f8f9fa',
          borderRadius: '12px',
          border: '1px solid #e0e0e0'
        }}>
          <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '15px' }}>
            ℹ️ Как получить генетические данные?
          </h3>
          <ol style={{ color: '#666', lineHeight: '1.8', paddingLeft: '20px', margin: 0 }}>
            <li>Закажите тест ДНК на 23andMe.com или AncestryDNA.com</li>
            <li>Дождитесь результатов (обычно 4-6 недель)</li>
            <li>Скачайте raw data (сырые данные) из личного кабинета</li>
            <li>Загрузите файл в BioCarta для анализа</li>
          </ol>
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '10px' }}>Генетика</h1>
          <p style={{ color: '#666' }}>
            Проанализировано {summary.total_variants} генетических вариантов
          </p>
        </div>
        <label style={{
          padding: '12px 24px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          borderRadius: '8px',
          fontWeight: '600',
          cursor: uploading ? 'not-allowed' : 'pointer',
          opacity: uploading ? 0.6 : 1
        }}>
          {uploading ? 'Загрузка...' : 'Загрузить новый файл'}
          <input
            type="file"
            accept=".txt,.json"
            onChange={handleFileUpload}
            disabled={uploading}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {message && (
        <div style={{
          marginBottom: '30px',
          padding: '15px',
          background: message.startsWith('✓') ? '#d4edda' : '#f8d7da',
          border: `1px solid ${message.startsWith('✓') ? '#c3e6cb' : '#f5c6cb'}`,
          borderRadius: '8px',
          color: message.startsWith('✓') ? '#155724' : '#721c24'
        }}>
          {message}
        </div>
      )}

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '40px' }}>
        <div style={{
          background: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          padding: '25px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '5px' }}>
            {summary.total_variants}
          </div>
          <div style={{ color: '#666', fontSize: '14px' }}>Всего вариантов</div>
        </div>

        <div style={{
          background: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          padding: '25px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '5px', color: '#dc3545' }}>
            {summary.high_risk.length}
          </div>
          <div style={{ color: '#666', fontSize: '14px' }}>Высокий риск</div>
        </div>

        <div style={{
          background: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '12px',
          padding: '25px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '36px', fontWeight: 'bold', marginBottom: '5px', color: '#ffc107' }}>
            {summary.moderate_risk.length}
          </div>
          <div style={{ color: '#666', fontSize: '14px' }}>Умеренный риск</div>
        </div>
      </div>

      {/* High Risk Variants */}
      {summary.high_risk.length > 0 && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
            ⚠️ Высокий риск
          </h2>
          <div style={{ display: 'grid', gap: '15px' }}>
            {summary.high_risk.map(variant => (
              <div key={variant.id} style={{
                background: 'white',
                border: '1px solid #e0e0e0',
                borderRadius: '12px',
                padding: '25px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                      <h3 style={{ fontSize: '18px', fontWeight: 'bold' }}>{variant.gene}</h3>
                      <span style={{
                        padding: '4px 8px',
                        background: getRiskColor(variant.risk_score),
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {getRiskLabel(variant.risk_score)}
                      </span>
                    </div>
                    <div style={{ color: '#666', fontSize: '14px' }}>
                      {variant.rsid} • Генотип: <strong>{variant.genotype}</strong>
                    </div>
                  </div>
                </div>
                <p style={{ color: '#666', lineHeight: '1.6', margin: 0 }}>
                  {variant.interpretation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Moderate Risk Variants */}
      {summary.moderate_risk.length > 0 && (
        <div style={{ marginBottom: '40px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '20px' }}>
            ⚡ Умеренный риск
          </h2>
          <div style={{ display: 'grid', gap: '15px' }}>
            {summary.moderate_risk.map(variant => (
              <div key={variant.id} style={{
                background: 'white',
                border: '1px solid #e0e0e0',
                borderRadius: '12px',
                padding: '25px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '15px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '5px' }}>
                      <h3 style={{ fontSize: '18px', fontWeight: 'bold' }}>{variant.gene}</h3>
                      <span style={{
                        padding: '4px 8px',
                        background: getRiskColor(variant.risk_score),
                        color: 'white',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600'
                      }}>
                        {getRiskLabel(variant.risk_score)}
                      </span>
                    </div>
                    <div style={{ color: '#666', fontSize: '14px' }}>
                      {variant.rsid} • Генотип: <strong>{variant.genotype}</strong>
                    </div>
                  </div>
                </div>
                <p style={{ color: '#666', lineHeight: '1.6', margin: 0 }}>
                  {variant.interpretation}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Genes Tested */}
      <div style={{
        padding: '25px',
        background: '#f8f9fa',
        borderRadius: '12px',
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '15px' }}>
          🧬 Проанализированные гены
        </h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {summary.genes_tested.map(gene => (
            <span key={gene} style={{
              padding: '6px 12px',
              background: 'white',
              border: '1px solid #e0e0e0',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600'
            }}>
              {gene}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default GeneticsPage
