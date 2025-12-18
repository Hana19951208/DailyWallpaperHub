#!/usr/bin/env python3
"""
每日必应壁纸自动归档脚本
- 下载必应每日壁纸
- 生成缩略图
- 更新 README 索引
- 更新 Gallery 页面
- 推送企业微信
"""
import argparse

import os
import json
import base64
import requests
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

from src.utils import send_image_to_wecom, send_markdown_to_wecom, send_story_to_wecom
from src.update_readme import update_readme
from src.update_gallery import update_gallery


BING_API = "https://www.bing.com/HPImageArchive.aspx"
BING_BASE = "https://www.bing.com"
THUMB_SIZE = (400, 225)  # 16:9 缩略图


def load_env():
    """手动从 .env 文件加载环境变量 (为了避免增加 python-dotenv 依赖)"""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


def get_date_from_meta(meta):
    """从元数据获取日期字符串 (YYYY-MM-DD)"""
    start_date = meta.get("startdate")
    if not start_date:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"


def fetch_bing_metadata():
    """获取必应每日壁纸元数据"""
    params = {
        "format": "js",
        "idx": 0,
        "n": 1,
        "mkt": "zh-CN"
    }
    resp = requests.get(BING_API, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["images"][0]


def download_image(url: str, save_path: Path):
    """下载图片到指定路径"""
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    save_path.write_bytes(r.content)


def generate_thumbnail(image_path: Path, thumb_path: Path):
    """生成缩略图"""
    with Image.open(image_path) as img:
        img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        # 确保目录存在 (为了 batch_fetch)
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(thumb_path, "JPEG", quality=85)


def generate_story(title, copyright, image_path: Path):
    """通过支持视觉的 LLM 生成壁纸背景故事"""
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model_name = os.environ.get("LLM_MODEL_NAME", "gpt-4o") # 默认尝试视觉模型
    
    if not api_key:
        return None

    # 从外部文件加载提示词
    prompt_file = Path(os.environ.get("STORY_PROMPT_FILE", "prompts/story_prompt.txt"))
    if prompt_file.exists():
        system_prompt = prompt_file.read_text(encoding="utf-8").strip()
    else:
        system_prompt =  "你是一位地理与文化深度旅行作家。请结合提供的图片内容、标题和背景信息，写一篇约 500 字的精美短文。要求：\n1. 直接输出 Markdown 正文，不要包含“好的”、“这是一篇...”等开头或结尾的客套话。\n2. 标题使用一级标题 (# Title)。\n3. 内容要包含对画面视觉细节（光影、色彩、构图）的细腻描写，并自然引出背后的地理文化故事。\n4. 语言风格优美、感性且富有深度。"
    
    print(f"[INFO] 正在为 '{title}' 生成视觉深度故事...")
    try:
        # 读取图片并编码为 base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "system", 
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"题目：{title}\n背景项：{copyright}\n请结合这张图片进行创作。"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        result = resp.json()
        story_text = result["choices"][0]["message"]["content"]
        
        # 在文章头部插入原图展示（根据图片文件名动态调整）
        image_filename = image_path.name  # 获取实际文件名
        final_content = f"![{title}]({image_filename})\n\n{story_text}"
        return final_content
    except Exception as e:
        print(f"[WARN] 视觉故事生成失败: {e}")
        return None


def push_to_wecom(webhook_url: str, image_path: Path, meta: dict, story_content: str = None):
    """推送图片、消息和故事到企业微信"""
    try:
        # 1. 发送图片
        send_image_to_wecom(webhook_url, str(image_path))
        print("[OK] 企业微信图片推送成功")

        # 2. 发送 markdown 消息（元数据）
        send_markdown_to_wecom(webhook_url, meta)
        print("[OK] 企业微信消息推送成功")
        
        # 3. 发送故事内容（如果存在）
        if story_content:
            send_story_to_wecom(webhook_url, meta, story_content)
            print("[OK] 企业微信故事推送成功")
    except Exception as e:
        print(f"[WARN] 企业微信推送失败: {e}")


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='抓取必应每日壁纸')
    parser.add_argument('--skip-story', action='store_true', help='跳过 AI 故事生成（快速模式）')
    args = parser.parse_args()
    
    load_env()

    # 1. 获取元数据（尝试今天，如果不存在则使用昨天）
    print(f"[INFO] 正在获取必应壁纸...")
    
    for idx in [0, 1]:  # 0=今天, 1=昨天
        params = {
            "format": "js",
            "idx": idx,
            "n": 1,
            "mkt": "zh-CN"
        }
        resp = requests.get(BING_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        meta = data["images"][0]
        
        # 使用 API 返回的日期作为文件夹名
        today = get_date_from_meta(meta)
        base_dir = Path("wallpapers/bing") / today
        
        # 如果该日期的壁纸已存在，跳过
        if base_dir.exists() and (base_dir / "image.jpg").exists():
            if idx == 0:
                print(f"[INFO] {today} 的壁纸已存在，不再重复下载。")
                return
            else:
                continue  # 尝试下一个
        
        # 找到可用的壁纸，跳出循环
        print(f"[INFO] 使用 {today} 的壁纸（idx={idx}）")
        break
    
    base_dir.mkdir(parents=True, exist_ok=True)

    # 2. 下载原图
    image_url = BING_BASE + meta["url"]
    image_path = base_dir / "image.jpg"
    download_image(image_url, image_path)
    print(f"[OK] 壁纸已下载: {image_path} ({meta.get('title')})")

    # 3. 生成缩略图
    thumb_path = base_dir / "thumb.jpg"
    generate_thumbnail(image_path, thumb_path)
    print(f"[OK] 缩略图已生成: {thumb_path}")

    # 4. 生成 AI 故事 (带视觉) - 可选
    story_content = None
    if not args.skip_story:
        story_content = generate_story(meta.get("title"), meta.get("copyright"), image_path)
        if story_content:
            (base_dir / "story.md").write_text(story_content, encoding="utf-8")
            print(f"[OK] AI 故事已生成: {base_dir / 'story.md'}")
    else:
        print(f"[INFO] 跳过故事生成（使用 --skip-story）")

    # 5. 保存元数据
    meta_path = base_dir / "meta.json"
    meta_info = {
        "date": today,
        "title": meta.get("title"),
        "copyright": meta.get("copyright"),
        "image_url": image_url,
        "has_story": bool(story_content)
    }
    meta_path.write_text(
        json.dumps(meta_info, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"[OK] 元数据已保存: {meta_path}")

    # 6. 更新 README
    update_readme()
    print("[OK] README.md 已更新")

    # 7. 更新 Gallery
    update_gallery()
    print("[OK] docs/index.html 已更新")

    # 8. 推送企业微信
    webhook_url = os.environ.get("WEWORK_WEBHOOK")
    if webhook_url:
        push_to_wecom(webhook_url, image_path, meta_info, story_content)
    else:
        print("[INFO] WEWORK_WEBHOOK 未配置，跳过推送")

    print(f"\n✅ 完成！壁纸已归档至 {base_dir}")


if __name__ == "__main__":
    main()
