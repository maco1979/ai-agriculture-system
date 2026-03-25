import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  MessageSquare,
  Heart,
  Share2,
  Search,
  PenSquare,
  Tag,
  ThumbsUp,
  ChevronDown,
  ChevronUp,
  Send,
  Flame,
  Clock,
  Star,
  Sprout,
  Cpu,
  FlaskConical,
  HelpCircle,
} from 'lucide-react'

// ───────────── 类型定义 ─────────────
interface Reply {
  id: number
  user: string
  content: string
  time: string
  likes: number
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
  { key: 'all',      label: '全部',   icon: Star },
  { key: '种植经验', label: '种植经验', icon: Sprout },
  { key: 'AI技术',  label: 'AI技术',  icon: Cpu },
  { key: '科学研究', label: '科学研究', icon: FlaskConical },
  { key: '提问求助', label: '提问求助', icon: HelpCircle },
]

// ───────────── 初始示例帖子 ─────────────
const INITIAL_POSTS: Post[] = [
  {
    id: 1,
    user: '农业科技达人',
    avatar: 'https://ui-avatars.com/api/?name=农业&background=22c55e&color=fff',
    title: '使用 AI 病虫害诊断功能，帮助我减少了40%的农药使用',
    content:
      '今年夏天水稻出现了一种我从来没见过的斑点，上传图片到系统后，AI 几秒就给出了"稻瘟病早期"的诊断，并推荐了低毒防治方案。最终农药用量比去年同期减少了40%，产量反而提升了，强烈推荐大家试试！',
    category: '种植经验',
    tags: ['病虫害', '水稻', 'AI诊断'],
    likes: 256,
    time: '4小时前',
    liked: false,
    replies: [
      { id: 1, user: 'AI爱好者', content: '太厉害了！请问上传图片在哪个页面？', time: '3小时前', likes: 8 },
      { id: 2, user: '老王种地', content: '我也遇到过类似情况，AI 给的建议确实准', time: '2小时前', likes: 5 },
    ],
  },
  {
    id: 2,
    user: '区块链开发者',
    avatar: 'https://ui-avatars.com/api/?name=开发&background=6366f1&color=fff',
    title: '项目的区块链溯源模块解析 — 数据如何做到不可篡改',
    content:
      '深入研究了一下本项目的区块链集成方案，核心是 Hyperledger Fabric 联盟链，每次农产品流通节点都会上链存证。与公链相比，联盟链吞吐量更高，且可控节点身份，非常适合农业供应链场景。有兴趣的朋友可以查看 blockchain 模块源码。',
    category: 'AI技术',
    tags: ['区块链', '溯源', 'Hyperledger'],
    likes: 192,
    time: '6小时前',
    liked: false,
    replies: [
      { id: 1, user: '好奇宝宝', content: '能分享一下上链的 gas 成本吗？联盟链是不是免费的？', time: '5小时前', likes: 3 },
    ],
  },
  {
    id: 3,
    user: 'AI爱好者小明',
    avatar: 'https://ui-avatars.com/api/?name=小明&background=f59e0b&color=fff',
    title: '模型训练速度提升30%的小技巧，附详细配置',
    content:
      '发现一个配置技巧：在 Settings 页把批处理大小从默认的 32 调整为 64，同时开启混合精度训练（FP16）。在我的 RTX 3060 上实测训练速度提升约 30%，显存占用却降低了 15%。具体步骤：进入【模型管理】→【训练配置】→调整 batch_size 和 mixed_precision 参数。',
    category: 'AI技术',
    tags: ['模型训练', '性能优化', 'GPU'],
    likes: 128,
    time: '昨天',
    liked: false,
    replies: [],
  },
  {
    id: 4,
    user: '新手求助',
    avatar: 'https://ui-avatars.com/api/?name=新手&background=ef4444&color=fff',
    title: '请问 DeepSeek API Key 怎么获取？',
    content:
      '刚下载了项目，看 .env.example 里说推荐用 DeepSeek，但不知道去哪里注册申请 API Key，有没有大佬指导一下？',
    category: '提问求助',
    tags: ['DeepSeek', 'API', '新手'],
    likes: 34,
    time: '2小时前',
    liked: false,
    replies: [
      {
        id: 1,
        user: '农业科技达人',
        content:
          '去 https://platform.deepseek.com 注册，实名认证后充值10元即可获得 API Key，非常便宜。',
        time: '1小时前',
        likes: 12,
      },
    ],
  },
]

// ───────────── 排序方式 ─────────────
type SortMode = 'hot' | 'latest'

// ───────────── 主组件 ─────────────
export function Community() {
  const [posts, setPosts] = useState<Post[]>(INITIAL_POSTS)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')
  const [sortMode, setSortMode] = useState<SortMode>('hot')
  const [expandedPost, setExpandedPost] = useState<number | null>(null)
  const [replyTexts, setReplyTexts] = useState<{ [key: number]: string }>({})

  // 发帖弹窗状态
  const [showNewPost, setShowNewPost] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState('种植经验')
  const [newTags, setNewTags] = useState('')

  // ── 过滤 + 排序 ──
  const filtered = posts
    .filter((p) => {
      const matchCat = activeCategory === 'all' || p.category === activeCategory
      const q = searchQuery.toLowerCase()
      const matchSearch =
        !q ||
        p.title.toLowerCase().includes(q) ||
        p.content.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q))
      return matchCat && matchSearch
    })
    .sort((a, b) =>
      sortMode === 'hot' ? b.likes - a.likes : b.id - a.id
    )

  // ── 点赞帖子 ──
  const handleLike = (postId: number) => {
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId
          ? { ...p, liked: !p.liked, likes: p.liked ? p.likes - 1 : p.likes + 1 }
          : p
      )
    )
  }

  // ── 提交回复 ──
  const handleReply = (postId: number) => {
    const text = replyTexts[postId]?.trim()
    if (!text) return
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId
          ? {
              ...p,
              replies: [
                ...p.replies,
                { id: Date.now(), user: '我', content: text, time: '刚刚', likes: 0 },
              ],
            }
          : p
      )
    )
    setReplyTexts((prev) => ({ ...prev, [postId]: '' }))
  }

  // ── 发布新帖 ──
  const handlePublish = () => {
    if (!newTitle.trim() || !newContent.trim()) return
    const post: Post = {
      id: Date.now(),
      user: '我',
      avatar: 'https://ui-avatars.com/api/?name=我&background=14b8a6&color=fff',
      title: newTitle.trim(),
      content: newContent.trim(),
      category: newCategory,
      tags: newTags
        .split(/[,，\s]+/)
        .map((t) => t.trim())
        .filter(Boolean),
      likes: 0,
      replies: [],
      time: '刚刚',
      liked: false,
    }
    setPosts((prev) => [post, ...prev])
    setNewTitle('')
    setNewContent('')
    setNewTags('')
    setNewCategory('种植经验')
    setShowNewPost(false)
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="bg-gradient-to-r from-tech-primary/10 to-tech-secondary/10 rounded-lg p-6 border border-tech-primary/20">
        <h1 className="text-3xl font-bold gradient-text mb-2">社区论坛</h1>
        <p className="text-gray-300">分享你的种植经验、技术心得，和来自全球的农业 AI 爱好者交流</p>
      </div>

      {/* 搜索 + 发帖 */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            placeholder="搜索帖子、标签或用户..."
            className="pl-10 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <Button
          variant="tech"
          className="flex items-center space-x-2 whitespace-nowrap"
          onClick={() => setShowNewPost(true)}
        >
          <PenSquare className="w-4 h-4" />
          <span>发布帖子</span>
        </Button>
      </div>

      {/* 发帖弹窗 */}
      {showNewPost && (
        <Card className="glass-effect border-tech-primary/40">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <PenSquare className="w-5 h-5 text-tech-primary" />
              <span>发布新帖</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Input
              placeholder="帖子标题（简洁有力）"
              className="bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
            />
            <textarea
              placeholder="详细描述你的想法、经验或问题..."
              className="w-full h-32 rounded-md bg-tech-dark/50 border border-tech-primary/20 text-white placeholder:text-gray-400 p-3 resize-none text-sm focus:outline-none focus:border-tech-primary/60"
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
            />
            <div className="flex flex-col sm:flex-row gap-3">
              <select
                className="flex-1 rounded-md bg-tech-dark/50 border border-tech-primary/20 text-white p-2 text-sm focus:outline-none"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              >
                {CATEGORIES.filter((c) => c.key !== 'all').map((c) => (
                  <option key={c.key} value={c.key}>
                    {c.label}
                  </option>
                ))}
              </select>
              <div className="relative flex-1">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  placeholder="标签（逗号分隔，如：水稻,AI,病虫害）"
                  className="pl-9 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400"
                  value={newTags}
                  onChange={(e) => setNewTags(e.target.value)}
                />
              </div>
            </div>
            <div className="flex justify-end space-x-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowNewPost(false)
                  setNewTitle('')
                  setNewContent('')
                  setNewTags('')
                }}
              >
                取消
              </Button>
              <Button
                variant="tech"
                disabled={!newTitle.trim() || !newContent.trim()}
                onClick={handlePublish}
              >
                发布
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 分类 + 排序 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* 分类 Tab */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => {
            const Icon = cat.icon
            return (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all duration-200 ${
                  activeCategory === cat.key
                    ? 'bg-tech-primary text-white'
                    : 'bg-tech-dark/50 text-gray-400 hover:text-white border border-tech-primary/20'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{cat.label}</span>
              </button>
            )
          })}
        </div>

        {/* 排序 */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSortMode('hot')}
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all duration-200 ${
              sortMode === 'hot'
                ? 'bg-orange-500/20 text-orange-400 border border-orange-500/40'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>热门</span>
          </button>
          <button
            onClick={() => setSortMode('latest')}
            className={`flex items-center space-x-1 px-3 py-1.5 rounded-full text-sm transition-all duration-200 ${
              sortMode === 'latest'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>最新</span>
          </button>
        </div>
      </div>

      {/* 帖子列表 */}
      <div className="space-y-4">
        {filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>还没有帖子，成为第一个发帖的人吧！</p>
          </div>
        )}

        {filtered.map((post) => {
          const isExpanded = expandedPost === post.id
          return (
            <Card key={post.id} className="glass-effect hover:border-tech-primary/40 transition-all duration-300">
              <CardContent className="pt-5 space-y-3">
                {/* 用户信息 + 分类 */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <img
                      src={post.avatar}
                      alt={post.user}
                      className="w-9 h-9 rounded-full"
                    />
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

                {/* 正文（折叠/展开） */}
                <p
                  className={`text-sm text-gray-300 leading-relaxed ${
                    isExpanded ? '' : 'line-clamp-3'
                  }`}
                >
                  {post.content}
                </p>

                {/* 标签 */}
                {post.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {post.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-0.5 bg-tech-primary/10 text-tech-primary/80 rounded-full"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                )}

                {/* 操作栏 */}
                <div className="flex items-center justify-between text-sm text-gray-400 pt-1">
                  <div className="flex items-center space-x-4">
                    {/* 点赞 */}
                    <button
                      onClick={() => handleLike(post.id)}
                      className={`flex items-center space-x-1.5 transition-colors ${
                        post.liked ? 'text-tech-primary' : 'hover:text-tech-primary'
                      }`}
                    >
                      <ThumbsUp className="w-4 h-4" />
                      <span>{post.likes}</span>
                    </button>

                    {/* 回复 */}
                    <button
                      onClick={() => setExpandedPost(isExpanded ? null : post.id)}
                      className="flex items-center space-x-1.5 hover:text-tech-primary transition-colors"
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span>{post.replies.length} 回复</span>
                    </button>

                    {/* 分享 */}
                    <button className="flex items-center space-x-1.5 hover:text-tech-primary transition-colors">
                      <Share2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* 展开/收起 */}
                  <button
                    onClick={() => setExpandedPost(isExpanded ? null : post.id)}
                    className="flex items-center space-x-1 text-xs hover:text-tech-primary transition-colors"
                  >
                    {isExpanded ? (
                      <>
                        <ChevronUp className="w-4 h-4" />
                        <span>收起</span>
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-4 h-4" />
                        <span>展开</span>
                      </>
                    )}
                  </button>
                </div>

                {/* 回复区（展开后显示） */}
                {isExpanded && (
                  <div className="border-t border-tech-primary/10 pt-4 space-y-4">
                    {/* 回复列表 */}
                    {post.replies.length > 0 ? (
                      <div className="space-y-3">
                        {post.replies.map((r) => (
                          <div key={r.id} className="flex space-x-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-tech-primary to-tech-secondary flex items-center justify-center text-xs font-bold flex-shrink-0">
                              {r.user.charAt(0)}
                            </div>
                            <div className="flex-1 bg-tech-dark/40 rounded-lg p-3">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-sm font-medium">{r.user}</span>
                                <span className="text-xs text-gray-400">{r.time}</span>
                              </div>
                              <p className="text-sm text-gray-300">{r.content}</p>
                              <button className="flex items-center space-x-1 mt-2 text-xs text-gray-400 hover:text-tech-primary transition-colors">
                                <Heart className="w-3 h-3" />
                                <span>{r.likes}</span>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 text-center">暂无回复，来说说你的想法</p>
                    )}

                    {/* 输入框 */}
                    <div className="flex space-x-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-tech-primary to-tech-secondary flex items-center justify-center text-xs font-bold flex-shrink-0">
                        我
                      </div>
                      <div className="flex-1 flex space-x-2">
                        <Input
                          placeholder="写下你的回复..."
                          className="flex-1 bg-tech-dark/50 border-tech-primary/20 text-white placeholder:text-gray-400 text-sm"
                          value={replyTexts[post.id] ?? ''}
                          onChange={(e) =>
                            setReplyTexts((prev) => ({ ...prev, [post.id]: e.target.value }))
                          }
                          onKeyDown={(e) => e.key === 'Enter' && handleReply(post.id)}
                        />
                        <Button
                          variant="tech"
                          size="icon"
                          disabled={!replyTexts[post.id]?.trim()}
                          onClick={() => handleReply(post.id)}
                        >
                          <Send className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 底部说明 */}
      <div className="text-center text-xs text-gray-500 py-4">
        <p>论坛数据仅保存在本地会话，刷新后重置。如需持久化，请配置后端数据库。</p>
      </div>
    </div>
  )
}

export default Community
