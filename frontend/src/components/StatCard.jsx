import { motion } from 'framer-motion'

export default function StatCard({ title, value, icon: Icon, trend, color = 'blue' }) {
  const colors = {
    blue: 'neon-blue',
    purple: 'neon-purple',
    pink: 'neon-pink',
    green: 'neon-green',
  }

  return (
    <motion.div
      whileHover={{ scale: 1.05, y: -5 }}
      className="glass rounded-xl p-6 border border-white/5 hover:border-neon-blue/50 transition-all group"
    >
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-dark-400 text-sm font-medium">{title}</p>
          <p className={`text-3xl font-bold mt-1 text-neon-${color}`}>{value}</p>
          {trend && (
            <p className={`text-xs mt-2 ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? '+' : ''}{trend}% from last hour
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-neon-${color}/10 group-hover:shadow-glow transition-all`}>
          <Icon size={24} className={`text-neon-${color}`} />
        </div>
      </div>
    </motion.div>
  )
}
