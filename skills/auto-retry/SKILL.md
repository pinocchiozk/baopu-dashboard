# Auto-Retry Skill

基于 claw-code 的 recovery_recipes.rs 设计，自动重试机制。

## 核心原则

```
known failure → auto-heal once → then escalate
```

不要让失败立即上报，先自动恢复一次。

## 重试策略

### 1. 幂等锁 + 超时

```javascript
const LOCK_DIR = '/tmp/openclaw/locks/';
const LOCK_TIMEOUT = 300; // 秒

function acquireLock(name) {
  const lockFile = `${LOCK_DIR}${name}.lock`;
  const pid = process.pid;
  const timestamp = Date.now();
  
  // 检查是否存在
  if (fs.existsSync(lockFile)) {
    const content = fs.readFileSync(lockFile, 'utf8').split('\n');
    const [oldPid, oldTime] = content;
    const oldTimestamp = parseInt(oldTime);
    
    // 超时释放
    if (Date.now() - oldTimestamp > LOCK_TIMEOUT * 1000) {
      fs.unlinkSync(lockFile);
    } else if (parseInt(oldPid) !== pid) {
      return false; // 被其他进程持有
    }
  }
  
  // 获取锁
  fs.writeFileSync(lockFile, `${pid}\n${timestamp}`);
  return true;
}

function releaseLock(name) {
  const lockFile = `${LOCK_DIR}${name}.lock`;
  if (fs.existsSync(lockFile)) {
    fs.unlinkSync(lockFile);
  }
}
```

### 2. 自动重试装饰器

```javascript
async function withAutoRetry(fn, options = {}) {
  const {
    maxRetries = 1,
    retryDelay = 1000,
    retryableErrors = ['ECONNRESET', 'ETIMEDOUT', 'ENOTFOUND'],
    onRetry = null
  } = options;
  
  let lastError;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // 判断是否可重试
      const isRetryable = retryableErrors.some(e => 
        error.message?.includes(e)
      );
      
      if (!isRetryable || attempt >= maxRetries) {
        break;
      }
      
      // 重试前回调
      if (onRetry) {
        onRetry(attempt + 1, error);
      }
      
      await new Promise(r => setTimeout(r, retryDelay * (attempt + 1)));
    }
  }
  
  throw lastError;
}
```

### 3. 恢复食谱（Recovery Recipes）

```javascript
const RECOVERY_RECIPES = {
  'sentiment_collection': {
    retryable: true,
    maxRetries: 1,
    recoveryActions: [
      'check_network',
      'retry_once',
      'skip_if_locked'
    ]
  },
  'kline_update': {
    retryable: true,
    maxRetries: 1,
    recoveryActions: [
      'wait_5min',
      'retry_once'
    ]
  },
  'feishu_push': {
    retryable: true,
    maxRetries: 2,
    recoveryActions: [
      'retry_with_backoff'
    ]
  }
};

async function executeWithRecovery(taskName, fn) {
  const recipe = RECOVERY_RECIPES[taskName];
  
  if (!recipe) {
    return await fn();
  }
  
  return withAutoRetry(fn, {
    maxRetries: recipe.maxRetries,
    onRetry: (attempt, error) => {
      console.log(`[${taskName}] Retry ${attempt}: ${error.message}`);
    }
  });
}
```

### 4. 熔断器（Circuit Breaker）

```javascript
class CircuitBreaker {
  constructor(options = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.resetTimeout = options.resetTimeout || 60000;
    this.failures = 0;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = 0;
  }
  
  async execute(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }
  
  onFailure() {
    this.failures++;
    if (this.failures >= this.failureThreshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.resetTimeout;
    }
  }
}
```

## HEARTBEAT 中的使用

在 HEARTBEAT.md 的定时任务中加入：

```javascript
// 执行前获取锁
if (!acquireLock('task_name')) {
  console.log('任务已在执行中，跳过');
  return;
}

try {
  await executeWithRecovery('task_name', async () => {
    // 执行任务
  });
} finally {
  releaseLock('task_name');
}
```

## 来源

claw-code/rust/crates/runtime/src/recovery_recipes.rs 的实现思路
