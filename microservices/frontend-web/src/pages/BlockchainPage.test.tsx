import React from 'react';
import { render, screen } from '@testing-library/react';
import BlockchainPage from './BlockchainPage';

describe('BlockchainPage Component', () => {
  test('renders BlockchainPage component with title and form', () => {
    render(<BlockchainPage />);
    
    // Check if title is rendered
    const titleElement = screen.getByText('Blockchain Integration');
    expect(titleElement).toBeInTheDocument();
    
    // Check if form elements are rendered
    const transactionLabel = screen.getByText('Transaction Data:');
    expect(transactionLabel).toBeInTheDocument();
    
    const submitButton = screen.getByText('Submit Transaction');
    expect(submitButton).toBeInTheDocument();
  });
});
