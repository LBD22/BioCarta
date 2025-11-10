// BiomarkerDetailView component - insert before BiomarkersPage

function BiomarkerDetailView({ history, onBack }: { history: any, onBack: () => void }) {
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
  
  // Prepare chart data
  const chartData = history.history.slice().reverse() // Oldest to newest for chart
  const hasMultiplePoints = chartData.length > 1
  
  // Calculate chart dimensions
  const chartWidth = 800
  const chartHeight = 400
  const padding = { top: 40, right: 40, bottom: 60, left: 60 }
  const plotWidth = chartWidth - padding.left - padding.right
  const plotHeight = chartHeight - padding.top - padding.bottom
  
  // Find min/max values for scaling
  const values = chartData.map((d: any) => d.value)
  const minValue = Math.min(...values, history.reference?.low || 0)
  const maxValue = Math.max(...values, history.reference?.high || 0)
  const valueRange = maxValue - minValue
  const yMin = minValue - valueRange * 0.1
  const yMax = maxValue + valueRange * 0.1
  
  // Scale functions
  const scaleX = (index: number) => padding.left + (index / (chartData.length - 1)) * plotWidth
  const scaleY = (value: number) => padding.top + plotHeight - ((value - yMin) / (yMax - yMin)) * plotHeight
  
  // Generate path for line chart
  const linePath = chartData.map((d: any, i: number) => {
    const x = scaleX(i)
    const y = scaleY(d.value)
    return i === 0 ? `M ${x} ${y}` : `L ${x} ${y}`
  }).join(' ')
  
  // Reference range rectangle
  const refLow = history.reference?.low
  const refHigh = history.reference?.high
  const refRectY = refHigh ? scaleY(refHigh) : padding.top
  const refRectHeight = (refLow && refHigh) ? scaleY(refLow) - scaleY(refHigh) : 0
  
  return (
    <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
      <button
        onClick={onBack}
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
        ← Назад к списку
      </button>
      
      <h1 style={{ marginBottom: '16px', fontSize: '32px', fontWeight: '700', color: '#1f2937' }}>
        {history.biomarker.name_ru}
      </h1>
      <p style={{ marginBottom: '32px', fontSize: '16px', color: '#6b7280' }}>
        {history.biomarker.code} • {history.count} измерений
      </p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        <div style={{ ...styles.card, borderLeft: '4px solid #667eea' }}>
          <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Последнее значение</div>
          <div style={{ fontSize: '32px', fontWeight: '700', color: '#1f2937' }}>
            {history.latest_value?.toFixed(2)} {history.biomarker.unit_std}
          </div>
          <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '8px' }}>
            {new Date(history.latest_date).toLocaleDateString('ru-RU')}
          </div>
        </div>
        
        <div style={{ ...styles.card, borderLeft: `4px solid ${statusColors[history.status]}` }}>
          <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '8px' }}>Статус</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: statusColors[history.status] }}>
            {statusLabels[history.status]}
          </div>
          {history.reference && (
            <div style={{ fontSize: '13px', color: '#6b7280', marginTop: '8px' }}>
              Норма: {history.reference.low} - {history.reference.high} {history.reference.unit}
            </div>
          )}
        </div>
      </div>
      
      {hasMultiplePoints && (
        <div style={{ ...styles.card, marginBottom: '40px' }}>
          <h2 style={{ fontSize: '22px', marginBottom: '20px', fontWeight: '600', color: '#1f2937' }}>График изменений</h2>
          <div style={{ overflowX: 'auto' }}>
            <svg width={chartWidth} height={chartHeight} style={{ display: 'block', margin: '0 auto' }}>
              {/* Reference range background */}
              {refLow && refHigh && (
                <rect
                  x={padding.left}
                  y={refRectY}
                  width={plotWidth}
                  height={refRectHeight}
                  fill="#10b981"
                  opacity="0.1"
                />
              )}
              
              {/* Grid lines */}
              {[0, 0.25, 0.5, 0.75, 1].map(ratio => {
                const y = padding.top + plotHeight * (1 - ratio)
                const value = yMin + (yMax - yMin) * ratio
                return (
                  <g key={ratio}>
                    <line
                      x1={padding.left}
                      y1={y}
                      x2={padding.left + plotWidth}
                      y2={y}
                      stroke="#e5e7eb"
                      strokeWidth="1"
                    />
                    <text
                      x={padding.left - 10}
                      y={y + 4}
                      textAnchor="end"
                      fontSize="12"
                      fill="#6b7280"
                    >
                      {value.toFixed(1)}
                    </text>
                  </g>
                )
              })}
              
              {/* Line chart */}
              <path
                d={linePath}
                fill="none"
                stroke="url(#lineGradient)"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              
              {/* Gradient definition */}
              <defs>
                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#667eea" />
                  <stop offset="100%" stopColor="#764ba2" />
                </linearGradient>
              </defs>
              
              {/* Data points */}
              {chartData.map((d: any, i: number) => {
                const x = scaleX(i)
                const y = scaleY(d.value)
                const color = statusColors[d.status] || '#6b7280'
                
                return (
                  <g key={i}>
                    <circle
                      cx={x}
                      cy={y}
                      r="6"
                      fill={color}
                      stroke="white"
                      strokeWidth="2"
                    />
                    {/* Date label */}
                    <text
                      x={x}
                      y={chartHeight - padding.bottom + 20}
                      textAnchor="middle"
                      fontSize="11"
                      fill="#6b7280"
                      transform={`rotate(-45, ${x}, ${chartHeight - padding.bottom + 20})`}
                    >
                      {new Date(d.date).toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' })}
                    </text>
                  </g>
                )
              })}
              
              {/* Axes */}
              <line
                x1={padding.left}
                y1={padding.top}
                x2={padding.left}
                y2={padding.top + plotHeight}
                stroke="#1f2937"
                strokeWidth="2"
              />
              <line
                x1={padding.left}
                y1={padding.top + plotHeight}
                x2={padding.left + plotWidth}
                y2={padding.top + plotHeight}
                stroke="#1f2937"
                strokeWidth="2"
              />
              
              {/* Y-axis label */}
              <text
                x={20}
                y={chartHeight / 2}
                textAnchor="middle"
                fontSize="14"
                fill="#1f2937"
                fontWeight="600"
                transform={`rotate(-90, 20, ${chartHeight / 2})`}
              >
                {history.biomarker.unit_std}
              </text>
            </svg>
          </div>
          <div style={{ textAlign: 'center', marginTop: '16px', fontSize: '13px', color: '#6b7280' }}>
            <span style={{ display: 'inline-block', width: '12px', height: '12px', background: '#10b98120', border: '2px solid #10b981', borderRadius: '2px', marginRight: '6px', verticalAlign: 'middle' }}></span>
            Референсный диапазон
          </div>
        </div>
      )}
      
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
              {history.history.map((h: any, idx: number) => (
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
