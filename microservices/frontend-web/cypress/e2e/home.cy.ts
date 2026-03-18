describe('Home Page', () => {
  it('should load home page successfully', () => {
    cy.visit('/');
    cy.contains('Welcome to Microservices Dashboard').should('be.visible');
    cy.contains('A modern, responsive dashboard for managing and monitoring microservices').should('be.visible');
  });

  it('should have navigation links', () => {
    cy.visit('/');
    cy.contains('Dashboard').should('be.visible');
    cy.contains('Decision Service').should('be.visible');
    cy.contains('Blockchain Integration').should('be.visible');
    cy.contains('Edge Computing').should('be.visible');
    cy.contains('Monitoring').should('be.visible');
  });
});
