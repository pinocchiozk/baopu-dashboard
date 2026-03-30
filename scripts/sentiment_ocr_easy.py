#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A 股市场情绪数据 OCR 识别脚本（EasyOCR 版本）
从开盘啦 App 截图中自动识别情绪数据
"""

import sys
import re
import easyocr

def extract_sentiment_data(image_path):
    """
    从截图中提取市场情绪数据
    返回字典格式的数据
    """
    # 初始化 EasyOCR（中文 + 英文）
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
    
    # 执行 OCR
    result = reader.readtext(image_path)
    
    # 提取文本
    texts = []
    for detection in result:
        if len(detection) >= 2:
            text = detection[1]  # 识别的文本
            confidence = detection[2]  # 置信度
            texts.append((text, confidence))
    
    # 合并所有文本用于分析
    all_text = ' '.join([t[0] for t in texts])
    
    # 提取各项数据
    data = {
        'sentiment_score': None,      # 市场情绪分数
        'limit_up': None,             # 涨停家数
        'limit_down': None,           # 跌停家数
        'up_count': None,             # 上涨家数
        'down_count': None,           # 下跌家数
        'sh_index': None,             # 上证指数
        'sh_change': None,            # 上证指数涨跌幅
        'real_volume': None,          # 实际量能
        'predict_volume': None,       # 预测量能
    }
    
    # 1. 提取市场情绪分数（综合强度）
    score_patterns = [
        r'综合强度\s*(\d+(?:\.\d+)?)\s*分',
        r'市场情绪\s*(\d+(?:\.\d+)?)\s*分',
        r'情绪\s*(\d+(?:\.\d+)?)\s*分',
        r'(\d+(?:\.\d+)?)\s*分',
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, all_text)
        if match:
            score = float(match.group(1))
            if 0 <= score <= 100:
                data['sentiment_score'] = int(score) if score == int(score) else score
                break
    
    # 2. 提取涨停家数
    for pattern in [r'涨停\s*(\d+)\s*家', r'涨停家数\s*(\d+)']:
        match = re.search(pattern, all_text)
        if match:
            data['limit_up'] = int(match.group(1))
            break
    
    # 3. 提取跌停家数
    for pattern in [r'跌停\s*(\d+)\s*家', r'跌停家数\s*(\d+)']:
        match = re.search(pattern, all_text)
        if match:
            data['limit_down'] = int(match.group(1))
            break
    
    # 4. 提取上涨家数
    for pattern in [r'上涨\s*(\d+)\s*家', r'上涨家数\s*(\d+)']:
        match = re.search(pattern, all_text)
        if match:
            data['up_count'] = int(match.group(1))
            break
    
    # 5. 提取下跌家数
    for pattern in [r'下跌\s*(\d+)\s*家', r'下跌家数\s*(\d+)']:
        match = re.search(pattern, all_text)
        if match:
            data['down_count'] = int(match.group(1))
            break
    
    # 6. 提取上证指数
    for pattern in [r'上证指数\s*([\d,]+(?:\.\d+)?)\s*\(([+\-]?\d+(?:\.\d+)?%?)\)']:
        match = re.search(pattern, all_text)
        if match:
            data['sh_index'] = float(match.group(1).replace(',', ''))
            data['sh_change'] = match.group(2)
            break
    
    # 7. 提取量能
    volumes_found = []
    for pattern in [r'(\d+(?:\.\d+)?)\s*万亿']:
        matches = re.findall(pattern, all_text)
        for m in matches:
            vol = float(m)
            if 0.1 <= vol <= 10:
                volumes_found.append(vol)
    
    if len(volumes_found) >= 1:
        data['real_volume'] = volumes_found[0]
        data['predict_volume'] = volumes_found[1] if len(volumes_found) >= 2 else volumes_found[0]
    
    return data, texts


def main():
    if len(sys.argv) < 2:
        print("用法：python3 sentiment_ocr_easy.py <截图路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        data, texts = extract_sentiment_data(image_path)
        
        # 输出（便于 bash 解析）
        print(f"SENTIMENT_SCORE={data['sentiment_score'] or 'NULL'}")
        print(f"LIMIT_UP={data['limit_up'] or 'NULL'}")
        print(f"LIMIT_DOWN={data['limit_down'] or 'NULL'}")
        print(f"UP_COUNT={data['up_count'] or 'NULL'}")
        print(f"DOWN_COUNT={data['down_count'] or 'NULL'}")
        print(f"SH_INDEX={data['sh_index'] or 'NULL'}")
        print(f"SH_CHANGE={data['sh_change'] or 'NULL'}")
        print(f"REAL_VOLUME={data['real_volume'] or 'NULL'}")
        print(f"PREDICT_VOLUME={data['predict_volume'] or 'NULL'}")
        
        # 调试输出
        print(f"\n[DEBUG] 识别到的文本:", file=sys.stderr)
        for text, conf in texts[:20]:  # 只显示前 20 条
            print(f"  {text} ({conf:.2f})", file=sys.stderr)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
