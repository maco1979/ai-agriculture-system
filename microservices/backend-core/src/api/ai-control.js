import express from 'express';
import { getAIStatus, getDevices, getMasterControlStatus } from './controllers/aiControlController.js';

const router = express.Router();

// AI控制系统状态
router.get('/status', getAIStatus);

// 设备列表
router.get('/devices', getDevices);

// 主控状态
router.get('/master-control/status', getMasterControlStatus);

export default router;
