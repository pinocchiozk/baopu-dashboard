#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A 股市场情绪数据 OCR 识别脚本
从开盘啦 App 截图中自动识别情绪数据
"""

import sys
import re
from paddleocr import PaddleOCR

def extract_sentiment_data(image_path):
    """
    从截图中提取市场情绪数据
    返回字典格式的数据
    """
    # 初始化 PaddleOCR（中文模型）
    import os
    os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    ocr = PaddleOCR(use_textline_orientation=False, lang='ch')
    
    # 执行 OCR
    result = ocr.predict(image_path)
    
    # 提取文本
    texts = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) >= 2:
                text = line[1][0]  # 识别的文本
                confidence = line[1][1]  # 置信度
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
    # 模式："综合强度 XX 分" 或 "情绪 XX 分" 或 单独的红色数字 + 分
    score_patterns = [
        r'综合强度\s*(\d+(?:\.\d+)?)\s*分',
        r'市场情绪\s*(\d+(?:\.\d+)?)\s*分',
        r'情绪\s*(\d+(?:\.\d+)?)\s*分',
        r'(\d+(?:\.\d+)?)\s*分',  # 最后的备选
    ]
    
    for pattern in score_patterns:
        match = re.search(pattern, all_text)
        if match:
            score = float(match.group(1))
            # 情绪分数通常在 0-100 之间
            if 0 <= score <= 100:
                data['sentiment_score'] = int(score) if score == int(score) else score
                break
    
    # 2. 提取涨停家数
    limit_up_patterns = [
        r'涨停\s*(\d+)\s*家',
        r'涨停家数\s*(\d+)',
    ]
    for pattern in limit_up_patterns:
        match = re.search(pattern, all_text)
        if match:
            data['limit_up'] = int(match.group(1))
            break
    
    # 3. 提取跌停家数
    limit_down_patterns = [
        r'跌停\s*(\d+)\s*家',
        r'跌停家数\s*(\d+)',
    ]
    for pattern in limit_down_patterns:
        match = re.search(pattern, all_text)
        if match:
            data['limit_down'] = int(match.group(1))
            break
    
    # 4. 提取上涨家数
    up_patterns = [
        r'上涨\s*(\d+)\s*家',
        r'上涨家数\s*(\d+)',
    ]
    for pattern in up_patterns:
        match = re.search(pattern, all_text)
        if match:
            data['up_count'] = int(match.group(1))
            break
    
    # 5. 提取下跌家数
    down_patterns = [
        r'下跌\s*(\d+)\s*家',
        r'下跌家数\s*(\d+)',
    ]
    for pattern in down_patterns:
        match = re.search(pattern, all_text)
        if match:
            data['down_count'] = int(match.group(1))
            break
    
    # 6. 提取上证指数
    sh_patterns = [
        r'上证指数\s*([\d,]+(?:\.\d+)?)\s*\(([+\-]?\d+(?:\.\d+)?%?)\)',
        r'上证\s*([\d,]+(?:\.\d+)?)\s*\(([+\-]?\d+(?:\.\d+)?%?)\)',
    ]
    for pattern in sh_patterns:
        match = re.search(pattern, all_text)
        if match:
            index_str = match.group(1).replace(',', '')
            change_str = match.group(2)
            data['sh_index'] = float(index_str)
            data['sh_change'] = change_str
            break
    
    # 7. 提取量能（万亿）
    volume_patterns = [
        r'实际量能\s*([\d.]+)\s*万亿',
        r'沪深\s*([\d.]+)\s*万亿',
        r'(\d+(?:\.\d+)?)\s*万亿',
    ]
    volumes_found = []
    for pattern in volume_patterns:
        matches = re.findall(pattern, all_text)
        for m in matches:
            vol = float(m)
            if 0.1 <= vol <= 10:  # 合理范围
                volumes_found.append(vol)
    
    if len(volumes_found) >= 1:
        data['real_volume'] = volumes_found[0]
        if len(volumes_found) >= 2:
            data['predict_volume'] = volumes_found[1]
        else:
            data['predict_volume'] = volumes_found[0]  # 如果没有预测，用实际值
    
    return data, texts


def main():
    if len(sys.argv) < 2:
        print("用法：python3 sentiment_ocr.py <截图路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        data, texts = extract_sentiment_data(image_path)
        
        # 输出 JSON 格式（便于 bash 脚本解析）
        print(f"SENTIMENT_SCORE={data['sentiment_score'] or 'NULL'}")
        print(f"LIMIT_UP={data['limit_up'] or 'NULL'}")
        print(f"LIMIT_DOWN={data['limit_down'] or 'NULL'}")
        print(f"UP_COUNT={data['up_count'] or 'NULL'}")
        print(f"DOWN_COUNT={data['down_count'] or 'NULL'}")
        print(f"SH_INDEX={data['sh_index'] or 'NULL'}")
        print(f"SH_CHANGE={data['sh_change'] or 'NULL'}")
        print(f"REAL_VOLUME={data['real_volume'] or 'NULL'}")
        print(f"PREDICT_VOLUME={data['predict_volume'] or 'NULL'}")
        
        # 调试输出到 stderr
        print(f"\n[DEBUG] 识别到的文本:", file=sys.stderr)
        for text, conf in texts:
            print(f"  {text} (置信度：{conf:.2f})", file=sys.stderr)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
