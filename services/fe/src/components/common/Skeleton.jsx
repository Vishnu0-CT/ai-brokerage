export default function Skeleton({ className = '', count = 1 }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={`bg-navy-700 rounded-lg animate-pulse ${className}`}
        />
      ))}
    </>
  )
}

export function CardSkeleton() {
  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5 space-y-3">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  )
}

export function TableSkeleton({ rows = 5 }) {
  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5 space-y-4">
      <Skeleton className="h-4 w-1/4" />
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <Skeleton className="h-4 w-1/5" />
          <Skeleton className="h-4 w-1/6" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-4 w-1/6" />
        </div>
      ))}
    </div>
  )
}

export function ChartSkeleton() {
  return (
    <div className="bg-navy-800 border border-navy-600 rounded-xl p-5">
      <Skeleton className="h-4 w-1/3 mb-4" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}
