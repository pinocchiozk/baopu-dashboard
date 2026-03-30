#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A 股市场情绪 OCR 服务 - 常驻内存，快速响应
启动后预加载模型，后续识别只需几秒钟
"""

import sys
import os
import re
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading

# 预加载 OCR 模型（只加载一次）
print("[OCR Service] 正在加载 EasyOCR 模型...", file=sys.stderr, flush=True)
import easyocr
OCR_READER = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
print("[OCR Service] 模型加载完成", file=sys.stderr, flush=True)


def extract_data_from_text(all_text):
    """从 OCR 文本中提取数据"""
    data = {
        'sentiment_score': None,
        'limit_up': None,
        'limit_down': None,
        'up_count': None,
        'down_count': None,
        'sh_index': None,
        'sh_change': None,
        'real_volume': None,
        'predict_volume': None,
    }
    
    # 1. 情绪分数 - 综合强度前面的数字（刻度尺格式）
    # 例如："41 10 20 30 40 50 60 70 80 90 100 综合强度"
    match = re.search(r'(\d+)\s+10\s+20\s+30\s+40\s+50\s+60\s+70\s+80\s+90\s+100\s+综合强度', all_text)
    if match:
        score = int(match.group(1))
        if 0 <= score <= 100:
            data['sentiment_score'] = score
    
    # 备选：市场情绪 XX 分
    if data['sentiment_score'] is None:
        match = re.search(r'市场情绪\s*(\d+(?:\.\d+)?)\s*分', all_text)
        if match:
            data['sentiment_score'] = int(float(match.group(1)))
    
    return data


def recognize_image(image_path):
    """识别单张图片"""
    try:
        result = OCR_READER.readtext(image_path)
        texts = [(d[1], d[2]) for d in result if len(d) >= 2]
        all_text = ' '.join([t[0] for t in texts])
        data = extract_data_from_text(all_text)
        # 调试：输出原始文本
        print(f"[DEBUG] OCR 文本：{all_text[:500]}", file=sys.stderr, flush=True)
        return data, texts
    except Exception as e:
        return None, str(e)


class OCRHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        image_path = data.get('image_path')
        if not image_path:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": "image_path required"}')
            return
        
        result, texts = recognize_image(image_path)
        
        response = {
            'data': result,
            'debug': texts[:10] if texts else None
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # 静默日志


def run_server(port=8765):
    server = HTTPServer(('127.0.0.1', port), OCRHandler)
    print(f"[OCR Service] 服务启动在端口 {port}", file=sys.stderr, flush=True)
    server.serve_forever()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--server':
        run_server()
    elif len(sys.argv) > 1:
        # 单次识别模式
        image_path = sys.argv[1]
        data, texts = recognize_image(image_path)
        if data:
            print(f"SENTIMENT_SCORE={data['sentiment_score'] or 'NULL'}")
            print(f"LIMIT_UP={data['limit_up'] or 'NULL'}")
            print(f"LIMIT_DOWN={data['limit_down'] or 'NULL'}")
            print(f"UP_COUNT={data['up_count'] or 'NULL'}")
            print(f"DOWN_COUNT={data['down_count'] or 'NULL'}")
            print(f"SH_INDEX={data['sh_index'] or 'NULL'}")
            print(f"SH_CHANGE={data['sh_change'] or 'NULL'}")
            print(f"REAL_VOLUME={data['real_volume'] or 'NULL'}")
            print(f"PREDICT_VOLUME={data['predict_volume'] or 'NULL'}")
        else:
            print(f"ERROR: {texts}", file=sys.stderr)
            sys.exit(1)
    else:
        print("用法：python3 sentiment_ocr_service.py --server  (启动服务)")
        print("     或：python3 sentiment_ocr_service.py <图片路径>  (单次识别)")
