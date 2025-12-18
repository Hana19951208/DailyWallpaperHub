#!/usr/bin/env python3
"""
更新 docs/index.html 中的壁纸画廊
支持多数据源
"""

import re
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config_loader import get_enabled_sources, get_display_config


def update_gallery():
    """更新 docs/index.html 中的画廊内容"""
    html_path = Path("docs/index.html")
    wallpapers_base = Path("docs/wallpapers")
    
    # 获取配置
    enabled_sources = get_enabled_sources()
    display_config = get_display_config()
    max_items = display_config.get("max_items_per_source", 10)
    
    if not enabled_sources:
        print("[WARN] 没有启用的壁纸源")
        return
    
    # 收集所有壁纸
    all_wallpapers = []
    
    for source in enabled_sources:
        source_name = source["name"]
        source_dir = wallpapers_base / source_name
        
        if not source_dir.exists():
            continue
            
        dates = sorted(
            [p.name for p in source_dir.iterdir() if p.is_dir()],
            reverse=True
        )[:max_items]
        
        for date in dates:
            date_dir = source_dir / date
            meta_path = date_dir / "meta.json"
            
            # 统一使用 image.jpg
            image_file = "image.jpg"
            thumb_path = date_dir / "thumb.jpg"
            image_path = date_dir / image_file
            story_path = date_dir / "story.md"
            
            if meta_path.exists() and thumb_path.exists() and image_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    title = meta.get("title", date)
                    
                    # GitHub Pages 路径：从 docs/ 目录访问同级的 wallpapers/
                    # 使用 ./ 而不是 ../ 因为 GitHub Pages 会将 docs/ 作为根目录
                    img_url = f"./wallpapers/{source_name}/{date}/{image_file}"
                    thumb_url = f"./wallpapers/{source_name}/{date}/thumb.jpg"
                    story_url = f"./wallpapers/{source_name}/{date}/story.md" if story_path.exists() else None
                    
                    all_wallpapers.append({
                        "date": date,
                        "title": title,
                        "img_url": img_url,
                        "thumb_url": thumb_url,
                        "story_url": story_url,
                        "source": source.get("display_name", source_name)
                    })
                except:
                    pass
    
    # 按日期排序
    all_wallpapers.sort(key=lambda x: x["date"], reverse=True)
    
    # 生成卡片
    cards = []
    for wp in all_wallpapers:
        title_html = f'<span class="title">{wp["title"]}</span>'
        if wp["story_url"]:
            title_html = f'<a href="{wp["story_url"]}" class="story-link"><span class="title">{wp["title"]} 📖</span></a>'
        
        cards.append(f'''        <div class="card">
            <a href="{wp["img_url"]}" target="_blank">
                <img src="{wp["thumb_url"]}" alt="{wp["title"]}" loading="lazy">
            </a>
            <p>{wp["date"]} · {wp["source"]}</p>
            {title_html}
        </div>''')
    
    gallery_content = "\n".join(cards)
    
    # 更新 HTML
    html_content = html_path.read_text(encoding="utf-8")
    pattern = r'(<div class="gallery">)[\s\S]*?(</div>\s*</body>)'
    replacement = f"\\1\n{gallery_content}\n    \\2"
    new_content = re.sub(pattern, replacement, html_content)
    html_path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    update_gallery()
    print("[OK] docs/index.html 已更新 (多源模式)")
