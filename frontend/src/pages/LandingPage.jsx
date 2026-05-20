import { Link } from 'react-router-dom'
import { Shield, Zap, BarChart3, Lock, ArrowRight, Github } from 'lucide-react'
import { motion } from 'framer-motion'

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.2, delayChildren: 0.3 },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.8 } },
  }

  return (
    <div className="min-h-screen bg-dark-900 overflow-hidden">
      {/* Animated gradient background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900" />
        <div className="absolute top-0 -right-40 w-80 h-80 bg-neon-purple/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 -left-40 w-80 h-80 bg-neon-blue/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-neon-pink/5 rounded-full blur-3xl" />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex justify-between items-center px-6 lg:px-12 py-6 backdrop-blur-sm">
        <div className="flex items-center gap-2 group">
          <div className="p-2 rounded-lg bg-gradient-to-r from-neon-blue to-neon-purple group-hover:shadow-glow transition-all">
            <Shield size={24} className="text-dark-900" />
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent">NIDS</span>
        </div>
        <div className="hidden md:flex gap-8">
          <a href="#features" className="text-dark-300 hover:text-neon-blue transition-colors">Features</a>
          <a href="#tech" className="text-dark-300 hover:text-neon-blue transition-colors">Tech Stack</a>
        </div>
        <Link to="/login" className="btn-primary">
          Login
        </Link>
      </nav>

      {/* Hero Section */}
      <motion.section
        className="relative z-10 min-h-[calc(100vh-80px)] flex items-center justify-center px-6 lg:px-12"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-4xl mx-auto text-center">
          <motion.h1
            variants={itemVariants}
            className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-neon-blue via-neon-purple to-neon-pink bg-clip-text text-transparent"
          >
            Real-Time Network Intrusion Detection
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="text-xl text-dark-400 mb-8 max-w-2xl mx-auto"
          >
            Advanced machine learning-powered threat detection system that monitors network packets in real-time and identifies potential cyber attacks with precision.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="flex flex-col md:flex-row gap-4 justify-center mb-16"
          >
            <Link
              to="/signup"
              className="btn-primary inline-flex items-center justify-center gap-2 text-lg"
            >
              Start Monitoring <ArrowRight size={20} />
            </Link>
            <button className="btn-secondary inline-flex items-center justify-center gap-2 text-lg">
              Learn More
            </button>
          </motion.div>

          {/* Floating cards */}
          <motion.div
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12"
          >
            {[
              { value: '156K+', label: 'Packets Analyzed' },
              { value: '99.8%', label: 'Detection Accuracy' },
              { value: '<50ms', label: 'Response Time' },
            ].map((stat, i) => (
              <motion.div
                key={i}
                whileHover={{ y: -10, scale: 1.05 }}
                className="glass rounded-xl p-6 border border-neon-blue/20 hover:border-neon-blue/50 hover:shadow-glow transition-all"
              >
                <div className="text-3xl font-bold text-neon-blue">{stat.value}</div>
                <div className="text-dark-400 mt-2">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </motion.section>

      {/* Features Section */}
      <motion.section
        id="features"
        className="relative z-10 py-24 px-6 lg:px-12"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-6xl mx-auto">
          <motion.h2
            variants={itemVariants}
            className="text-4xl font-bold text-center mb-16 bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent"
          >
            Powerful Features
          </motion.h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Zap, title: 'Real-Time Detection', desc: 'Instant threat identification' },
              { icon: BarChart3, title: 'Analytics Dashboard', desc: 'Comprehensive insights' },
              { icon: Lock, title: 'Secure Storage', desc: 'Encrypted logs' },
              { icon: Shield, title: 'ML Powered', desc: 'AI-driven classification' },
            ].map((feature, i) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={i}
                  variants={itemVariants}
                  whileHover={{ scale: 1.05, y: -5 }}
                  className="glass rounded-xl p-6 border border-white/5 hover:border-neon-blue/50 hover:shadow-glow transition-all"
                >
                  <div className="mb-4 p-3 rounded-lg bg-neon-blue/10 w-fit">
                    <Icon size={24} className="text-neon-blue" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-dark-400 text-sm">{feature.desc}</p>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.section>

      {/* Tech Stack Section */}
      <motion.section
        id="tech"
        className="relative z-10 py-24 px-6 lg:px-12"
        variants={containerVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
      >
        <div className="max-w-6xl mx-auto">
          <motion.h2
            variants={itemVariants}
            className="text-4xl font-bold text-center mb-16 bg-gradient-to-r from-neon-blue to-neon-purple bg-clip-text text-transparent"
          >
            Enterprise Tech Stack
          </motion.h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {['React', 'Python Flask', 'Scikit-learn', 'SQLite', 'Scapy', 'Tailwind CSS', 'Random Forest', 'Real-time WebSockets'].map((tech, i) => (
              <motion.div
                key={i}
                variants={itemVariants}
                className="glass rounded-lg p-4 border border-white/5 hover:border-neon-purple/50 transition-all"
              >
                <p className="font-semibold text-neon-blue">{tech}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* CTA Section */}
      <motion.section
        className="relative z-10 py-24 px-6 lg:px-12"
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
      >
        <div className="max-w-4xl mx-auto glass-dark rounded-2xl p-12 text-center border border-neon-blue/30">
          <h2 className="text-3xl font-bold mb-6">Ready to Secure Your Network?</h2>
          <p className="text-dark-400 mb-8">Start monitoring threats in real-time with our advanced AI-powered detection system.</p>
          <Link to="/signup" className="btn-primary inline-flex items-center gap-2 text-lg">
            Get Started Now <ArrowRight size={20} />
          </Link>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-dark-700 py-8 px-6 lg:px-12 text-center text-dark-400">
        <p>&copy; 2026 NIDS - Network Intrusion Detection System. All rights reserved.</p>
      </footer>
    </div>
  )
}
