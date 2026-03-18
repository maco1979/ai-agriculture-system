import express from 'express';
import systemRoutes from './system.js';
import aiControlRoutes from './ai-control.js';
import modelRoutes from './models.js';
import inferenceRoutes from './inference.js';

const router = express.Router();

// 系统管理路由
router.use('/system', systemRoutes);

// AI控制路由
router.use('/ai-control', aiControlRoutes);

// 模型管理路由
router.use('/models', modelRoutes);

// 推理服务路由
router.use('/inference', inferenceRoutes);

// API版本信息
router.get('/version', (req, res) => {
  res.status(200).json({
    version: '1.0.0',
    service: 'backend-core',
    timestamp: new Date().toISOString()
  });
});

export default router;
