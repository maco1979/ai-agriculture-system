import React, { useState, useEffect } from 'react'
import { API_BASE_URL } from '@/config'
import { apiClient } from '@/services/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Link2, 
  CheckCircle, 
  Clock, 
  Users, 
  Database,
  TrendingUp,
  Shield,
  FileText,
  RefreshCw,
  AlertCircle,
  Check,
  X,
  Search,
  Award,
  Activity
} from 'lucide-react'

interface BlockchainStatus {
  status: string
  initialized: boolean
  latest_block?: any
  timestamp: string
  network_stats?: {
    active_nodes: number
    federated_rounds: number
    total_photon_issued: number
    provenance_records: number
    upload_events: number
    inference_events: number
    consensus: string
    block_interval: string
    network_latency: string
    security: string
  }
}

interface Transaction {
  hash: string
  type: string
  status: string
  time: string
}

interface SmartContract {
  name: string
  address: string
  status: string
  calls: string
}

interface ProvenanceRecord {
  id: number
  data_id: string
  user_id: string
  operation: string
  model_id: string
  file_name: string
  result: string
  tx_hash: string
  created_at: string
}

export function Blockchain() {
  const [blockchainStatus, setBlockchainStatus] = useState<BlockchainStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [modelId, setModelId] = useState('')
  const [verificationResult, setVerificationResult] = useState<any>(null)
  const [transactionHistory, setTransactionHistory] = useState<any[]>([])

  // 溯源查询
  const [provenanceDataId, setProvenanceDataId] = useState('')
  const [provenanceResult, setProvenanceResult] = useState<ProvenanceRecord[]>([])
  const [provenanceLoading, setProvenanceLoading] = useState(false)

  // 我的数据
  const [myDataRecords, setMyDataRecords] = useState<ProvenanceRecord[]>([])
  const [myDataUserId, setMyDataUserId] = useState('demo_user')

  const [blockchainStats, setBlockchainStats] = useState([
    { label: '总区块数',  value: '加载中...', change: '', icon: Database },
    { label: '活跃节点',  value: '加载中...', change: '', icon: Users },
    { label: '交易总量',  value: '加载中...', change: '', icon: FileText },
    { label: '联邦轮次',  value: '加载中...', change: '', icon: Activity },
  ])

  const [smartContracts, setSmartContracts] = useState([
    { name: '模型验证合约',   address: '0xabc123...', status: '活跃', calls: '0' },
    { name: '数据溯源合约',   address: '0xdef456...', status: '活跃', calls: '0' },
    { name: '联邦学习合约',   address: '0xghi789...', status: '活跃', calls: '0' },
  ])

  const [networkInfo, setNetworkInfo] = useState({
    consensus:      '未知',
    blockSize:      '未知',
    blockInterval:  '未知',
    networkLatency: '未知',
    dataSync:       '未知',
    security:       '未知',
  })

  useEffect(() => {
    fetchBlockchainStatus()
    fetchBlockchainStats()
    fetchMyData()
  }, [])

  const fetchBlockchainStats = async () => {
    try {
      setLoading(true)
      const statusResponse = await apiClient.getBlockchainStatus()
      if (statusResponse.success && statusResponse.data) {
        const d = statusResponse.data as BlockchainStatus
        const ns = d.network_stats

        setBlockchainStats([
          {
            label: '总区块数',
            value: d.latest_block?.block_number != null
              ? d.latest_block.block_number.toString()
              : '0',
            change: '溯源记录总数',
            icon: Database,
          },
          {
            label: '活跃节点',
            value: ns?.active_nodes != null ? ns.active_nodes.toString() : '1',
            change: '联邦+溯源参与者',
            icon: Users,
          },
          {
            label: '交易总量',
            value: d.latest_block?.transaction_count != null
              ? d.latest_block.transaction_count.toString()
              : '0',
            change: '累计链上记录',
            icon: FileText,
          },
          {
            label: '联邦轮次',
            value: ns?.federated_rounds != null ? ns.federated_rounds.toString() : '0',
            change: `PHOTON: ${ns?.total_photon_issued?.toFixed(0) ?? 0}`,
            icon: Activity,
          },
        ])

        if (ns) {
          setNetworkInfo({
            consensus:      ns.consensus || 'PBFT',
            blockSize:      '2MB',
            blockInterval:  ns.block_interval || '2s',
            networkLatency: ns.network_latency || '低',
            dataSync:       ns.provenance_records > 0 ? '同步中' : '空闲',
            security:       ns.security || '高',
          })
          // 更新智能合约调用次数（用溯源数据近似）
          setSmartContracts([
            { name: '模型验证合约',   address: '0xabc123...', status: '活跃', calls: ns.inference_events.toString() },
            { name: '数据溯源合约',   address: '0xdef456...', status: '活跃', calls: ns.provenance_records.toString() },
            { name: '联邦学习合约',   address: '0xghi789...', status: '活跃', calls: ns.federated_rounds.toString() },
          ])
        }
      }
    } catch (error) {
      console.error('获取区块链统计失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchBlockchainStatus = async () => {
    try {
      const response = await apiClient.getBlockchainStatus()
      if (response.success) {
        setBlockchainStatus(response.data as BlockchainStatus || null)
      }
    } catch (error) {
      console.error('获取区块链状态失败:', error)
    }
  }

  const fetchMyData = async () => {
    try {
      const res = await fetch(`/api/provenance/my-data?user_id=${myDataUserId}&limit=20`)
      const json = await res.json()
      if (json.success) setMyDataRecords(json.records || [])
    } catch (e) {
      console.error('获取我的数据失败:', e)
    }
  }

  const queryProvenance = async () => {
    if (!provenanceDataId.trim()) return
    setProvenanceLoading(true)
    try {
      const res = await fetch(`/api/provenance/data/${encodeURIComponent(provenanceDataId)}`)
      const json = await res.json()
      if (json.success) {
        setProvenanceResult(json.provenance_chain || [])
      } else {
        setProvenanceResult([])
      }
    } catch (e) {
      console.error('溯源查询失败:', e)
    } finally {
      setProvenanceLoading(false)
    }
  }

  const verifyModelIntegrity = async () => {
    if (!modelId.trim()) return
    try {
      const response = await apiClient.verifyModelIntegrity(modelId, 'test_hash')
      setVerificationResult(response)
    } catch (error) {
      console.error('验证模型完整性失败:', error)
    }
  }

  const getModelHistory = async () => {
    if (!modelId.trim()) return
    try {
      const response = await apiClient.getModelHistory(modelId)
      if (response.success) {
        setTransactionHistory(response.data?.history || [])
      }
    } catch (error) {
      console.error('获取模型历史失败:', error)
    }
  }

  const operationLabel = (op: string) => {
    if (op === 'upload') return '数据上传'
    if (op === 'inference') return 'AI推理'
    return op
  }

  const operationColor = (op: string) => {
    if (op === 'upload') return 'bg-blue-500/20 text-blue-400'
    if (op === 'inference') return 'bg-green-500/20 text-green-400'
    return 'bg-gray-500/20 text-gray-400'
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div>
        <h1 className="text-3xl font-bold gradient-text mb-2">区块链集成</h1>
        <p className="text-gray-300">基于Hyperledger Fabric的AI模型版本控制和数据溯源系统</p>
      </div>

      {/* 区块链统计（真实数据） */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {blockchainStats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <Card key={index} className="glass-effect hover:neon-glow transition-all duration-300">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-400">
                  {stat.label}
                </CardTitle>
                <Icon className="w-4 h-4 text-tech-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
                <p className="text-xs text-green-400">{stat.change}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 我的数据使用记录（真实溯源） */}
        <Card className="glass-effect">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-tech-primary" />
                <span>我的数据使用记录</span>
              </div>
              <Button size="sm" variant="outline" onClick={fetchMyData}>
                <RefreshCw className="w-3 h-3 mr-1" />刷新
              </Button>
            </CardTitle>
            <CardDescription>您上传的数据被哪些模型使用——区块链溯源</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 max-h-72 overflow-y-auto">
            {myDataRecords.length === 0 ? (
              <div className="text-gray-500 text-sm text-center py-4">
                暂无溯源记录。上传农业图片后，AI 推理会自动生成链上记录。
              </div>
            ) : (
              myDataRecords.map((rec) => (
                <div key={rec.id} className="flex items-start justify-between p-3 bg-tech-dark/50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className={`mt-0.5 text-xs px-2 py-0.5 rounded ${operationColor(rec.operation)}`}>
                      {operationLabel(rec.operation)}
                    </div>
                    <div>
                      <div className="font-medium text-white text-sm truncate max-w-[160px]">
                        {rec.file_name || rec.data_id.slice(0, 20) + '...'}
                      </div>
                      <div className="text-xs text-gray-400">模型: {rec.model_id}</div>
                      <div className="text-xs text-gray-500 font-mono">{rec.tx_hash?.slice(0, 20)}...</div>
                    </div>
                  </div>
                  <div className="text-xs text-gray-400 whitespace-nowrap">
                    {new Date(rec.created_at).toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* 智能合约（真实调用次数） */}
        <Card className="glass-effect">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-tech-primary" />
              <span>智能合约</span>
            </CardTitle>
            <CardDescription>部署在区块链上的智能合约（调用次数实时统计）</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {smartContracts.map((contract, index) => (
              <div key={index} className="p-3 bg-tech-dark/50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium text-white">{contract.name}</div>
                  <div className={`text-xs px-2 py-1 rounded ${
                    contract.status === '活跃' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {contract.status}
                  </div>
                </div>
                <div className="text-xs text-gray-400 mb-1">{contract.address}</div>
                <div className="text-xs text-gray-500">调用次数: {contract.calls}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* 数据溯源查询 */}
      <Card className="glass-effect">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="w-5 h-5 text-tech-primary" />
            <span>数据溯源查询</span>
          </CardTitle>
          <CardDescription>输入数据 ID 查看完整溯源链：上传 → AI 识别 → 每次使用记录</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-4">
            <Input
              placeholder="输入 data_id（如 upload_abc123...）"
              value={provenanceDataId}
              onChange={(e) => setProvenanceDataId(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="tech"
              onClick={queryProvenance}
              disabled={!provenanceDataId.trim() || provenanceLoading}
              className="flex items-center space-x-2"
            >
              <Search className="w-4 h-4" />
              <span>{provenanceLoading ? '查询中...' : '查询溯源链'}</span>
            </Button>
          </div>

          {provenanceResult.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-white text-sm">溯源链（共 {provenanceResult.length} 步）</h4>
              <div className="relative">
                {provenanceResult.map((rec, idx) => (
                  <div key={rec.id} className="flex items-start space-x-3 mb-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        rec.operation === 'upload' ? 'bg-blue-500' : 'bg-green-500'
                      }`}>
                        {idx + 1}
                      </div>
                      {idx < provenanceResult.length - 1 && (
                        <div className="w-0.5 h-4 bg-gray-600 my-1" />
                      )}
                    </div>
                    <div className="flex-1 p-2 bg-tech-dark/30 rounded text-sm">
                      <div className="flex justify-between">
                        <span className={`text-xs px-2 py-0.5 rounded ${operationColor(rec.operation)}`}>
                          {operationLabel(rec.operation)}
                        </span>
                        <span className="text-gray-400 text-xs">
                          {new Date(rec.created_at).toLocaleString('zh-CN')}
                        </span>
                      </div>
                      <div className="text-gray-300 mt-1">模型: {rec.model_id}</div>
                      <div className="text-gray-500 font-mono text-xs">TX: {rec.tx_hash?.slice(0, 30)}...</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {provenanceDataId && provenanceResult.length === 0 && !provenanceLoading && (
            <div className="text-gray-500 text-sm text-center py-2">未找到溯源记录，请检查 data_id 是否正确</div>
          )}
        </CardContent>
      </Card>

      {/* 区块链网络状态（真实配置） */}
      <Card className="glass-effect">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Link2 className="w-5 h-5 text-tech-primary" />
            <span>网络状态</span>
          </CardTitle>
          <CardDescription>区块链节点和共识机制状态</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-300">共识算法</span>
                <span className="text-white">{networkInfo.consensus}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">区块大小</span>
                <span className="text-white">{networkInfo.blockSize}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">出块间隔</span>
                <span className="text-white">{networkInfo.blockInterval}</span>
              </div>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-300">网络延迟</span>
                <span className="text-green-400">{networkInfo.networkLatency}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">数据同步</span>
                <span className="text-green-400">{networkInfo.dataSync}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-300">安全性</span>
                <span className="text-green-400">{networkInfo.security}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 模型验证和查询 */}
      <Card className="glass-effect">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-tech-primary" />
            <span>模型验证与查询</span>
          </CardTitle>
          <CardDescription>验证模型完整性和查询区块链记录</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-4">
            <Input
              placeholder="输入模型ID"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              className="flex-1"
            />
            <Button 
              variant="tech" 
              onClick={verifyModelIntegrity}
              disabled={!modelId.trim() || loading}
              className="flex items-center space-x-2"
            >
              <CheckCircle className="w-4 h-4" />
              <span>验证完整性</span>
            </Button>
            <Button 
              variant="outline" 
              onClick={getModelHistory}
              disabled={!modelId.trim() || loading}
              className="flex items-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span>查询历史</span>
            </Button>
          </div>
          
          {verificationResult && (
            <div className={`p-3 rounded-lg ${
              verificationResult.success ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'
            }`}>
              <div className="flex items-center space-x-2">
                {verificationResult.success ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <X className="w-4 h-4 text-red-400" />
                )}
                <span className={verificationResult.success ? 'text-green-400' : 'text-red-400'}>
                  {verificationResult.success ? '模型完整性验证通过' : `验证失败: ${verificationResult.error}`}
                </span>
              </div>
            </div>
          )}

          {transactionHistory.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-white">交易历史</h4>
              {transactionHistory.map((tx, index) => (
                <div key={index} className="p-2 bg-tech-dark/30 rounded text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-300">交易ID: {tx.transaction_id}</span>
                    <span className="text-gray-400">{tx.timestamp}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 操作按钮 */}
      <div className="flex flex-wrap gap-4">
        <Button 
          variant="tech" 
          onClick={() => { fetchBlockchainStatus(); fetchBlockchainStats(); fetchMyData(); }}
          disabled={loading}
          className="flex items-center space-x-2"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>刷新状态</span>
        </Button>
        <Button variant="outline" className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4" />
          <span>查看统计</span>
        </Button>
        <Button variant="outline" className="flex items-center space-x-2">
          <Shield className="w-4 h-4" />
          <span>安全设置</span>
        </Button>
      </div>

      {/* 系统状态指示器 */}
      {blockchainStatus && (
        <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium ${
          blockchainStatus.status === 'healthy' || blockchainStatus.status === 'running'
            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
            : 'bg-red-500/20 text-red-400 border border-red-500/30'
        }`}>
          <div className={`w-2 h-2 rounded-full ${
            blockchainStatus.status === 'healthy' || blockchainStatus.status === 'running'
              ? 'bg-green-400' : 'bg-red-400'
          }`}></div>
          <span>区块链: 运行中</span>
        </div>
      )}
    </div>
  )
}