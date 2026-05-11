#!/usr/bin/env node

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const PORT = process.env.UI_PORT || 3000;
const HOST = process.env.UI_HOST || 'localhost';
const API_URL = process.env.API_URL || 'http://localhost:8000';

const app = express();

app.use('/api', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
}));

app.use('/health', createProxyMiddleware({
  target: API_URL,
  changeOrigin: true,
}));

app.use(express.static(path.join(__dirname, 'public')));

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, HOST, () => {
  console.log(`\n  🎨 HydraFlow AI UI 已启动`);
  console.log(`  访问: http://${HOST}:${PORT}`);
  console.log(`  API:  ${API_URL}\n`);
});
