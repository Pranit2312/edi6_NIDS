# NIDS Frontend - Quick Start Guide

## Prerequisites
- Node.js 16+ (download from https://nodejs.org/)
- npm 7+ (comes with Node.js)

## Setup Steps

### 1. Install Dependencies
```bash
npm install
```

This will install all required packages:
- react
- react-router-dom
- axios
- tailwindcss
- framer-motion
- recharts
- And more...

### 2. Development Server
```bash
npm run dev
```

Frontend will start on `http://localhost:3000`

### 3. Build for Production
```bash
npm run build
```

This creates a `dist/` folder ready for deployment.

### 4. Preview Production Build
```bash
npm run preview
```

## Project Structure

```
frontend/
├── index.html             # HTML entry point
├── vite.config.js         # Vite configuration
├── tailwind.config.js     # Tailwind CSS config
├── postcss.config.js      # PostCSS config
├── package.json           # Dependencies
└── src/
    ├── main.jsx           # React entry point
    ├── App.jsx            # Main component
    ├── components/        # Reusable components
    │   ├── Navbar.jsx
    │   ├── StatCard.jsx
    │   └── ThreatAlert.jsx
    ├── pages/             # Page components
    │   ├── LandingPage.jsx
    │   ├── LoginPage.jsx
    │   ├── SignupPage.jsx
    │   ├── Dashboard.jsx
    │   ├── LiveMonitoring.jsx
    │   ├── ThreatAnalytics.jsx
    │   ├── LogsAndAlerts.jsx
    │   └── SettingsPage.jsx
    ├── services/          # API services
    │   └── api.js
    ├── utils/             # Utility functions
    │   └── helpers.js
    └── styles/            # Global styles
        └── globals.css
```

## Environment Configuration

The frontend proxies API requests to the backend.

**Proxy Configuration** (in `vite.config.js`):
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:5050',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, ''),
  }
}
```

To change backend URL:
1. Edit `vite.config.js`
2. Change `target: 'http://localhost:5000'` to your backend URL
3. Restart dev server

## Available Routes

- `/` - Landing page
- `/login` - Login page
- `/signup` - Signup page
- `/dashboard` - Main dashboard (protected)
- `/monitoring` - Live monitoring (protected)
- `/analytics` - Threat analytics (protected)
- `/logs` - Logs & alerts (protected)
- `/settings` - Settings (protected)

## Demo Credentials

```
Username: demo
Password: demo123
```

## Troubleshooting

### Port 3000 already in use
```bash
# Change port in vite.config.js
server: {
  port: 3001,  // Change to different port
}
```

### API Connection Errors
1. Ensure backend is running on `http://localhost:5000`
2. Check CORS is enabled in Flask (`flask-cors` installed)
3. Check proxy configuration in `vite.config.js`

### Dependencies not installing
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Build fails
```bash
# Check for syntax errors
npm run build -- --verbose

# Rebuild
npm run build
```

## Key Technologies

- **React 18** - UI framework
- **Vite** - Lightning fast build tool
- **Tailwind CSS** - Utility-first CSS
- **Framer Motion** - Animation library
- **Recharts** - Chart library
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Lucide React** - Icon library

## Performance Optimization

1. **Code Splitting** - Routes are automatically code-split by Vite
2. **Image Optimization** - Use modern formats (WebP)
3. **CSS Optimization** - Tailwind purges unused styles in production
4. **Bundle Analysis** - Use `rollup-plugin-visualizer` for analysis

## Deployment

### Netlify
```bash
npm run build
# Deploy dist/ folder
```

### Vercel
```bash
npm run build
# Connect git repo to Vercel
```

### Traditional Server
```bash
npm run build
# Copy dist/ to web server (nginx, Apache, etc.)
```

### With Backend Hosting
1. Build frontend: `npm run build`
2. Update API endpoint in code
3. Host dist/ folder
4. Ensure CORS is configured correctly

## CSS Framework

Using **Tailwind CSS v3** with custom configuration:

**Custom Colors (dark theme):**
```
dark-50 to dark-900 - Grayscale
neon-blue - #00d9ff
neon-purple - #b536d9
neon-pink - #ff006e
neon-green - #00ff88
```

**Custom Utilities:**
```
glass - Glassmorphism effect
glow-blue, glow-purple - Neon glow effects
animated-gradient - Animated background
```

## Components Documentation

### StatCard
Props: title, value, icon, trend, color
- Displays metric with trend
- Animated on hover
- Supports custom colors

### ThreatAlert
Props: title, description, severity, onClose
- Alert notification component
- Severity-based coloring
- Auto-dismiss option

### Navbar
Props: onLogout
- Navigation with active state
- Mobile responsive menu
- Logo and links

## State Management

Currently using React local state with hooks:
- `useState` - Local component state
- `useEffect` - Side effects and data fetching
- `useContext` - For future global state

For larger app, consider:
- Redux
- Zustand
- Recoil
