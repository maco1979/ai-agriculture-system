import React from 'react'

const MonitoringPage: React.FC = () => {
  return (
    <div className="monitoring-page">
      <h1>监控中心</h1>
      <p>实时监控系统各组件的运行状态和性能指标。</p>
      <div className="monitoring-sections">
        <div className="section">
          <h3>服务状态</h3>
          <ul className="service-list">
            <li className="service-item active">API Gateway</li>
            <li className="service-item active">Backend Core</li>
            <li className="service-item active">Decision Service</li>
            <li className="service-item active">Edge Computing</li>
            <li className="service-item active">Blockchain Integration</li>
          </ul>
        </div>
        <div className="section">
          <h3>性能指标</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <span className="metric-name">响应时间</span>
              <span className="metric-value">23ms</span>
            </div>
            <div className="metric-item">
              <span className="metric-name">CPU 使用率</span>
              <span className="metric-value">45%</span>
            </div>
            <div className="metric-item">
              <span className="metric-name">内存使用</span>
              <span className="metric-value">60%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MonitoringPage