import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Play, Pause, RotateCcw, Trash2, CheckCircle2,
  Circle, Clock, AlertCircle, Zap, Loader2,
  ChevronDown, ChevronUp, Terminal, Brain,
  Leaf, BarChart3, Shield, Cpu, Globe,
  CheckSquare, XCircle, RefreshCw
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ─── 类型 ───
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'paused'
type TaskPriority = 'low' | 'medium' | 'high'

interface ToolCall {
  id: string
  name: string
  args: Record<string, any>
  result?: string
  status: 'pending' | 'running' | 'success' | 'error'
  duration?: number
}

interface TaskStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'done' | 'error'
  detail?: string
  toolCalls?: ToolCall[]
}

interface Task {
  id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  progress: number
  createdAt: Date
  startedAt?: Date
  completedAt?: Date
  steps: TaskStep[]
  category: string
  model: string
  result?: string
  error?: string
}

// ─── Mock数据 ───
const MOCK_TASKS: Task[] = [
  {
    id: 't1',
    title: '作物病虫害批量诊断',
    description: '对 15 块田地的传感器图像进行 AI 病虫害识别，生成处理报告',
    status: 'running',
    priority: 'high',
    progress: 62,
    createdAt: new Date(Date.now() - 480000),
    startedAt: new Date(Date.now() - 300000),
    category: '农业诊断',
    model: 'DeepSeek Chat',
    steps: [
      { id: 's1', label: '加载图像数据', status: 'done', detail: '已加载 15 张田地图像' },
      { id: 's2', label: '调用计算机视觉模型', status: 'done', detail: 'ResNet50 模型推理完成', toolCalls: [
        { id: 'tc1', name: 'vision_model.predict', args: { model: 'ResNet50', batch_size: 15 }, result: '{"diseases": ["稻瘟病x3", "白叶枯x2"]}', status: 'success', duration: 1240 }
      ]},
      { id: 's3', label: '生成诊断报告', status: 'running', detail: '正在整合分析结果...', toolCalls: [
        { id: 'tc2', name: 'report.generate', args: { template: 'disease_report', lang: 'zh' }, status: 'running' }
      ]},
      { id: 's4', label: '推送结果通知', status: 'pending' },
    ]
  },
  {
    id: 't2',
    title: '月度农业数据分析',
    description: '分析 3 月份传感器数据，生成土壤、气候、产量趋势报告',
    status: 'completed',
    priority: 'medium',
    progress: 100,
    createdAt: new Date(Date.now() - 3600000),
    startedAt: new Date(Date.now() - 3500000),
    completedAt: new Date(Date.now() - 1800000),
    category: '数据分析',
    model: 'GPT-4o',
    result: '报告已生成，包含 12 项关键指标分析，建议优化 4 号田块灌溉策略',
    steps: [
      { id: 's1', label: '数据采集与清洗', status: 'done' },
      { id: 's2', label: '统计分析建模', status: 'done' },
      { id: 's3', label: '趋势预测', status: 'done' },
      { id: 's4', label: '报告渲染', status: 'done' },
    ]
  },
  {
    id: 't3',
    title: '精准灌溉调度优化',
    description: '基于土壤湿度和天气预报，优化未来 7 天灌溉调度方案',
    status: 'pending',
    priority: 'medium',
    progress: 0,
    createdAt: new Date(Date.now() - 120000),
    category: '决策优化',
    model: 'DeepSeek R1',
    steps: [
      { id: 's1', label: '获取天气预报数据', status: 'pending' },
      { id: 's2', label: '读取土壤湿度传感器', status: 'pending' },
      { id: 's3', label: '运行强化学习优化器', status: 'pending' },
      { id: 's4', label: '生成调度方案', status: 'pending' },
    ]
  },
  {
    id: 't4',
    title: '农药喷洒路径规划',
    description: '为无人机规划最优喷洒路径，减少农药用量',
    status: 'failed',
    priority: 'high',
    progress: 45,
    createdAt: new Date(Date.now() - 7200000),
    startedAt: new Date(Date.now() - 7100000),
    category: '路径规划',
    model: '农业专用模型',
    error: '无人机通信超时，任务中断（错误码: DRONE_TIMEOUT_408）',
    steps: [
      { id: 's1', label: '加载地图数据', status: 'done' },
      { id: 's2', label: '连接无人机控制器', status: 'error', detail: '连接超时 (30s)' },
      { id: 's3', label: '路径算法计算', status: 'pending' },
      { id: 's4', label: '任务下发', status: 'pending' },
    ]
  },
]

// ─── 工具函数 ───
const STATUS_CONFIG: Record<TaskStatus, { icon: React.FC<any>; color: string; label: string; bg: string }> = {
  pending: { icon: Circle, color: 'text-gray-400', label: '等待中', bg: 'bg-gray-400/10' },
  running: { icon: Loader2, color: 'text-cyber-cyan', label: '运行中', bg: 'bg-cyber-cyan/10' },
  completed: { icon: CheckCircle2, color: 'text-green-400', label: '已完成', bg: 'bg-green-400/10' },
  failed: { icon: XCircle, color: 'text-red-400', label: '失败', bg: 'bg-red-400/10' },
  paused: { icon: Pause, color: 'text-yellow-400', label: '已暂停', bg: 'bg-yellow-400/10' },
}

const PRIORITY_CONFIG: Record<TaskPriority, { color: string; label: string }> = {
  low: { color: 'text-gray-500 bg-gray-500/10', label: '低' },
  medium: { color: 'text-blue-400 bg-blue-400/10', label: '中' },
  high: { color: 'text-red-400 bg-red-400/10', label: '高' },
}

const CATEGORY_ICONS: Record<string, React.FC<any>> = {
  '农业诊断': Leaf,
  '数据分析': BarChart3,
  '决策优化': Brain,
  '路径规划': Globe,
  '安全检测': Shield,
  '推理服务': Cpu,
}

const formatDuration = (start: Date, end?: Date) => {
  const diff = (end || new Date()).getTime() - start.getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ${s % 60}s`
  return `${Math.floor(m / 60)}h ${m % 60}m`
}

const generateId = () => Math.random().toString(36).slice(2, 10)

// ─── 步骤列表组件 ───
function StepList({ steps }: { steps: TaskStep[] }) {
  const [expandedTools, setExpandedTools] = useState<string>('')

  return (
    <div className="space-y-1.5">
      {steps.map((step, i) => {
        const isExpanded = expandedTools === step.id
        const hasTools = (step.toolCalls?.length || 0) > 0

        return (
          <div key={step.id}>
            <div
              className={cn(
                'flex items-start gap-2.5 px-3 py-2 rounded-lg transition-colors',
                hasTools && 'cursor-pointer hover:bg-white/3'
              )}
              onClick={() => hasTools && setExpandedTools(isExpanded ? '' : step.id)}
            >
              {/* 步骤图标 */}
              <div className="mt-0.5 shrink-0">
                {step.status === 'done' && <CheckCircle2 size={15} className="text-green-400" />}
                {step.status === 'running' && <Loader2 size={15} className="text-cyber-cyan animate-spin" />}
                {step.status === 'error' && <XCircle size={15} className="text-red-400" />}
                {step.status === 'pending' && <Circle size={15} className="text-gray-600" />}
              </div>

              {/* 连接线 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    'text-sm',
                    step.status === 'done' ? 'text-gray-400 line-through' :
                    step.status === 'running' ? 'text-white' :
                    step.status === 'error' ? 'text-red-400' :
                    'text-gray-600'
                  )}>
                    {i + 1}. {step.label}
                  </span>
                  {hasTools && (
                    <span className="text-[10px] text-gray-600 flex items-center gap-0.5">
                      <Terminal size={10} /> {step.toolCalls?.length}
                      {isExpanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                    </span>
                  )}
                </div>
                {step.detail && (
                  <p className="text-[11px] text-gray-600 mt-0.5">{step.detail}</p>
                )}
              </div>
            </div>

            {/* 工具调用展开 */}
            <AnimatePresence>
              {isExpanded && step.toolCalls && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden ml-8 mb-1"
                >
                  <div className="space-y-1.5 py-1">
                    {step.toolCalls.map(tc => (
                      <div key={tc.id} className="rounded-lg bg-black/30 border border-white/5 p-2.5">
                        <div className="flex items-center gap-2 mb-1">
                          <Terminal size={12} className="text-cyber-purple" />
                          <code className="text-xs text-cyber-purple font-mono">{tc.name}</code>
                          <span className={cn(
                            'ml-auto text-[10px] px-1.5 py-0.5 rounded-full',
                            tc.status === 'success' ? 'bg-green-400/15 text-green-400' :
                            tc.status === 'error' ? 'bg-red-400/15 text-red-400' :
                            tc.status === 'running' ? 'bg-cyber-cyan/15 text-cyber-cyan' :
                            'bg-gray-400/15 text-gray-400'
                          )}>
                            {tc.status === 'running' ? '执行中...' : tc.status === 'success' ? `✓ ${tc.duration}ms` : tc.status}
                          </span>
                        </div>
                        <div className="text-[10px] text-gray-600 font-mono">
                          <span className="text-gray-500">参数: </span>
                          {JSON.stringify(tc.args)}
                        </div>
                        {tc.result && (
                          <div className="text-[10px] text-green-400/80 font-mono mt-1">
                            <span className="text-gray-500">结果: </span>{tc.result}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}

// ─── 任务卡片组件 ───
function TaskCard({ task, onDelete, onRetry, onTogglePause }: {
  task: Task
  onDelete: (id: string) => void
  onRetry: (id: string) => void
  onTogglePause: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(task.status === 'running')
  const cfg = STATUS_CONFIG[task.status]
  const priCfg = PRIORITY_CONFIG[task.priority]
  const CatIcon = CATEGORY_ICONS[task.category] || Zap

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="rounded-xl border border-white/8 bg-white/3 hover:bg-white/5 transition-colors overflow-hidden"
    >
      {/* 卡片头部 */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* 类别图标 */}
          <div className="w-10 h-10 rounded-xl bg-cyber-cyan/10 flex items-center justify-center shrink-0">
            <CatIcon size={20} className="text-cyber-cyan" />
          </div>

          <div className="flex-1 min-w-0">
            {/* 标题行 */}
            <div className="flex items-start gap-2 mb-1">
              <h3 className="text-sm font-semibold text-white truncate flex-1">{task.title}</h3>
              <span className={cn('text-[10px] px-1.5 py-0.5 rounded-full shrink-0', priCfg.color)}>
                {priCfg.label}优先
              </span>
            </div>

            <p className="text-xs text-gray-500 line-clamp-2">{task.description}</p>

            {/* 元数据行 */}
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {/* 状态 */}
              <div className={cn('flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px]', cfg.bg, cfg.color)}>
                <cfg.icon size={11} className={task.status === 'running' ? 'animate-spin' : ''} />
                {cfg.label}
              </div>

              {/* 类别 */}
              <span className="text-[11px] text-gray-600">{task.category}</span>

              {/* 模型 */}
              <span className="text-[11px] text-gray-600 flex items-center gap-1">
                <Brain size={10} />
                {task.model}
              </span>

              {/* 耗时 */}
              {task.startedAt && (
                <span className="text-[11px] text-gray-600 flex items-center gap-1">
                  <Clock size={10} />
                  {formatDuration(task.startedAt, task.completedAt)}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 进度条 */}
        {(task.status === 'running' || task.status === 'completed') && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] text-gray-500">进度</span>
              <span className="text-[11px] text-gray-400">{task.progress}%</span>
            </div>
            <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-cyber-purple to-cyber-cyan rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${task.progress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}

        {/* 错误信息 */}
        {task.error && (
          <div className="mt-3 px-3 py-2 rounded-lg bg-red-400/8 border border-red-400/15">
            <div className="flex items-start gap-2">
              <AlertCircle size={13} className="text-red-400 mt-0.5 shrink-0" />
              <p className="text-xs text-red-400/80">{task.error}</p>
            </div>
          </div>
        )}

        {/* 完成结果 */}
        {task.result && (
          <div className="mt-3 px-3 py-2 rounded-lg bg-green-400/8 border border-green-400/15">
            <div className="flex items-start gap-2">
              <CheckSquare size={13} className="text-green-400 mt-0.5 shrink-0" />
              <p className="text-xs text-green-400/80">{task.result}</p>
            </div>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-white/5">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-white transition-colors"
          >
            <Terminal size={12} />
            {expanded ? '收起' : '展开'}详细步骤
            {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>

          <div className="flex-1" />

          {task.status === 'failed' && (
            <button
              onClick={() => onRetry(task.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyber-cyan/10 text-cyber-cyan text-xs hover:bg-cyber-cyan/20 transition-colors"
            >
              <RefreshCw size={12} />
              重试
            </button>
          )}
          {task.status === 'running' && (
            <button
              onClick={() => onTogglePause(task.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-yellow-400/10 text-yellow-400 text-xs hover:bg-yellow-400/20 transition-colors"
            >
              <Pause size={12} />
              暂停
            </button>
          )}
          {task.status === 'paused' && (
            <button
              onClick={() => onTogglePause(task.id)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-green-400/10 text-green-400 text-xs hover:bg-green-400/20 transition-colors"
            >
              <Play size={12} />
              继续
            </button>
          )}

          <button
            onClick={() => onDelete(task.id)}
            className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-colors"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* 步骤详情折叠区 */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-white/5 bg-black/20"
          >
            <div className="p-4">
              <p className="text-[11px] text-gray-600 mb-2 uppercase tracking-wider">执行步骤</p>
              <StepList steps={task.steps} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ─── 新建任务弹窗 ───
function NewTaskModal({ onClose, onCreate }: {
  onClose: () => void
  onCreate: (task: Task) => void
}) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '农业诊断',
    priority: 'medium' as TaskPriority,
    model: 'deepseek-chat',
  })

  const CATEGORIES = ['农业诊断', '数据分析', '决策优化', '路径规划', '安全检测', '推理服务']

  const handleCreate = () => {
    if (!form.title.trim()) return
    const task: Task = {
      id: generateId(),
      ...form,
      status: 'pending',
      progress: 0,
      createdAt: new Date(),
      steps: [
        { id: generateId(), label: '初始化任务环境', status: 'pending' },
        { id: generateId(), label: '加载数据资源', status: 'pending' },
        { id: generateId(), label: 'AI 模型推理', status: 'pending' },
        { id: generateId(), label: '生成结果报告', status: 'pending' },
      ]
    }
    onCreate(task)
    onClose()
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <motion.div
        initial={{ scale: 0.95, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 20 }}
        className="w-full max-w-md bg-[#13131f] border border-white/10 rounded-2xl p-6 shadow-2xl"
      >
        <h3 className="text-lg font-semibold text-white mb-5">新建 AI 任务</h3>

        <div className="space-y-4">
          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">任务标题 *</label>
            <input
              value={form.title}
              onChange={e => setForm(p => ({ ...p, title: e.target.value }))}
              placeholder="描述你的任务..."
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-gray-600 outline-none focus:border-cyber-cyan/50 transition-colors"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1.5 block">任务描述</label>
            <textarea
              value={form.description}
              onChange={e => setForm(p => ({ ...p, description: e.target.value }))}
              placeholder="详细说明任务需要做什么..."
              rows={3}
              className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-gray-600 outline-none focus:border-cyber-cyan/50 transition-colors resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-gray-500 mb-1.5 block">任务类别</label>
              <select
                value={form.category}
                onChange={e => setForm(p => ({ ...p, category: e.target.value }))}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-cyber-cyan/50 transition-colors"
              >
                {CATEGORIES.map(c => <option key={c} value={c} className="bg-[#1a1a2e]">{c}</option>)}
              </select>
            </div>

            <div>
              <label className="text-xs text-gray-500 mb-1.5 block">优先级</label>
              <select
                value={form.priority}
                onChange={e => setForm(p => ({ ...p, priority: e.target.value as TaskPriority }))}
                className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-cyber-cyan/50 transition-colors"
              >
                <option value="low" className="bg-[#1a1a2e]">低优先级</option>
                <option value="medium" className="bg-[#1a1a2e]">中优先级</option>
                <option value="high" className="bg-[#1a1a2e]">高优先级</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button onClick={onClose} className="flex-1 py-2.5 rounded-xl border border-white/10 text-gray-400 text-sm hover:bg-white/5 transition-colors">
            取消
          </button>
          <button
            onClick={handleCreate}
            disabled={!form.title.trim()}
            className="flex-1 py-2.5 rounded-xl bg-cyber-cyan text-black text-sm font-medium hover:bg-cyber-cyan/80 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            创建任务
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ─── 主页面 ───
export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>(MOCK_TASKS)
  const [filter, setFilter] = useState<TaskStatus | 'all'>('all')
  const [showNewModal, setShowNewModal] = useState(false)

  // 模拟运行中任务的进度推进
  useEffect(() => {
    const timer = setInterval(() => {
      setTasks(prev => prev.map(t => {
        if (t.status !== 'running') return t
        const newProgress = Math.min(t.progress + 1, 99)
        return { ...t, progress: newProgress }
      }))
    }, 2000)
    return () => clearInterval(timer)
  }, [])

  const filteredTasks = filter === 'all' ? tasks : tasks.filter(t => t.status === filter)

  const handleDelete = (id: string) => setTasks(prev => prev.filter(t => t.id !== id))
  const handleRetry = (id: string) => setTasks(prev => prev.map(t =>
    t.id === id ? { ...t, status: 'running', progress: 0, error: undefined, startedAt: new Date(), steps: t.steps.map(s => ({ ...s, status: 'pending' as const })) } : t
  ))
  const handleTogglePause = (id: string) => setTasks(prev => prev.map(t =>
    t.id === id ? { ...t, status: t.status === 'running' ? 'paused' : 'running' } : t
  ))
  const handleCreate = (task: Task) => setTasks(prev => [task, ...prev])

  // 统计数据
  const stats = {
    total: tasks.length,
    running: tasks.filter(t => t.status === 'running').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
  }

  const FILTERS: Array<{ key: TaskStatus | 'all'; label: string; count: number }> = [
    { key: 'all', label: '全部', count: stats.total },
    { key: 'running', label: '运行中', count: stats.running },
    { key: 'completed', label: '已完成', count: stats.completed },
    { key: 'pending', label: '等待中', count: tasks.filter(t => t.status === 'pending').length },
    { key: 'failed', label: '失败', count: stats.failed },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* 页面头部 */}
      <div className="px-6 py-5 border-b border-white/5 shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-white">AI 任务中心</h1>
            <p className="text-sm text-gray-500 mt-0.5">管理和监控所有 AI 自动化任务</p>
          </div>
          <button
            onClick={() => setShowNewModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyber-cyan text-black text-sm font-medium hover:bg-cyber-cyan/80 transition-colors shadow-lg shadow-cyber-cyan/20"
          >
            <Plus size={16} />
            新建任务
          </button>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: '总任务', value: stats.total, color: 'text-white', icon: CheckSquare },
            { label: '运行中', value: stats.running, color: 'text-cyber-cyan', icon: Loader2 },
            { label: '已完成', value: stats.completed, color: 'text-green-400', icon: CheckCircle2 },
            { label: '失败', value: stats.failed, color: 'text-red-400', icon: XCircle },
          ].map(s => (
            <div key={s.label} className="px-4 py-3 rounded-xl bg-white/3 border border-white/5">
              <div className="flex items-center gap-2 mb-1">
                <s.icon size={14} className={s.color} />
                <span className="text-xs text-gray-500">{s.label}</span>
              </div>
              <p className={cn('text-2xl font-bold', s.color)}>{s.value}</p>
            </div>
          ))}
        </div>

        {/* 过滤器 */}
        <div className="flex items-center gap-2 mt-4 overflow-x-auto custom-scrollbar pb-1">
          {FILTERS.map(f => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs whitespace-nowrap transition-colors',
                filter === f.key
                  ? 'bg-cyber-cyan/15 border border-cyber-cyan/30 text-cyber-cyan'
                  : 'bg-white/5 border border-white/5 text-gray-400 hover:bg-white/8'
              )}
            >
              {f.label}
              <span className={cn(
                'px-1.5 py-0.5 rounded-full text-[10px]',
                filter === f.key ? 'bg-cyber-cyan/20' : 'bg-white/5'
              )}>
                {f.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 任务列表 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-4">
        <AnimatePresence mode="popLayout">
          {filteredTasks.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-64 text-gray-600"
            >
              <CheckSquare size={40} className="mb-3 opacity-30" />
              <p className="text-sm">暂无{filter !== 'all' ? `"${FILTERS.find(f => f.key === filter)?.label}"` : ''}任务</p>
              <button
                onClick={() => setShowNewModal(true)}
                className="mt-4 text-xs text-cyber-cyan hover:underline"
              >
                + 创建第一个任务
              </button>
            </motion.div>
          ) : (
            <div className="space-y-3">
              {filteredTasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onDelete={handleDelete}
                  onRetry={handleRetry}
                  onTogglePause={handleTogglePause}
                />
              ))}
            </div>
          )}
        </AnimatePresence>
      </div>

      {/* 新建任务弹窗 */}
      <AnimatePresence>
        {showNewModal && (
          <NewTaskModal onClose={() => setShowNewModal(false)} onCreate={handleCreate} />
        )}
      </AnimatePresence>
    </div>
  )
}
