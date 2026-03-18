import React from 'react';
import { render, screen } from '@testing-library/react';
import HomePage from './HomePage';

describe('HomePage Component', () => {
  test('renders HomePage component with title and description', () => {
    render(<HomePage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('Welcome to Microservices Dashboard');
    expect(titleElement).toBeInTheDocument();
    
    // Check if description is rendered
    const descriptionElement = screen.getByText('A modern, responsive dashboard for managing and monitoring microservices');
    expect(descriptionElement).toBeInTheDocument();
    
    // Check if feature cards are rendered
    const dashboardCard = screen.getByText('Dashboard');
    expect(dashboardCard).toBeInTheDocument();
    
    const decisionCard = screen.getByText('Decision Service');
    expect(decisionCard).toBeInTheDocument();
    
    const blockchainCard = screen.getByText('Blockchain Integration');
    expect(blockchainCard).toBeInTheDocument();
    
    const edgeCard = screen.getByText('Edge Computing');
    expect(edgeCard).toBeInTheDocument();
    
    const monitoringCard = screen.getByText('Monitoring');
    expect(monitoringCard).toBeInTheDocument();
  });
});
