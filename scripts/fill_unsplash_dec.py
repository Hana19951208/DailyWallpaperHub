#!/usr/bin/env python3
"""
填充 Unsplash 12月9-18日的壁纸数据
"""

import os
import sys
import json
import requests
from pathlib import Path
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
import fetch_bing_wallpaper

UNSPLASH_API = "https://api.unsplash.com/photos/random"


def fill_unsplash_december():
    """填充 Unsplash 12月9-18日的数据"""
    print("🚀 开始填充 Unsplash 12月数据...")
    
    fetch_bing_wallpaper.load_env()
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    
    if not access_key:
        print("[ERROR] UNSPLASH_ACCESS_KEY 未配置")
        return
    
    # 目标日期列表（12月9-18日）
    dates = [f"2025-12-{str(day).zfill(2)}" for day in range(9, 19)]
    
    count = 0
    for date_str in dates:
        base_dir = Path("docs/wallpapers/unsplash") / date_str
        
        # 如果已存在，跳过
        if base_dir.exists() and (base_dir / "image.jpg").exists():
            print(f"[SKIP] {date_str} 已存在")
            continue
        
        # 抓取一张照片
        headers = {"Authorization": f"Client-ID {access_key}"}
        params = {
            "featured": "true",
            "orientation": "landscape",
            "query": "nature,landscape,architecture"
        }
        
        try:
            resp = requests.get(UNSPLASH_API, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            photo = resp.json()
            
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # 下载图片
            image_url = photo["urls"]["full"]
            image_path = base_dir / "image.jpg"
            fetch_bing_wallpaper.download_image(image_url, image_path)
            
            # 生成缩略图
            thumb_path = base_dir / "thumb.jpg"
            fetch_bing_wallpaper.generate_thumbnail(image_path, thumb_path)
            
            # 保存元数据（暂不生成故事）
            title = photo.get("description") or photo.get("alt_description") or "Unsplash Featured Photo"
            author = photo.get("user", {}).get("name", "Unknown")
            copyright_info = f"Photo by {author} on Unsplash"
            
            meta_info = {
                "date": date_str,
                "title": title,
                "copyright": copyright_info,
                "image_url": photo["links"]["html"],
                "photographer": author,
                "has_story": False  # 故事稍后异步生成
            }
            (base_dir / "meta.json").write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")
            
            print(f"✅ 已填充 {date_str}: {title}")
            count += 1
            
        except Exception as e:
            print(f"[ERROR] 填充 {date_str} 失败: {e}")
            continue
    
    print(f"\n✅ 填充完成：新增 {count} 张 Unsplash 壁纸")
    print("💡 提示：运行 'python scripts/generate_missing_stories.py' 生成 AI 故事")


if __name__ == "__main__":
    fill_unsplash_december()
