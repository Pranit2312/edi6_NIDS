import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, ComposedChart } from 'recharts'
import { motion } from 'framer-motion'

const API_BASE = 'http://localhost:8081/api'

export default function ThreatAnalytics({ onLogout }) {
  const [timeRange, setTimeRange] = useState('24h')
  const [analyticsData, setAnalyticsData] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalyticsData()
  }, [timeRange])

  const fetchAnalyticsData = async () => {
    setLoading(true)
    try {
      // Fetch attack trends
      const trendsResponse = await fetch(`${API_BASE}/analytics/traffic-trends?range=${timeRange}`)
      const trendsData = trendsResponse.ok ? await trendsResponse.json() : []

      // Fetch threat heatmap (top sources)
      const heatmapResponse = await fetch(`${API_BASE}/analytics/threat-heatmap`)
      const heatmapData = heatmapResponse.ok ? await heatmapResponse.json() : []

      // Fetch detection stats
      const statsResponse = await fetch(`${API_BASE}/analytics/detection-stats`)
      const statsData = statsResponse.ok ? await statsResponse.json() : []

      // Fetch attack distribution
      const distributionResponse = await fetch(`${API_BASE}/analytics/attack-distribution`)
      const distributionData = distributionResponse.ok ? await distributionResponse.json() : []

      // Fetch confidence distribution
      const confidenceResponse = await fetch(`${API_BASE}/analytics/confidence-distribution`)
      const confidenceData = confidenceResponse.ok ? await confidenceResponse.json() : []

      // Transform and set data
      setAnalyticsData({
        attackTrends: trendsData.length > 0 ? trendsData : generateMockTrends(),
        topThreats: heatmapData.length > 0 ? heatmapData.slice(0, 5) : generateMockThreats(),
        detectionStats: statsData.length > 0 ? statsData : generateMockStats(),
        confidenceData: confidenceData.length > 0 ? confidenceData : generateMockConfidence(),
      })
    } catch (error) {
      console.error('Error fetching analytics data:', error)
      // Fallback to mock data
      setAnalyticsData({
        attackTrends: generateMockTrends(),
        topThreats: generateMockThreats(),
        detectionStats: generateMockStats(),
        confidenceData: generateMockConfidence(),
      })
    } finally {
      setLoading(false)
    }
  }

  const generateMockTrends = () => {
    return Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      dos: Math.floor(Math.random() * 50),
      portScan: Math.floor(Math.random() * 30),
      bruteForce: Math.floor(Math.random() * 20),
      suspicious: Math.floor(Math.random() * 15),
    }))
  }

  const generateMockThreats = () => {
    return [
      { ip: '192.168.1.105', threats: 45, type: 'Port Scan' },
      { ip: '192.168.1.108', threats: 38, type: 'DoS' },
      { ip: '192.168.1.112', threats: 32, type: 'Brute Force' },
      { ip: '192.168.1.115', threats: 28, type: 'Suspicious' },
      { ip: '192.168.1.118', threats: 22, type: 'Port Scan' },
    ]
  }

  const generateMockStats = () => {
    return [
      { category: 'True Positive', value: 94, color: '#00ff88' },
      { category: 'False Positive', value: 4, color: '#ffb003' },
      { category: 'False Negative', value: 2, color: '#ff006e' },
    ]
  }

  const generateMockConfidence = () => {
    return Array.from({ length: 10 }, (_, i) => ({
      range: `${(i * 10)}-${(i + 1) * 10}%`,
      count: Math.floor(Math.random() * 50) + 10,
    }))
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
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent mb-2">
                Threat Analytics
              </h1>
              <p className="text-dark-400">Comprehensive threat analysis and statistics</p>
            </div>
            <div className="flex gap-2">
              {['24h', '7d', '30d'].map(range => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range)}
                  className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                    timeRange === range
                      ? 'bg-neon-blue/20 text-neon-blue border border-neon-blue/50'
                      : 'bg-dark-800 text-dark-400 border border-dark-700 hover:border-neon-blue'
                  }`}
                >
                  {range}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Charts Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ staggerChildren: 0.1 }}
          className="space-y-6"
        >
          {/* Attack Trends */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <h3 className="text-lg font-semibold mb-6">Attack Trends (24h)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={analyticsData.attackTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="time" stroke="#a8b3be" />
                <YAxis stroke="#a8b3be" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
                <Legend />
                <Bar dataKey="dos" stackId="a" fill="#ff006e" />
                <Bar dataKey="portScan" stackId="a" fill="#b536d9" />
                <Bar dataKey="bruteForce" stackId="a" fill="#ffb003" />
                <Bar dataKey="suspicious" stackId="a" fill="#00d9ff" />
              </ComposedChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Top Row - 2 Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Threat Sources */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="glass rounded-xl p-6 border border-white/5"
            >
              <h3 className="text-lg font-semibold mb-6">Top Threat Sources</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analyticsData.topThreats} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis type="number" stroke="#a8b3be" />
                  <YAxis dataKey="ip" type="category" stroke="#a8b3be" width={120} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                    labelStyle={{ color: '#00d9ff' }}
                  />
                  <Bar dataKey="threats" fill="#ff006e" />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Detection Accuracy */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass rounded-xl p-6 border border-white/5"
            >
              <h3 className="text-lg font-semibold mb-6">Detection Accuracy</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analyticsData.detectionStats}
                    cx="50%"
                    cy="50%"
                    labelLine={true}
                    label={({ name, percent, category }) => `${category || name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {analyticsData.detectionStats?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                    labelStyle={{ color: '#00d9ff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </motion.div>
          </div>

          {/* Threat Confidence Distribution */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="glass rounded-xl p-6 border border-white/5"
          >
            <h3 className="text-lg font-semibold mb-6">Threat Confidence Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData.confidenceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="range" stroke="#a8b3be" />
                <YAxis stroke="#a8b3be" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#2d333b', border: '1px solid #00d9ff', borderRadius: '8px' }}
                  labelStyle={{ color: '#00d9ff' }}
                />
                <Bar dataKey="count" fill="#b536d9" />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>

          {/* Summary Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="grid grid-cols-1 md:grid-cols-4 gap-4"
          >
            {[
              { label: 'Avg Detection Time', value: '23ms', color: 'blue' },
              { label: 'Total Alerts', value: '1,234', color: 'purple' },
              { label: 'Blocked Attacks', value: '156', color: 'pink' },
              { label: 'Prevention Rate', value: '99.2%', color: 'green' },
            ].map((stat, i) => (
              <div key={i} className="glass rounded-lg p-4 border border-white/5">
                <p className="text-dark-400 text-sm mb-2">{stat.label}</p>
                <p className={`text-2xl font-bold text-neon-${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </main>
    </div>
  )
}
