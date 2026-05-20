import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { Search, Filter, Download, RotateCcw } from 'lucide-react'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { generateMockPackets, formatBytes, formatDate, getSeverityColor, getSeverityBg } from '../utils/helpers'

const API_BASE = 'http://localhost:8081/api'

export default function LiveMonitoring({ onLogout }) {
  const [packets, setPackets] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [filterProtocol, setFilterProtocol] = useState('all')
  const [filterThreat, setFilterThreat] = useState('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [isMonitoring, setIsMonitoring] = useState(true)
  const [loading, setLoading] = useState(true)
  const packetsPerPage = 15

  // Fetch real packets from backend
  useEffect(() => {
    const fetchPackets = async () => {
      try {
        const response = await fetch(`${API_BASE}/packets?limit=50`)
        if (response.ok) {
          const data = await response.json()
          // Transform backend packet format to frontend format
          // Backend returns array directly
          const packetList = Array.isArray(data) ? data : (data.packets || [])
          const transformedPackets = packetList.map((p, idx) => ({
            id: p.id || idx,
            sourceIP: p.src_ip || '0.0.0.0',
            destIP: p.dst_ip || '0.0.0.0',
            protocol: (p.protocol || 'OTHER').toUpperCase(),
            size: p.packet_size || 0,
            timestamp: p.timestamp || new Date().toISOString(),
            threatStatus: p.threat_status === 'Attack' ? 'threat' : 'safe',
            attackType: p.attack_type || 'None',
            confidence: p.ml_confidence || 0
          }))
          setPackets(transformedPackets)
        } else {
          setPackets(generateMockPackets(50))
        }
      } catch (error) {
        console.error('Error fetching packets:', error)
        setPackets(generateMockPackets(50))
      } finally {
        setLoading(false)
      }
    }

    fetchPackets()
    
    const interval = setInterval(fetchPackets, 3000)
    return () => clearInterval(interval)
  }, [])

  // Auto-refresh packets while monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      if (isMonitoring) {
        // Packets are auto-fetched every 3s, this keeps the UI responsive
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [isMonitoring])

  const filteredPackets = packets.filter(packet => {
    const matchSearch = 
      packet.sourceIP.includes(searchTerm) ||
      packet.destIP.includes(searchTerm)
    const matchProtocol = filterProtocol === 'all' || packet.protocol === filterProtocol
    const matchThreat = filterThreat === 'all' || packet.threatStatus === filterThreat
    return matchSearch && matchProtocol && matchThreat
  })

  const paginatedPackets = filteredPackets.slice(
    (currentPage - 1) * packetsPerPage,
    currentPage * packetsPerPage
  )

  const totalPages = Math.ceil(filteredPackets.length / packetsPerPage)

  const handleExport = () => {
    const csv = [
      ['Source IP', 'Dest IP', 'Protocol', 'Size', 'Timestamp', 'Threat Status', 'Attack Type', 'Confidence'],
      ...filteredPackets.map(p => [
        p.sourceIP,
        p.destIP,
        p.protocol,
        p.size,
        p.timestamp,
        p.threatStatus,
        p.attackType,
        p.confidence,
      ]),
    ]
    const csvContent = csv.map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `packets-${Date.now()}.csv`
    a.click()
    toast.success('Packets exported successfully!')
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
                Live Packet Monitoring
              </h1>
              <p className="text-dark-400">Real-time network packet analysis and filtering</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setIsMonitoring(!isMonitoring)}
                className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                  isMonitoring
                    ? 'bg-green-500/20 text-green-400 border border-green-500/50'
                    : 'bg-red-500/20 text-red-400 border border-red-500/50'
                }`}
              >
                {isMonitoring ? '🔴 Monitoring' : '⚫ Paused'}
              </button>
            </div>
          </div>
        </motion.div>

        {/* Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-xl p-6 border border-white/5 mb-6"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search size={18} className="absolute left-3 top-3 text-neon-blue" />
              <input
                type="text"
                placeholder="Search by IP..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow"
              />
            </div>

            {/* Protocol Filter */}
            <div className="relative">
              <Filter size={18} className="absolute left-3 top-3 text-neon-blue" />
              <select
                value={filterProtocol}
                onChange={(e) => {
                  setFilterProtocol(e.target.value)
                  setCurrentPage(1)
                }}
                className="w-full bg-dark-800 border border-dark-700 rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow appearance-none cursor-pointer"
              >
                <option value="all">All Protocols</option>
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="ICMP">ICMP</option>
                <option value="HTTP">HTTP</option>
                <option value="HTTPS">HTTPS</option>
                <option value="DNS">DNS</option>
              </select>
            </div>

            {/* Threat Filter */}
            <select
              value={filterThreat}
              onChange={(e) => {
                setFilterThreat(e.target.value)
                setCurrentPage(1)
              }}
              className="w-full bg-dark-800 border border-dark-700 rounded-lg px-4 py-2 focus:outline-none focus:border-neon-blue focus:shadow-glow appearance-none cursor-pointer"
            >
              <option value="all">All Threats</option>
              <option value="Threat">Threats</option>
              <option value="Safe">Safe</option>
            </select>

            {/* Export button */}
            <button
              onClick={handleExport}
              className="flex items-center justify-center gap-2 bg-gradient-to-r from-neon-blue to-neon-purple hover:shadow-glow rounded-lg px-4 py-2 font-semibold transition-all"
            >
              <Download size={18} />
              Export CSV
            </button>
          </div>

          {/* Stats */}
          <div className="mt-4 flex gap-4 text-sm">
            <span className="text-dark-400">Total: <span className="text-neon-blue">{filteredPackets.length}</span></span>
            <span className="text-dark-400">Threats: <span className="text-neon-pink">{filteredPackets.filter(p => p.threatStatus === 'Threat').length}</span></span>
            <span className="text-dark-400">Safe: <span className="text-neon-green">{filteredPackets.filter(p => p.threatStatus === 'Safe').length}</span></span>
          </div>
        </motion.div>

        {/* Table */}
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
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Source IP</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Dest IP</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Protocol</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Size</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Time</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Status</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Type</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-neon-blue">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {paginatedPackets.length > 0 ? (
                  paginatedPackets.map((packet, idx) => (
                    <motion.tr
                      key={packet.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.05 }}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="px-6 py-4 text-sm text-dark-300">{packet.sourceIP}</td>
                      <td className="px-6 py-4 text-sm text-dark-300">{packet.destIP}</td>
                      <td className="px-6 py-4 text-sm"><span className="px-2 py-1 rounded bg-neon-blue/20 text-neon-blue text-xs">{packet.protocol}</span></td>
                      <td className="px-6 py-4 text-sm text-dark-300">{formatBytes(packet.size)}</td>
                      <td className="px-6 py-4 text-sm text-dark-300">{new Date(packet.timestamp).toLocaleTimeString()}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`px-2 py-1 rounded text-xs ${packet.threatStatus === 'Threat' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                          {packet.threatStatus}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-dark-300">{packet.attackType}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-dark-700 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-neon-blue to-neon-purple" style={{ width: `${packet.confidence}%` }} />
                          </div>
                          <span className="text-neon-blue">{packet.confidence}%</span>
                        </div>
                      </td>
                    </motion.tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" className="px-6 py-12 text-center text-dark-400">
                      No packets found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-6 py-4 border-t border-white/5 flex items-center justify-between">
            <div className="text-sm text-dark-400">
              Page {currentPage} of {totalPages || 1}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 rounded bg-dark-800 border border-dark-700 hover:border-neon-blue disabled:opacity-50 transition-all"
              >
                Previous
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 rounded bg-dark-800 border border-dark-700 hover:border-neon-blue disabled:opacity-50 transition-all"
              >
                Next
              </button>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
