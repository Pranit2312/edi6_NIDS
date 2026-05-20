import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, Shield } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { authAPI } from '../services/api'

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    
    if (!username || !password) {
      toast.error('Please fill in all fields')
      return
    }

    setLoading(true)
    try {
      const response = await authAPI.login(username, password)
      const { token, user } = response.data
      
      localStorage.setItem('authToken', token)
      localStorage.setItem('userData', JSON.stringify(user))
      
      toast.success('Login successful!')
      onLoginSuccess()
      navigate('/dashboard')
    } catch (error) {
      console.error('Login error:', error)
      toast.error(error.response?.data?.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center px-6 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 -right-40 w-80 h-80 bg-neon-purple/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 -left-40 w-80 h-80 bg-neon-blue/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="glass rounded-2xl p-8 border border-white/10">
          {/* Logo */}
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="p-3 rounded-lg bg-gradient-to-r from-neon-blue to-neon-purple">
              <Shield size={28} className="text-dark-900" />
            </div>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">NIDS</h1>
          </div>

          <h2 className="text-2xl font-bold text-center mb-2">Welcome Back</h2>
          <p className="text-dark-400 text-center mb-8">Sign in to your account</p>

          <form onSubmit={handleLogin} className="space-y-4">
            {/* Username */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dark-200">Username</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3 top-3 text-neon-blue" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow text-dark-100 placeholder-dark-500"
                />
              </div>
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dark-200">Password</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3 top-3 text-neon-blue" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-10 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow text-dark-100 placeholder-dark-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-dark-400 hover:text-neon-blue transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Remember me */}
            <div className="flex items-center gap-2">
              <input type="checkbox" id="remember" className="w-4 h-4 rounded border-dark-700" />
              <label htmlFor="remember" className="text-sm text-dark-400">Remember me</label>
            </div>

            {/* Login button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 font-semibold disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-dark-700" />
            <span className="text-dark-500 text-sm">or</span>
            <div className="flex-1 h-px bg-dark-700" />
          </div>

          {/* Signup link */}
          <p className="text-center text-dark-400">
            Don't have an account?{' '}
            <Link to="/signup" className="text-neon-blue hover:text-neon-purple transition-colors font-semibold">
              Sign up
            </Link>
          </p>
        </div>

        {/* Demo credentials */}
        <div className="mt-6 glass rounded-lg p-4 border border-neon-blue/20 text-center">
          <p className="text-xs text-dark-400 mb-2">Demo Credentials:</p>
          <p className="text-sm text-neon-blue">Username: demo</p>
          <p className="text-sm text-neon-blue">Password: demo123</p>
        </div>
      </motion.div>
    </div>
  )
}
