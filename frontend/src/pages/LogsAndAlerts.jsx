import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { Download, Trash2, Search } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'

const API_BASE = 'http://localhost:8081/api'

export default function LogsAndAlerts({ onLogout }) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  // Fetch real logs from backend
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await fetch(`${API_BASE}/logs?limit=100`)
        if (response.ok) {
          const data = await response.json()
          // Transform backend log format to frontend format
          const transformedLogs = (data.logs || []).map(log => ({
            id: log.id,
            timestamp: log.timestamp,
            type: log.attack_type || 'Unknown',
            ip: log.src_ip || '0.0.0.0',
            severity: (log.severity || 'medium').toLowerCase(),
            status: log.detection_method === 'ML' ? 'Blocked' : 'Logged'
          }))
          setLogs(transformedLogs)
        } else {
          // Fallback to mock data
          setLogs([
            { id: 1, timestamp: new Date(Date.now() - 300000).toISOString(), type: 'Port Scan', ip: '192.168.1.105', severity: 'high', status: 'Blocked' },
            { id: 2, timestamp: new Date(Date.now() - 600000).toISOString(), type: 'Normal', ip: '192.168.1.50', severity: 'low', status: 'Allowed' },
            { id: 3, timestamp: new Date(Date.now() - 900000).toISOString(), type: 'DoS Attack', ip: '10.0.0.15', severity: 'critical', status: 'Blocked' },
          ])
        }
      } catch (error) {
        console.error('Error fetching logs:', error)
        // Fallback to mock data
        setLogs([
          { id: 1, timestamp: new Date(Date.now() - 300000).toISOString(), type: 'Port Scan', ip: '192.168.1.105', severity: 'high', status: 'Blocked' },
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
    const interval = setInterval(fetchLogs, 5000)
    return () => clearInterval(interval)
  }, [])

  const filteredLogs = logs.filter(log => {
    const matchSearch = log.ip.includes(searchTerm) || log.type.toLowerCase().includes(searchTerm.toLowerCase())
    const matchType = filterType === 'all' || log.type === filterType
    return matchSearch && matchType
  })

  const getSeverityColor = (severity) => {
    const colors = {
      critical: 'text-red-500 bg-red-500/20',
      high: 'text-orange-500 bg-orange-500/20',
      medium: 'text-yellow-500 bg-yellow-500/20',
      low: 'text-green-500 bg-green-500/20',
    }
    return colors[severity] || colors.low
  }

  const getStatusColor = (status) => {
    const colors = {
      'Blocked': 'text-red-500 bg-red-500/20',
      'Allowed': 'text-green-500 bg-green-500/20',
      'Logged': 'text-blue-500 bg-blue-500/20',
    }
    return colors[status] || colors['Logged']
  }

  const handleExport = () => {
    const csv = [
      ['ID', 'Timestamp', 'Type', 'IP Address', 'Severity', 'Status'],
      ...filteredLogs.map(log => [
        log.id,
        new Date(log.timestamp).toLocaleString(),
        log.type,
        log.ip,
        log.severity,
        log.status,
      ]),
    ]
    const csvContent = csv.map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs-${Date.now()}.csv`
    a.click()
    toast.success('Logs exported successfully!')
  }

  const handleClearLogs = () => {
    if (window.confirm('Are you sure you want to clear all logs?')) {
      setLogs([])
      toast.success('All logs have been cleared')
    }
  }

  return (
    <div className="min-h-screen bg-dark-900">
      <Navbar onLogout={onLogout} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent mb-2">
            Logs & Alerts
          </h1>
          <p className="text-dark-400">Threat detection logs and security alerts</p>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
        >
          <div className="glass rounded-lg p-4 border border-white/5">
            <p className="text-dark-400 text-sm mb-2">Total Logs</p>
            <p className="text-2xl font-bold text-neon-blue">{logs.length}</p>
          </div>
          <div className="glass rounded-lg p-4 border border-white/5">
            <p className="text-dark-400 text-sm mb-2">Critical</p>
            <p className="text-2xl font-bold text-red-500">{logs.filter(l => l.severity === 'critical').length}</p>
          </div>
          <div className="glass rounded-lg p-4 border border-white/5">
            <p className="text-dark-400 text-sm mb-2">High</p>
            <p className="text-2xl font-bold text-orange-500">{logs.filter(l => l.severity === 'high').length}</p>
          </div>
          <div className="glass rounded-lg p-4 border border-white/5">
            <p className="text-dark-400 text-sm mb-2">Blocked Threats</p>
            <p className="text-2xl font-bold text-neon-pink">{logs.filter(l => l.status === 'Blocked').length}</p>
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-xl p-6 border border-white/5 mb-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            {/* Search */}
            <div className="relative">
              <Search size={18} className="absolute left-3 top-3 text-neon-blue" />
              <input
                type="text"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow"
              />
            </div>

            {/* Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow appearance-none cursor-pointer"
            >
              <option value="all">All Types</option>
              <option value="Port Scan">Port Scan</option>
              <option value="DoS Attack">DoS Attack</option>
              <option value="Brute Force">Brute Force</option>
              <option value="Suspicious Traffic">Suspicious Traffic</option>
              <option value="Normal">Normal</option>
            </select>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleExport}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-neon-blue to-neon-purple hover:shadow-glow rounded-lg px-4 py-2 font-semibold transition-all"
              >
                <Download size={18} />
                Export
              </button>
              <button
                onClick={handleClearLogs}
                className="flex-1 flex items-center justify-center gap-2 bg-red-500/20 border border-red-500/50 text-red-400 hover:bg-red-500/30 rounded-lg px-4 py-2 font-semibold transition-all"
              >
                <Trash2 size={18} />
                Clear
              </button>
            </div>
          </div>
        </motion.div>

        {/* Logs Table */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass rounded-xl border border-white/5 overflow-hidden"
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5 bg-dark-800/50">
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">ID</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Timestamp</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Type</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">IP Address</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Severity</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.length > 0 ? (
                  filteredLogs.map((log, idx) => (
                    <motion.tr
                      key={log.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="px-6 py-4 text-sm text-dark-300">#{log.id}</td>
                      <td className="px-6 py-4 text-sm text-dark-300">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 rounded bg-neon-blue/20 text-neon-blue text-xs">{log.type}</span></td>
                      <td className="px-6 py-4 text-sm text-dark-300 font-mono">{log.ip}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(log.severity)}`}>
                          {log.severity.charAt(0).toUpperCase() + log.severity.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(log.status)}`}>
                          {log.status}
                        </span>
                      </td>
                    </motion.tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-6 py-12 text-center text-dark-400">
                      No logs found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
