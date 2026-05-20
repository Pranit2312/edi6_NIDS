import { AlertTriangle, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function ThreatAlert({ title, description, severity = 'high', onClose }) {
  const severityColors = {
    critical: 'from-red-500 to-red-600',
    high: 'from-orange-500 to-orange-600',
    medium: 'from-yellow-500 to-yellow-600',
    low: 'from-blue-500 to-blue-600',
  }

  const borderColors = {
    critical: 'border-red-500/50',
    high: 'border-orange-500/50',
    medium: 'border-yellow-500/50',
    low: 'border-blue-500/50',
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        className={`glass rounded-xl p-4 border ${borderColors[severity]} bg-gradient-to-r ${severityColors[severity]}/20 mb-3`}
      >
        <div className="flex gap-3 items-start">
          <AlertTriangle size={20} className="flex-shrink-0 mt-1" />
          <div className="flex-1">
            <h4 className="font-semibold text-white">{title}</h4>
            <p className="text-sm text-dark-300 mt-1">{description}</p>
          </div>
          <button
            onClick={onClose}
            className="hover:bg-white/10 p-1 rounded transition-all"
          >
            <X size={16} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
