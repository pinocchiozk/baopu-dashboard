const WebSocket = require('ws');

const ws = new WebSocket('ws://127.0.0.1:18789');

ws.on('open', () => {
  console.log('Connected to gateway');
  
  const request = {
    jsonrpc: '2.0',
    id: 1,
    method: 'tool_call',
    params: {
      tool: 'feishu_doc',
      args: {
        action: 'create',
        title: 'A 股市场情绪数据采集流程',
        owner_open_id: 'ou_ca28f9bde02c28278caca087790d9a52'
      }
    }
  };
  
  ws.send(JSON.stringify(request));
});

ws.on('message', (data) => {
  console.log('Response:', data.toString());
  ws.close();
});

ws.on('error', (err) => {
  console.error('Error:', err);
});
