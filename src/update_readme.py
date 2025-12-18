#!/usr/bin/env python3
"""
更新 README.md 中的壁纸索引
支持多数据源、路径修复、数量限制
"""

import re
import json
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config_loader import get_enabled_sources, get_display_config


def update_readme():
    """更新 README.md 中 WALLPAPER_INDEX 锚点区域的内容"""
    readme_path = Path("README.md")
    # 获取壁纸数据
    wallpapers_base = Path("docs/wallpapers")
    
    # 获取配置
    enabled_sources = get_enabled_sources()
    display_config = get_display_config()
    max_items = display_config.get("max_items_per_source", 10)
    
    # 按日期聚合所有源的壁纸
    date_wallpapers = defaultdict(dict)  # {date: {source_name: {meta, paths}}}
    
    for source in enabled_sources:
        source_name = source["name"]
        source_dir = wallpapers_base / source_name
        
        if not source_dir.exists():
            continue
            
        # 获取该源的所有日期目录
        dates = sorted(
            [p.name for p in source_dir.iterdir() if p.is_dir()],
            reverse=True
        )
        
        for date in dates:
            date_dir = source_dir / date
            meta_path = date_dir / "meta.json"
            thumb_path = date_dir / "thumb.jpg"
            image_path = date_dir / "image.jpg"
            story_path = date_dir / "story.md"
            
            if meta_path.exists() and thumb_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    date_wallpapers[date][source_name] = {
                        "meta": meta,
                        "thumb": f"docs/wallpapers/{source_name}/{date}/thumb.jpg",
                        "image": f"docs/wallpapers/{source_name}/{date}/image.jpg",
                        "story": f"docs/wallpapers/{source_name}/{date}/story.md" if story_path.exists() else None,
                        "display_name": source.get("display_name", source_name)
                    }
                except:
                    pass
    
    # 排序并限制数量
    sorted_dates = sorted(date_wallpapers.keys(), reverse=True)[:max_items]
    
    if not sorted_dates:
        print("[WARN] 没有找到任何壁纸")
        return
    
    # 生成 HTML 表格（日期为行，源为列）
    html_output = ['<table width="100%">']
    
    # 添加表头
    header_row = '<tr><th width="15%">日期</th>'
    for source in enabled_sources:
        col_width = f"{85 // len(enabled_sources)}%"
        header_row += f'<th width="{col_width}">{source.get("display_name", source["name"])}</th>'
    header_row += '</tr>'
    html_output.append(header_row)
    
    # 生成每一行
    for date in sorted_dates:
        html_output.append('<tr>')
        
        # 日期列
        html_output.append(f'<td align="center"><b>{date}</b></td>')
        
        # 每个源的列
        for source in enabled_sources:
            source_name = source["name"]
            
            if source_name in date_wallpapers[date]:
                data = date_wallpapers[date][source_name]
                title = data["meta"].get("title", date)
                thumb = data["thumb"]
                image = data["image"]
                story = data["story"]
                
                # 标题链接
                if story:
                    title_html = f'<a href="{story}"><small>{title} 📖</small></a>'
                else:
                    title_html = f'<small>{title}</small>'
                
                cell_content = f'<td align="center" valign="top"><a href="{image}"><img src="{thumb}" width="100%" style="border-radius:10px;"></a><br />{title_html}</td>'
            else:
                # 该源在这一天没有壁纸
                cell_content = '<td align="center" valign="top"><small>-</small></td>'
            
            html_output.append(cell_content)
        
        html_output.append('</tr>')
    
    html_output.append('</table>')
    
    index_block = "\n".join(html_output)
    
    # 读取并更新 README
    readme_content = readme_path.read_text(encoding="utf-8")
    pattern = r"(<!-- WALLPAPER_INDEX_START -->)[\s\S]*?(<!-- WALLPAPER_INDEX_END -->)"
    replacement = f"\\1\n{index_block}\n\\2"
    new_content = re.sub(pattern, replacement, readme_content)
    readme_path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    update_readme()
    print("[OK] README.md 已更新 (多源模式)")
