import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { Settings, Bell, Shield, Zap, Save, Wifi } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

const API_BASE = 'http://localhost:8081/api'

export default function SettingsPage({ onLogout }) {
  const [isMonitoring, setIsMonitoring] = useState(true)
  const [sensitivity, setSensitivity] = useState(7)
  const [darkMode, setDarkMode] = useState(true)
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    pushNotifications: true,
    criticalOnly: false,
    dailyReport: true,
  })
  const [autoResponse, setAutoResponse] = useState(true)
  const [blockThreshold, setBlockThreshold] = useState(75)
  const [interfaces, setInterfaces] = useState([])
  const [selectedInterface, setSelectedInterface] = useState('auto')

  useEffect(() => {
    fetchInterfaces()
  }, [])

  const fetchInterfaces = async () => {
    try {
      const response = await fetch(`${API_BASE}/interfaces`)
      if (response.ok) {
        const data = await response.json()
        setInterfaces(data)
      }
    } catch (error) {
      console.error('Error fetching interfaces:', error)
    }
  }

  const handleInterfaceChange = async (iface) => {
    setSelectedInterface(iface)
    try {
      const response = await fetch(`${API_BASE}/settings/interface`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interface: iface })
      })
      if (response.ok) {
        toast.success(`Interface changed to ${iface === 'auto' ? 'Auto-detect' : iface}`)
      } else {
        toast.error('Failed to change interface')
      }
    } catch (error) {
      toast.error('Error connecting to backend')
    }
  }

  const handleSave = () => {
    toast.success('Settings saved successfully!')
  }

  const toggleNotification = (key) => {
    setNotifications(prev => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar onLogout={onLogout} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent mb-2">
            Settings
          </h1>
          <p className="text-dark-400">Configure NIDS monitoring preferences and alerts</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ staggerChildren: 0.1 }}
          className="space-y-6"
        >
          {/* Monitoring Control */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Shield size={24} className="text-neon-blue" />
                  <h2 className="text-xl font-semibold">Monitoring Control</h2>
                </div>
                <p className="text-dark-400">Start or stop real-time packet monitoring</p>
              </div>
              <button
                onClick={() => setIsMonitoring(!isMonitoring)}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  isMonitoring
                    ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                    : 'bg-red-500/20 text-red-400 border border-red-500/50'
                }`}
              >
                {isMonitoring ? '🔴 Monitoring' : '⚫ Paused'}
              </button>
            </div>
          </motion.div>

          {/* Network Interface */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <div className="flex items-center gap-3 mb-6">
              <Wifi size={24} className="text-neon-blue" />
              <h2 className="text-xl font-semibold">Network Interface</h2>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-dark-400 text-sm mb-4">Select the interface to monitor</p>
                <select 
                  value={selectedInterface}
                  onChange={(e) => handleInterfaceChange(e.target.value)}
                  className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 focus:outline-none focus:border-neon-blue text-dark-200"
                >
                  <option value="auto">Auto-detect Active Interface</option>
                  {interfaces.map(iface => (
                    <option key={iface.name} value={iface.name}>
                      {iface.description || iface.name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-dark-500 mt-2 italic">
                  * Changing interface will restart the detection engine.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Detection Sensitivity */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <div className="flex items-center gap-3 mb-6">
              <Zap size={24} className="text-neon-purple" />
              <h2 className="text-xl font-semibold">Detection Sensitivity</h2>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-dark-300">Sensitivity Level: <span className="text-neon-purple font-semibold">{sensitivity}/10</span></span>
                  <span className="text-dark-400 text-sm">
                    {sensitivity <= 3 ? 'Low' : sensitivity <= 6 ? 'Medium' : 'High'}
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={sensitivity}
                  onChange={(e) => setSensitivity(Number(e.target.value))}
                  className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #b536d9 0%, #b536d9 ${sensitivity * 10}%, #3e4451 ${sensitivity * 10}%, #3e4451 100%)`
                  }}
                />
                <p className="text-dark-400 text-sm mt-2">
                  {sensitivity <= 3 && 'Only critical threats will be flagged'}
                  {sensitivity > 3 && sensitivity <= 6 && 'Normal and high-risk threats will be detected'}
                  {sensitivity > 6 && 'Maximum detection - all anomalies will be flagged'}
                </p>
              </div>
            </div>
          </motion.div>

          {/* Block Threshold */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <h2 className="text-xl font-semibold mb-6">Auto-Block Threshold</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-dark-300">Block Confidence Threshold: <span className="text-neon-pink font-semibold">{blockThreshold}%</span></span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  value={blockThreshold}
                  onChange={(e) => setBlockThreshold(Number(e.target.value))}
                  className="w-full h-2 bg-dark-700 rounded-lg appearance-none cursor-pointer"
                  style={{
                    background: `linear-gradient(to right, #ff006e 0%, #ff006e ${blockThreshold - 50}%, #3e4451 ${blockThreshold - 50}%, #3e4451 100%)`
                  }}
                />
                <p className="text-dark-400 text-sm mt-2">
                  Threats with confidence score above {blockThreshold}% will be automatically blocked
                </p>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoResponse}
                  onChange={(e) => setAutoResponse(e.target.checked)}
                  className="w-4 h-4 rounded border-dark-700 cursor-pointer"
                />
                <span className="text-dark-300">Enable automatic threat blocking</span>
              </label>
            </div>
          </motion.div>

          {/* Notifications */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <div className="flex items-center gap-3 mb-6">
              <Bell size={24} className="text-neon-blue" />
              <h2 className="text-xl font-semibold">Notification Settings</h2>
            </div>
            <div className="space-y-4">
              {[
                { key: 'emailAlerts', label: 'Email Alerts', desc: 'Receive threat alerts via email' },
                { key: 'pushNotifications', label: 'Push Notifications', desc: 'Get real-time browser notifications' },
                { key: 'criticalOnly', label: 'Critical Threats Only', desc: 'Only notify for critical severity threats' },
                { key: 'dailyReport', label: 'Daily Report', desc: 'Receive daily security summary report' },
              ].map(item => (
                <label key={item.key} className="flex items-start gap-3 cursor-pointer hover:bg-white/5 p-3 rounded-lg transition-all">
                  <input
                    type="checkbox"
                    checked={notifications[item.key]}
                    onChange={() => toggleNotification(item.key)}
                    className="w-5 h-5 rounded border-dark-700 cursor-pointer mt-1"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-dark-200">{item.label}</p>
                    <p className="text-sm text-dark-400">{item.desc}</p>
                  </div>
                </label>
              ))}
            </div>
          </motion.div>

          {/* Interface Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <div className="flex items-center gap-3 mb-6">
              <Settings size={24} className="text-neon-purple" />
              <h2 className="text-xl font-semibold">Interface Settings</h2>
            </div>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={darkMode}
                  onChange={(e) => setDarkMode(e.target.checked)}
                  className="w-4 h-4 rounded border-dark-700 cursor-pointer"
                />
                <span className="text-dark-300">Dark Mode (Recommended)</span>
              </label>
              <div className="pt-4 border-t border-dark-700">
                <p className="text-dark-400 text-sm mb-4">Auto-refresh interval</p>
                <select className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 focus:outline-none focus:border-neon-blue">
                  <option>1 second</option>
                  <option selected>5 seconds</option>
                  <option>10 seconds</option>
                  <option>30 seconds</option>
                  <option>1 minute</option>
                </select>
              </div>
            </div>
          </motion.div>

          {/* About & Info */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <h2 className="text-xl font-semibold mb-4">System Information</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-dark-400 mb-1">NIDS Version</p>
                <p className="text-neon-blue font-semibold">1.0.0</p>
              </div>
              <div>
                <p className="text-dark-400 mb-1">ML Model</p>
                <p className="text-neon-blue font-semibold">Random Forest</p>
              </div>
              <div>
                <p className="text-dark-400 mb-1">Database</p>
                <p className="text-neon-blue font-semibold">SQLite</p>
              </div>
              <div>
                <p className="text-dark-400 mb-1">Uptime</p>
                <p className="text-neon-blue font-semibold">14d 5h 32m</p>
              </div>
              <div>
                <p className="text-dark-400 mb-1">Active Rules</p>
                <p className="text-neon-blue font-semibold">256</p>
              </div>
              <div>
                <p className="text-dark-400 mb-1">Last Update</p>
                <p className="text-neon-blue font-semibold">2 hours ago</p>
              </div>
            </div>
          </motion.div>

          {/* Save Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="flex gap-4"
          >
            <button
              onClick={handleSave}
              className="flex-1 btn-primary py-3 font-semibold flex items-center justify-center gap-2"
            >
              <Save size={20} />
              Save Settings
            </button>
            <button className="flex-1 btn-secondary py-3 font-semibold">
              Reset to Default
            </button>
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
