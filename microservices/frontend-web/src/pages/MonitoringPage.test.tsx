import React from 'react';
import { render, screen } from '@testing-library/react';
import MonitoringPage from './MonitoringPage';

describe('MonitoringPage Component', () => {
  test('renders MonitoringPage component with title and metrics', () => {
    render(<MonitoringPage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('System Monitoring');
    expect(titleElement).toBeInTheDocument();
    
    // Check if metrics sections are rendered
    const systemMetrics = screen.getByText('System Metrics');
    expect(systemMetrics).toBeInTheDocument();
    
    const serviceMetrics = screen.getByText('Service Metrics');
    expect(serviceMetrics).toBeInTheDocument();
  });
});
