import React from 'react';
import { render, screen } from '@testing-library/react';
import DecisionPage from './DecisionPage';

describe('DecisionPage Component', () => {
  test('renders DecisionPage component with title and form', () => {
    render(<DecisionPage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('Decision Service');
    expect(titleElement).toBeInTheDocument();
    
    // Check if form elements are rendered
    const amountLabel = screen.getByText('Amount:');
    expect(amountLabel).toBeInTheDocument();
    
    const riskLabel = screen.getByText('Risk Level:');
    expect(riskLabel).toBeInTheDocument();
    
    const submitButton = screen.getByText('Make Decision');
    expect(submitButton).toBeInTheDocument();
  });
});
