#!/usr/bin/env python3
"""
批量抓取壁纸脚本 (支持多数据源)
用法:
  python batch_fetch.py bing 2025-12        # 抓取 Bing 2025年12月的所有壁纸
  python batch_fetch.py bing 2025-12-10     # 抓取 Bing 2025年12月10日的壁纸
  python batch_fetch.py unsplash 2025-12    # 抓取 Unsplash 2025年12月的所有壁纸
"""

import os
import sys
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

# 导入主脚本的工具函数
import fetch_bing_wallpaper
from src.update_readme import update_readme
from src.update_gallery import update_gallery


BING_API = "https://www.bing.com/HPImageArchive.aspx"
BING_BASE = "https://www.bing.com"
UNSPLASH_API = "https://api.unsplash.com/photos/random"


def batch_fetch_bing(target_date):
    """批量抓取 Bing 壁纸"""
    print(f"🚀 开始批量抓取 Bing {target_date} 的壁纸...")
    
    fetch_bing_wallpaper.load_env()
    count = 0
    story_count = 0
    
    # 尝试抓取多页
    all_images = []
    for idx_start in [0, 8, 16]:
        params = {
            "format": "js",
            "idx": idx_start,
            "n": 8,
            "mkt": "zh-CN"
        }
        try:
            resp = requests.get(BING_API, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            all_images.extend(data.get("images", []))
        except Exception as e:
            print(f"⚠️ 无法获取 idx={idx_start} 的数据: {e}")
    
    for img in all_images:
        start_date = img.get("startdate")
        if not start_date:
            continue
        
        date_str = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
        
        # 过滤日期
        if not date_str.startswith(target_date):
            continue
        
        base_dir = Path("docs/wallpapers/bing") / date_str
        base_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = base_dir / "image.jpg"
        meta_path = base_dir / "meta.json"
        thumb_path = base_dir / "thumb.jpg"
        story_path = base_dir / "story.md"
        
        # 1. 下载图片
        if not image_path.exists():
            image_url = BING_BASE + img["url"]
            print(f"📥 正在下载 {date_str}: {img.get('title')}")
            fetch_bing_wallpaper.download_image(image_url, image_path)
            fetch_bing_wallpaper.generate_thumbnail(image_path, thumb_path)
            count += 1
        
        # 2. 生成 AI 故事
        has_story = story_path.exists()
        if not has_story:
            story_content = fetch_bing_wallpaper.generate_story(
                img.get("title"),
                img.get("copyright"),
                image_path
            )
            if story_content:
                story_path.write_text(story_content, encoding="utf-8")
                print(f"📖 已生成故事: {date_str}")
                has_story = True
                story_count += 1
        
        # 3. 更新元数据
        meta_info = {
            "date": date_str,
            "title": img.get("title"),
            "copyright": img.get("copyright"),
            "image_url": BING_BASE + img["url"],
            "has_story": has_story
        }
        meta_path.write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")
    
    print(f"✅ Bing 批量处理完成：新增图片 {count} 张，补全故事 {story_count} 篇。")


def batch_fetch_unsplash(target_date):
    """批量抓取 Unsplash 壁纸"""
    print(f"🚀 开始抓取 Unsplash {target_date} 的壁纸...")
    print("⚠️ 注意：Unsplash API 不支持按日期查询历史壁纸")
    print("    将抓取当前精选照片并保存到指定日期目录")
    
    fetch_bing_wallpaper.load_env()
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    
    if not access_key:
        print("[ERROR] UNSPLASH_ACCESS_KEY 未配置")
        return
    
    # 解析目标日期
    if len(target_date) == 7:  # YYYY-MM 格式
        # 抓取整月（实际上是抓取多张当前照片）
        year, month = target_date.split('-')
        import calendar
        days_in_month = calendar.monthrange(int(year), int(month))[1]
        dates_to_fetch = [f"{target_date}-{str(day).zfill(2)}" for day in range(1, days_in_month + 1)]
    elif len(target_date) == 10:  # YYYY-MM-DD 格式
        dates_to_fetch = [target_date]
    else:
        print("[ERROR] 日期格式错误，应为 YYYY-MM 或 YYYY-MM-DD")
        return
    
    count = 0
    for date_str in dates_to_fetch:
        base_dir = Path("docs/wallpapers/unsplash") / date_str
        
        # 如果已存在，跳过
        if base_dir.exists() and (base_dir / "image.jpg").exists():
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
            
            # 生成故事
            title = photo.get("description") or photo.get("alt_description") or "Unsplash Featured Photo"
            author = photo.get("user", {}).get("name", "Unknown")
            copyright_info = f"Photo by {author} on Unsplash"
            
            story_content = fetch_bing_wallpaper.generate_story(title, copyright_info, image_path)
            if story_content:
                (base_dir / "story.md").write_text(story_content, encoding="utf-8")
            
            # 保存元数据
            meta_info = {
                "date": date_str,
                "title": title,
                "copyright": copyright_info,
                "image_url": photo["links"]["html"],
                "photographer": author,
                "has_story": bool(story_content)
            }
            (base_dir / "meta.json").write_text(json.dumps(meta_info, ensure_ascii=False, indent=2), encoding="utf-8")
            
            print(f"📥 已抓取 {date_str}: {title}")
            count += 1
            
        except Exception as e:
            print(f"[ERROR] 抓取 {date_str} 失败: {e}")
            continue
    
    print(f"✅ Unsplash 批量处理完成：新增 {count} 张照片。")


def main():
    if len(sys.argv) < 3:
        print("用法:")
        print("  python batch_fetch.py bing 2025-12        # 抓取 Bing 2025年12月")
        print("  python batch_fetch.py bing 2025-12-10     # 抓取 Bing 指定日期")
        print("  python batch_fetch.py unsplash 2025-12    # 抓取 Unsplash 2025年12月")
        print("  python batch_fetch.py unsplash 2025-12-10 # 抓取 Unsplash 指定日期")
        sys.exit(1)
    
    source = sys.argv[1].lower()  # 忽略大小写
    target_date = sys.argv[2]
    
    if source == "bing":
        batch_fetch_bing(target_date)
    elif source == "unsplash":
        batch_fetch_unsplash(target_date)
    else:
        print(f"❌ 不支持的数据源: {source}")
        print("支持的数据源: bing, unsplash")
        sys.exit(1)
    
    # 更新索引
    print("🔄 正在更新 README 和 Gallery...")
    update_readme()
    update_gallery()
    print("✅ 全部完成！")


if __name__ == "__main__":
    main()
