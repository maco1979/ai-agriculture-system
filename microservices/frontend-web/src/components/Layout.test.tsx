import React from 'react';
import { render, screen } from '@testing-library/react';
import Layout from './Layout';

jest.mock('./Header', () => () => <div data-testid="header">Header</div>);
jest.mock('./Sidebar', () => () => <div data-testid="sidebar">Sidebar</div>);

describe('Layout Component', () => {
  test('renders Layout component with Header, Sidebar, and children', () => {
    const testContent = 'Test Content';
    
    render(
      <Layout>
        <div>{testContent}</div>
      </Layout>
    );
    
    // Check if Header is rendered
    const headerElement = screen.getByTestId('header');
    expect(headerElement).toBeInTheDocument();
    
    // Check if Sidebar is rendered
    const sidebarElement = screen.getByTestId('sidebar');
    expect(sidebarElement).toBeInTheDocument();
    
    // Check if children are rendered
    const contentElement = screen.getByText(testContent);
    expect(contentElement).toBeInTheDocument();
  });
});
