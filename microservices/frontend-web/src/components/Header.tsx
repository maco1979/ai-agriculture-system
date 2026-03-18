import React from 'react'
import { Link } from 'react-router-dom'

const Header: React.FC = () => {
  return (
    <header style={headerStyle}>
      <div style={headerContentStyle}>
        <h1 style={titleStyle}>AI农业平台</h1>
        <nav style={navStyle}>
          <ul style={navListStyle}>
            <li style={navItemStyle}>
              <Link to="/" style={navLinkStyle}>首页</Link>
            </li>
            <li style={navItemStyle}>
              <Link to="/dashboard" style={navLinkStyle}>仪表盘</Link>
            </li>
            <li style={navItemStyle}>
              <Link to="/monitoring" style={navLinkStyle}>监控</Link>
            </li>
            <li style={navItemStyle}>
              <Link to="/decision" style={navLinkStyle}>决策</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  )
}

// 样式
const headerStyle = {
  backgroundColor: '#ffffff',
  borderBottom: '1px solid #e0e0e0',
  padding: '12px 0',
  marginBottom: '24px'
}

const headerContentStyle = {
  maxWidth: '1200px',
  margin: '0 auto',
  padding: '0 24px',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center'
}

const titleStyle = {
  fontSize: '20px',
  fontWeight: '600',
  color: '#007bff',
  margin: 0
}

const navStyle = {
  margin: 0
}

const navListStyle = {
  listStyle: 'none',
  display: 'flex',
  gap: '24px',
  margin: 0,
  padding: 0
}

const navItemStyle = {
  margin: 0
}

const navLinkStyle = {
  color: '#333',
  textDecoration: 'none',
  fontSize: '14px',
  fontWeight: '500',
  transition: 'color 0.2s ease'
}

export default Header