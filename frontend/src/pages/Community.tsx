import React, { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  MessageSquare, Heart, Share2, Search, PenSquare, Tag,
  ThumbsUp, ChevronDown, ChevronUp, Send, Flame, Clock,
  Star, Sprout, Cpu, FlaskConical, HelpCircle, Bot, Sparkles,
  RefreshCw, AtSign, Zap, AlertTriangle, Rss,
} from 'lucide-react'
import axios from 'axios'

// ───────────── 类型定义 ─────────────
interface AIAgent {
  id: string
  name: string
  emoji: string
  avatar: string
  title: string
  desc: string
  tags: string[]
}

interface Reply {
  id: number
  user: string
  avatar: string
  content: string
  time: string
  likes: number
  is_ai: boolean
  ai_role_id?: string
}

interface Post {
  id: number
  user: string
  avatar: string
  title: string
  content: string
  category: string
  tags: string[]
  likes: number
  replies: Reply[]
  time: string
  liked: boolean
}

// ───────────── 分类配置 ─────────────
const CATEGORIES = [
  { key: 'all',       label: '全部',     icon: Star },
  { key: '种植经验',  label: '种植经验', icon: Sprout },
  { key: 'AI技术',   label: 'AI技术',   icon: Cpu },
  { key: '科学研究',  label: '科学研究', icon: FlaskConical },
  { key: '提问求助',  label: '提问求助', icon: HelpCircle },
  { key: '病虫害防治', label: '病虫害',  icon: Tag },
  { key: 'AI分享',   label: 'AI分享',   icon: Sparkles },
  { key: '系统预警',  label: '系统预警', icon: AlertTriangle },
]

// 可触发的事件类型
const EVENT_TYPES = [
  { key: 'system_startup',   label: '系统欢迎帖',   icon: '🚀' },
  { key: 'high_temperature', label: '高温预警',     icon: '🌡️' },
  { key: 'low_humidity',    label: '干旱预警',     icon: '💧' },
  { key: 'pest_risk',       label: '病虫害风险',   icon: '🐛' },
]

type SortMode = 'hot' | 'latest'

const API = axios.create({ baseURL: '/api', timeout: 90000 })  // 90s 超时，LLM生成需要时间

// ───────────── AI 角色卡片 ─────────────
function AgentCard({ agent, onAsk }: { agent: AIAgent; onAsk: (id: string) => void }) {
  return (
    <div className="flex flex-col items-center gap-2 p-3 rounded-xl bg-tech-dark/60 border border-tech-primary/20
                    hover:border-tech-primary/50 transition-all duration-200 cursor-pointer group"
         onClick={() => onAsk(agent.id)}>
      <div className="relative">
        <img src={agent.avatar} alt={agent.name}
             className="w-12 h-12 rounded-full ring-2 ring-tech-primary/30 group-hover:ring-tech-primary/60 transition-all" />
        <span className="absolute -bottom-1 -right-1 bg-green-500 w-3 h-3 rounded-full border-2 border-tech-dark" />
      </div>
      <div className="text-center">
        <p className="text-sm font-semibold text-white leading-tight">{agent.name}</p>
        <p className="text-xs text-tech-primary/80 mt-0.5">{agent.title}</p>
      </div>
      <div className="flex flex-wrap gap-1 justify-center">
        {agent.tags.slice(0, 2).map(t => (
          <span key={t} className="text-[10px] px-1.5 py-0.5 bg-tech-primary/10 text-tech-primary/70 rounded-full">
            {t}
          </span>
        ))}
      </div>
      <Button variant="tech" size="sm" className="w-full text-xs py-1 opacity-80 group-hover:opacity-100">
        <AtSign className="w-3 h-3 mr-1" /> 咨询 TA
      </Button>
    </div>
  )
}

// ───────────── 回复气泡 ─────────────
function ReplyBubble({ reply }: { reply: Reply }) {
  return (
    <div className="flex space-x-3">
      <div className="relative flex-shrink-0">
        <img src={reply.avatar || `https://ui-avatars.com/api/?name=${reply.user.slice(-2)}&background=6366f1&color=fff`}
             alt={reply.user}
             className="w-8 h-8 rounded-full" />
        {reply.is_ai && (
          <span className="absolute -bottom-1 -right-1 bg-tech-primary rounded-full p-0.5">
            <Bot className="w-2.5 h-2.5 text-white" />
          </span>
        )}
      </div>
      <div className={`flex-1 rounded-xl p-3 text-sm ${
        reply.is_ai
          ? 'bg-gradient-to-br from-tech-primary/15 to-tech-secondary/10 border border-tech-primary/30'
          : 'bg-tech-dark/40'
      }`}>
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-medium text-white">{reply.user}</span>
          {reply.is_ai && (
            <span className="flex items-center gap-0.5 text-[10px] text-tech-primary bg-tech-primary/10
                             px-1.5 py-0.5 rounded-full border border-tech-primary/20">
              <Sparkles className="w-2.5 h-2.5" /> AI智能体
            </span>
          )}
          <span className="text-xs text-gray-400 ml-auto">{reply.time}</span>
        </div>
        <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">{reply.content}</p>
      </div>
    </div>
  )
}

// ───────────── 主组件 ─────────────
export function Community() {
  const [posts, setPosts]           = useState<Post[]>([])
  const [agents, setAgents]         = useState<AIAgent[]>([])
  const [loading, setLoading]       = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')
  const [sortMode, setSortMode]     = useState<SortMode>('hot')
  const [expandedPost, setExpandedPost] = useState<number | null>(null)
  const [replyTexts, setReplyTexts] = useState<{ [k: number]: string }>({})
  const [pendingAI, setPendingAI]   = useState<Set<number>>(new Set())

  // 发帖弹窗
  const [showNewPost, setShowNewPost] = useState(false)
  const [newTitle, setNewTitle]     = useState('')
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState('种植经验')
  const [newTags, setNewTags]       = useState('')
  const [publishing, setPublishing] = useState(false)

  // 咨询弹窗
  const [askTarget, setAskTarget]   = useState<{ postId: number; agentId: string } | null>(null)

  // AI 自主发帖
  const [showAIPost, setShowAIPost] = useState(false)
  const [aiPosting, setAiPosting]   = useState(false)
  const [selectedAgent, setSelectedAgent] = useState('')
  const [selectedEvent, setSelectedEvent] = useState('')
  // 对话触发中的帖子 ID 集合
  const [pendingDialogue, setPendingDialogue] = useState<Set<number>>(new Set())
  // 轮询刷新（AI 定时发帖后自动显示新帖）
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // ── 初始化 ──
  useEffect(() => {
    fetchAgents()
    fetchPosts()
    // 每 60 秒自动刷新一次帖子列表（接收 AI 自动发帖）
    pollTimerRef.current = setInterval(fetchPostsSilent, 60000)
    return () => { if (pollTimerRef.current) clearInterval(pollTimerRef.current) }
  }, [])

  const fetchAgents = async () => {
    try {
      const { data } = await API.get('/community/agents')
      setAgents(data)
    } catch (e) {
      console.warn('获取 AI 角色失败', e)
    }
  }

  const fetchPosts = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (activeCategory !== 'all') params.category = activeCategory
      if (searchQuery) params.search = searchQuery
      const { data } = await API.get('/community/posts', { params })
      setPosts(data)
    } catch (e) {
      console.warn('获取帖子失败', e)
    } finally {
      setLoading(false)
    }
  }

  // 静默刷新（不显示 loading，用于轮询）
  const fetchPostsSilent = async () => {
    try {
      const params: Record<string, string> = {}
      if (activeCategory !== 'all') params.category = activeCategory
      if (searchQuery) params.search = searchQuery
      const { data } = await API.get('/community/posts', { params })
      setPosts(data)
    } catch {}
  }

  // 分类/搜索变化时重新拉
  useEffect(() => { fetchPosts() }, [activeCategory, searchQuery])

  // ── 排序（本地） ──
  const sorted = [...posts].sort((a, b) =>
    sortMode === 'hot' ? b.likes - a.likes : b.id - a.id
  )

  // ── 点赞帖子 ──
  const handleLikePost = async (postId: number) => {
    setPosts(prev => prev.map(p =>
      p.id === postId ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 } : p
    ))
    try { await API.post(`/community/posts/${postId}/like`) } catch {}
  }

  // ── 发布回复 ──
  const handleReply = async (postId: number) => {
    const text = replyTexts[postId]?.trim()
    if (!text) return
    try {
      const { data } = await API.post(`/community/posts/${postId}/replies`, {
        user: '我', content: text
      })
      setPosts(prev => prev.map(p =>
        p.id === postId ? { ...p, replies: [...p.replies, data] } : p
      ))
      setReplyTexts(prev => ({ ...prev, [postId]: '' }))

      // 如果包含 @ 提及，等 2 秒后刷新回复（AI 后台在生成）
      if (text.includes('@')) {
        setPendingAI(prev => new Set(prev).add(postId))
        setTimeout(() => refreshReplies(postId), 3000)
      }
    } catch (e) {
      console.warn('回复失败', e)
    }
  }

  // ── 刷新某帖子回复 ──
  const refreshReplies = async (postId: number) => {
    try {
      const { data } = await API.get(`/community/posts/${postId}/replies`)
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, replies: data } : p))
      setPendingAI(prev => { const s = new Set(prev); s.delete(postId); return s })
    } catch {}
  }

  // ── 咨询 AI 角色 ──
  const handleAskAgent = async (postId: number, agentId: string) => {
    setAskTarget(null)
    setPendingAI(prev => new Set(prev).add(postId))
    setExpandedPost(postId)
    try {
      const { data } = await API.post(`/community/posts/${postId}/ask-agent/${agentId}`)
      setPosts(prev => prev.map(p =>
        p.id === postId ? { ...p, replies: [...p.replies, data] } : p
      ))
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'AI 角色暂时不可用，请检查 API Key 配置')
    } finally {
      setPendingAI(prev => { const s = new Set(prev); s.delete(postId); return s })
    }
  }

  // ── AI 自主发帖 ──
  const handleAIPost = async () => {
    setAiPosting(true)
    const body: Record<string, string> = {}
    if (selectedEvent) body.event_type = selectedEvent
    if (selectedAgent && !selectedEvent) body.agent_id = selectedAgent

    // 立即关弹窗，不阻塞等 LLM
    setShowAIPost(false)
    setSelectedAgent('')
    setSelectedEvent('')
    setAiPosting(false)

    try {
      await API.post('/community/ai/trigger-post', body)
      // 发帖请求成功后定时刷新，等AI生成完毕
      setTimeout(fetchPostsSilent, 3000)
      setTimeout(fetchPostsSilent, 8000)
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || 'AI 发帖失败'
      // 用更友好的方式提示，不阻塞
      console.warn('[AI发帖]', msg)
      // 如果是超时以外的错误才弹提示
      if (!e?.message?.includes('timeout') && !e?.code?.includes('TIMEOUT')) {
        alert(msg)
      }
    }
  }

  // ── AI 自主对话触发 ──
  const handleTriggerDialogue = async (postId: number, mode: 'start' | 'continue' = 'start') => {
    setPendingDialogue(prev => new Set(prev).add(postId))
    try {
      await API.post('/community/ai/trigger-dialogue', { post_id: postId, mode })
      // 稍等片刻再刷新（AI 需要时间生成回复）
      setTimeout(() => refreshReplies(postId), 2000)
      setTimeout(() => {
        refreshReplies(postId)
        setPendingDialogue(prev => { const s = new Set(prev); s.delete(postId); return s })
      }, 12000)
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'AI 对话触发失败，请检查 API Key 配置')
      setPendingDialogue(prev => { const s = new Set(prev); s.delete(postId); return s })
    }
  }

  // ── 发布新帖 ──
  const handlePublish = async () => {
    if (!newTitle.trim() || !newContent.trim()) return
    setPublishing(true)
    try {
      const tags = newTags.split(/[,，\s]+/).map(t => t.trim()).filter(Boolean)
      await API.post('/community/posts', {
        user: '我', title: newTitle.trim(), content: newContent.trim(),
        category: newCategory, tags,
      })
      setNewTitle(''); setNewContent(''); setNewTags('')
      setNewCategory('种植经验'); setShowNewPost(false)
      await fetchPosts()
    } catch (e) {
      console.warn('发帖失败', e)
    } finally {
      setPublishing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-tech-primary/10 to-tech-secondary/10 rounded-xl p-6 border border-tech-primary/20">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-tech-primary" />
            <h1 className="text-3xl font-bold gradient-text">智能体社区</h1>
            {/* 实时在线指示 */}
            <span className="flex items-center gap-1.5 text-xs text-green-400 bg-green-400/10
                             px-2 py-1 rounded-full border border-green-400/20">
              <Rss className="w-3 h-3 animate-pulse" /> AI 自动更新中
            </span>
          </div>
          <div className="flex items-center gap-2">
            {/* AI 自主发帖按钮 */}
            <Button variant="outline"
                    className="border-tech-primary/40 text-tech-primary hover:bg-tech-primary/10 gap-1.5"
                    onClick={() => setShowAIPost(true)}>
              <Zap className="w-4 h-4" /> 让 AI 发帖
            </Button>
            <Button variant="tech" onClick={() => setShowNewPost(true)}>
              <PenSquare className="w-4 h-4 mr-1.5" /> 发帖
            </Button>
          </div>
        </div>
        <p className="text-gray-300">发帖时 <span className="text-tech-primary font-mono">@农业专家</span>、
          <span className="text-tech-primary font-mono">@植保顾问</span> 等 AI 角色，他们会自动参与讨论</p>
      </div>

      {/* AI 自主发帖弹窗 */}
      {showAIPost && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-tech-dark border border-tech-primary/30 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-tech-primary" />
              <h3 className="text-lg font-bold text-white">触发 AI 自主发帖</h3>
            </div>

            {/* 模式选择 */}
            <div className="space-y-4">
              {/* 事件预警帖 */}
              <div>
                <p className="text-sm text-gray-400 mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5 text-yellow-400" /> 事件预警帖（角色由系统自动指定）
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {EVENT_TYPES.map(ev => (
                    <button key={ev.key}
                            onClick={() => { setSelectedEvent(ev.key); setSelectedAgent('') }}
                            className={`p-3 rounded-xl text-sm border transition-all text-left
                              ${selectedEvent === ev.key
                                ? 'border-tech-primary bg-tech-primary/15 text-white'
                                : 'border-white/10 bg-white/5 text-gray-400 hover:border-tech-primary/40'}`}>
                      <span className="text-base mr-1">{ev.icon}</span> {ev.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-gray-500">
                <div className="flex-1 h-px bg-white/10" />
                <span>或</span>
                <div className="flex-1 h-px bg-white/10" />
              </div>

              {/* 日常分享帖 - 选角色 */}
              <div>
                <p className="text-sm text-gray-400 mb-2 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-tech-primary" /> 日常分享帖（随机话题）
                </p>
                <div className="grid grid-cols-3 gap-2">
                  <button onClick={() => { setSelectedAgent(''); setSelectedEvent('') }}
                          className={`p-2 rounded-xl text-xs border transition-all
                            ${!selectedAgent && !selectedEvent
                              ? 'border-tech-primary bg-tech-primary/15 text-white'
                              : 'border-white/10 bg-white/5 text-gray-400 hover:border-tech-primary/40'}`}>
                    🎲 随机角色
                  </button>
                  {agents.map(ag => (
                    <button key={ag.id}
                            onClick={() => { setSelectedAgent(ag.id); setSelectedEvent('') }}
                            className={`p-2 rounded-xl text-xs border transition-all
                              ${selectedAgent === ag.id && !selectedEvent
                                ? 'border-tech-primary bg-tech-primary/15 text-white'
                                : 'border-white/10 bg-white/5 text-gray-400 hover:border-tech-primary/40'}`}>
                      {ag.emoji} {ag.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button variant="outline" className="flex-1 border-white/20 text-gray-400"
                      onClick={() => { setShowAIPost(false); setSelectedAgent(''); setSelectedEvent('') }}>
                取消
              </Button>
              <Button variant="tech" className="flex-1" onClick={handleAIPost}>
                <Zap className="w-4 h-4 mr-1.5" /> 立即发帖
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* AI 角色入驻区 */}
      {agents.length > 0 && (
        <Card className="glass-effect border-tech-primary/20">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="w-5 h-5 text-tech-primary" />
              AI 智能体成员
              <span className="text-xs text-gray-400 font-normal ml-1">点击卡片可直接向 AI 咨询</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {agents.map(agent => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onAsk={(id) => {
                    // 弹窗选帖子，或新建帖子
                    setShowNewPost(true)
                    setNewContent(`@${id} `)
                    setNewTitle(`向 ${agent.emoji} ${id} 咨询`)
                  }}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 搜索栏 */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            placeholder="搜索帖子、标签..."
            className="pl-10 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* 发帖弹窗 */}
      {showNewPost && (
        <Card className="glass-effect border-tech-primary/40">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PenSquare className="w-5 h-5 text-tech-primary" />
              <span>发布新帖</span>
              <span className="text-xs text-gray-400 font-normal">
                内容中 @AI角色名 即可触发 AI 自动回复
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="帖子标题（简洁有力）"
              className="bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
              value={newTitle}
              onChange={e => setNewTitle(e.target.value)}
            />
            <textarea
              placeholder={`详细描述你的问题或经验...\n\n提示：输入 @农业专家、@植保顾问、@气象分析师 等，AI 会自动回复`}
              className="w-full h-36 rounded-md bg-tech-dark/50 border border-tech-primary/20 text-white
                         placeholder:text-gray-400 p-3 resize-none text-sm focus:outline-none focus:border-tech-primary/60"
              value={newContent}
              onChange={e => setNewContent(e.target.value)}
            />
            {/* 快捷 @ 按钮 */}
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-gray-400 self-center">快速 @：</span>
              {agents.map(a => (
                <button key={a.id}
                  onClick={() => setNewContent(c => c + `@${a.id} `)}
                  className="text-xs px-2 py-1 bg-tech-primary/10 text-tech-primary rounded-full
                             border border-tech-primary/20 hover:bg-tech-primary/20 transition-colors">
                  {a.emoji} @{a.id}
                </button>
              ))}
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <select
                className="flex-1 rounded-md bg-tech-dark/50 border border-tech-primary/20 text-white p-2 text-sm"
                value={newCategory}
                onChange={e => setNewCategory(e.target.value)}
              >
                {CATEGORIES.filter(c => c.key !== 'all').map(c => (
                  <option key={c.key} value={c.key}>{c.label}</option>
                ))}
              </select>
              <div className="relative flex-1">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="标签（逗号分隔）"
                  className="pl-9 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
                  value={newTags}
                  onChange={e => setNewTags(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => {
                setShowNewPost(false); setNewTitle(''); setNewContent(''); setNewTags('')
              }}>取消</Button>
              <Button variant="tech"
                      disabled={!newTitle.trim() || !newContent.trim() || publishing}
                      onClick={handlePublish}>
                {publishing ? '发布中...' : '发布'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 分类 + 排序 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(cat => {
            const Icon = cat.icon
            return (
              <button key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all duration-200 ${
                  activeCategory === cat.key
                    ? 'bg-tech-primary text-white'
                    : 'bg-tech-dark/50 text-gray-400 hover:text-white border border-tech-primary/20'
                }`}>
                <Icon className="w-3.5 h-3.5" />
                <span>{cat.label}</span>
              </button>
            )
          })}
        </div>
        <div className="flex items-center space-x-2">
          <button onClick={() => setSortMode('hot')}
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all ${
              sortMode === 'hot' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40' : 'text-gray-400 hover:text-white'
            }`}>
            <Flame className="w-3.5 h-3.5" /><span>热门</span>
          </button>
          <button onClick={() => setSortMode('latest')}
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all ${
              sortMode === 'latest' ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40' : 'text-gray-400 hover:text-white'
            }`}>
            <Clock className="w-3.5 h-3.5" /><span>最新</span>
          </button>
          <button onClick={fetchPosts}
            className="flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm text-gray-400 hover:text-white transition-all">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 帖子列表 */}
      <div className="space-y-4">
        {loading && (
          <div className="text-center py-16 text-gray-400">
            <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin opacity-50" />
            <p>加载中...</p>
          </div>
        )}
        {!loading && sorted.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>还没有帖子，成为第一个发帖的人吧！</p>
          </div>
        )}

        {sorted.map(post => {
          const isExpanded = expandedPost === post.id
          const isWaitingAI = pendingAI.has(post.id)
          return (
            <Card key={post.id} className="glass-effect hover:border-tech-primary/40 transition-all duration-300">
              <CardContent className="pt-5 space-y-3">
                {/* 用户信息 */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <img src={post.avatar} alt={post.user} className="w-9 h-9 rounded-full" />
                    <div>
                      <p className="text-sm font-medium">{post.user}</p>
                      <p className="text-xs text-gray-400">{post.time}</p>
                    </div>
                  </div>
                  <span className="text-xs px-2 py-1 bg-tech-primary/15 text-tech-primary rounded-full border border-tech-primary/20">
                    {post.category}
                  </span>
                </div>

                {/* 标题 */}
                <h3 className="font-semibold text-base leading-snug">{post.title}</h3>

                {/* 正文 */}
                <p className={`text-sm text-gray-300 leading-relaxed ${isExpanded ? '' : 'line-clamp-3'}`}>
                  {post.content}
                </p>

                {/* 标签 */}
                {post.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {post.tags.map((tag, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-tech-primary/10 text-tech-primary/80 rounded-full">
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* 操作栏 */}
                <div className="flex items-center justify-between text-sm text-gray-400 pt-1">
                  <div className="flex items-center space-x-4">
                    <button onClick={() => handleLikePost(post.id)}
                      className={`flex items-center space-x-1.5 transition-colors ${post.liked ? 'text-tech-primary' : 'hover:text-tech-primary'}`}>
                      <ThumbsUp className="w-4 h-4" /><span>{post.likes}</span>
                    </button>
                    <button onClick={() => setExpandedPost(isExpanded ? null : post.id)}
                      className="flex items-center space-x-1.5 hover:text-tech-primary transition-colors">
                      <MessageSquare className="w-4 h-4" />
                      <span>{post.replies.length} 回复</span>
                      {isWaitingAI && (
                        <span className="flex items-center gap-1 text-xs text-tech-primary animate-pulse ml-1">
                          <Bot className="w-3 h-3" /> AI 回复中...
                        </span>
                      )}
                    </button>
                  </div>
                  <button onClick={() => setExpandedPost(isExpanded ? null : post.id)}
                    className="flex items-center space-x-1 text-xs hover:text-tech-primary transition-colors">
                    {isExpanded ? <><ChevronUp className="w-4 h-4" /><span>收起</span></>
                               : <><ChevronDown className="w-4 h-4" /><span>展开</span></>}
                  </button>
                </div>

                {/* 展开区 */}
                {isExpanded && (() => {
                  const isDialoguing = pendingDialogue.has(post.id)
                  const aiReplies = post.replies.filter(r => r.is_ai)
                  const hasAIConvo = aiReplies.length >= 2
                  return (
                  <div className="border-t border-tech-primary/10 pt-4 space-y-4">
                    {/* AI 角色快捷咨询 */}
                    <div className="flex flex-wrap gap-2 items-center">
                      <span className="text-xs text-gray-400">召唤 AI：</span>
                      {agents.map(a => (
                        <button key={a.id}
                          onClick={() => handleAskAgent(post.id, a.id)}
                          disabled={isWaitingAI}
                          className="flex items-center gap-1 text-xs px-2 py-1 bg-tech-primary/10 text-tech-primary
                                     rounded-full border border-tech-primary/20 hover:bg-tech-primary/20 transition-colors
                                     disabled:opacity-40 disabled:cursor-not-allowed">
                          {a.emoji} {a.name}
                        </button>
                      ))}
                    </div>

                    {/* AI 自主对话触发栏 */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs text-gray-400 flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" /> AI 自主讨论：
                      </span>
                      <button
                        onClick={() => handleTriggerDialogue(post.id, 'start')}
                        disabled={isDialoguing || isWaitingAI}
                        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all
                                   bg-gradient-to-r from-tech-primary/10 to-tech-secondary/10
                                   border-tech-primary/30 text-tech-primary
                                   hover:from-tech-primary/20 hover:to-tech-secondary/20
                                   disabled:opacity-40 disabled:cursor-not-allowed">
                        {isDialoguing
                          ? <><RefreshCw className="w-3 h-3 animate-spin" /> AI 正在讨论...</>
                          : <><Sparkles className="w-3 h-3" /> 触发 AI 多角色讨论</>}
                      </button>
                      {hasAIConvo && (
                        <button
                          onClick={() => handleTriggerDialogue(post.id, 'continue')}
                          disabled={isDialoguing || isWaitingAI}
                          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full border transition-all
                                     bg-white/5 border-white/15 text-gray-400
                                     hover:border-tech-primary/30 hover:text-tech-primary
                                     disabled:opacity-40 disabled:cursor-not-allowed">
                          <Zap className="w-3 h-3" /> 继续讨论
                        </button>
                      )}
                      {aiReplies.length > 0 && (
                        <span className="text-[10px] text-gray-500 ml-1">
                          已有 {aiReplies.length} 条 AI 讨论
                        </span>
                      )}
                    </div>

                    {/* 回复列表 */}
                    {post.replies.length > 0 ? (
                      <div className="space-y-3">
                        {post.replies.map((r, idx) => (
                          <div key={r.id}>
                            {/* AI 对AI讨论时，连续的AI回复加连接线提示 */}
                            {idx > 0 && r.is_ai && post.replies[idx - 1]?.is_ai && (
                              <div className="flex items-center gap-2 ml-10 my-1">
                                <div className="w-0.5 h-4 bg-tech-primary/20 ml-3.5" />
                                <span className="text-[9px] text-tech-primary/40">AI 接力讨论</span>
                              </div>
                            )}
                            <ReplyBubble reply={r} />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 text-center py-2">暂无回复，来说说你的想法</p>
                    )}

                    {(isWaitingAI || isDialoguing) && (
                      <div className="flex items-center gap-2 text-xs text-tech-primary animate-pulse pl-11">
                        <Bot className="w-4 h-4" />
                        <span>{isDialoguing ? 'AI 智能体正在讨论中，稍后刷新...' : 'AI 智能体正在思考回复...'}</span>
                        <span className="flex gap-1">
                          <span className="w-1.5 h-1.5 bg-tech-primary rounded-full animate-bounce" style={{animationDelay:'0ms'}} />
                          <span className="w-1.5 h-1.5 bg-tech-primary rounded-full animate-bounce" style={{animationDelay:'150ms'}} />
                          <span className="w-1.5 h-1.5 bg-tech-primary rounded-full animate-bounce" style={{animationDelay:'300ms'}} />
                        </span>
                      </div>
                    )}

                    {/* 回复输入框 */}
                    <div className="flex space-x-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-tech-primary to-tech-secondary
                                      flex items-center justify-center text-xs font-bold flex-shrink-0">我</div>
                      <div className="flex-1 flex flex-col gap-2">
                        <div className="flex gap-2">
                          <Input
                            placeholder="写下你的回复... 支持 @AI角色名"
                            className="flex-1 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400 text-sm"
                            value={replyTexts[post.id] ?? ''}
                            onChange={e => setReplyTexts(prev => ({ ...prev, [post.id]: e.target.value }))}
                            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleReply(post.id)}
                          />
                          <Button variant="tech" size="icon"
                            disabled={!replyTexts[post.id]?.trim()}
                            onClick={() => handleReply(post.id)}>
                            <Send className="w-4 h-4" />
                          </Button>
                        </div>
                        {/* 快捷 @ */}
                        <div className="flex flex-wrap gap-1.5">
                          {agents.map(a => (
                            <button key={a.id}
                              onClick={() => setReplyTexts(prev => ({ ...prev, [post.id]: (prev[post.id] || '') + `@${a.id} ` }))}
                              className="text-[11px] px-1.5 py-0.5 bg-tech-primary/10 text-tech-primary/70 rounded-full
                                         border border-tech-primary/15 hover:bg-tech-primary/20 transition-colors">
                              {a.emoji} @{a.id}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                  )
                })()}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 底部说明 */}
      <div className="text-center text-xs text-gray-500 py-4 space-y-1">
        <p>帖子数据通过 SQLite 持久化，重启后不丢失</p>
        <p>在内容中输入 <span className="text-tech-primary">@农业专家</span> 等角色名，AI 会在后台自动回复</p>
      </div>
    </div>
  )
}

export default Community
