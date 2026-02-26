import Header from './Header'
import Nav from './Nav'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-navy-900 flex flex-col">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Nav />
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
