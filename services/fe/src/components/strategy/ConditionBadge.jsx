const CONDITION_ICONS = {
  price_relative: '\ud83d\udcc8',
  price_absolute: '\ud83d\udcb0',
  indicator: '\ud83d\udcca',
  oi: '\ud83d\udcc9',
  time: '\u23f0',
  target: '\ud83c\udfaf',
  stoploss: '\ud83d\uded1',
  time_based: '\u23f1\ufe0f',
  trailing: '\ud83d\udccd'
}

const OPERATOR_LABELS = {
  greater_than: '>',
  less_than: '<',
  equals: '=',
  greater_than_by: '+',
  less_than_by: '-',
  increasing: '\u2191',
  decreasing: '\u2193',
  crosses_above: '\u2197',
  crosses_below: '\u2198'
}

const INDICATOR_LABELS = {
  spot_price: 'Price',
  days_high: "Day's High",
  days_low: "Day's Low",
  prev_close: 'Prev Close',
  open_interest: 'OI',
  oi_change: 'OI Change',
  volume: 'Volume',
  rsi: 'RSI',
  ema_20: 'EMA 20',
  ema_50: 'EMA 50',
  vwap: 'VWAP',
  atr: 'ATR'
}

export default function ConditionBadge({ condition, type = 'entry' }) {
  const icon = CONDITION_ICONS[condition.type] || '\ud83d\udccb'

  const formatCondition = () => {
    if (type === 'exit') {
      switch (condition.type) {
        case 'target':
          return `Target +${condition.value}${condition.unit === 'percent' ? '%' : ' pts'}`
        case 'stoploss':
          return `Stop Loss -${condition.value}${condition.unit === 'percent' ? '%' : ' pts'}`
        case 'time_based':
          return `Exit at ${condition.value}`
        case 'trailing':
          return `Trailing SL ${condition.value}${condition.unit === 'percent' ? '%' : ' pts'}`
        default:
          return JSON.stringify(condition)
      }
    }

    const indicator = INDICATOR_LABELS[condition.indicator] || condition.indicator
    const operator = OPERATOR_LABELS[condition.operator] || condition.operator

    if (condition.type === 'price_relative') {
      const reference = INDICATOR_LABELS[condition.reference] || condition.reference
      return `${indicator} ${operator}${condition.value} ${condition.unit || ''} from ${reference}`
    }

    if (condition.type === 'oi' || condition.operator === 'increasing' || condition.operator === 'decreasing') {
      return `${indicator} ${operator === '\u2191' ? 'Increasing' : operator === '\u2193' ? 'Decreasing' : operator}`
    }

    if (condition.type === 'indicator') {
      return `${indicator} ${operator} ${condition.value || ''}`
    }

    if (condition.type === 'time') {
      return `Time ${operator} ${condition.value}`
    }

    return `${indicator} ${operator} ${condition.value || ''} ${condition.unit || ''}`
  }

  const bgColor = type === 'exit'
    ? condition.type === 'target'
      ? 'bg-positive/10 border-positive/30 text-positive'
      : condition.type === 'stoploss'
        ? 'bg-negative/10 border-negative/30 text-negative'
        : 'bg-navy-600 border-navy-500 text-slate-300'
    : 'bg-accent/10 border-accent/30 text-accent'

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border ${bgColor}`}>
      <span className="text-base">{icon}</span>
      <span className="text-sm font-medium">{formatCondition()}</span>
    </div>
  )
}
