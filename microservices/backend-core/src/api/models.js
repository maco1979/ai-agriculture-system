import express from 'express';
import { getModels, getModelById, createModel, updateModel, deleteModel } from './controllers/modelController.js';

const router = express.Router();

// 模型列表
router.get('/', getModels);

// 模型详情
router.get('/:modelId', getModelById);

// 创建模型
router.post('/', createModel);

// 更新模型
router.put('/:modelId', updateModel);

// 删除模型
router.delete('/:modelId', deleteModel);

export default router;
