// 保存原始的 NODE_ENV
const originalNodeEnv = process.env.NODE_ENV;

// 直接设置 NODE_ENV 为 development
process.env.NODE_ENV = 'development';

import request from 'supertest';
import app from '../src/main.js';

// 在测试结束后恢复原始的 NODE_ENV
afterAll(() => {
  process.env.NODE_ENV = originalNodeEnv;
});

describe('Decision Service Main Module', () => {
  describe('Health Check Endpoint', () => {
    test('should return 200 for health check', async () => {
      const response = await request(app).get('/health');
      expect(response.status).toBe(200);
      expect(response.body.status).toBe('healthy');
      expect(response.body.service).toBe('decision-service');
      expect(response.body.version).toBe('1.0.0');
    });
  });

  describe('Service Info Endpoint', () => {
    test('should return 200 for service info', async () => {
      const response = await request(app).get('/info');
      expect(response.status).toBe(200);
      expect(response.body.name).toBe('decision-service');
      expect(response.body.version).toBe('1.0.0');
      expect(response.body.description).toBe('Decision service for AI-powered decision making');
    });
  });

  describe('Decision Making Endpoint', () => {
    test('should return 200 for valid decision request', async () => {
      const decisionRequest = {
        type: 'approval',
        data: {
          user_id: '123',
          amount: 1000,
          risk_score: 0.75
        }
      };

      const response = await request(app)
        .post('/api/decision/make')
        .send(decisionRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(200);
      expect(response.body.status).toBe('success');
      expect(response.body.message).toBe('Decision made successfully');
      expect(response.body.data.type).toBe('approval');
      expect(response.body.data.status).toBe('approved');
      expect(response.body.data.confidence).toBeDefined();
      expect(response.body.data.confidence).toBeGreaterThanOrEqual(0.7);
    });

    test('should return 400 for missing required fields', async () => {
      const decisionRequest = {
        data: {
          user_id: '123',
          amount: 1000
        }
      };

      const response = await request(app)
        .post('/api/decision/make')
        .send(decisionRequest)
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);
      expect(response.body.status).toBe('fail');
      expect(response.body.message).toBe('Missing required fields: type and data');
    });

    test('should return 400 for empty request body', async () => {
      const response = await request(app)
        .post('/api/decision/make')
        .send({})
        .set('Content-Type', 'application/json');

      expect(response.status).toBe(400);
      expect(response.body.status).toBe('fail');
      expect(response.body.message).toBe('Missing required fields: type and data');
    });
  });

  describe('404 Handling', () => {
    test('should return 404 for non-existent route', async () => {
      const response = await request(app).get('/non-existent-route');
      expect(response.status).toBe(404);
      expect(response.body.status).toBe('fail');
      expect(response.body.message).toBe('The requested resource was not found');
    });
  });
});
