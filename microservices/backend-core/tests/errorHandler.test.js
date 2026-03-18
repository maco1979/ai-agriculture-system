import { AppError, errorHandler } from '../src/errors/errorHandler';

// 模拟console.error
jest.spyOn(console, 'error').mockImplementation();

describe('Error Handler Module', () => {
  describe('AppError Class', () => {
    test('should create an instance with default values', () => {
      const message = 'Test error';
      const statusCode = 400;
      const error = new AppError(message, statusCode);
      
      expect(error).toBeInstanceOf(Error);
      expect(error.message).toBe(message);
      expect(error.statusCode).toBe(statusCode);
      expect(error.status).toBe('fail');
      expect(error.isOperational).toBe(true);
      expect(error.stack).toBeDefined();
    });

    test('should create an instance with custom isOperational', () => {
      const message = 'Test error';
      const statusCode = 500;
      const isOperational = false;
      const error = new AppError(message, statusCode, isOperational);
      
      expect(error.isOperational).toBe(false);
      expect(error.status).toBe('error');
    });

    test('should create an instance with custom stack', () => {
      const message = 'Test error';
      const statusCode = 400;
      const customStack = 'Custom stack trace';
      const error = new AppError(message, statusCode, true, customStack);
      
      expect(error.stack).toBe(customStack);
    });

    test('should set status to "error" for 5xx status codes', () => {
      const message = 'Test error';
      const statusCode = 500;
      const error = new AppError(message, statusCode);
      
      expect(error.status).toBe('error');
    });

    test('should set status to "fail" for 4xx status codes', () => {
      const message = 'Test error';
      const statusCode = 404;
      const error = new AppError(message, statusCode);
      
      expect(error.status).toBe('fail');
    });
  });

  describe('errorHandler Middleware', () => {
    let req, res, next;

    beforeEach(() => {
      req = {};
      res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };
      next = jest.fn();
      jest.clearAllMocks();
    });

    test('should handle development environment errors', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      const err = new AppError('Test error', 400);
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        error: err,
        message: 'Test error',
        stack: err.stack
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle production environment errors for operational errors', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      const err = new AppError('Test error', 400);
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        message: 'Test error'
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle production environment errors for non-operational errors', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      const err = new AppError('Test error', 500, false);
      
      errorHandler(err, req, res, next);
      
      expect(console.error).toHaveBeenCalledWith('ERROR 💥', expect.objectContaining({
        message: 'Test error',
        statusCode: 500,
        status: 'error',
        isOperational: false
      }));
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        message: 'An unexpected error occurred'
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle CastError', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      const err = {
        name: 'CastError',
        message: 'Cast to ObjectId failed',
        path: '_id',
        value: 'invalid-id'
      };
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        message: 'Invalid _id: invalid-id.'
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle ValidationError', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      const err = {
        name: 'ValidationError',
        message: 'Validation failed',
        errors: {
          field1: { message: 'Field1 is required' },
          field2: { message: 'Field2 is invalid' }
        }
      };
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        message: 'Invalid input data. Field1 is required. Field2 is invalid'
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle duplicate fields error', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'production';
      
      const err = {
        code: 11000,
        errmsg: 'E11000 duplicate key error collection: test.users index: email_1 dup key: { email: "test@example.com" }'
      };
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(400);
      expect(res.json).toHaveBeenCalledWith({
        status: 'fail',
        message: 'Duplicate field value: test@example.com. Please use another value.'
      });
      
      process.env.NODE_ENV = originalEnv;
    });

    test('should handle errors with no status code', () => {
      const originalEnv = process.env.NODE_ENV;
      process.env.NODE_ENV = 'development';
      
      const err = new Error('Test error');
      
      errorHandler(err, req, res, next);
      
      expect(res.status).toHaveBeenCalledWith(500);
      expect(res.json).toHaveBeenCalledWith({
        status: 'error',
        error: err,
        message: 'Test error',
        stack: err.stack
      });
      
      process.env.NODE_ENV = originalEnv;
    });
  });
});
