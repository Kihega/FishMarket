import { useState } from 'react'
import { MenuIcon } from './Icons'

/**
 * Reusable sidebar dashboard shell, shared by Admin/Seller/Buyer.
 * `items` = [{ key, label, icon }] — icon is a small SVG component.
 * `activeKey` / `onSelect` control which content panel shows.
 *
 * The sidebar header no longer repeats the "SmartFish" brand text — it's
 * already shown in the top bar. Instead it's a (☰) menu icon: tapping it
 * shows/hides the sidebar's menu buttons (collapses to icons-only).
 * On small screens the sidebar still behaves as a slide-out drawer.
 */
export default function DashboardLayout({ items, activeKey, onSelect, children }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(true)

  return (
    <div className="flex min-h-[calc(100vh-64px)] bg-gray-50">
      {/* Mobile top bar with hamburger */}
      <div className="md:hidden fixed top-16 left-0 right-0 bg-white border-b z-30 flex items-center px-4 py-3">
        <button
          onClick={() => setMobileOpen(true)}
          className="text-blue-700 font-semibold flex items-center gap-2"
          aria-label="Open menu"
        >
          <MenuIcon className="w-6 h-6" />
          Menu
        </button>
      </div>

      {/* Sidebar — desktop: static, mobile: slide-over drawer */}
      <aside
        className={`fixed md:static top-0 left-0 h-full md:h-auto bg-blue-900 text-white flex flex-col z-40
          transform transition-all duration-200
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          ${menuOpen ? 'w-64' : 'w-16'}`}
      >
        <div className={`p-5 border-b border-blue-800 flex items-center ${menuOpen ? 'justify-between' : 'justify-center'}`}>
          <button
            onClick={() => setMenuOpen((open) => !open)}
            className="text-white hover:text-blue-200 flex-shrink-0"
            aria-label={menuOpen ? 'Hide menu' : 'Show menu'}
          >
            <MenuIcon className="w-6 h-6" />
          </button>
          <button className="md:hidden" onClick={() => setMobileOpen(false)} aria-label="Close menu">✕</button>
        </div>

        <nav className="flex-1 overflow-y-auto py-4">
          {items.map((item) => (
            <button
              key={item.key}
              onClick={() => {
                onSelect(item.key)
                setMobileOpen(false)
              }}
              title={item.label}
              className={`w-full flex items-center gap-3 px-5 py-3 text-left transition
                ${activeKey === item.key
                  ? 'bg-blue-700 border-r-4 border-white font-semibold'
                  : 'text-blue-100 hover:bg-blue-800'}`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {menuOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>
      </aside>

      {/* Backdrop for mobile drawer */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Content area */}
      <main className="flex-1 p-4 md:p-8 pt-20 md:pt-8 overflow-x-hidden">
        {children}
      </main>
    </div>
  )
}
