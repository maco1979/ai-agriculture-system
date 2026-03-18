import express from 'express';
import { checkHealth, getSystemInfo, getSystemMetrics } from './controllers/systemController.js';

const router = express.Router();

// 系统健康检查
router.get('/health', checkHealth);

// 系统信息
router.get('/info', getSystemInfo);

// 系统指标
router.get('/metrics', getSystemMetrics);

export default router;
