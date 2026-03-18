import React from 'react'

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      <h1>欢迎来到智能农业决策系统</h1>
      <p>这是系统的主页面，您可以从左侧导航栏访问各个功能模块。</p>
      <div className="feature-grid">
        <div className="feature-card">
          <h3>数据监控</h3>
          <p>实时监控农场数据和设备状态</p>
        </div>
        <div className="feature-card">
          <h3>智能决策</h3>
          <p>基于AI的农业生产决策支持</p>
        </div>
        <div className="feature-card">
          <h3>边缘计算</h3>
          <p>高效的本地数据处理和分析</p>
        </div>
        <div className="feature-card">
          <h3>区块链集成</h3>
          <p>安全透明的数据存储和交易</p>
        </div>
      </div>
    </div>
  )
}

export default HomePage