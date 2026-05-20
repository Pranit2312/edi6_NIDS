import { Link, useLocation } from 'react-router-dom'
import { Shield, Activity, AlertTriangle, Settings, LogOut, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { motion } from 'framer-motion'

export default function Navbar({ onLogout }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  
  const isActive = (path) => location.pathname === path

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Activity },
    { path: '/monitoring', label: 'Live Monitor', icon: AlertTriangle },
    { path: '/analytics', label: 'Analytics', icon: Activity },
    { path: '/logs', label: 'Logs & Alerts', icon: AlertTriangle },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  return (
    <nav className="glass-dark sticky top-0 z-50 border-b border-neon-blue/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2 group">
            <div className="p-2 rounded-lg bg-gradient-to-r from-neon-blue to-neon-purple group-hover:shadow-glow transition-all">
              <Shield size={20} className="text-dark-900" />
            </div>
            <span className="font-bold text-lg bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">NIDS</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                    isActive(item.path)
                      ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/50'
                      : 'text-dark-300 hover:text-neon-blue hover:bg-neon-blue/10'
                  }`}
                >
                  <Icon size={16} />
                  <span className="text-sm font-medium">{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Right side actions */}
          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={onLogout}
              className="px-4 py-2 rounded-lg border border-neon-pink text-neon-pink hover:bg-neon-pink/10 transition-all text-sm font-medium flex items-center gap-2"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden p-2 hover:bg-neon-blue/10 rounded-lg transition-all"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden pb-4 border-t border-neon-blue/20"
          >
            <div className="flex flex-col gap-2 pt-4">
              {navItems.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-all ${
                      isActive(item.path)
                        ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/50'
                        : 'text-dark-300 hover:text-neon-blue hover:bg-neon-blue/10'
                    }`}
                  >
                    <Icon size={16} />
                    <span className="text-sm font-medium">{item.label}</span>
                  </Link>
                )
              })}
              <button
                onClick={() => {
                  setMobileMenuOpen(false)
                  onLogout()
                }}
                className="px-4 py-2 rounded-lg border border-neon-pink text-neon-pink hover:bg-neon-pink/10 transition-all text-sm font-medium flex items-center gap-2 mt-2"
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </nav>
  )
}
