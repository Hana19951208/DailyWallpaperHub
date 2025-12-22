#!/usr/bin/env python3
"""
集成功能测试脚本
用于验证：
1. 企业微信推送（多源标识、消息清洗）
2. 腾讯云 COS 上传功能
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_bing_wallpaper import load_env
from src.utils import send_image_to_wecom, send_markdown_to_wecom, send_story_to_wecom, upload_to_cos

def test_wecom_push():
    print("\n--- [1/2] 测试企业微信推送 ---")
    webhook_url = os.environ.get("WEWORK_WEBHOOK")
    if not webhook_url:
        print("❌ 错误: WEWORK_WEBHOOK 未配置，跳过测试")
        return False

    # 寻找一个现有的图片进行测试
    sample_image = None
    for path in Path("docs/wallpapers").rglob("thumb.jpg"):
        sample_image = path
        break
    
    if not sample_image:
        print("⚠️ 警告: docs/wallpapers 目录下没有找到测试图片，请先运行抓取脚本")
        return False

    meta_test = {
        "title": "测试推送 - 集成功能验证",
        "copyright": "Antigravity Test Suite",
        "date": datetime.now().strftime("%Y-%m-%d")
    }
    
    story_test_content = """# 测试故事标题内容
![TEST](image.jpg)

这是一段用于测试的故事文本。
包含了一些应该被清洗掉的 Markdown 语法，比如上面的图片标签。
以及一段足够长的话来测试内容截断逻辑... """ + "测试文本" * 50

    try:
        print(f"1. 正在推送图片: {sample_image}")
        send_image_to_wecom(webhook_url, str(sample_image))
        
        print("2. 正在推送 Unsplash 标识的 Markdown 消息")
        send_markdown_to_wecom(webhook_url, meta_test, source_name="Unsplash")
        
        print("3. 正在推送清洗后的故事内容")
        send_story_to_wecom(webhook_url, meta_test, story_test_content)
        
        print("✅ 企业微信推送测试流程通过")
        return True
    except Exception as e:
        print(f"❌ 企业微信推送测试失败: {e}")
        return False

def test_cos_upload():
    print("\n--- [2/2] 测试腾讯云 COS 上传 ---")
    
    # 创建一个临时的测试文件
    test_file = Path("cos_test_temp.txt")
    test_file.write_text(f"COS Integration Test at {datetime.now()}", encoding="utf-8")
    
    cos_path = f"tests/integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    try:
        print(f"正在上传测试文件到: {cos_path}")
        url = upload_to_cos(str(test_file), cos_path)
        if url:
            print(f"✅ COS 上传成功! 访问地址: {url}")
            return True
        else:
            print("❌ COS 上传返回为空 (可能是配置缺失)")
            return False
    except Exception as e:
        print(f"❌ COS 上传测试过程报错: {e}")
        return False
    finally:
        if test_file.exists():
            test_file.unlink()

def main():
    load_env()
    
    print("🚀 开始集成功能验证...")
    wecom_ok = test_wecom_push()
    cos_ok = test_cos_upload()
    
    print("\n" + "="*30)
    print("测试结果汇总:")
    print(f"企业微信推送: {'✅ 通过' if wecom_ok else '❌ 未通过'}")
    print(f"腾讯云 COS:   {'✅ 通过' if cos_ok else '❌ 未通过' or '⚠️ 未配置'}")
    print("="*30)
    
    if wecom_ok and cos_ok:
        print("\n🎉 恭喜！所有新集成功能均已就绪。")
    else:
        print("\n💡 请检查 .env 配置文件中的密钥是否正确。")

if __name__ == "__main__":
    main()
