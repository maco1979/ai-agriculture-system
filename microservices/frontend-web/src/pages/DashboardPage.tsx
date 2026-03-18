import React from 'react'

const DashboardPage: React.FC = () => {
  return (
    <div className="dashboard-page">
      <h1>系统仪表盘</h1>
      <p>这里显示系统的关键指标和状态信息。</p>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <h3>系统状态</h3>
          <p>所有服务运行正常</p>
        </div>
        <div className="dashboard-card">
          <h3>设备数量</h3>
          <p>24 台设备在线</p>
        </div>
        <div className="dashboard-card">
          <h3>数据采集</h3>
          <p>每小时 1,200 条记录</p>
        </div>
        <div className="dashboard-card">
          <h3>AI 决策</h3>
          <p>今日 48 次决策</p>
        </div>
      </div>
    </div>
  )
}

export default DashboardPage