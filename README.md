# Cloud Price Monitor - 云服务器价格监控

监控香港地区云服务器价格变动和厂商活动。

## 功能

- **价格监控**: 腾讯、阿里、华为、AWS 轻量应用服务器
- **活动监控**: 智能去重，检测新活动
- **Telegram 通知**: 价格变动 + 新活动推送
- **历史记录**: 本地 JSON 存储，支持版本对比

## 监控厂商

| 厂商 | 产品 | 地区 |
|------|------|------|
| 腾讯云 | 轻量应用服务器 | 香港 |
| 阿里云 | 轻量应用服务器 | 香港 |
| 华为云 | HECS | 香港 |
| AWS | Lightsail | 香港 |
| Vultr | VPS | - |

## 配置

复制 `.env.example` 并修改：

```bash
cp .env.example .env
# 编辑 .env 填入你的 Telegram bot token 和 chat_id
```

## 运行

```bash
# 安装依赖
pip install requests beautifulsoup4 playwright

# 手动运行
python3 cloud_price_monitor_github.py

# 定时任务（crontab）
# 每天 8:00 和 20:00
0 8,20 * * * cd /path/to/repo && python3 cloud_price_monitor_github.py
```

## 目录结构

```
cloud-price-monitor/
├── cloud_price_monitor_github.py  # 主脚本
├── cloud_price_monitor.py         # 旧版本脚本
├── lib/
│   ├── scrapers.py                # 价格爬虫
│   ├── activities.py              # 活动监控
│   └── notify.py                  # Telegram 通知
├── cloud_prices/
│   ├── prices.json                # 价格数据
│   ├── activities.json            # 活动数据
│   └── history.json               # 历史记录
└── .env                           # Telegram 配置（不提交）
```

## GitHub Actions

可配置 CI 自动运行，每天定时抓取价格。
