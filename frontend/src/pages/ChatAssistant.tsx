import React, { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Plus, Send, Trash2, MessageSquare, ChevronDown,
  Bot, User, Copy, Check, RotateCcw, Square,
  Sparkles, Zap, Paperclip, Mic, Settings2,
  ChevronRight, Leaf, Brain, Code, FileText, Globe
} from 'lucide-react'
import { cn } from '@/lib/utils'

// ────────────────────────────── 类型 ──────────────────────────────
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  isStreaming?: boolean
  model?: string
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  model: string
}

interface Model {
  id: string
  name: string
  provider: string
  tag?: string
  description?: string
}

// ────────────────────────────── 常量 ──────────────────────────────
const AVAILABLE_MODELS: Model[] = [
  { id: 'deepseek-chat', name: 'DeepSeek Chat', provider: 'DeepSeek', tag: '推荐', description: '高性价比通用模型' },
  { id: 'deepseek-reasoner', name: 'DeepSeek R1', provider: 'DeepSeek', tag: '推理', description: '深度推理增强版' },
  { id: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', description: '多模态旗舰模型' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', tag: '快速', description: '轻量高速版本' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', description: '卓越代码与分析' },
  { id: 'hunyuan-lite', name: '混元 Lite', provider: '腾讯', description: '中文理解优化' },
  { id: 'qwen-plus', name: '通义千问 Plus', provider: '阿里', description: '长文本处理' },
  { id: 'glm-4', name: 'GLM-4', provider: '智谱', description: '中英文双语' },
  { id: 'agriculture-local', name: '农业专用模型', provider: '本地', tag: '本地', description: '本地农业AI模型' },
]

const QUICK_PROMPTS = [
  { icon: Leaf, label: '作物诊断', prompt: '帮我分析一下农作物的病虫害症状，请告诉我需要描述哪些信息' },
  { icon: Zap, label: '施肥方案', prompt: '根据土壤条件和作物类型，为我制定一份精准施肥方案' },
  { icon: Globe, label: '气象分析', prompt: '分析当前气象数据对农业生产的影响，并给出建议' },
  { icon: Code, label: '数据处理', prompt: '帮我写一段Python代码来处理农业传感器数据' },
  { icon: FileText, label: '报告生成', prompt: '根据以下数据，生成一份农业生产季度报告' },
  { icon: Brain, label: '决策支持', prompt: '基于当前农场数据，给出下一步农业管理决策建议' },
]

// ────────────────────────────── 工具函数 ──────────────────────────────
const generateId = () => Math.random().toString(36).slice(2, 10)

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const getConvTitle = (messages: Message[]) => {
  const first = messages.find(m => m.role === 'user')
  if (!first) return '新对话'
  return first.content.slice(0, 28) + (first.content.length > 28 ? '...' : '')
}

// ────────────────────────────── 模拟流式输出 ──────────────────────────────
async function* mockStreamResponse(userMsg: string, model: string): AsyncGenerator<string> {
  const agriResponses: Record<string, string> = {
    '施肥': `## 精准施肥方案

根据您的描述，建议如下施肥方案：

**基础肥料配比（每亩）：**
- 氮肥（N）：15-20 kg（分2-3次追施）
- 磷肥（P₂O₅）：8-12 kg（基施）  
- 钾肥（K₂O）：10-15 kg（基施 + 追施）

**施肥时机：**
1. **基施**：播种前 7-10 天深翻入土
2. **追施一**：幼苗期（出苗后 15 天）
3. **追施二**：拔节期或花期

> 💡 建议结合土壤检测数据调整配比，有机肥与化肥混合使用效果更佳`,
    default: `我是 **${model}**，正在为您分析...

根据您的问题，我来提供专业的农业AI辅助建议。

**分析结果：**

基于当前的农业知识库和AI模型，我建议从以下几个维度考虑：

1. **环境因素** - 温湿度、光照、土壤pH值
2. **作物状态** - 生长周期、叶色、根系健康度  
3. **历史数据** - 往年同期对比、产量趋势

如需更精准的建议，请提供具体的传感器数据或照片，系统将调用计算机视觉模型进行深度分析。

---
*本回答由 ${model} 生成，仅供参考，具体操作请结合实地情况判断。*`
  }

  const key = Object.keys(agriResponses).find(k => userMsg.includes(k)) || 'default'
  const text = agriResponses[key]
  const words = text.split('')
  
  for (let i = 0; i < words.length; i++) {
    yield words[i]
    if (i % 3 === 0) await new Promise(r => setTimeout(r, 12))
  }
}

// ────────────────────────────── 子组件 ──────────────────────────────

// 消息气泡
function MessageBubble({ msg, onCopy }: { msg: Message; onCopy: (text: string) => void }) {
  const [copied, setCopied] = useState(false)
  const isUser = msg.role === 'user'

  const handleCopy = () => {
    onCopy(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className={cn('group flex gap-3 px-4 py-3', isUser ? 'flex-row-reverse' : 'flex-row')}
    >
      {/* 头像 */}
      <div className={cn(
        'w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-1',
        isUser
          ? 'bg-cyber-cyan/20 border border-cyber-cyan/30'
          : 'bg-gradient-to-br from-cyber-purple to-cyber-cyan'
      )}>
        {isUser
          ? <User size={16} className="text-cyber-cyan" />
          : <Bot size={16} className="text-white" />
        }
      </div>

      {/* 气泡 */}
      <div className={cn('flex flex-col gap-1 max-w-[75%]', isUser ? 'items-end' : 'items-start')}>
        {/* 模型标签 */}
        {!isUser && msg.model && (
          <span className="text-[11px] text-gray-500 px-1">{msg.model}</span>
        )}

        <div className={cn(
          'relative rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-cyber-cyan/15 border border-cyber-cyan/25 text-white rounded-tr-sm'
            : 'bg-white/5 border border-white/8 text-gray-200 rounded-tl-sm'
        )}>
          {/* Streaming 光标 */}
          {msg.isStreaming && (
            <span className="inline-block w-0.5 h-4 bg-cyber-cyan animate-pulse ml-0.5 align-middle" />
          )}

          {/* Markdown-lite 渲染 */}
          <div className="prose prose-sm prose-invert max-w-none whitespace-pre-wrap break-words">
            {msg.content.split('\n').map((line, i) => {
              if (line.startsWith('## ')) return <h2 key={i} className="text-cyber-cyan font-semibold text-base mt-2 mb-1">{line.slice(3)}</h2>
              if (line.startsWith('**') && line.endsWith('**')) return <p key={i} className="font-semibold text-white">{line.slice(2, -2)}</p>
              if (line.startsWith('- ') || line.startsWith('* ')) return <li key={i} className="ml-4 text-gray-300">{line.slice(2)}</li>
              if (line.startsWith('> ')) return <blockquote key={i} className="border-l-2 border-cyber-cyan/50 pl-3 text-gray-400 italic">{line.slice(2)}</blockquote>
              if (line.startsWith('---')) return <hr key={i} className="border-white/10 my-2" />
              if (line === '') return <br key={i} />
              return <p key={i} className="text-gray-200">{line}</p>
            })}
          </div>
        </div>

        {/* 操作栏 */}
        <div className={cn(
          'flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity',
          isUser ? 'flex-row-reverse' : 'flex-row'
        )}>
          <span className="text-[11px] text-gray-600">{formatTime(msg.timestamp)}</span>
          <button
            onClick={handleCopy}
            className="p-1 rounded text-gray-600 hover:text-gray-400 transition-colors"
            title="复制"
          >
            {copied ? <Check size={13} className="text-green-400" /> : <Copy size={13} />}
          </button>
        </div>
      </div>
    </motion.div>
  )
}

// 模型选择器
function ModelSelector({ selected, onChange }: { selected: string; onChange: (id: string) => void }) {
  const [open, setOpen] = useState(false)
  const model = AVAILABLE_MODELS.find(m => m.id === selected) || AVAILABLE_MODELS[0]
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // 按 provider 分组
  const grouped = AVAILABLE_MODELS.reduce((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = []
    acc[m.provider].push(m)
    return acc
  }, {} as Record<string, Model[]>)

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-sm text-gray-300 transition-colors"
      >
        <Sparkles size={14} className="text-cyber-cyan" />
        <span>{model.name}</span>
        {model.tag && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-cyber-cyan/20 text-cyber-cyan">{model.tag}</span>}
        <ChevronDown size={14} className={cn('transition-transform text-gray-500', open && 'rotate-180')} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.15 }}
            className="absolute bottom-full mb-2 left-0 w-72 rounded-xl bg-[#1a1a2e] border border-white/10 shadow-2xl overflow-hidden z-50"
          >
            <div className="p-2 border-b border-white/5">
              <p className="text-xs text-gray-500 px-2 py-1">选择模型</p>
            </div>
            <div className="overflow-y-auto max-h-72 custom-scrollbar p-1">
              {Object.entries(grouped).map(([provider, models]) => (
                <div key={provider}>
                  <p className="text-[11px] text-gray-600 px-3 py-1.5 uppercase tracking-wider">{provider}</p>
                  {models.map(m => (
                    <button
                      key={m.id}
                      onClick={() => { onChange(m.id); setOpen(false) }}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-colors',
                        m.id === selected ? 'bg-cyber-cyan/10 text-cyber-cyan' : 'hover:bg-white/5 text-gray-300'
                      )}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{m.name}</span>
                          {m.tag && <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-cyber-cyan/20 text-cyber-cyan">{m.tag}</span>}
                        </div>
                        {m.description && <p className="text-[11px] text-gray-500 truncate">{m.description}</p>}
                      </div>
                      {m.id === selected && <Check size={14} />}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ────────────────────────────── 主页面 ──────────────────────────────
export default function ChatAssistant() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [selectedModel, setSelectedModel] = useState('deepseek-chat')
  const [isStreaming, setIsStreaming] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const abortRef = useRef<boolean>(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const activeConv = conversations.find(c => c.id === activeId) || null

  // 自动滚到底
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConv?.messages])

  // textarea 自适应高度
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'
  }, [input])

  // 新建对话
  const newConversation = useCallback(() => {
    const conv: Conversation = {
      id: generateId(),
      title: '新对话',
      messages: [],
      createdAt: new Date(),
      model: selectedModel,
    }
    setConversations(prev => [conv, ...prev])
    setActiveId(conv.id)
    setInput('')
  }, [selectedModel])

  // 删除对话
  const deleteConversation = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setConversations(prev => prev.filter(c => c.id !== id))
    if (activeId === id) {
      const remaining = conversations.filter(c => c.id !== id)
      setActiveId(remaining[0]?.id || null)
    }
  }, [activeId, conversations])

  // 复制文本
  const handleCopy = useCallback((text: string) => {
    navigator.clipboard.writeText(text).catch(() => {})
  }, [])

  // 停止生成
  const stopGeneration = () => { abortRef.current = true }

  // 发送消息
  const sendMessage = useCallback(async (text?: string) => {
    const content = (text ?? input).trim()
    if (!content || isStreaming) return

    // 确保有活跃对话
    let convId = activeId
    if (!convId) {
      const conv: Conversation = {
        id: generateId(), title: '新对话', messages: [], createdAt: new Date(), model: selectedModel
      }
      setConversations(prev => [conv, ...prev])
      convId = conv.id
      setActiveId(conv.id)
    }

    const userMsg: Message = { id: generateId(), role: 'user', content, timestamp: new Date() }
    const assistantId = generateId()
    const assistantMsg: Message = {
      id: assistantId, role: 'assistant', content: '', timestamp: new Date(),
      isStreaming: true, model: AVAILABLE_MODELS.find(m => m.id === selectedModel)?.name
    }

    setConversations(prev => prev.map(c => c.id === convId
      ? { ...c, messages: [...c.messages, userMsg, assistantMsg], title: getConvTitle([...c.messages, userMsg]) }
      : c
    ))
    setInput('')
    setIsStreaming(true)
    abortRef.current = false

    try {
      let accumulated = ''
      for await (const chunk of mockStreamResponse(content, selectedModel)) {
        if (abortRef.current) break
        accumulated += chunk
        const finalAcc = accumulated
        setConversations(prev => prev.map(c => c.id === convId
          ? { ...c, messages: c.messages.map(m => m.id === assistantId ? { ...m, content: finalAcc } : m) }
          : c
        ))
      }
    } finally {
      setConversations(prev => prev.map(c => c.id === convId
        ? { ...c, messages: c.messages.map(m => m.id === assistantId ? { ...m, isStreaming: false } : m) }
        : c
      ))
      setIsStreaming(false)
    }
  }, [input, activeId, isStreaming, selectedModel])

  // 键盘快捷键
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // ── 渲染 ──
  return (
    <div className="flex h-full bg-[#0d0d1a] overflow-hidden">
      {/* ── 左侧会话列表 ── */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 260, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col h-full border-r border-white/5 bg-[#0f0f1e] shrink-0 overflow-hidden"
          >
            {/* 顶部操作 */}
            <div className="p-3 border-b border-white/5">
              <button
                onClick={newConversation}
                className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/20 text-cyber-cyan text-sm hover:bg-cyber-cyan/20 transition-colors"
              >
                <Plus size={16} />
                <span className="font-medium">新建对话</span>
              </button>
            </div>

            {/* 会话列表 */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-0.5">
              <AnimatePresence>
                {conversations.length === 0 ? (
                  <div className="py-8 text-center text-gray-600 text-sm">
                    <MessageSquare size={28} className="mx-auto mb-2 opacity-40" />
                    <p>暂无对话</p>
                    <p className="text-xs mt-1">点击"新建对话"开始</p>
                  </div>
                ) : (
                  conversations.map(conv => (
                    <motion.button
                      key={conv.id}
                      initial={{ opacity: 0, x: -16 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -16 }}
                      onClick={() => setActiveId(conv.id)}
                      className={cn(
                        'w-full group flex items-start gap-2 px-3 py-2.5 rounded-xl text-left transition-colors',
                        conv.id === activeId ? 'bg-white/8 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-white'
                      )}
                    >
                      <MessageSquare size={15} className="mt-0.5 shrink-0 text-gray-500" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm truncate">{conv.title}</p>
                        <p className="text-[11px] text-gray-600 mt-0.5">{formatTime(conv.createdAt)}</p>
                      </div>
                      <button
                        onClick={(e) => deleteConversation(conv.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded text-gray-600 hover:text-red-400 transition-all"
                      >
                        <Trash2 size={13} />
                      </button>
                    </motion.button>
                  ))
                )}
              </AnimatePresence>
            </div>

            {/* 底部模型信息 */}
            <div className="p-3 border-t border-white/5">
              <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-white/3">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-xs text-gray-500 truncate">
                  {AVAILABLE_MODELS.find(m => m.id === selectedModel)?.provider} 服务在线
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── 右侧主对话区 ── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* 顶栏 */}
        <div className="h-14 flex items-center gap-3 px-4 border-b border-white/5 shrink-0">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/5 transition-colors"
          >
            <ChevronRight size={18} className={cn('transition-transform', sidebarOpen && 'rotate-180')} />
          </button>

          <div className="flex-1" />

          {/* 模型选择 */}
          <ModelSelector selected={selectedModel} onChange={setSelectedModel} />

          <button className="p-1.5 rounded-lg text-gray-500 hover:text-white hover:bg-white/5 transition-colors">
            <Settings2 size={17} />
          </button>
        </div>

        {/* 消息区 */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {!activeConv || activeConv.messages.length === 0 ? (
            // 欢迎页
            <div className="flex flex-col items-center justify-center h-full px-6 pb-16 select-none">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4 }}
                className="text-center"
              >
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyber-purple to-cyber-cyan flex items-center justify-center mx-auto mb-5 neon-glow-cyan">
                  <Bot size={32} className="text-white" />
                </div>
                <h2 className="text-2xl font-bold gradient-text mb-2">农业 AI 助手</h2>
                <p className="text-gray-500 text-sm max-w-md">
                  基于多模型协同的农业智能决策系统，支持作物诊断、精准施肥、气象分析等专业场景
                </p>
              </motion.div>

              {/* 快捷问题 */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.4 }}
                className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-10 w-full max-w-2xl"
              >
                {QUICK_PROMPTS.map((qp, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(qp.prompt)}
                    className="flex items-start gap-3 p-4 rounded-xl bg-white/4 border border-white/8 hover:bg-white/8 hover:border-cyber-cyan/30 text-left transition-all group"
                  >
                    <qp.icon size={18} className="text-cyber-cyan mt-0.5 shrink-0 group-hover:scale-110 transition-transform" />
                    <div>
                      <p className="text-sm font-medium text-white">{qp.label}</p>
                      <p className="text-[11px] text-gray-500 mt-0.5 line-clamp-2">{qp.prompt}</p>
                    </div>
                  </button>
                ))}
              </motion.div>
            </div>
          ) : (
            // 消息列表
            <div className="py-4">
              {activeConv.messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} onCopy={handleCopy} />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* 输入区 */}
        <div className="px-4 pb-4 pt-2 shrink-0">
          <div className={cn(
            'relative rounded-2xl border transition-all duration-200',
            isStreaming ? 'border-cyber-cyan/40 bg-white/5' : 'border-white/10 bg-white/5 hover:border-white/20 focus-within:border-cyber-cyan/50'
          )}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isStreaming ? 'AI 正在思考中...' : '输入消息，Shift+Enter 换行...'}
              disabled={isStreaming}
              rows={1}
              className="w-full bg-transparent text-sm text-white placeholder:text-gray-600 px-4 pt-3 pb-12 resize-none outline-none leading-relaxed custom-scrollbar"
              style={{ maxHeight: 200 }}
            />

            {/* 底部操作栏 */}
            <div className="absolute bottom-3 left-3 right-3 flex items-center gap-2">
              <button className="p-1.5 rounded-lg text-gray-600 hover:text-gray-400 transition-colors" title="附件">
                <Paperclip size={16} />
              </button>
              <button className="p-1.5 rounded-lg text-gray-600 hover:text-gray-400 transition-colors" title="语音">
                <Mic size={16} />
              </button>

              <div className="flex-1" />

              <span className="text-[11px] text-gray-600">
                {input.length > 0 && `${input.length} 字`}
              </span>

              {isStreaming ? (
                <button
                  onClick={stopGeneration}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 text-xs hover:bg-red-500/30 transition-colors"
                >
                  <Square size={12} fill="currentColor" />
                  停止
                </button>
              ) : (
                <button
                  onClick={() => sendMessage()}
                  disabled={!input.trim()}
                  className={cn(
                    'flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-sm font-medium transition-all',
                    input.trim()
                      ? 'bg-cyber-cyan text-black hover:bg-cyber-cyan/80 shadow-lg shadow-cyber-cyan/20'
                      : 'bg-white/5 text-gray-600 cursor-not-allowed'
                  )}
                >
                  <Send size={14} />
                  发送
                </button>
              )}
            </div>
          </div>

          {/* 底部提示 */}
          <p className="text-center text-[11px] text-gray-700 mt-2">
            AI 可能出错，请核实重要信息 · 当前模型：{AVAILABLE_MODELS.find(m => m.id === selectedModel)?.name}
          </p>
        </div>
      </div>
    </div>
  )
}
