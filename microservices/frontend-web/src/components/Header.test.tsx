import React from 'react';
import { render, screen } from '@testing-library/react';
import Header from './Header';

jest.mock('react-router-dom', () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  )
}));

describe('Header Component', () => {
  test('renders Header component with logo and navigation links', () => {
    render(<Header />);
    
    // Check if logo is rendered
    const logoElement = screen.getByText('Microservices Dashboard');
    expect(logoElement).toBeInTheDocument();
    
    // Check if navigation links are rendered
    const dashboardLink = screen.getByText('Dashboard');
    expect(dashboardLink).toBeInTheDocument();
    expect(dashboardLink).toHaveAttribute('href', '/dashboard');
    
    const decisionLink = screen.getByText('Decision');
    expect(decisionLink).toBeInTheDocument();
    expect(decisionLink).toHaveAttribute('href', '/decision');
    
    const blockchainLink = screen.getByText('Blockchain');
    expect(blockchainLink).toBeInTheDocument();
    expect(blockchainLink).toHaveAttribute('href', '/blockchain');
    
    const edgeLink = screen.getByText('Edge');
    expect(edgeLink).toBeInTheDocument();
    expect(edgeLink).toHaveAttribute('href', '/edge');
    
    const monitoringLink = screen.getByText('Monitoring');
    expect(monitoringLink).toBeInTheDocument();
    expect(monitoringLink).toHaveAttribute('href', '/monitoring');
  });
});
