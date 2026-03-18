import React from 'react';
import { render, screen } from '@testing-library/react';
import EdgeComputingPage from './EdgeComputingPage';

describe('EdgeComputingPage Component', () => {
  test('renders EdgeComputingPage component with title and form', () => {
    render(<EdgeComputingPage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('Edge Computing');
    expect(titleElement).toBeInTheDocument();
    
    // Check if form elements are rendered
    const dataLabel = screen.getByText('Sensor Data:');
    expect(dataLabel).toBeInTheDocument();
    
    const submitButton = screen.getByText('Process Data');
    expect(submitButton).toBeInTheDocument();
  });
});
