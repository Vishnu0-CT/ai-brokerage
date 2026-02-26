export default function ErrorMessage({ error, onRetry }) {
  const message = error?.message || 'Something went wrong'

  return (
    <div className="bg-negative/10 border border-negative/30 rounded-xl p-6 text-center">
      <div className="w-12 h-12 rounded-full bg-negative/20 flex items-center justify-center mx-auto mb-4">
        <svg className="w-6 h-6 text-negative" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      </div>
      <p className="text-sm text-negative mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 text-sm font-medium bg-negative/20 text-negative hover:bg-negative/30 rounded-lg transition-colors"
        >
          Retry
        </button>
      )}
    </div>
  )
}
