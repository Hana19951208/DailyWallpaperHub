#!/usr/bin/env python3
"""
企业微信群机器人推送工具
"""

import base64
import hashlib
import os
import requests
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys


def send_image_to_wecom(webhook_url: str, image_path: str):
    """
    发送图片到企业微信群机器人
    """
    with open(image_path, "rb") as f:
        image_data = f.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")
        image_md5 = hashlib.md5(image_data).hexdigest()

    payload = {
        "msgtype": "image",
        "image": {
            "base64": image_base64,
            "md5": image_md5
        }
    }

    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    
    result = resp.json()
    if result.get("errcode") != 0:
        raise Exception(f"WeChat push failed: {result.get('errmsg')}")


def send_markdown_to_wecom(webhook_url: str, meta: dict, source_name: str = "Bing"):
    """
    发送 Markdown 消息到企业微信群机器人
    """
    title = meta.get("title", "")
    copyright_info = meta.get("copyright", "")
    date = meta.get("date", "")

    content = f"""### 🖼 今日{source_name}壁纸 · {date}

**{title}**

> {copyright_info}

📦 已自动归档至 [GitHub 仓库](https://github.com/Hana19951208/DailyWallpaperHub)
🔁 自动化定时任务运行中"""

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }

    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()
    
    result = resp.json()
    if result.get("errcode") != 0:
        raise Exception(f"WeChat push failed: {result.get('errmsg')}")


def send_story_to_wecom(webhook_url: str, meta: dict, story_content: str):
    """
    推送壁纸故事到企业微信（Markdown 格式）
    """
    try:
        title = meta.get("title", "每日壁纸")
        date = meta.get("date", "")
        
        # 构建 Markdown 内容
        # 移除任何形式的图片引用 (Markdown 格式: ![alt](url))
        import re
        story_text = re.sub(r'!\[.*?\]\(.*?\)', '', story_content).strip()
        
        # 限制长度（企业微信限制 2048 字节）
        max_length = 1800 
        if len(story_text.encode('utf-8')) > max_length:
            content_bytes = story_text.encode('utf-8')[:max_length]
            story_text = content_bytes.decode('utf-8', errors='ignore') + "\n\n...\n\n> 查看完整故事请访问 GitHub 仓库"
        
        markdown_text = f"# 📖 {title}\n\n**日期**: {date}\n\n---\n\n{story_text}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_text
            }
        }
        
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        
        if result.get("errcode") != 0:
            print(f"[WARN] 企业微信故事推送返回错误: {result.get('errmsg')}")
    except Exception as e:
        print(f"[ERROR] 企业微信故事推送失败: {e}")


def upload_to_cos(local_path: str, cos_path: str):
    """
    上传文件到腾讯云 COS
    """
    secret_id = os.environ.get('COS_SECRET_ID')
    secret_key = os.environ.get('COS_SECRET_KEY')
    region = os.environ.get('COS_REGION')
    bucket = os.environ.get('COS_BUCKET')

    if not all([secret_id, secret_key, region, bucket]):
        print("[INFO] COS 配置不全，跳过 COS 上传")
        return None

    try:
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(config)

        with open(local_path, 'rb') as f:
            response = client.put_object(
                Bucket=bucket,
                Body=f,
                Key=cos_path,
                StorageClass='STANDARD',
                EnableMD5=False
            )
        
        cos_url = f"https://{bucket}.cos.{region}.myqcloud.com/{cos_path}"
        print(f"[OK] 文件已上传至 COS: {cos_url}")
        return cos_url
    except Exception as e:
        print(f"[ERROR] COS 上传失败: {e}")
        return None
