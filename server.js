const express = require('express');
const cors = require('cors');
const path = require('path');

console.log('🚀 Starting Bagpack server...');

// Load .env from the parent directory
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const connectDB = require('./config/database');

const app = express();

// Connect to MongoDB
connectDB();

// Enhanced CORS configuration
const corsOptions = {
  origin: [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    process.env.FRONTEND_URL
  ].filter(Boolean),
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true
};

app.use(cors(corsOptions));

// Handle preflight requests explicitly
app.options('*', cors(corsOptions));

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Import routes
const authRoutes = require('./routes/auth');
const adventureRoutes = require('./routes/adventures');
const communityRoutes = require('./routes/community');

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/adventures', adventureRoutes);
app.use('/api/community', communityRoutes);

// Basic route
app.get('/', (req, res) => {
  res.json({ 
    message: 'Bagpack API Server is running!',
    version: '1.0.0',
    endpoints: [
      '/api/auth',
      '/api/adventures', 
      '/api/community'
    ]
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error details:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// 404 handler
app.use((req, res) => {
  console.log(`404 - Route not found: ${req.method} ${req.path}`);
  res.status(404).json({ 
    error: 'Not found',
    message: `Route ${req.method} ${req.path} not found`
  });
});

const PORT = process.env.NODE_PORT || 3001;

app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
  console.log(`📊 Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`🔗 Available routes:`);
  console.log(`   - http://localhost:${PORT}/api/auth`);
  console.log(`   - http://localhost:${PORT}/api/adventures`);
  console.log(`   - http://localhost:${PORT}/api/community`);
});