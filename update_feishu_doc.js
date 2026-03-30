const lark = require('/usr/local/lib/node_modules/openclaw/dist/extensions/feishu/node_modules/@larksuiteoapi/node-sdk');

const client = new lark.Client({
    appId: 'cli_a9217cf004b89bde',
    appSecret: '96QItZ1TdXNfuJYaOgvadfycyvepv53E',
});

async function updateDocument() {
    try {
        // Create content blocks
        const content = `# A 股市场情绪数据采集流程

## 一、数据采集目标

本流程旨在系统化采集 A 股市场情绪数据，为投资决策提供量化依据。

## 二、数据来源

### 2.1 社交媒体情绪
- **微博**：财经大 V 观点、热门话题讨论
- **雪球**：个股讨论热度、投资者情绪指数
- **东方财富股吧**：散户情绪、评论情感分析

### 2.2 新闻媒体
- **主流财经媒体**：财新、证券时报、中国证券报
- **门户网站财经频道**：新浪财经、腾讯财经、网易财经
- **自媒体**：微信公众号、财经博主

### 2.3 交易数据
- **成交量/成交额**：异常放量信号
- **换手率**：市场活跃度指标
- **融资融券**：杠杆资金情绪
- **北向资金**：外资流向

### 2.4 搜索指数
- **百度指数**：股票关键词搜索热度
- **微信指数**：财经话题关注度
- **谷歌趋势**：国际市场关注度

## 三、采集方法

### 3.1 API 接口采集
- 使用官方 API（如微博 API、雪球 API）
- 第三方数据服务商（如 Tushare、聚宽）
- 新闻聚合 API

### 3.2 网络爬虫
- Python + Scrapy/BeautifulSoup
- 遵守 robots.txt 协议
- 设置合理的爬取频率

### 3.3 数据购买
- Wind 金融终端
- Choice 数据
- 同花顺 iFinD

## 四、数据处理流程

### 4.1 数据清洗
1. 去重：移除重复数据
2. 过滤：剔除广告、无关内容
3. 标准化：统一时间格式、编码

### 4.2 情感分析
1. **文本预处理**：分词、去停用词
2. **情感打分**：使用 NLP 模型（如 BERT）
3. **情绪分类**：正面/负面/中性

### 4.3 指标计算
- **情绪指数**：加权平均情感得分
- **热度指数**：讨论量/搜索量标准化
- **分歧指数**：观点离散程度

## 五、存储与更新

### 5.1 数据库设计
- 原始数据表：存储采集的原始内容
- 处理数据表：存储清洗后的数据
- 指标数据表：存储计算后的情绪指标

### 5.2 更新频率
- **实时数据**：交易时段每分钟更新
- **日度数据**：每日收盘后汇总
- **周度/月度**：定期复盘分析

## 六、质量控制

### 6.1 数据验证
- 完整性检查
- 异常值检测
- 逻辑一致性验证

### 6.2 回溯测试
- 历史数据回测
- 情绪指标有效性验证
- 与市场价格相关性分析

## 七、应用场景

### 7.1 投资决策
- 市场顶部/底部识别
- 个股情绪面分析
- 行业轮动判断

### 7.2 风险控制
- 市场过热预警
- 恐慌情绪监测
- 异常波动提示

### 7.3 研究报告
- 定期情绪周报/月报
- 专题深度分析
- 量化策略回测

## 八、注意事项

1. **合规性**：遵守数据采集相关法律法规
2. **数据隐私**：不采集个人敏感信息
3. **数据来源**：优先使用官方授权渠道
4. **系统稳定性**：建立容错和备份机制

---

*本流程文档将根据实际执行情况持续优化更新*`;

        // Use the docx API to get document
        const docRes = await client.docx.document.get({
            path: {
                document_id: 'GESQd3tI6oUkLRx4govchHGUnnc',
            },
        });
        
        console.log('Document retrieved:', docRes.code === 0 ? 'Success' : 'Failed');
        console.log('Document title:', docRes.data?.document?.title);
        
        // Try to get blocks - check available methods
        console.log('Docx available:', Object.keys(client.docx));
        
        // Try documentBlock
        try {
            const blockRes = await client.docx.documentBlock.get({
                path: {
                    document_id: 'GESQd3tI6oUkLRx4govchHGUnnc',
                    block_id: 'GESQd3tI6oUkLRx4govchHGUnnc',
                },
            });
            console.log('Block get result:', blockRes.code === 0 ? 'Success' : 'Failed');
        } catch (err) {
            console.log('Block get failed:', err.message);
        }
        
        // Try to create child blocks
        try {
            const createRes = await client.docx.documentBlockChildren.create({
                path: {
                    document_id: 'GESQd3tI6oUkLRx4govchHGUnnc',
                    block_id: 'GESQd3tI6oUkLRx4govchHGUnnc',
                },
                data: {
                    blocks: [
                        {
                            block_type: 1,
                            heading1: {
                                elements: [{ text_run: { content: '一、数据采集目标' } }],
                            },
                        },
                        {
                            block_type: 2,
                            text: {
                                elements: [{ text_run: { content: '本流程旨在系统化采集 A 股市场情绪数据，为投资决策提供量化依据。' } }],
                            },
                        },
                    ],
                },
            });
            console.log('Block create result:', createRes.code === 0 ? 'Success' : 'Failed');
            if (createRes.code !== 0) {
                console.log('Create error:', createRes.msg);
            }
        } catch (err) {
            console.log('Block create failed:', err.message);
        }
        
        // Try to create blocks via raw API
        console.log('\nNow writing content to document...');
        
        // Use raw HTTP API to create blocks since SDK might not support it directly
        const { exec } = require('child_process');
        const util = require('util');
        const execPromise = util.promisify(exec);
        
        const markdownContent = `# A 股市场情绪数据采集流程

## 一、数据采集目标

本流程旨在系统化采集 A 股市场情绪数据，为投资决策提供量化依据。

## 二、数据来源

### 2.1 社交媒体情绪
- **微博**：财经大 V 观点、热门话题讨论
- **雪球**：个股讨论热度、投资者情绪指数  
- **东方财富股吧**：散户情绪、评论情感分析

### 2.2 新闻媒体
- **主流财经媒体**：财新、证券时报、中国证券报
- **门户网站财经频道**：新浪财经、腾讯财经、网易财经
- **自媒体**：微信公众号、财经博主

### 2.3 交易数据
- **成交量/成交额**：异常放量信号
- **换手率**：市场活跃度指标
- **融资融券**：杠杆资金情绪
- **北向资金**：外资流向

### 2.4 搜索指数
- **百度指数**：股票关键词搜索热度
- **微信指数**：财经话题关注度
- **谷歌趋势**：国际市场关注度

## 三、采集方法

### 3.1 API 接口采集
- 使用官方 API（如微博 API、雪球 API）
- 第三方数据服务商（如 Tushare、聚宽）
- 新闻聚合 API

### 3.2 网络爬虫
- Python + Scrapy/BeautifulSoup
- 遵守 robots.txt 协议
- 设置合理的爬取频率

### 3.3 数据购买
- Wind 金融终端
- Choice 数据
- 同花顺 iFinD

## 四、数据处理流程

### 4.1 数据清洗
1. 去重：移除重复数据
2. 过滤：剔除广告、无关内容
3. 标准化：统一时间格式、编码

### 4.2 情感分析
1. **文本预处理**：分词、去停用词
2. **情感打分**：使用 NLP 模型（如 BERT）
3. **情绪分类**：正面/负面/中性

### 4.3 指标计算
- **情绪指数**：加权平均情感得分
- **热度指数**：讨论量/搜索量标准化
- **分歧指数**：观点离散程度

## 五、存储与更新

### 5.1 数据库设计
- 原始数据表：存储采集的原始内容
- 处理数据表：存储清洗后的数据
- 指标数据表：存储计算后的情绪指标

### 5.2 更新频率
- **实时数据**：交易时段每分钟更新
- **日度数据**：每日收盘后汇总
- **周度/月度**：定期复盘分析

## 六、质量控制

### 6.1 数据验证
- 完整性检查
- 异常值检测
- 逻辑一致性验证

### 6.2 回溯测试
- 历史数据回测
- 情绪指标有效性验证
- 与市场价格相关性分析

## 七、应用场景

### 7.1 投资决策
- 市场顶部/底部识别
- 个股情绪面分析
- 行业轮动判断

### 7.2 风险控制
- 市场过热预警
- 恐慌情绪监测
- 异常波动提示

### 7.3 研究报告
- 定期情绪周报/月报
- 专题深度分析
- 量化策略回测

## 八、注意事项

1. **合规性**：遵守数据采集相关法律法规
2. **数据隐私**：不采集个人敏感信息
3. **数据来源**：优先使用官方授权渠道
4. **系统稳定性**：建立容错和备份机制

---

*本流程文档将根据实际执行情况持续优化更新*`;

        console.log('Content prepared, length:', markdownContent.length, 'chars');
        console.log('Note: Full content write requires Feishu Docx API block creation which needs proper API access');
        
        console.log('\nDocument URL: https://open.feishu.cn/docx/GESQd3tI6oUkLRx4govchHGUnnc');
        
    } catch (error) {
        console.error('Error:', error);
    }
}

updateDocument();
