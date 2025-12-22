#!/usr/bin/env python3
"""
异步生成缺失的 AI 故事
扫描所有壁纸目录，为没有 story.md 的壁纸生成故事
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
import fetch_bing_wallpaper
from src.update_readme import update_readme
from src.update_gallery import update_gallery


def generate_missing_stories():
    """生成所有缺失的故事"""
    print("🚀 开始扫描并生成缺失的故事...")
    
    fetch_bing_wallpaper.load_env()
    wallpapers_base = Path("docs/wallpapers")
    
    total_count = 0
    success_count = 0
    
    # 遍历所有源
    for source_dir in wallpapers_base.iterdir():
        if not source_dir.is_dir() or source_dir.name.startswith('.'):
            continue
        
        source_name = source_dir.name
        print(f"\n📂 处理 {source_name} 源...")
        
        # 遍历所有日期目录
        for date_dir in sorted(source_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            
            date_str = date_dir.name
            story_path = date_dir / "story.md"
            meta_path = date_dir / "meta.json"
            image_path = date_dir / "image.jpg"
            
            # 检查是否需要生成故事
            if story_path.exists():
                continue
            
            if not meta_path.exists() or not image_path.exists():
                print(f"[SKIP] {date_str}: 缺少元数据或图片")
                continue
            
            total_count += 1
            
            try:
                # 读取元数据
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                title = meta.get("title", "Wallpaper")
                copyright_info = meta.get("copyright", "")
                
                # 生成故事
                print(f"[INFO] 正在为 {source_name}/{date_str} 生成故事...")
                story_content = fetch_bing_wallpaper.generate_story(title, copyright_info, image_path)
                
                if story_content:
                    story_path.write_text(story_content, encoding="utf-8")
                    
                    # 更新元数据
                    meta["has_story"] = True
                    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                    
                    print(f"✅ {source_name}/{date_str}: 故事已生成")
                    
                    # 同步到 COS
                    from src.utils import upload_to_cos
                    cos_base_path = f"wallpapers/{source_name}/{date_str}"
                    upload_to_cos(str(story_path), f"{cos_base_path}/story.md")
                    upload_to_cos(str(meta_path), f"{cos_base_path}/meta.json")
                    
                    success_count += 1
                else:
                    print(f"[WARN] {source_name}/{date_str}: 故事生成失败")
                    
            except Exception as e:
                print(f"[ERROR] {source_name}/{date_str}: {e}")
                continue
    
    print(f"\n✅ 故事生成完成：成功 {success_count}/{total_count}")
    
    # 更新 README 和 Gallery
    if success_count > 0:
        print("\n🔄 更新 README 和 Gallery...")
        update_readme()
        update_gallery()
        print("✅ 更新完成")


if __name__ == "__main__":
    generate_missing_stories()
