#!/usr/bin/env node

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import path from 'path';
import { fileURLToPath } from 'url';

const PORT = process.env.UI_PORT || 3001;
const HOST = process.env.UI_HOST || 'localhost';
const API_URL = process.env.API_URL || 'http://localhost:8000';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();

app.use(express.json());

const publicPath = path.join(__dirname, 'public');
app.use(express.static(publicPath));

app.get('/login', (req, res) => {
  res.sendFile(path.join(publicPath, 'login.html'));
});

app.get('/', (req, res) => {
  res.redirect('/login');
});

app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;
  
  if (username === 'admin' && password === 'admin123') {
    res.json({
      success: true,
      user: {
        username: 'admin',
        role: 'admin',
        email: 'admin@清悦印象.ai'
      }
    });
  } else {
    res.status(401).json({
      success: false,
      message: '用户名或密码错误'
    });
  }
});

app.use('/api', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
}));

app.use('/health', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
}));

app.get('*', (req, res) => {
  const requestedPath = req.path.replace(/^\//, '');
  
  if (requestedPath && requestedPath !== 'index.html') {
    const filePath = path.join(publicPath, requestedPath);
    res.sendFile(filePath, (err) => {
      if (err) {
        res.sendFile(path.join(publicPath, 'index.html'));
      }
    });
  } else {
    res.sendFile(path.join(publicPath, 'index.html'));
  }
});

app.listen(PORT, HOST, () => {
  console.log(`\n  🎨 清悦印象 AI UI 已启动`);
  console.log(`  访问: http://${HOST}:${PORT}`);
  console.log(`  API:  ${API_URL}\n`);
});