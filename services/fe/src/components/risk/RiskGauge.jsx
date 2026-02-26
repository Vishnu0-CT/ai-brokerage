export default function RiskGauge({ label, value, max, unit, status, description }) {
  const percentage = Math.min((value / max) * 100, 100)

  const getStatusColor = () => {
    if (status === 'critical') return 'text-negative'
    if (status === 'warning') return 'text-warning'
    if (status === 'elevated') return 'text-warning'
    return 'text-positive'
  }

  const getBarColor = () => {
    if (percentage > 90) return 'bg-negative'
    if (percentage > 70) return 'bg-warning'
    if (percentage > 50) return 'bg-warning/70'
    return 'bg-positive'
  }

  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-sm font-medium text-slate-300">{label}</h4>
          <p className="text-xs text-slate-500 mt-0.5">{description}</p>
        </div>
        <div className={`text-xs font-medium px-2 py-1 rounded ${
          status === 'critical' ? 'bg-negative/20 text-negative' :
          status === 'warning' || status === 'elevated' ? 'bg-warning/20 text-warning' :
          'bg-positive/20 text-positive'
        }`}>
          {status?.toUpperCase() || 'NORMAL'}
        </div>
      </div>

      {/* Gauge bar */}
      <div className="relative h-3 bg-navy-700 rounded-full overflow-hidden mb-3">
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all duration-500 ${getBarColor()}`}
          style={{ width: `${percentage}%` }}
        />
        <div className="absolute left-1/2 top-0 w-px h-full bg-navy-500" />
        <div className="absolute left-3/4 top-0 w-px h-full bg-navy-500" />
      </div>

      {/* Value display */}
      <div className="flex items-end justify-between">
        <div>
          <span className={`font-mono text-2xl font-semibold ${getStatusColor()}`}>
            {typeof value === 'number' ? value.toLocaleString('en-IN') : value}
          </span>
          {unit && <span className="text-slate-500 text-sm ml-1">{unit}</span>}
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-500">of {max.toLocaleString('en-IN')}</span>
          <div className="font-mono text-sm text-slate-400">{percentage.toFixed(0)}%</div>
        </div>
      </div>
    </div>
  )
}
