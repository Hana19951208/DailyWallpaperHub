#!/usr/bin/env python3
"""
Unsplash 每日壁纸抓取脚本
使用 Unsplash API 获取精选照片
"""

import argparse

import os
import json
import base64
import requests
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

# 复用主脚本的函数
import sys
sys.path.insert(0, str(Path(__file__).parent))
from fetch_bing_wallpaper import generate_thumbnail, generate_story, load_env
from src.utils import send_image_to_wecom, send_markdown_to_wecom, send_story_to_wecom
from src.update_readme import update_readme
from src.update_gallery import update_gallery


UNSPLASH_API = "https://api.unsplash.com/photos/random"


def fetch_unsplash_photo():
    """获取 Unsplash 随机精选照片"""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not access_key:
        print("[ERROR] UNSPLASH_ACCESS_KEY 未配置")
        return None
    
    headers = {
        "Authorization": f"Client-ID {access_key}"
    }
    params = {
        "featured": "true",  # 只获取精选照片
        "orientation": "landscape",  # 横向照片
        "query": "nature,landscape,architecture"  # 主题过滤
    }
    
    try:
        resp = requests.get(UNSPLASH_API, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[ERROR] Unsplash API 请求失败: {e}")
        return None


def download_image(url: str, save_path: Path):
    """下载图片"""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    save_path.write_bytes(r.content)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='抓取 Unsplash 精选壁纸')
    parser.add_argument('--skip-story', action='store_true', help='跳过 AI 故事生成（快速模式）')
    args = parser.parse_args()
    
    load_env()
    
    # 1. 获取照片
    print("[INFO] 正在获取 Unsplash 精选照片...")
    photo = fetch_unsplash_photo()
    
    if not photo:
        return
    
    # 使用今天的日期
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    base_dir = Path("docs/wallpapers/unsplash") / today
    
    if base_dir.exists() and (base_dir / "image.jpg").exists():
        print(f"[INFO] {today} 的 Unsplash 壁纸已存在")
        return
    
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. 下载原图
    image_url = photo["urls"]["full"]  # 使用全尺寸图片
    image_path = base_dir / "image.jpg"
    download_image(image_url, image_path)
    print(f"[OK] Unsplash 照片已下载: {photo.get('description', 'Untitled')}")
    
    # 3. 生成缩略图
    thumb_path = base_dir / "thumb.jpg"
    generate_thumbnail(image_path, thumb_path)
    print(f"[OK] 缩略图已生成")
    
    # 4. 生成 AI 故事 - 可选
    title = photo.get("description") or photo.get("alt_description") or "Unsplash Featured Photo"
    author = photo.get("user", {}).get("name", "Unknown")
    copyright_info = f"Photo by {author} on Unsplash"
    
    story_content = None
    if not args.skip_story:
        story_content = generate_story(title, copyright_info, image_path)
        if story_content:
            (base_dir / "story.md").write_text(story_content, encoding="utf-8")
            print(f"[OK] AI 故事已生成")
    else:
        print(f"[INFO] 跳过故事生成（使用 --skip-story）")
    
    # 5. 保存元数据
    meta_path = base_dir / "meta.json"
    meta_info = {
        "date": today,
        "title": title,
        "copyright": copyright_info,
        "image_url": photo["links"]["html"],
        "photographer": author,
        "has_story": bool(story_content)
    }
    meta_path.write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] 元数据已保存")
    
    # 6. 更新 README
    update_readme()
    print("[OK] README.md 已更新")
    
    # 7. 更新 Gallery
    update_gallery()
    print("[OK] docs/index.html 已更新")
    
    # 8. 推送企业微信（可选）
    webhook_url = os.environ.get("WEWORK_WEBHOOK")
    if webhook_url:
        try:
            send_image_to_wecom(webhook_url, str(image_path))
            send_markdown_to_wecom(webhook_url, meta_info)
            if story_content:
                send_story_to_wecom(webhook_url, meta_info, story_content)
            print("[OK] 企业微信推送成功")
        except Exception as e:
            print(f"[WARN] 企业微信推送失败: {e}")
    
    print(f"\n✅ 完成！Unsplash 壁纸已归档至 {base_dir}")


if __name__ == "__main__":
    main()
