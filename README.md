# 📸 Daily Bing Wallpaper Archive

> 自动采集必应 (Bing) 每日高清壁纸，支持 GitHub Actions 自动化归档、在线画廊展示与企业微信机器人提醒。

[![Daily Update](https://github.com/Hana19951208/DailyBingWallpaper/actions/workflows/daily.yml/badge.svg)](https://github.com/Hana19951208/DailyBingWallpaper/actions/workflows/daily.yml)
[![Pages](https://img.shields.io/badge/GitHub%20Pages-Online-brightgreen)](https://Hana19951208.github.io/DailyBingWallpaper/)

---

## ✨ 项目特性

- **自动化**: 利用 GitHub Actions 每天北京时间 08:00 自动抓取。
- **持久化**: 高清原图、缩略图及元数据 (JSON) 自动提交至仓库，永不丢失。
- **现代化展示**: 内置 GitHub Pages 在线画廊，支持响应式布局与暗黑模式。
- **多端推送**: 集成企业微信群机器人，消息样式精美。
- **零成本**: 完全基于 GitHub 免费资源构建。

---

## 🖼 效果展示

### 在线画廊

![Gallery Screenshot](https://via.placeholder.com/800x400.png?text=Preview+of+Glassmorphism+Gallery)

---

## 📅 壁纸索引 (最新)

<!-- WALLPAPER_INDEX_START -->
- **2025-12-18**  
  ![](wallpapers/2025-12-18/thumb.jpg)
<!-- WALLPAPER_INDEX_END -->

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Hana19951208/DailyBingWallpaper.git
cd DailyBingWallpaper
```

### 2. 本地测试

```bash
# 安装依赖
pip install requests Pillow

# 配置 Webhook (可选)
export WEWORK_WEBHOOK="https://qyapi.weixin.qq.com/..."

# 运行脚本
python fetch_bing_wallpaper.py
```

### 3. 部署指南

1. **Fork 仓库**: 将本项目 Fork 到你自己的账号。
2. **配置 Secrets**: 在仓库 `Settings > Secrets and variables > Actions` 中添加 `WEWORK_WEBHOOK` 地址。
3. **开启 Pages**: 在仓库 `Settings > Pages` 中，设置 Source 为 `main` 分支的 `/docs` 目录。
4. **激活 Actions**: 在 `Actions` 标签页，启用工作流。

---

## 📂 目录结构

```text
.
├── .github/workflows/   # CI/CD 自动化流
├── docs/                # GitHub Pages 静态网页
├── wallpapers/          # 存档的壁纸素材 (按日期分类)
├── src/                 # 核心模块
│   ├── utils.py         # 工具库 (WeChat 推送等)
│   ├── update_readme.py # README 索引更新
│   └── update_gallery.py# 画廊 HTML 更新
├── fetch_bing_wallpaper.py # 主入口脚本
└── README.md            # 项目文档
```

---

## ⚖️ 开源协议

本项目基于 MIT 协议开源。仅供学习交流，壁纸版权归微软必应所有。
