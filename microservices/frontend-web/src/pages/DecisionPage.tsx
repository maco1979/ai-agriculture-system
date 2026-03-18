import React from 'react'

const DecisionPage: React.FC = () => {
  return (
    <div className="decision-page">
      <h1>智能决策中心</h1>
      <p>基于AI的农业生产决策支持系统。</p>
      <div className="decision-sections">
        <div className="section">
          <h3>决策历史</h3>
          <table className="decision-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>类型</th>
                <th>结果</th>
                <th>状态</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>2026-02-04 10:30</td>
                <td>灌溉决策</td>
                <td>建议灌溉</td>
                <td>已执行</td>
              </tr>
              <tr>
                <td>2026-02-04 08:15</td>
                <td>施肥决策</td>
                <td>建议施肥</td>
                <td>已执行</td>
              </tr>
              <tr>
                <td>2026-02-03 16:45</td>
                <td>病虫害防治</td>
                <td>无需防治</td>
                <td>已确认</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default DecisionPage