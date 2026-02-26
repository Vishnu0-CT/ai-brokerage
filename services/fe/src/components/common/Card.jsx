export default function Card({ children, className = '', padding = 'p-5', onClick }) {
  return (
    <div className={`bg-navy-800 border border-navy-600 rounded-xl ${padding} ${className}`} onClick={onClick}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

export function StatCard({ label, value, subValue, trend, icon }) {
  const trendColor = trend === 'up' ? 'text-positive' : trend === 'down' ? 'text-negative' : 'text-slate-400'

  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
          <p className="text-2xl font-mono font-semibold text-slate-100 mt-1">{value}</p>
          {subValue && (
            <p className={`text-xs font-mono mt-1 ${trendColor}`}>{subValue}</p>
          )}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-navy-700 flex items-center justify-center text-slate-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}
