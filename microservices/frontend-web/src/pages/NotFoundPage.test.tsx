import React from 'react';
import { render, screen } from '@testing-library/react';
import NotFoundPage from './NotFoundPage';

describe('NotFoundPage Component', () => {
  test('renders NotFoundPage component with error message', () => {
    render(<NotFoundPage />);
    
    // Check if error message is rendered
    const errorElement = screen.getByText('404 - Page Not Found');
    expect(errorElement).toBeInTheDocument();
    
    // Check if description is rendered
    const descriptionElement = screen.getByText('The page you are looking for does not exist.');
    expect(descriptionElement).toBeInTheDocument();
  });
});
