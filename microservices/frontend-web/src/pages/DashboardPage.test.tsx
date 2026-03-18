import React from 'react';
import { render, screen } from '@testing-library/react';
import DashboardPage from './DashboardPage';

describe('DashboardPage Component', () => {
  test('renders DashboardPage component with title and service status cards', () => {
    render(<DashboardPage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('Service Dashboard');
    expect(titleElement).toBeInTheDocument();
    
    // Check if service status cards are rendered
    const apiGatewayCard = screen.getByText('API Gateway');
    expect(apiGatewayCard).toBeInTheDocument();
    
    const decisionServiceCard = screen.getByText('Decision Service');
    expect(decisionServiceCard).toBeInTheDocument();
    
    const blockchainCard = screen.getByText('Blockchain Integration');
    expect(blockchainCard).toBeInTheDocument();
    
    const edgeCard = screen.getByText('Edge Computing');
    expect(edgeCard).toBeInTheDocument();
    
    const monitoringCard = screen.getByText('Monitoring Service');
    expect(monitoringCard).toBeInTheDocument();
  });
});
