import { formatResponse, validateBody } from '../../utils/utils.js';

// 模型列表
const getModels = (req, res) => {
  try {
    const models = [
      {
        id: 'model-1',
        name: 'Wheat Yield Predictor',
        type: 'regression',
        status: 'active',
        version: '1.0.0',
        description: '小麦产量预测模型',
        accuracy: 0.92,
        created_at: '2026-01-01T00:00:00Z'
      },
      {
        id: 'model-2',
        name: 'Pest Detector',
        type: 'classification',
        status: 'active',
        version: '1.1.0',
        description: '病虫害检测模型',
        accuracy: 0.88,
        created_at: '2026-01-02T00:00:00Z'
      }
    ];
    
    const response = {
      data: models,
      total: models.length
    };
    
    res.status(200).json(formatResponse(response, 'Model list retrieved successfully'));
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Failed to retrieve model list',
      error: error.message
    });
  }
};

// 模型详情
const getModelById = (req, res) => {
  try {
    const { modelId } = req.params;
    
    const model = {
      id: modelId,
      name: 'Wheat Yield Predictor',
      type: 'regression',
      status: 'active',
      version: '1.0.0',
      description: '小麦产量预测模型',
      accuracy: 0.92,
      created_at: '2026-01-01T00:00:00Z',
      metadata: {
        input_features: ['temperature', 'humidity', 'rainfall', 'soil_ph'],
        output_features: ['yield'],
        training_dataset: 'wheat_dataset_2025'
      }
    };
    
    res.status(200).json(formatResponse(model, 'Model details retrieved successfully'));
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Failed to retrieve model details',
      error: error.message
    });
  }
};

// 创建模型
const createModel = (req, res) => {
  try {
    const validation = validateBody(req.body, ['name', 'type', 'description']);
    if (!validation.valid) {
      return res.status(400).json({
        status: 'error',
        message: validation.message
      });
    }
    
    const modelData = req.body;
    const newModel = {
      id: 'model-' + Date.now(),
      ...modelData,
      status: 'pending',
      created_at: new Date().toISOString()
    };
    
    res.status(201).json(formatResponse(newModel, 'Model created successfully'));
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Failed to create model',
      error: error.message
    });
  }
};

// 更新模型
const updateModel = (req, res) => {
  try {
    const { modelId } = req.params;
    const updates = req.body;
    
    const updatedModel = {
      id: modelId,
      name: 'Wheat Yield Predictor',
      ...updates,
      updated_at: new Date().toISOString()
    };
    
    res.status(200).json(formatResponse(updatedModel, 'Model updated successfully'));
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Failed to update model',
      error: error.message
    });
  }
};

// 删除模型
const deleteModel = (req, res) => {
  try {
    const { modelId } = req.params;
    
    res.status(200).json(formatResponse(null, `Model ${modelId} deleted successfully`));
  } catch (error) {
    res.status(500).json({
      status: 'error',
      message: 'Failed to delete model',
      error: error.message
    });
  }
};

export {
  getModels,
  getModelById,
  createModel,
  updateModel,
  deleteModel
};