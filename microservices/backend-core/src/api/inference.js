import express from 'express';
import { predict, batchPredict, getInferenceStatus, getInferenceHistory } from './controllers/inferenceController.js';

const router = express.Router();

// 执行推理
router.post('/predict', predict);

// 批量推理
router.post('/batch-predict', batchPredict);

// 推理状态
router.get('/status/:requestId', getInferenceStatus);

// 推理历史
router.get('/history', getInferenceHistory);

export default router;
