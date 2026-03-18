// 加密工具函数，用于安全存储API密钥

/**
 * 加密字符串
 * @param text 需要加密的文本
 * @returns 加密后的文本
 */
export function encrypt(text: string): string {
  try {
    // 使用简单的加密算法，实际项目中可以使用更复杂的加密方法
    const encoded = btoa(unescape(encodeURIComponent(text)));
    // 添加随机字符混淆
    const salt = Math.random().toString(36).substring(2, 8);
    const encrypted = salt + encoded.split('').reverse().join('') + salt;
    return encrypted;
  } catch (error) {
    console.error('加密失败:', error);
    return text;
  }
}

/**
 * 解密字符串
 * @param encryptedText 加密后的文本
 * @returns 解密后的文本
 */
export function decrypt(encryptedText: string): string {
  try {
    // 移除盐值
    const saltLength = 6;
    if (encryptedText.length < saltLength * 2) {
      return encryptedText;
    }

    const encoded = encryptedText.substring(saltLength, encryptedText.length - saltLength);
    const reversed = encoded.split('').reverse().join('');
    const decoded = decodeURIComponent(escape(atob(reversed)));
    return decoded;
  } catch (error) {
    console.error('解密失败:', error);
    return encryptedText;
  }
}

/**
 * 安全存储模型API密钥
 * @param keys 模型API密钥列表
 */
export function saveEncryptedModelApiKeys(keys: any[]): void {
  try {
    const encryptedKeys = keys.map(key => ({
      ...key,
      apiKey: key.apiKey ? encrypt(key.apiKey) : '',
    }));
    localStorage.setItem('modelApiKeys', JSON.stringify(encryptedKeys));
  } catch (error) {
    console.error('保存加密模型API密钥失败:', error);
  }
}

/**
 * 获取解密后的模型API密钥
 * @returns 解密后的模型API密钥列表
 */
export function getDecryptedModelApiKeys(): any[] {
  try {
    const keys = localStorage.getItem('modelApiKeys');
    if (!keys) {
      return [];
    }

    const encryptedKeys = JSON.parse(keys);
    return encryptedKeys.map((key: any) => ({
      ...key,
      apiKey: key.apiKey ? decrypt(key.apiKey) : '',
    }));
  } catch (error) {
    console.error('获取解密模型API密钥失败:', error);
    return [];
  }
}

/**
 * 掩码处理API密钥，用于显示
 * @param apiKey API密钥
 * @returns 掩码处理后的API密钥
 */
export function maskApiKey(apiKey: string): string {
  if (!apiKey || apiKey.length < 8) {
    return apiKey;
  }

  const prefix = apiKey.substring(0, 4);
  const suffix = apiKey.substring(apiKey.length - 4);
  const maskLength = apiKey.length - 8;
  const mask = '*'.repeat(Math.min(maskLength, 12));

  return `${prefix}${mask}${suffix}`;
}
