import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, User, Shield } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { authAPI } from '../services/api'

export default function SignupPage({ onSignupSuccess }) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const validateForm = () => {
    if (!username || !email || !password || !confirmPassword) {
      toast.error('Please fill in all fields')
      return false
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match')
      return false
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters')
      return false
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      toast.error('Please enter a valid email')
      return false
    }
    return true
  }

  const handleSignup = async (e) => {
    e.preventDefault()
    
    if (!validateForm()) return

    setLoading(true)
    try {
      const response = await authAPI.signup(username, email, password)
      const { token, user } = response.data
      
      localStorage.setItem('authToken', token)
      localStorage.setItem('userData', JSON.stringify(user))
      
      toast.success('Account created successfully!')
      onSignupSuccess()
      navigate('/dashboard')
    } catch (error) {
      console.error('Signup error:', error)
      toast.error(error.response?.data?.message || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center px-6 relative overflow-hidden py-12">
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

          <h2 className="text-2xl font-bold text-center mb-2">Create Account</h2>
          <p className="text-dark-400 text-center mb-8">Join us for advanced threat detection</p>

          <form onSubmit={handleSignup} className="space-y-4">
            {/* Username */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dark-200">Username</label>
              <div className="relative">
                <User size={18} className="absolute left-3 top-3 text-neon-blue" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Choose a username"
                  className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow text-dark-100 placeholder-dark-500"
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dark-200">Email</label>
              <div className="relative">
                <Mail size={18} className="absolute left-3 top-3 text-neon-blue" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
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
                  placeholder="Create a password"
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

            {/* Confirm Password */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-dark-200">Confirm Password</label>
              <div className="relative">
                <Lock size={18} className="absolute left-3 top-3 text-neon-blue" />
                <input
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-10 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow text-dark-100 placeholder-dark-500"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-3 text-dark-400 hover:text-neon-blue transition-colors"
                >
                  {showConfirm ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            {/* Terms */}
            <div className="flex items-center gap-2">
              <input type="checkbox" id="terms" className="w-4 h-4 rounded border-dark-700" required />
              <label htmlFor="terms" className="text-sm text-dark-400">
                I agree to the terms and conditions
              </label>
            </div>

            {/* Signup button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 font-semibold disabled:opacity-50"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-dark-700" />
            <span className="text-dark-500 text-sm">or</span>
            <div className="flex-1 h-px bg-dark-700" />
          </div>

          {/* Login link */}
          <p className="text-center text-dark-400">
            Already have an account?{' '}
            <Link to="/login" className="text-neon-blue hover:text-neon-purple transition-colors font-semibold">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
