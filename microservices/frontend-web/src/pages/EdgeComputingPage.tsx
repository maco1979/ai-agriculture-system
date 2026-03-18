import React from 'react'

const EdgeComputingPage: React.FC = () => {
  return (
    <div className="edge-computing-page">
      <h1>边缘计算管理</h1>
      <p>管理和监控边缘计算节点的运行状态。</p>
      <div className="edge-sections">
        <div className="section">
          <h3>边缘节点</h3>
          <ul className="node-list">
            <li className="node-item active">
              <span className="node-name">Node-001</span>
              <span className="node-status">在线</span>
              <span className="node-cpu">CPU: 35%</span>
            </li>
            <li className="node-item active">
              <span className="node-name">Node-002</span>
              <span className="node-status">在线</span>
              <span className="node-cpu">CPU: 28%</span>
            </li>
            <li className="node-item">
              <span className="node-name">Node-003</span>
              <span className="node-status">离线</span>
              <span className="node-cpu">CPU: 0%</span>
            </li>
          </ul>
        </div>
        <div className="section">
          <h3>任务管理</h3>
          <div className="task-list">
            <div className="task-item">
              <span className="task-name">数据采集</span>
              <span className="task-status">运行中</span>
              <span className="task-node">Node-001</span>
            </div>
            <div className="task-item">
              <span className="task-name">模型推理</span>
              <span className="task-status">运行中</span>
              <span className="task-node">Node-002</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EdgeComputingPage