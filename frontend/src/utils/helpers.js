export const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

export const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

export const formatTime = (date) => {
  return new Date(date).toLocaleTimeString()
}

export const getSeverityColor = (severity) => {
  const colors = {
    critical: 'text-red-500',
    high: 'text-orange-500',
    medium: 'text-yellow-500',
    low: 'text-green-500',
    normal: 'text-blue-500',
  }
  return colors[severity] || colors.low
}

export const getSeverityBg = (severity) => {
  const colors = {
    critical: 'bg-red-500/10',
    high: 'bg-orange-500/10',
    medium: 'bg-yellow-500/10',
    low: 'bg-green-500/10',
    normal: 'bg-blue-500/10',
  }
  return colors[severity] || colors.low
}

export const getSeverityBorder = (severity) => {
  const colors = {
    critical: 'border-red-500/50',
    high: 'border-orange-500/50',
    medium: 'border-yellow-500/50',
    low: 'border-green-500/50',
    normal: 'border-blue-500/50',
  }
  return colors[severity] || colors.low
}

export const generateMockPackets = (count = 50) => {
  const protocols = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS']
  const attackTypes = ['Normal', 'DoS', 'Port Scan', 'Brute Force', 'Suspicious']
  const packets = []

  for (let i = 0; i < count; i++) {
    packets.push({
      id: i + 1,
      sourceIP: `192.168.1.${Math.floor(Math.random() * 255)}`,
      destIP: `10.0.0.${Math.floor(Math.random() * 255)}`,
      protocol: protocols[Math.floor(Math.random() * protocols.length)],
      size: Math.floor(Math.random() * 1500) + 64,
      timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
      threatStatus: Math.random() > 0.8 ? 'Threat' : 'Safe',
      attackType: attackTypes[Math.floor(Math.random() * attackTypes.length)],
      confidence: (Math.random() * 100).toFixed(2),
    })
  }

  return packets
}

export const generateMockStats = () => {
  return {
    totalPackets: 156234,
    threatsDetected: 234,
    safeTraffic: 98.5,
    activeConnections: 45,
    cpuUsage: 42,
    memoryUsage: 58,
  }
}
