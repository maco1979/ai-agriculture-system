import React from 'react'

const BlockchainPage: React.FC = () => {
  return (
    <div className="blockchain-page">
      <h1>区块链集成</h1>
      <p>查看和管理区块链上的数据和交易。</p>
      <div className="blockchain-sections">
        <div className="section">
          <h3>最近交易</h3>
          <table className="transaction-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>哈希</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2026-02-04 11:20</td>
                <td>数据上链</td>
                <td>0x1a2b3c...</td>
                <td>已确认</td>
              </tr>
              <tr>
                <td>2026-02-04 10:45</td>
                <td>智能合约</td>
                <td>0x4d5e6f...</td>
                <td>已确认</td>
              </tr>
              <tr>
                <td>2026-02-04 09:15</td>
                <td>数据上链</td>
                <td>0x7g8h9i...</td>
                <td>已确认</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default BlockchainPage