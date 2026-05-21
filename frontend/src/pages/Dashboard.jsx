import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import StatCard from '../components/StatCard'
import ThreatAlert from '../components/ThreatAlert'
import { Activity, AlertTriangle, Shield, Wifi, Cpu, HardDrive } from 'lucide-react'
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { motion } from 'framer-motion'
import { generateMockStats, generateMockPackets } from '../utils/helpers'

const API_BASE = 'http://localhost:8081/api'

export default function Dashboard({ onLogout }) {
  const [stats, setStats] = useState(generateMockStats())
  const [threats, setThreats] = useState([])
  const [chartData, setChartData] = useState([])
  const [attackData, setAttackData] = useState([])

  useEffect(() => {
    const initializeData = async () => {
      await generateChartData()
      await generateAttackData()
      await fetchRealData()
    }
    
    initializeData()

    const statsInterval = setInterval(fetchRealData, 3000)
    const chartsInterval = setInterval(() => {
      generateChartData()
      generateAttackData()
    }, 10000)

    return () => {
      clearInterval(statsInterval)
      clearInterval(chartsInterval)
    }
  }, [])

  const fetchRealData = async () => {
    try {
      // Fetch real stats from backend
      const statsResponse = await fetch(`${API_BASE}/stats`)
      if (!statsResponse.ok) throw new Error('Failed to fetch stats')
      
      const statsData = await statsResponse.json()
      
      setStats({
        totalPackets: statsData.totalPackets || 0,
        threatsDetected: statsData.threatsDetected || 0,
        safeTraffic: statsData.safeTraffic || 0,
        activeConnections: statsData.activeConnections || 0,
        cpuUsage: statsData.cpuUsage || 0,
        memoryUsage: statsData.memoryUsage || 0,
        pps: statsData.packetsPerSecond || 0,
        apps: statsData.attackPacketsPerSecond || 0
      })

      // Fetch real alerts/threats from backend
      const alertsResponse = await fetch(`${API_BASE}/alerts?limit=3`)
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json()
        // Transform backend alerts (which can be from memory or database)
        const alertList = Array.isArray(alertsData) ? alertsData : alertsData.alerts || []
        const threatsList = alertList.slice(0, 3).map((alert, idx) => ({
          id: alert.id || idx,
          title: alert.title || alert.type || 'Security Alert',
          desc: alert.description || `${alert.attack_type || alert.type || 'Threat'} detected on ${alert.source_ip || alert.src_ip || 'unknown'}`,
          severity: (alert.severity || 'medium').toLowerCase()
        }))
        setThreats(threatsList)
      }
    } catch (error) {
      console.error('Error fetching real data:', error)
    }
  }

  const generateChartData = async () => {
    try {
      const response = await fetch(`${API_BASE}/analytics/traffic-trends?range=24h`)
      if (response.ok) {
        const data = await response.json()
        setChartData(data && data.length > 0 ? data : generateMockChartData())
      } else {
        setChartData(generateMockChartData())
      }
    } catch (error) {
      console.error('Error fetching chart data:', error)
      setChartData(generateMockChartData())
    }
  }

  const generateMockChartData = () => {
    const data = []
    for (let i = 0; i < 24; i++) {
      data.push({
        time: `${i}:00`,
        packets: Math.floor(Math.random() * 5000) + 2000,
        threats: Math.floor(Math.random() * 50) + 10,
      })
    }
    return data
  }

  const generateAttackData = async () => {
    try {
      const response = await fetch(`${API_BASE}/analytics/attack-distribution`)
      if (response.ok) {
        const data = await response.json()
        if (data && data.length > 0) {
          setAttackData(data)
        } else {
          setAttackData(generateMockAttackData())
        }
      } else {
        setAttackData(generateMockAttackData())
      }
    } catch (error) {
      console.error('Error fetching attack data:', error)
      setAttackData(generateMockAttackData())
    }
  }

  const generateMockAttackData = () => {
    return [
      { name: 'Normal', value: 85, color: '#00d9ff' },
      { name: 'DoS', value: 8, color: '#ff006e' },
      { name: 'Port Scan', value: 4, color: '#b536d9' },
      { name: 'Brute Force', value: 2, color: '#ffb003' },
      { name: 'Suspicious', value: 1, color: '#ff0066' },
    ]
  }

  const generateThreats = () => {
    setThreats([
      { id: 1, title: 'High CPU Usage Detected', desc: 'CPU usage exceeded 85% threshold', severity: 'high' },
      { id: 2, title: 'Unusual Traffic Pattern', desc: 'Detected 1200 requests from single IP', severity: 'medium' },
      { id: 3, title: 'Port Scan Attempt', desc: 'Scanning detected on ports 20-65535', severity: 'high' },
    ])
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
            Dashboard
          </h1>
          <p className="text-dark-400">Real-time network monitoring and threat detection</p>
        </motion.div>

        {/* Active Threats */}
        {threats.length > 0 && (
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="mb-8"
          >
            <h2 className="text-lg font-semibold mb-4">Active Threats</h2>
            <div className="space-y-2">
              {threats.map((threat) => (
                <ThreatAlert
                  key={threat.id}
                  title={threat.title}
                  description={threat.desc}
                  severity={threat.severity}
                  onClose={() => setThreats(threats.filter(t => t.id !== threat.id))}
                />
              ))}
            </div>
          </motion.div>
        )}

        {/* Stats Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ staggerChildren: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <StatCard
            title="Total Packets"
            value={stats.totalPackets.toLocaleString()}
            icon={Activity}
            trend={Math.floor(Math.random() * 20) - 10}
            color="blue"
          />
          <StatCard
            title="Threats Detected"
            value={stats.threatsDetected}
            icon={AlertTriangle}
            trend={-5}
            color="pink"
          />
          <StatCard
            title="Safe Traffic"
            value={`${stats.safeTraffic}%`}
            icon={Shield}
            trend={2}
            color="green"
          />
          <StatCard
            title="Packets / Sec"
            value={stats.pps}
            icon={Wifi}
            color="purple"
          />
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ staggerChildren: 0.1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8"
        >
          <StatCard
            title="Active Connections"
            value={stats.activeConnections}
            icon={Wifi}
            color="purple"
          />
          <StatCard
            title="CPU Usage"
            value={`${stats.cpuUsage}%`}
            icon={Cpu}
            color="blue"
          />
          <StatCard
            title="Memory Usage"
            value={`${stats.memoryUsage}%`}
            icon={HardDrive}
            color="purple"
          />
          <StatCard
            title="Attack PPS"
            value={stats.apps}
            icon={AlertTriangle}
            color="pink"
          />
        </motion.div>

        {/* Charts Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          {/* Traffic Chart */}
          <div className="lg:col-span-2 glass rounded-xl p-6 border border-white/5">
            <h3 className="text-lg font-semibold mb-6">Network Traffic (24h)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPackets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d9ff" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#00d9ff" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff006e" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#ff006e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="#a8b3be" />
                <YAxis stroke="#a8b3be" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
                <Legend />
                <Area type="monotone" dataKey="packets" stroke="#00d9ff" fillOpacity={1} fill="url(#colorPackets)" />
                <Area type="monotone" dataKey="threats" stroke="#ff006e" fillOpacity={1} fill="url(#colorThreats)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Attack Distribution */}
          <div className="glass rounded-xl p-6 border border-white/5">
            <h3 className="text-lg font-semibold mb-6">Attack Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={attackData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {attackData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Bottom info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 glass rounded-xl p-6 border border-white/5 text-center"
        >
          <p className="text-dark-400">
            Last updated: {new Date().toLocaleTimeString()}
          </p>
        </motion.div>
      </main>
    </div>
  )
}
