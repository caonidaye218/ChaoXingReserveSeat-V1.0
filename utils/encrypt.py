from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
from hashlib import md5
import random
from uuid import uuid1
import time
import urllib.parse

def AES_Encrypt(data):
    key = b"u2oh6Vu^HWe4_AES"  # Convert to bytes
    iv = b"u2oh6Vu^HWe4_AES"  # Convert to bytes
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode('utf-8')) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    enctext = base64.b64encode(encrypted_data).decode('utf-8')
    return enctext
    
def resort(submit_info):
    return {key: submit_info[key] for key in sorted(submit_info.keys())}

def enc(submit_info):
    add = lambda x, y: x + y
    processed_info = resort(submit_info)
    needed = [add(add('[', key), '=' + str(value)) + ']' for key, value in processed_info.items()]
    pattern = "%sd`~7^/>N4!Q#){''"
    needed.append(add('[', pattern) + ']')
    seq = ''.join(needed)
    return md5(seq.encode("utf-8")).hexdigest()

def generate_captcha_key(timestamp: int):
    captcha_key = md5((str(timestamp) + str(uuid1())).encode("utf-8")).hexdigest()
    encoded_timestamp = md5(
        (str(timestamp) + "42sxgHoTPTKbt0uZxPJ7ssOvtXr3ZgZ1" + "slide" + captcha_key).encode("utf-8")
    ).hexdigest() + ":" + str(int(timestamp) + 0x493e0)
    return [captcha_key, encoded_timestamp]

def generate_behavior_analysis():
    """生成复杂的行为分析数据 - 基于真实抓包数据结构"""
    import base64
    import json
    
    # 基于你的抓包数据，生成更复杂的behaviorAnalysis
    timestamp = int(time.time() * 1000)
    
    # 模拟复杂的用户行为数据
    behavior_data = {
        # 鼠标移动轨迹 - 更多数据点
        "mouseEvents": [
            {
                "type": "mousemove",
                "x": random.randint(100 + i * 10, 1200 - i * 5),
                "y": random.randint(100 + i * 5, 800 - i * 3),
                "timestamp": timestamp + i * random.randint(10, 50)
            } for i in range(random.randint(50, 100))
        ],
        
        # 点击事件
        "clickEvents": [
            {
                "type": "click",
                "x": random.randint(300, 900),
                "y": random.randint(200, 600),
                "timestamp": timestamp + random.randint(2000, 8000),
                "button": 0
            } for _ in range(random.randint(5, 12))
        ],
        
        # 键盘事件
        "keyEvents": [
            {
                "type": "keydown",
                "key": random.choice(["Tab", "Enter", "Space"]),
                "timestamp": timestamp + random.randint(3000, 9000)
            } for _ in range(random.randint(2, 6))
        ],
        
        # 滚动事件
        "scrollEvents": [
            {
                "type": "scroll",
                "deltaX": 0,
                "deltaY": random.randint(-300, 300),
                "timestamp": timestamp + random.randint(1000, 7000)
            } for _ in range(random.randint(3, 8))
        ],
        
        # 页面焦点事件
        "focusEvents": [
            {
                "type": "focus",
                "target": random.choice(["input", "button", "select"]),
                "timestamp": timestamp + random.randint(1500, 6000)
            } for _ in range(random.randint(2, 5))
        ],
        
        # 页面停留时间
        "pageMetrics": {
            "loadTime": timestamp - random.randint(5000, 15000),
            "interactionTime": random.randint(10000, 30000),
            "scrollDepth": random.randint(20, 80)
        },
        
        # 设备信息
        "deviceInfo": {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "screen": f"{random.choice([1920, 1366, 1536])}x{random.choice([1080, 768, 864])}",
            "viewport": f"{random.randint(1200, 1800)}x{random.randint(600, 900)}",
            "colorDepth": 24,
            "timezone": -480
        },
        
        # 随机标识
        "sessionId": ''.join(random.choices('abcdef0123456789', k=32)),
        "fingerprint": ''.join(random.choices('0123456789abcdef', k=16)),
        
        # 时间戳和版本信息
        "timestamp": timestamp,
        "version": "2.1.0",
        "platform": "web"
    }
    
    # 将数据序列化为JSON
    json_data = json.dumps(behavior_data, separators=(',', ':'))
    
    # Base64编码
    encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
    
    # URL编码（模拟真实的传输格式）
    final_encoded = urllib.parse.quote_plus(encoded_data)
    
    return final_encoded

def generate_realistic_behavior_analysis():
    """生成更真实的behaviorAnalysis数据，基于抓包数据模式"""
    
    # 从你的抓包数据中，我看到behaviorAnalysis是一个很长的URL编码字符串
    # 让我们生成一个类似结构的数据
    
    timestamp = int(time.time() * 1000)
    base_data = []
    
    # 生成鼠标轨迹数据 (格式: x,y,timestamp)
    for i in range(random.randint(80, 150)):
        x = random.randint(50, 1400)
        y = random.randint(50, 900)
        t = timestamp + i * random.randint(15, 80)
        base_data.append(f"{x},{y},{t}")
    
    # 添加点击事件 (格式: click,x,y,timestamp)
    for i in range(random.randint(8, 15)):
        x = random.randint(200, 1000)
        y = random.randint(150, 700)
        t = timestamp + random.randint(2000, 12000)
        base_data.append(f"click,{x},{y},{t}")
    
    # 添加键盘事件
    for i in range(random.randint(5, 12)):
        key_code = random.choice([9, 13, 32, 37, 38, 39, 40])  # Tab, Enter, Space, 方向键
        t = timestamp + random.randint(3000, 15000)
        base_data.append(f"key,{key_code},{t}")
    
    # 添加滚动事件
    for i in range(random.randint(3, 10)):
        delta = random.randint(-500, 500)
        t = timestamp + random.randint(1000, 10000)
        base_data.append(f"scroll,{delta},{t}")
    
    # 连接所有数据
    behavior_string = "|".join(base_data)
    
    # 添加一些额外的元数据
    meta_info = f"&meta=v2.1.0&sid={''.join(random.choices('0123456789abcdef', k=32))}&ts={timestamp}"
    behavior_string += meta_info
    
    # 进行URL编码
    encoded_behavior = urllib.parse.quote_plus(behavior_string)
    
    return encoded_behavior
