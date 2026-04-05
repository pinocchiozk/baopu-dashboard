#!/usr/bin/env node
/**
 * prompt-hygiene - 输入安全过滤脚本
 * 
 * 从Claude Code源码泄露事件中学到的安全实践
 * 用于过滤可能的prompt注入攻击
 */

const fs = require('fs');

// 高危模式 - 直接拦截
const HIGH_RISK_PATTERNS = [
  /^(你是一个?|你现在是|从现在起你是)/im,
  /^(ignore\s+(all\s+)?previous|reset\s+prompt)/im,
  /^(CRITICAL[:：]|系统指令)/m,
  /\[SYSTEM\]|### SYSTEM|SYSTEM:/im,
  /base64[\s:]*[A-Za-z0-9+/=]{50,}/,
];

// 中危模式 - 告警提示
const MEDIUM_RISK_PATTERNS = [
  /https?:\/\/[^\s]+/gi,
  /curl\s+|wget\s+/i,
  /<[a-z]+[^>]*>/gi,
  /\S{500,}/,
];

/**
 * 过滤函数
 * @param {string} content - 待检测内容
 * @returns {object} - {blocked: boolean, warning: boolean, reason: string}
 */
function filter(content) {
  // 取前50000字符（防止过大输入）
  const checkContent = content.slice(0, 50000);
  
  // 检查高危模式
  for (const pattern of HIGH_RISK_PATTERNS) {
    if (pattern.test(checkContent)) {
      return {
        blocked: true,
        warning: false,
        reason: `High-risk pattern matched: ${pattern}`
      };
    }
  }
  
  // 检查中危模式
  for (const pattern of MEDIUM_RISK_PATTERNS) {
    if (pattern.test(checkContent)) {
      return {
        blocked: false,
        warning: true,
        reason: `Warning pattern matched: ${pattern}`
      };
    }
  }
  
  return {
    blocked: false,
    warning: false,
    reason: 'Clean'
  };
}

// CLI入口
if (require.main === module) {
  const input = fs.readFileSync('/dev/stdin', 'utf8');
  const result = filter(input);
  
  if (result.blocked) {
    console.error('[BLOCKED]', result.reason);
    process.exit(1);
  }
  if (result.warning) {
    console.warn('[WARNING]', result.reason);
    process.exit(2);
  }
  console.log('[CLEAN]');
  process.exit(0);
}

module.exports = { filter };
