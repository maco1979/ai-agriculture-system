import { initMonitoring, trackPageView, trackEvent, trackError, trackPerformance } from './monitoring';

describe('Frontend Monitoring', () => {
  beforeEach(() => {
    // Mock console.log to avoid cluttering test output
    jest.spyOn(console, 'log').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initMonitoring initializes monitoring successfully', () => {
    expect(() => initMonitoring()).not.toThrow();
  });

  test('trackPageView tracks page views successfully', () => {
    expect(() => trackPageView('/test')).not.toThrow();
  });

  test('trackEvent tracks events successfully', () => {
    expect(() => trackEvent('test-event', { action: 'click' })).not.toThrow();
  });

  test('trackError tracks errors successfully', () => {
    const error = new Error('Test error');
    expect(() => trackError(error, { component: 'TestComponent' })).not.toThrow();
  });

  test('trackPerformance tracks performance metrics successfully', () => {
    expect(() => trackPerformance('test-metric', 100)).not.toThrow();
  });
});
