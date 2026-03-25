import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Plus, 
  Search, 
  Filter, 
  Download, 
  Upload,
  Play,
  Pause,
  Edit,
  Trash2,
  Brain,
  RefreshCw,
  FileDown,
  Cloud,
  Server
} from 'lucide-react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectLabel, SelectSeparator } from '@/components/ui/select'
import { useModelsQuery } from '@/hooks/useModelsQuery'
import { apiClient } from '@/services/api'
import toast from 'react-hot-toast'

export function ModelManagement() {
  const [searchTerm, setSearchTerm] = useState('')
  const [exporting, setExporting] = useState(false)

  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showMarketImportModal, setShowMarketImportModal] = useState(false)
  const [operatingModel, setOperatingModel] = useState<{id: string, operation: string} | null>(null);
  const navigate = useNavigate()
  const [createForm, setCreateForm] = useState({
    name: '',
    description: '',
    type: 'ai'
  })
  const [importForm, setImportForm] = useState({
    name: '',
    file: null as File | null,
    fileName: ''
  })
  const [marketImportForm, setMarketImportForm] = useState({
    model_source: 'cloud',        // 'cloud' | 'local'
    model_name_or_path: '',
    model_format: 'openai',       // 云端: openai/deepseek/anthropic/hunyuan/qwen/zhipu  本地: huggingface/onnx
    model_type: 'nlp',
    name: '',
    api_key: ''                   // 可选，临时覆盖 .env 中的 Key
  })
  const { data: models = [], isLoading: loading, refetch, isRefetching } = useModelsQuery()

  const handleExport = async (fmt: 'csv' | 'json') => {
    setExporting(true)
    try {
      await apiClient.exportModels(fmt)
      toast.success(`模型列表已导出为 ${fmt.toUpperCase()} 格式`)
    } catch (e) {
      toast.error('导出失败，请稍后重试')
    } finally {
      setExporting(false)
    }
  }
  
  // 转换API数据格式
  const modelList = models.map(model => ({

    id: model.id,
    name: model.name,
    type: model.description || 'AI模型',
    status: (['ready', 'active', 'deployed'] as string[]).includes(model.status) ? '运行中' : 
            model.status === 'training' ? '训练中' : '已停止',
    accuracy: model.accuracy ? `${(model.accuracy * 100).toFixed(1)}%` : '--',
    size: model.size ? `${(model.size / 1024 / 1024).toFixed(2)} MB` : '--',
    lastTrained: model.updated_at ? new Date(model.updated_at).toLocaleDateString() : '--',
    version: model.version || 'v1.0.0',
    isCloud: (model as any).is_cloud === true || (model as any).model_source === 'cloud',
    provider: (model as any).provider || '',
  })) || []

  const filteredModels = modelList.filter(model =>
    model.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    model.type.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case '运行中': return 'text-green-400'
      case '训练中': return 'text-yellow-400'
      case '已停止': return 'text-red-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold gradient-text mb-2">模型管理</h1>
          <p className="text-gray-300">管理和监控AI模型的训练、部署和版本控制</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="tech" className="flex items-center space-x-2" onClick={() => setShowCreateModal(true)}>
            <Plus className="w-4 h-4" />
            <span>新建模型</span>
          </Button>
          <Select onValueChange={(value) => {
            if (value === 'import') setShowImportModal(true);
            if (value === 'market') setShowMarketImportModal(true);
          }}>
            <SelectTrigger className="w-[120px] flex items-center space-x-2">
              <Upload className="w-4 h-4" />
              <SelectValue placeholder="导入模型" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="import">从文件导入</SelectItem>
              <SelectItem value="market">从市场导入</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            className="flex items-center space-x-2"
            onClick={() => refetch()}
            disabled={loading}
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </Button>
          <Select onValueChange={(value) => handleExport(value as 'csv' | 'json')}>
            <SelectTrigger
              className="w-[120px] flex items-center space-x-2"
              disabled={exporting || loading}
            >
              <FileDown className="w-4 h-4" />
              <SelectValue placeholder={exporting ? '导出中…' : '导出'} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="json">导出 JSON</SelectItem>
              <SelectItem value="csv">导出 CSV</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 搜索和筛选 */}
      <Card className="glass-effect">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="搜索模型名称或类型..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline" className="flex items-center space-x-2">
              <Filter className="w-4 h-4" />
              <span>筛选</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 模型列表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredModels.map((model) => (
          <Card key={model.id || 'unknown'} className="glass-effect hover:neon-glow transition-all duration-300 cursor-pointer" onClick={() => {
            if (!model.id) {
              console.error('Model ID is undefined:', model)
              toast.error('模型ID缺失，无法查看详情')
              return
            }
            navigate(`/models/${encodeURIComponent(model.id)}`)
          }}>

            <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-tech-primary to-tech-secondary rounded-lg flex items-center justify-center">
                    {model.isCloud ? <Cloud className="w-6 h-6 text-white" /> : <Brain className="w-6 h-6 text-white" />}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{model.name}</CardTitle>
                    <CardDescription>{model.type}</CardDescription>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className={`text-sm font-medium ${getStatusColor(model.status)}`}>
                    {model.status}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    model.isCloud
                      ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                      : 'bg-green-500/20 text-green-300 border border-green-500/30'
                  }`}>
                    {model.isCloud ? `☁️ ${model.provider || '云端'}` : '💻 本地'}
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">准确率:</span>
                  <span className="ml-2 text-white">{model.accuracy}</span>
                </div>
                <div>
                  <span className="text-gray-400">模型大小:</span>
                  <span className="ml-2 text-white">{model.size}</span>
                </div>
                <div>
                  <span className="text-gray-400">最后训练:</span>
                  <span className="ml-2 text-white">{model.lastTrained}</span>
                </div>
                <div>
                  <span className="text-gray-400">版本:</span>
                  <span className="ml-2 text-white">{model.version}</span>
                </div>
              </div>
              
              <div className="flex justify-between pt-2 border-t border-tech-light">
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline" className="flex items-center space-x-1" onClick={async (e) => {
                    e.stopPropagation();
                    setOperatingModel({id: model.id, operation: 'start'});
                    try {
                      const response = await apiClient.startModel(model.id);
                      if (response.success) {
                        toast.success(`${model.name} 启动成功`);
                      } else {
                        toast.error(`${model.name} 启动失败: ${response.error || '未知错误'}`);
                      }
                      refetch(); // 刷新模型列表
                    } catch (error) {
                      console.error('启动模型失败:', error);
                      toast.error(`${model.name} 启动失败`);
                    } finally {
                      setOperatingModel(null);
                    }
                  }} disabled={loading || isRefetching || (operatingModel?.id === model.id && operatingModel.operation === 'start')}>
                    {operatingModel?.id === model.id && operatingModel.operation === 'start' ? (
                      <>
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>启动中</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3 h-3" />
                        <span>启动</span>
                      </>
                    )}
                  </Button>
                  <Button size="sm" variant="outline" className="flex items-center space-x-1" onClick={async (e) => {
                    e.stopPropagation();
                    setOperatingModel({id: model.id, operation: 'pause'});
                    try {
                      const response = await apiClient.pauseModel(model.id);
                      if (response.success) {
                        toast.success(`${model.name} 暂停成功`);
                      } else {
                        toast.error(`${model.name} 暂停失败: ${response.error || '未知错误'}`);
                      }
                      refetch(); // 刷新模型列表
                    } catch (error) {
                      console.error('暂停模型失败:', error);
                      toast.error(`${model.name} 暂停失败`);
                    } finally {
                      setOperatingModel(null);
                    }
                  }} disabled={loading || isRefetching || (operatingModel?.id === model.id && operatingModel.operation === 'pause')}>
                    {operatingModel?.id === model.id && operatingModel.operation === 'pause' ? (
                      <>
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        <span>暂停中</span>
                      </>
                    ) : (
                      <>
                        <Pause className="w-3 h-3" />
                        <span>暂停</span>
                      </>
                    )}
                  </Button>
                </div>
                <div className="flex space-x-2">
                  <Button size="sm" variant="ghost" onClick={(e) => e.stopPropagation()}>
                    <Edit className="w-3 h-3" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={(e) => e.stopPropagation()}>
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 统计信息 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-effect">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-tech-primary">
                {loading ? '--' : modelList.length}
              </div>
              <div className="text-gray-400 mt-1">总模型数量</div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-effect">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-400">
                {loading ? '--' : modelList.filter(m => m.status === '运行中').length}
              </div>
              <div className="text-gray-400 mt-1">运行中模型</div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass-effect">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-400">
                {loading ? '--' : modelList.filter(m => m.status === '训练中').length}
              </div>
              <div className="text-gray-400 mt-1">训练中模型</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 新建模型模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="glass-effect w-full max-w-md">
            <CardHeader>
              <CardTitle>新建模型</CardTitle>
              <CardDescription>创建一个新的AI模型</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">模型名称</label>
                  <Input
                    placeholder="请输入模型名称"
                    value={createForm.name}
                    onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">模型描述</label>
                  <Input
                    placeholder="请输入模型描述"
                    value={createForm.description}
                    onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">模型类型</label>
                  <div className="flex space-x-2">
                    <Button
                      variant={createForm.type === 'ai' ? 'tech' : 'outline'}
                      onClick={() => setCreateForm({ ...createForm, type: 'ai' })}
                    >
                      AI模型
                    </Button>
                    <Button
                      variant={createForm.type === 'ml' ? 'tech' : 'outline'}
                      onClick={() => setCreateForm({ ...createForm, type: 'ml' })}
                    >
                      机器学习模型
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
            <div className="p-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                取消
              </Button>
              <Button variant="tech" onClick={async () => {
                try {
                  console.log('开始创建模型，表单数据:', createForm)
                  const response = await apiClient.createModel({
                    name: createForm.name,
                    description: createForm.description,
                    status: 'ready',
                    version: 'v1.0.0'
                  })
                  console.log('创建模型API响应:', response)
                  if (response.success) {
                    console.log('模型创建成功:', response.data)
                    refetch() // 刷新模型列表
                    setShowCreateModal(false)
                    setCreateForm({ name: '', description: '', type: 'ai' }) // 重置表单
                  } else {
                    console.error('模型创建失败:', response.error)
                  }
                } catch (error) {
                  console.error('创建模型时发生错误:', error)
                }
              }}>
                创建
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* 导入模型模态框 */}
      {showImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="glass-effect w-full max-w-md">
            <CardHeader>
              <CardTitle>导入模型</CardTitle>
              <CardDescription>从文件导入模型</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">模型名称</label>
                  <Input
                    placeholder="请输入模型名称"
                    value={importForm.name}
                    onChange={(e) => setImportForm({ ...importForm, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">模型文件</label>
                  <div
                    className={`border-2 rounded-lg p-6 text-center ${importForm.file ? 'border-tech-primary bg-tech-primary/10' : 'border-dashed border-gray-600'}`}
                    onClick={() => document.getElementById('model-file-input')?.click()}
                    onDragOver={(e) => {
                      e.preventDefault()
                      e.currentTarget.classList.add('border-tech-primary')
                    }}
                    onDragLeave={(e) => {
                      e.preventDefault()
                      if (!importForm.file) {
                        e.currentTarget.classList.remove('border-tech-primary')
                      }
                    }}
                    onDrop={(e) => {
                      e.preventDefault()
                      e.currentTarget.classList.remove('border-tech-primary')
                      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                        const file = e.dataTransfer.files[0]
                        setImportForm({ ...importForm, file, fileName: file.name })
                      }
                    }}
                  >
                    {importForm.file ? (
                      <div className="flex flex-col items-center">
                        <div className="w-10 h-10 bg-tech-primary/20 rounded-full flex items-center justify-center mb-2">
                          <Upload className="w-6 h-6 text-tech-primary" />
                        </div>
                        <p className="text-sm text-white mb-1">{importForm.fileName}</p>
                        <p className="text-xs text-gray-400">{Math.round(importForm.file.size / 1024)} KB</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-2"
                          onClick={(e) => {
                            e.stopPropagation()
                            setImportForm({ ...importForm, file: null, fileName: '' })
                          }}
                        >
                          更换文件
                        </Button>
                      </div>
                    ) : (
                      <>
                        <Upload className="w-10 h-10 text-gray-500 mx-auto mb-2" />
                        <p className="text-gray-400 mb-2">点击或拖拽文件到此处上传</p>
                        <Button variant="outline">选择文件</Button>
                      </>
                    )}
                  </div>
                  <input
                    id="model-file-input"
                    type="file"
                    accept=".pt,.pth,.onnx,.pb"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        const file = e.target.files[0]
                        setImportForm({ ...importForm, file, fileName: file.name })
                      }
                    }}
                  />
                </div>
                <div className="text-xs text-gray-400">
                  支持的文件格式: .pt, .pth, .onnx, .pb (PyTorch、ONNX、TensorFlow格式)
                </div>
              </div>
            </CardContent>
            <div className="p-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={() => {
                setShowImportModal(false)
                setImportForm({ name: '', file: null, fileName: '' })
              }}>
                取消
              </Button>
              <Button
                variant="tech"
                disabled={!importForm.name || !importForm.file}
                onClick={async () => {
                  try {
                    if (!importForm.name || !importForm.file) return
                    
                    const response = await apiClient.importModel(
                      { name: importForm.name },
                      importForm.file
                    )
                    if (response.success) {
                      console.log('模型导入成功:', response.data)
                      refetch() // 刷新模型列表
                      setShowImportModal(false)
                      setImportForm({ name: '', file: null, fileName: '' }) // 重置表单
                    } else {
                      console.error('模型导入失败:', response.error)
                      // 这里可以添加错误提示
                    }
                  } catch (error) {
                    console.error('导入模型时发生错误:', error)
                    // 这里可以添加错误提示
                  }
                }}
              >
                导入
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* 从市场导入模型模态框 */}
      {showMarketImportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <Card className="glass-effect w-full max-w-lg">
            <CardHeader>
              <CardTitle>从市场导入模型</CardTitle>
              <CardDescription>支持云端 API 模型与本地开源模型（如 Hugging Face）</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">

                {/* ── 模型来源切换 ── */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">模型来源</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setMarketImportForm({ ...marketImportForm, model_source: 'cloud', model_format: 'openai' })}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-sm font-medium transition-all ${
                        marketImportForm.model_source === 'cloud'
                          ? 'border-tech-primary bg-tech-primary/20 text-tech-primary'
                          : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      <Cloud className="w-4 h-4" />
                      云端模型 (API)
                    </button>
                    <button
                      type="button"
                      onClick={() => setMarketImportForm({ ...marketImportForm, model_source: 'local', model_format: 'huggingface' })}
                      className={`flex items-center justify-center gap-2 p-3 rounded-lg border text-sm font-medium transition-all ${
                        marketImportForm.model_source === 'local'
                          ? 'border-tech-primary bg-tech-primary/20 text-tech-primary'
                          : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500'
                      }`}
                    >
                      <Server className="w-4 h-4" />
                      本地模型 (下载)
                    </button>
                  </div>
                  {marketImportForm.model_source === 'cloud' && (
                    <p className="mt-2 text-xs text-gray-500">通过 API Key 调用，无需本地算力，响应快</p>
                  )}
                  {marketImportForm.model_source === 'local' && (
                    <p className="mt-2 text-xs text-gray-500">下载到本地运行，数据不出境，需要 GPU/CPU 资源</p>
                  )}
                </div>

                {/* ── 云端模型配置 ── */}
                {marketImportForm.model_source === 'cloud' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">服务商</label>
                      <select
                        className="w-full p-2 rounded-md bg-gray-900 border border-gray-700 text-white"
                        value={marketImportForm.model_format}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, model_format: e.target.value, model_name_or_path: '' })}
                      >
                        <optgroup label="推荐（价格低廉）">
                          <option value="deepseek">DeepSeek — deepseek-chat / deepseek-reasoner</option>
                          <option value="zhipu">智谱 GLM — glm-4-flash / glm-4</option>
                          <option value="qwen">阿里通义千问 — qwen-plus / qwen-turbo</option>
                        </optgroup>
                        <optgroup label="国际云端">
                          <option value="openai">OpenAI — gpt-4o / gpt-4o-mini</option>
                          <option value="anthropic">Anthropic — claude-3-5-sonnet</option>
                        </optgroup>
                        <optgroup label="国内云端">
                          <option value="hunyuan">腾讯混元 — hunyuan-standard / pro</option>
                        </optgroup>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">模型名称</label>
                      <Input
                        placeholder={
                          marketImportForm.model_format === 'deepseek' ? 'deepseek-chat' :
                          marketImportForm.model_format === 'openai' ? 'gpt-4o-mini' :
                          marketImportForm.model_format === 'anthropic' ? 'claude-3-5-sonnet-20241022' :
                          marketImportForm.model_format === 'hunyuan' ? 'hunyuan-standard' :
                          marketImportForm.model_format === 'qwen' ? 'qwen-plus' :
                          marketImportForm.model_format === 'zhipu' ? 'glm-4-flash' : '模型名称'
                        }
                        value={marketImportForm.model_name_or_path}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, model_name_or_path: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        API Key <span className="text-gray-500 font-normal">（可选，不填则使用 .env 中的配置）</span>
                      </label>
                      <Input
                        type="password"
                        placeholder="sk-... 或留空使用环境变量"
                        value={marketImportForm.api_key}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, api_key: e.target.value })}
                      />
                    </div>
                  </>
                )}

                {/* ── 本地模型配置 ── */}
                {marketImportForm.model_source === 'local' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">模型格式</label>
                      <select
                        className="w-full p-2 rounded-md bg-gray-900 border border-gray-700 text-white"
                        value={marketImportForm.model_format}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, model_format: e.target.value })}
                      >
                        <option value="huggingface">Hugging Face（自动下载权重）</option>
                        <option value="onnx">ONNX（跨平台推理）</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">模型路径或名称</label>
                      <Input
                        placeholder="例如: gpt2, bert-base-uncased, HuggingFaceH4/zephyr-7b-beta"
                        value={marketImportForm.model_name_or_path}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, model_name_or_path: e.target.value })}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">模型任务类型</label>
                      <select
                        className="w-full p-2 rounded-md bg-gray-900 border border-gray-700 text-white"
                        value={marketImportForm.model_type}
                        onChange={(e) => setMarketImportForm({ ...marketImportForm, model_type: e.target.value })}
                      >
                        <option value="nlp">自然语言处理（文本生成/分类）</option>
                        <option value="cv">计算机视觉（图像识别/检测）</option>
                        <option value="multimodal">多模态（图文混合）</option>
                        <option value="audio">音频处理</option>
                        <option value="transformer">通用 Transformer</option>
                      </select>
                    </div>
                  </>
                )}

                {/* ── 公共：显示名称 ── */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">显示名称 <span className="text-gray-500 font-normal">（可选）</span></label>
                  <Input
                    placeholder="模型在系统中的显示名称"
                    value={marketImportForm.name}
                    onChange={(e) => setMarketImportForm({ ...marketImportForm, name: e.target.value })}
                  />
                </div>
              </div>
            </CardContent>
            <div className="p-4 flex justify-end space-x-2">
              <Button variant="outline" onClick={() => {
                setShowMarketImportModal(false)
                setMarketImportForm({ model_source: 'cloud', model_name_or_path: '', model_format: 'openai', model_type: 'nlp', name: '', api_key: '' })
              }}>
                取消
              </Button>
              <Button
                variant="tech"
                disabled={!marketImportForm.model_name_or_path}
                onClick={async () => {
                  try {
                    if (!marketImportForm.model_name_or_path) return

                    let response
                    if (marketImportForm.model_source === 'cloud') {
                      // 云端模型：注册到系统，调用时走 API
                      response = await apiClient.importCloudModel({
                        model_name: marketImportForm.model_name_or_path,
                        provider: marketImportForm.model_format,
                        model_type: marketImportForm.model_type,
                        display_name: marketImportForm.name || marketImportForm.model_name_or_path,
                        api_key: marketImportForm.api_key || undefined,
                      })
                    } else {
                      // 本地模型：触发下载/注册
                      response = await apiClient.loadPretrainedModel({
                        model_name_or_path: marketImportForm.model_name_or_path,
                        model_format: marketImportForm.model_format,
                        model_type: marketImportForm.model_type,
                        name: marketImportForm.name,
                      })
                    }

                    if (response.success) {
                      toast.success(
                        marketImportForm.model_source === 'cloud'
                          ? `云端模型 ${marketImportForm.model_name_or_path} 注册成功`
                          : `本地模型 ${marketImportForm.model_name_or_path} 导入成功`
                      )
                      refetch()
                      setShowMarketImportModal(false)
                      setMarketImportForm({ model_source: 'cloud', model_name_or_path: '', model_format: 'openai', model_type: 'nlp', name: '', api_key: '' })
                    } else {
                      toast.error(`导入失败: ${response.error || '未知错误'}`)
                    }
                  } catch (error) {
                    console.error('从市场导入模型时发生错误:', error)
                    toast.error('导入失败，请检查网络或 API Key')
                  }
                }}
              >
                {marketImportForm.model_source === 'cloud' ? '注册云端模型' : '一键导入'}
              </Button>
            </div>
          </Card>
        </div>
      )}

    </div>
  )
}