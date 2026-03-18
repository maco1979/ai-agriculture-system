import React from 'react';
import { render, screen } from '@testing-library/react';
import Sidebar from './Sidebar';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  )
}));

describe('Sidebar Component', () => {
  test('renders Sidebar component with navigation links', () => {
    render(<Sidebar />);
    
    // Check if navigation links are rendered
    const homeLink = screen.getByText('Home');
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute('href', '/');
    
    const dashboardLink = screen.getByText('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    
    const decisionLink = screen.getByText('Decision Service');
    expect(decisionLink).toBeInTheDocument();
    expect(decisionLink).toHaveAttribute('href', '/decision');
    
    const blockchainLink = screen.getByText('Blockchain');
    expect(blockchainLink).toBeInTheDocument();
    expect(blockchainLink).toHaveAttribute('href', '/blockchain');
    
    const edgeLink = screen.getByText('Edge Computing');
    expect(edgeLink).toBeInTheDocument();
    expect(edgeLink).toHaveAttribute('href', '/edge');
    
    const monitoringLink = screen.getByText('Monitoring');
    expect(monitoringLink).toBeInTheDocument();
    expect(monitoringLink).toHaveAttribute('href', '/monitoring');
  });
});
