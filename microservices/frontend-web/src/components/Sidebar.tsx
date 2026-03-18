import React from 'react'
import { Link, useLocation } from 'react-router-dom'

const Sidebar: React.FC = () => {
  const location = useLocation()
  
  const menuItems = [
    { path: '/', label: '首页', icon: '🏠' },
    { path: '/dashboard', label: '仪表盘', icon: '📊' },
    { path: '/monitoring', label: '监控', icon: '🔍' },
    { path: '/decision', label: '决策', icon: '🎯' },
    { path: '/edge-computing', label: '边缘计算', icon: '🌐' },
    { path: '/blockchain', label: '区块链', icon: '⛓️' }
  ]

  return (
    <aside style={sidebarStyle}>
      <div style={sidebarHeaderStyle}>
        <h2 style={sidebarTitleStyle}>导航菜单</h2>
      </div>
      <nav style={sidebarNavStyle}>
        <ul style={sidebarListStyle}>
          {menuItems.map((item) => (
            <li key={item.path} style={sidebarItemStyle}>
              <Link 
                to={item.path} 
                style={{
                  ...sidebarLinkStyle,
                  ...(location.pathname === item.path ? activeLinkStyle : {})
                }}
              >
                <span style={iconStyle}>{item.icon}</span>
                <span style={labelStyle}>{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}

// 样式
const sidebarStyle = {
  width: '240px',
  backgroundColor: '#ffffff',
  borderRight: '1px solid #e0e0e0',
  position: 'fixed' as 'fixed',
  top: 0,
  left: 0,
  height: '100vh',
  overflowY: 'auto' as 'auto',
  transition: 'width 0.3s ease'
}

const sidebarHeaderStyle = {
  padding: '24px',
  borderBottom: '1px solid #f0f0f0'
}

const sidebarTitleStyle = {
  fontSize: '16px',
  fontWeight: '600',
  margin: 0,
  color: '#333'
}

const sidebarNavStyle = {
  padding: '16px 0'
}

const sidebarListStyle = {
  listStyle: 'none',
  padding: 0,
  margin: 0
}

const sidebarItemStyle = {
  margin: 0
}

const sidebarLinkStyle = {
  display: 'flex',
  alignItems: 'center',
  padding: '12px 24px',
  color: '#666',
  textDecoration: 'none',
  transition: 'all 0.2s ease'
}

const activeLinkStyle = {
  backgroundColor: '#f0f8ff',
  color: '#007bff',
  fontWeight: '500'
}

const iconStyle = {
  marginRight: '12px',
  fontSize: '16px'
}

const labelStyle = {
  fontSize: '14px'
}

export default Sidebar