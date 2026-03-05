# ☁️ 云服务器价格监控系统

监控主流云厂商的香港地区服务器价格和优惠活动。

## 📊 监控厂商

| 厂商 | 产品 | 地区 |
|------|------|------|
| 腾讯云 | 轻量应用服务器 (Lighthouse) | 香港 |
| 阿里云 | 轻量应用服务器 (SWAS) | 香港 |
| 华为云 | HECS 云服务器 | 香港 |
| AWS | Lightsail | Asia Pacific (Hong Kong) |

## 🎯 监控配置

- **内存配置**: 2G / 4G / 8G
- **检查频率**: 每天 2 次（北京时间 8:00 和 20:00）
- **通知方式**: Telegram
- **通知规则**: 
  - 每天 2 次定时报告（无论有无变化）
  - 价格/活动变动立即通知

## 🚀 GitHub Actions 自动运行

本系统通过 GitHub Actions 定时运行，自动推送价格数据到本仓库。

### 配置 Secrets

在仓库 Settings → Secrets and variables → Actions 中配置：

| Secret Name | Value |
|-------------|-------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID |

### 手动触发

1. 进入 **Actions** 标签
2. 选择 **Cloud Price Monitor**
3. 点击 **Run workflow**

## 📁 文件结构

```
cloud-price-monitor/
├── .github/workflows/
│   └── cloud_price_monitor.yml    # GitHub Actions 配置
├── tools/
│   └── cloud_price_monitor_github.py    # 监控脚本
├── cloud_prices/
│   ├── prices.json               # 当前价格数据
│   ├── activities.json           # 活动监控数据
│   ├── history.json              # 历史记录
│   └── README.md                 # 详细说明
└── README.md                     # 本文件
```

## 💰 当前价格参考

### 4G 内存配置（月付）

| 厂商 | 配置 | 月付 | 年付 |
|------|------|------|------|
| 腾讯云轻量 | 2 核 4G | ¥72 | ¥720 |
| 华为云 HECS | 2 核 4G | ¥82 | ¥820 |
| 阿里云轻量 | 2 核 4G | ¥89 | ¥890 |
| AWS Lightsail | 2 核 4G | ¥172 | ¥2073 |

### 8G 内存配置（月付）

| 厂商 | 配置 | 月付 | 年付 |
|------|------|------|------|
| 腾讯云轻量 | 4 核 8G | ¥144 | ¥1440 |
| 华为云 HECS | 4 核 8G | ¥165 | ¥1650 |
| 阿里云轻量 | 4 核 8G | ¥178 | ¥1780 |
| AWS Lightsail | 4 核 8G | ¥345 | ¥4147 |

> 💡 **性价比推荐**: 腾讯云轻量 - 带宽最大（30Mbps），价格最低

## ⚠️ 注意事项

1. **价格准确性**: 当前为预设参考价，实际价格以官网为准
2. **活动监控限制**: 只能监控公开页面，登录后可见的专享优惠无法监控
3. **汇率**: AWS 价格按 1 USD = 7.2 CNY 计算

## 📝 更新价格

编辑 `tools/cloud_price_monitor_github.py` 中的价格函数：
- `fetch_tencent_prices()`
- `fetch_aliyun_prices()`
- `fetch_huawei_prices()`
- `fetch_aws_prices()`

## 🔗 链接

- GitHub 仓库：https://github.com/zxmlysxl/cloud-price-monitor
- Actions 日志：https://github.com/zxmlysxl/cloud-price-monitor/actions

---

**最后更新**: 2026-03-05
