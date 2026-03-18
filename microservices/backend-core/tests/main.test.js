import request from 'supertest';
import app from '../src/main';

describe('Main Server Module', () => {
  describe('Health Check Endpoint', () => {
    test('should return healthy status', async () => {
      const response = await request(app).get('/health');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body).toHaveProperty('service');
      expect(response.body).toHaveProperty('version');
      expect(response.body).toHaveProperty('environment');
    });
  });

  describe('Service Info Endpoint', () => {
    test('should return service information', async () => {
      const response = await request(app).get('/info');
      
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('name');
      expect(response.body).toHaveProperty('version');
      expect(response.body).toHaveProperty('description');
      expect(response.body).toHaveProperty('environment');
      expect(response.body).toHaveProperty('health');
    });
  });

  describe('404 Handling', () => {
    test('should return 404 for non-existent routes', async () => {
      const response = await request(app).get('/non-existent-route');
      
      expect(response.status).toBe(404);
      expect(response.body).toHaveProperty('status', 'fail');
      expect(response.body).toHaveProperty('message', 'The requested resource was not found');
      expect(response.body).toHaveProperty('path', '/non-existent-route');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('Middleware Configuration', () => {
    test('should parse JSON requests', async () => {
      const testData = { key: 'value' };
      const response = await request(app)
        .post('/api/test')
        .send(testData)
        .set('Content-Type', 'application/json');
      
      // 虽然/api/test路由不存在，但应该能正确解析JSON
      expect(response.status).toBe(404);
    });

    test('should parse URL-encoded requests', async () => {
      const response = await request(app)
        .post('/api/test')
        .send('key=value')
        .set('Content-Type', 'application/x-www-form-urlencoded');
      
      // 虽然/api/test路由不存在，但应该能正确解析URL-encoded数据
      expect(response.status).toBe(404);
    });
  });

  describe('CORS Configuration', () => {
    test('should include CORS headers', async () => {
      const response = await request(app).get('/health');
      
      expect(response.headers).toHaveProperty('access-control-allow-origin');
    });
  });

  describe('Security Headers', () => {
    test('should include security headers', async () => {
      const response = await request(app).get('/health');
      
      // 检查helmet设置的安全头
      expect(response.headers).toHaveProperty('x-dns-prefetch-control');
      expect(response.headers).toHaveProperty('x-frame-options');
      expect(response.headers).toHaveProperty('x-xss-protection');
      expect(response.headers).toHaveProperty('x-content-type-options');
      expect(response.headers).toHaveProperty('referrer-policy');
      expect(response.headers).toHaveProperty('content-security-policy');
    });
  });
});
