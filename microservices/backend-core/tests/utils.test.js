import {
  generateId,
  formatResponse,
  formatError,
  validateBody,
  validateParams,
  delay,
  isValidJson,
  safeParseJson,
  generateRandomString,
  formatTimestamp,
  measureExecutionTime
} from '../src/utils/utils';

describe('Utils Module', () => {
  describe('generateId', () => {
    test('should generate a non-empty string', () => {
      const id = generateId();
      expect(typeof id).toBe('string');
      expect(id.length).toBeGreaterThan(0);
    });

    test('should generate unique IDs', () => {
      const id1 = generateId();
      const id2 = generateId();
      expect(id1).not.toBe(id2);
    });
  });

  describe('formatResponse', () => {
    test('should format response with default values', () => {
      const data = { key: 'value' };
      const response = formatResponse(data);
      
      expect(response).toEqual({
        status: 'success',
        message: 'Success',
        data,
        timestamp: expect.any(String)
      });
    });

    test('should format response with custom message', () => {
      const data = { key: 'value' };
      const message = 'Custom message';
      const response = formatResponse(data, message);
      
      expect(response.message).toBe(message);
    });

    test('should format response with custom status', () => {
      const data = { key: 'value' };
      const status = 'custom';
      const response = formatResponse(data, 'Message', status);
      
      expect(response.status).toBe(status);
    });
  });

  describe('formatError', () => {
    test('should format error with default values', () => {
      const message = 'Error message';
      const error = formatError(message);
      
      expect(error).toEqual({
        status: 'error',
        message,
        code: 500,
        timestamp: expect.any(String)
      });
    });

    test('should format error with custom status', () => {
      const message = 'Error message';
      const status = 'custom';
      const error = formatError(message, status);
      
      expect(error.status).toBe(status);
    });

    test('should format error with custom code', () => {
      const message = 'Error message';
      const code = 400;
      const error = formatError(message, 'error', code);
      
      expect(error.code).toBe(code);
    });
  });

  describe('validateBody', () => {
    test('should return invalid for empty body', () => {
      const result = validateBody(null, ['field1']);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Request body is required');
    });

    test('should return valid for body with all required fields', () => {
      const body = { field1: 'value1', field2: 'value2' };
      const requiredFields = ['field1', 'field2'];
      const result = validateBody(body, requiredFields);
      expect(result.valid).toBe(true);
    });

    test('should return invalid for body missing required fields', () => {
      const body = { field1: 'value1' };
      const requiredFields = ['field1', 'field2'];
      const result = validateBody(body, requiredFields);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Missing required fields: field2');
    });

    test('should return valid for empty required fields array', () => {
      const body = { field1: 'value1' };
      const result = validateBody(body, []);
      expect(result.valid).toBe(true);
    });
  });

  describe('validateParams', () => {
    test('should return invalid for empty params', () => {
      const result = validateParams(null, ['param1']);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Request parameters are required');
    });

    test('should return valid for params with all required parameters', () => {
      const params = { param1: 'value1', param2: 'value2' };
      const requiredParams = ['param1', 'param2'];
      const result = validateParams(params, requiredParams);
      expect(result.valid).toBe(true);
    });

    test('should return invalid for params missing required parameters', () => {
      const params = { param1: 'value1' };
      const requiredParams = ['param1', 'param2'];
      const result = validateParams(params, requiredParams);
      expect(result.valid).toBe(false);
      expect(result.message).toBe('Missing required parameters: param2');
    });

    test('should return valid for empty required parameters array', () => {
      const params = { param1: 'value1' };
      const result = validateParams(params, []);
      expect(result.valid).toBe(true);
    });
  });

  describe('delay', () => {
    test('should resolve after specified time', async () => {
      const delayTime = 100;
      const start = Date.now();
      await delay(delayTime);
      const end = Date.now();
      expect(end - start).toBeGreaterThanOrEqual(delayTime);
    });
  });

  describe('isValidJson', () => {
    test('should return true for valid JSON string', () => {
      const validJson = '{"key": "value"}';
      expect(isValidJson(validJson)).toBe(true);
    });

    test('should return false for invalid JSON string', () => {
      const invalidJson = '{"key": "value"';
      expect(isValidJson(invalidJson)).toBe(false);
    });
  });

  describe('safeParseJson', () => {
    test('should parse valid JSON string', () => {
      const validJson = '{"key": "value"}';
      const result = safeParseJson(validJson);
      expect(result).toEqual({ key: 'value' });
    });

    test('should return default value for invalid JSON string', () => {
      const invalidJson = '{"key": "value"';
      const defaultValue = { default: 'value' };
      const result = safeParseJson(invalidJson, defaultValue);
      expect(result).toEqual(defaultValue);
    });

    test('should return empty object for invalid JSON string with no default', () => {
      const invalidJson = '{"key": "value"';
      const result = safeParseJson(invalidJson);
      expect(result).toEqual({});
    });
  });

  describe('generateRandomString', () => {
    test('should generate string with default length', () => {
      const result = generateRandomString();
      expect(typeof result).toBe('string');
      expect(result.length).toBe(10);
    });

    test('should generate string with custom length', () => {
      const length = 5;
      const result = generateRandomString(length);
      expect(typeof result).toBe('string');
      expect(result.length).toBe(length);
    });
  });

  describe('formatTimestamp', () => {
    test('should format timestamp to ISO string', () => {
      const timestamp = Date.now();
      const result = formatTimestamp(timestamp);
      expect(typeof result).toBe('string');
      expect(new Date(result).getTime()).toBeCloseTo(timestamp, -3);
    });
  });

  describe('measureExecutionTime', () => {
    test('should measure execution time of function', () => {
      const fn = () => {
        let sum = 0;
        for (let i = 0; i < 100000; i++) {
          sum += i;
        }
        return sum;
      };
      
      const result = measureExecutionTime(fn);
      expect(result).toHaveProperty('result');
      expect(result).toHaveProperty('executionTime');
      expect(typeof result.executionTime).toBe('number');
      expect(result.executionTime).toBeGreaterThanOrEqual(0);
    });
  });
});
