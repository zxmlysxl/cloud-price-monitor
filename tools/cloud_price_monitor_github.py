#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云服务器价格监控 - 香港地区
监控厂商：腾讯云、阿里云、华为云、AWS
配置：4G/8G 内存
功能：价格监控 + 活动页面监控
"""

import json
import hashlib
import os
import subprocess
from datetime import datetime
from pathlib import Path
import re
import requests
from bs4 import BeautifulSoup

# 配置 - 使用相对于脚本所在仓库的路径
SCRIPT_DIR = Path(__file__).parent.parent
DATA_DIR = SCRIPT_DIR / "cloud_prices"
DATA_DIR.mkdir(exist_ok=True)
PRICE_FILE = DATA_DIR / "prices.json"
HISTORY_FILE = DATA_DIR / "history.json"
ACTIVITY_FILE = DATA_DIR / "activities.json"

# Telegram 配置（从环境变量读取）
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1088831643")

# 云厂商配置 - 仅香港地区
PROVIDERS = {
    "tencent": {
        "name": "腾讯云轻量",
        "url": "https://cloud.tencent.com/product/lighthouse",
        "activity_url": "https://cloud.tencent.com/act",
        "region": "香港",
    },
    "aliyun": {
        "name": "阿里云轻量",
        "url": "https://www.aliyun.com/product/swas",
        "activity_url": "https://www.aliyun.com/activity",
        "region": "香港",
    },
    "huawei": {
        "name": "华为云 HECS",
        "url": "https://www.huaweicloud.com/product/hecs.html",
        "activity_url": "https://activity.huaweicloud.com",
        "region": "香港",
    },
    "aws": {
        "name": "AWS Lightsail",
        "url": "https://aws.amazon.com/lightsail/pricing/",
        "activity_url": "https://aws.amazon.com/cn/free/",
        "region": "Hong Kong",
    },
    "vultr": {
        "name": "Vultr",
        "url": "https://www.vultr.com/products/cloud-compute/",
        "activity_url": "https://www.vultr.com/promo/",
        "region": "Hong Kong",
    },
    "pccw": {
        "name": "PCCW Global",
        "url": "https://www.pccwglobal.com/",
        "activity_url": "https://www.pccwglobal.com/",
        "region": "Hong Kong",
    },
    "bandwagon": {
        "name": "BandwagonHost (搬瓦工)",
        "url": "https://bwh81.net/",
        "activity_url": "https://bwh81.net/",
        "region": "Hong Kong CN2 GIA",
    },
    "dmit": {
        "name": "DMIT",
        "url": "https://www.dmit.io/",
        "activity_url": "https://www.dmit.io/",
        "region": "Hong Kong",
    },
}

# 目标配置
TARGET_CONFIGS = ["4G", "8G"]


def load_prices():
    """加载当前价格数据"""
    if PRICE_FILE.exists():
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_history():
    """加载历史记录"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def load_activities():
    """加载活动数据"""
    if ACTIVITY_FILE.exists():
        with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"activities": {}, "last_check": None}


def save_activities(activities):
    """保存活动数据"""
    with open(ACTIVITY_FILE, "w", encoding="utf-8") as f:
        json.dump(activities, f, ensure_ascii=False, indent=2)


def save_prices(prices):
    """保存价格数据"""
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, ensure_ascii=False, indent=2)


def save_history(history):
    """保存历史记录"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_data_hash(data):
    """生成数据哈希用于检测变化"""
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()


def fetch_tencent_prices():
    """
    腾讯云轻量应用服务器价格
    由于需要登录和动态加载，使用预设价格（需定期更新）
    """
    # 这些是常见配置的价格（月付，人民币）
    # 实际价格需要从官网获取或手动更新
    return [
        {
            "provider": "tencent",
            "provider_name": "腾讯云轻量",
            "config": "2 核 2G",
            "cpu": 2,
            "memory": "2G",
            "storage": "50GB SSD",
            "bandwidth": "30Mbps",
            "traffic": "2000GB/月",
            "price_monthly": 48,
            "price_yearly": 480,
            "currency": "CNY",
            "region": "香港",
            "url": "https://cloud.tencent.com/product/lighthouse",
        },
        {
            "provider": "tencent",
            "provider_name": "腾讯云轻量",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "30Mbps",
            "traffic": "3000GB/月",
            "price_monthly": 72,
            "price_yearly": 720,
            "currency": "CNY",
            "region": "香港",
            "url": "https://cloud.tencent.com/product/lighthouse",
        },
        {
            "provider": "tencent",
            "provider_name": "腾讯云轻量",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "100GB SSD",
            "bandwidth": "30Mbps",
            "traffic": "4000GB/月",
            "price_monthly": 144,
            "price_yearly": 1440,
            "currency": "CNY",
            "region": "香港",
            "url": "https://cloud.tencent.com/product/lighthouse",
        },
    ]


def fetch_aliyun_prices():
    """
    阿里云轻量应用服务器价格
    """
    return [
        {
            "provider": "aliyun",
            "provider_name": "阿里云轻量",
            "config": "2 核 2G",
            "cpu": 2,
            "memory": "2G",
            "storage": "60GB SSD",
            "bandwidth": "5Mbps",
            "traffic": "1500GB/月",
            "price_monthly": 59,
            "price_yearly": 590,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.aliyun.com/product/swas",
        },
        {
            "provider": "aliyun",
            "provider_name": "阿里云轻量",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "6Mbps",
            "traffic": "2000GB/月",
            "price_monthly": 89,
            "price_yearly": 890,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.aliyun.com/product/swas",
        },
        {
            "provider": "aliyun",
            "provider_name": "阿里云轻量",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "120GB SSD",
            "bandwidth": "8Mbps",
            "traffic": "3000GB/月",
            "price_monthly": 178,
            "price_yearly": 1780,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.aliyun.com/product/swas",
        },
    ]


def fetch_huawei_prices():
    """
    华为云 HECS 价格
    """
    return [
        {
            "provider": "huawei",
            "provider_name": "华为云 HECS",
            "config": "2 核 2G",
            "cpu": 2,
            "memory": "2G",
            "storage": "40GB SSD",
            "bandwidth": "1Mbps",
            "traffic": "按量",
            "price_monthly": 52,
            "price_yearly": 520,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.huaweicloud.com/product/hecs.html",
        },
        {
            "provider": "huawei",
            "provider_name": "华为云 HECS",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "60GB SSD",
            "bandwidth": "2Mbps",
            "traffic": "按量",
            "price_monthly": 82,
            "price_yearly": 820,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.huaweicloud.com/product/hecs.html",
        },
        {
            "provider": "huawei",
            "provider_name": "华为云 HECS",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "100GB SSD",
            "bandwidth": "3Mbps",
            "traffic": "按量",
            "price_monthly": 165,
            "price_yearly": 1650,
            "currency": "CNY",
            "region": "香港",
            "url": "https://www.huaweicloud.com/product/hecs.html",
        },
    ]


def fetch_aws_prices():
    """
    AWS Lightsail 价格（美元）
    """
    # AWS 价格通常是美元，需要转换
    usd_to_cny = 7.2  # 汇率，可更新
    return [
        {
            "provider": "aws",
            "provider_name": "AWS Lightsail",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "60GB SSD",
            "bandwidth": "2Mbps",
            "traffic": "2000GB/月",
            "price_monthly": int(12 * usd_to_cny),
            "price_yearly": int(12 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Asia Pacific (Hong Kong)",
            "url": "https://aws.amazon.com/lightsail/pricing/",
        },
        {
            "provider": "aws",
            "provider_name": "AWS Lightsail",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "3Mbps",
            "traffic": "3000GB/月",
            "price_monthly": int(24 * usd_to_cny),
            "price_yearly": int(24 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Asia Pacific (Hong Kong)",
            "url": "https://aws.amazon.com/lightsail/pricing/",
        },
        {
            "provider": "aws",
            "provider_name": "AWS Lightsail",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "160GB SSD",
            "bandwidth": "5Mbps",
            "traffic": "5000GB/月",
            "price_monthly": int(48 * usd_to_cny),
            "price_yearly": int(48 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Asia Pacific (Hong Kong)",
            "url": "https://aws.amazon.com/lightsail/pricing/",
        },
    ]


def fetch_google_prices():
    """
    Google Cloud 价格（美元转换）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "google",
            "provider_name": "Google Cloud",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "40GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(15 * usd_to_cny),
            "price_yearly": int(15 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "asia-east1",
            "url": "https://cloud.google.com/compute",
        },
        {
            "provider": "google",
            "provider_name": "Google Cloud",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "60GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(35 * usd_to_cny),
            "price_yearly": int(35 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "asia-east1",
            "url": "https://cloud.google.com/compute",
        },
        {
            "provider": "google",
            "provider_name": "Google Cloud",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "100GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(70 * usd_to_cny),
            "price_yearly": int(70 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "asia-east1",
            "url": "https://cloud.google.com/compute",
        },
    ]


def fetch_azure_prices():
    """
    Microsoft Azure 价格（美元转换）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "azure",
            "provider_name": "Microsoft Azure",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "32GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(12 * usd_to_cny),
            "price_yearly": int(12 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "East Asia",
            "url": "https://azure.microsoft.com/zh-cn/pricing/details/virtual-machines/",
        },
        {
            "provider": "azure",
            "provider_name": "Microsoft Azure",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "64GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(30 * usd_to_cny),
            "price_yearly": int(30 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "East Asia",
            "url": "https://azure.microsoft.com/zh-cn/pricing/details/virtual-machines/",
        },
        {
            "provider": "azure",
            "provider_name": "Microsoft Azure",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "128GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(60 * usd_to_cny),
            "price_yearly": int(60 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "East Asia",
            "url": "https://azure.microsoft.com/zh-cn/pricing/details/virtual-machines/",
        },
    ]


def fetch_oracle_prices():
    """
    Oracle Cloud 价格（含免费层）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "oracle",
            "provider_name": "Oracle Cloud",
            "config": "免费层 1G",
            "cpu": 1,
            "memory": "1G",
            "storage": "50GB",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": 0,
            "price_yearly": 0,
            "currency": "CNY",
            "region": "Asia Pacific",
            "url": "https://www.oracle.com/cloud/free/",
            "note": "永久免费层",
        },
        {
            "provider": "oracle",
            "provider_name": "Oracle Cloud",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "60GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(25 * usd_to_cny),
            "price_yearly": int(25 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Asia Pacific",
            "url": "https://www.oracle.com/cloud/compute/",
        },
        {
            "provider": "oracle",
            "provider_name": "Oracle Cloud",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "100GB SSD",
            "bandwidth": "按量",
            "traffic": "按量",
            "price_monthly": int(50 * usd_to_cny),
            "price_yearly": int(50 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Asia Pacific",
            "url": "https://www.oracle.com/cloud/compute/",
        },
    ]


def fetch_digitalocean_prices():
    """
    DigitalOcean Droplets 价格（美元转换）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "digitalocean",
            "provider_name": "DigitalOcean",
            "config": "1 核 1G",
            "cpu": 1,
            "memory": "1G",
            "storage": "25GB SSD",
            "bandwidth": "1TB/月",
            "traffic": "1000GB/月",
            "price_monthly": int(6 * usd_to_cny),
            "price_yearly": int(6 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.digitalocean.com/pricing",
        },
        {
            "provider": "digitalocean",
            "provider_name": "DigitalOcean",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "50GB SSD",
            "bandwidth": "2TB/月",
            "traffic": "2000GB/月",
            "price_monthly": int(12 * usd_to_cny),
            "price_yearly": int(12 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.digitalocean.com/pricing",
        },
        {
            "provider": "digitalocean",
            "provider_name": "DigitalOcean",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "4TB/月",
            "traffic": "4000GB/月",
            "price_monthly": int(24 * usd_to_cny),
            "price_yearly": int(24 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.digitalocean.com/pricing",
        },
        {
            "provider": "digitalocean",
            "provider_name": "DigitalOcean",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "160GB SSD",
            "bandwidth": "5TB/月",
            "traffic": "5000GB/月",
            "price_monthly": int(48 * usd_to_cny),
            "price_yearly": int(48 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.digitalocean.com/pricing",
        },
    ]


def fetch_vultr_prices():
    """
    Vultr Cloud Compute 价格（美元转换）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "vultr",
            "provider_name": "Vultr",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "55GB SSD",
            "bandwidth": "2TB/月",
            "traffic": "2000GB/月",
            "price_monthly": int(12 * usd_to_cny),
            "price_yearly": int(12 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.vultr.com/products/cloud-compute/",
        },
        {
            "provider": "vultr",
            "provider_name": "Vultr",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "3TB/月",
            "traffic": "3000GB/月",
            "price_monthly": int(24 * usd_to_cny),
            "price_yearly": int(24 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.vultr.com/products/cloud-compute/",
        },
        {
            "provider": "vultr",
            "provider_name": "Vultr",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "160GB SSD",
            "bandwidth": "4TB/月",
            "traffic": "4000GB/月",
            "price_monthly": int(48 * usd_to_cny),
            "price_yearly": int(48 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.vultr.com/products/cloud-compute/",
        },
    ]


def fetch_linode_prices():
    """
    Linode (Akamai) 价格（美元转换）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "linode",
            "provider_name": "Linode (Akamai)",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "50GB SSD",
            "bandwidth": "2TB/月",
            "traffic": "2000GB/月",
            "price_monthly": int(10 * usd_to_cny),
            "price_yearly": int(10 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.linode.com/pricing/",
        },
        {
            "provider": "linode",
            "provider_name": "Linode (Akamai)",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "4TB/月",
            "traffic": "4000GB/月",
            "price_monthly": int(20 * usd_to_cny),
            "price_yearly": int(20 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.linode.com/pricing/",
        },
        {
            "provider": "linode",
            "provider_name": "Linode (Akamai)",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "160GB SSD",
            "bandwidth": "5TB/月",
            "traffic": "5000GB/月",
            "price_monthly": int(40 * usd_to_cny),
            "price_yearly": int(40 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Singapore",
            "url": "https://www.linode.com/pricing/",
        },
    ]


def fetch_pccw_prices():
    """
    PCCW Global 价格（预设参考价）
    """
    return [
        {
            "provider": "pccw",
            "provider_name": "PCCW Global",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "10Mbps",
            "traffic": "不限",
            "price_monthly": 180,
            "price_yearly": 1800,
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.pccwglobal.com/",
        },
        {
            "provider": "pccw",
            "provider_name": "PCCW Global",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "120GB SSD",
            "bandwidth": "20Mbps",
            "traffic": "不限",
            "price_monthly": 360,
            "price_yearly": 3600,
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.pccwglobal.com/",
        },
    ]


def fetch_bandwagon_prices():
    """
    BandwagonHost (搬瓦工) CN2 GIA 价格
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "bandwagon",
            "provider_name": "BandwagonHost (搬瓦工)",
            "config": "1 核 1G",
            "cpu": 1,
            "memory": "1G",
            "storage": "20GB SSD",
            "bandwidth": "1Gbps",
            "traffic": "1000GB/月",
            "price_monthly": int(5 * usd_to_cny),
            "price_yearly": int(5 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong CN2 GIA",
            "url": "https://bwh81.net/",
            "note": "CN2 GIA 线路",
        },
        {
            "provider": "bandwagon",
            "provider_name": "BandwagonHost (搬瓦工)",
            "config": "2 核 2G",
            "cpu": 2,
            "memory": "2G",
            "storage": "40GB SSD",
            "bandwidth": "1Gbps",
            "traffic": "2000GB/月",
            "price_monthly": int(10 * usd_to_cny),
            "price_yearly": int(10 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong CN2 GIA",
            "url": "https://bwh81.net/",
            "note": "CN2 GIA 线路",
        },
        {
            "provider": "bandwagon",
            "provider_name": "BandwagonHost (搬瓦工)",
            "config": "4 核 4G",
            "cpu": 4,
            "memory": "4G",
            "storage": "80GB SSD",
            "bandwidth": "2.5Gbps",
            "traffic": "3000GB/月",
            "price_monthly": int(20 * usd_to_cny),
            "price_yearly": int(20 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong CN2 GIA",
            "url": "https://bwh81.net/",
            "note": "CN2 GIA 线路",
        },
    ]


def fetch_dmit_prices():
    """
    DMIT 价格（预设参考价）
    """
    usd_to_cny = 7.2
    return [
        {
            "provider": "dmit",
            "provider_name": "DMIT",
            "config": "1 核 2G",
            "cpu": 1,
            "memory": "2G",
            "storage": "30GB SSD",
            "bandwidth": "100Mbps",
            "traffic": "800GB/月",
            "price_monthly": int(8 * usd_to_cny),
            "price_yearly": int(8 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.dmit.io/",
            "note": "CN2/9929 线路可选",
        },
        {
            "provider": "dmit",
            "provider_name": "DMIT",
            "config": "2 核 4G",
            "cpu": 2,
            "memory": "4G",
            "storage": "60GB SSD",
            "bandwidth": "200Mbps",
            "traffic": "1500GB/月",
            "price_monthly": int(16 * usd_to_cny),
            "price_yearly": int(16 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.dmit.io/",
            "note": "CN2/9929 线路可选",
        },
        {
            "provider": "dmit",
            "provider_name": "DMIT",
            "config": "4 核 8G",
            "cpu": 4,
            "memory": "8G",
            "storage": "120GB SSD",
            "bandwidth": "400Mbps",
            "traffic": "3000GB/月",
            "price_monthly": int(32 * usd_to_cny),
            "price_yearly": int(32 * usd_to_cny * 12),
            "currency": "CNY",
            "region": "Hong Kong",
            "url": "https://www.dmit.io/",
            "note": "CN2/9929 线路可选",
        },
    ]


def fetch_all_prices():
    """获取所有厂商价格 - 仅香港地区"""
    all_prices = []
    all_prices.extend(fetch_tencent_prices())
    all_prices.extend(fetch_aliyun_prices())
    all_prices.extend(fetch_huawei_prices())
    all_prices.extend(fetch_aws_prices())
    all_prices.extend(fetch_vultr_prices())
    all_prices.extend(fetch_pccw_prices())
    all_prices.extend(fetch_bandwagon_prices())
    all_prices.extend(fetch_dmit_prices())
    return all_prices


def compare_prices(old_prices, new_prices):
    """比较价格变化"""
    changes = []
    old_dict = {(p["provider"], p["config"]): p for p in old_prices}
    
    for new in new_prices:
        key = (new["provider"], new["config"])
        old = old_dict.get(key)
        
        if old is None:
            changes.append({
                "type": "new",
                "provider": new["provider_name"],
                "config": new["config"],
                "new_price": new["price_monthly"],
            })
        elif old["price_monthly"] != new["price_monthly"]:
            diff = new["price_monthly"] - old["price_monthly"]
            change_type = "up" if diff > 0 else "down"
            changes.append({
                "type": change_type,
                "provider": new["provider_name"],
                "config": new["config"],
                "old_price": old["price_monthly"],
                "new_price": new["price_monthly"],
                "diff": abs(diff),
            })
    
    return changes


def generate_price_table(prices):
    """生成价格对比表（Markdown 格式）"""
    # 按配置分组
    configs = {}
    for p in prices:
        mem = p["memory"]
        if mem not in configs:
            configs[mem] = []
        configs[mem].append(p)
    
    lines = []
    lines.append("## 🌐 云服务器价格对比（香港地区）")
    lines.append(f"_更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n")
    
    for mem in sorted(configs.keys()):
        lines.append(f"### 💾 {mem} 内存配置\n")
        lines.append("| 厂商 | 配置 | CPU | 存储 | 带宽 | 流量 | 月付 | 年付 |")
        lines.append("|------|------|-----|------|------|------|------|------|")
        
        for p in sorted(configs[mem], key=lambda x: x["price_monthly"]):
            lines.append(
                f"| {p['provider_name']} | {p['config']} | {p['cpu']}核 | "
                f"{p['storage']} | {p['bandwidth']} | {p['traffic']} | "
                f"¥{p['price_monthly']} | ¥{p['price_yearly']} |"
            )
        lines.append("")
    
    # 最便宜推荐
    lines.append("### 💰 性价比推荐\n")
    for mem in sorted(configs.keys()):
        cheapest = min(configs[mem], key=lambda x: x["price_monthly"])
        lines.append(
            f"- **{mem}**: {cheapest['provider_name']} {cheapest['config']} "
            f"¥{cheapest['price_monthly']}/月"
        )
    
    return "\n".join(lines)


def generate_change_message(changes):
    """生成价格变动通知"""
    if not changes:
        return "📊 价格监控报告\n\n本次检查无价格变动。"
    
    lines = ["🚨 **价格变动提醒**\n"]
    
    for c in changes:
        if c["type"] == "new":
            lines.append(
                f"🆕 {c['provider']} {c['config']}: ¥{c['new_price']}/月 (新上架)"
            )
        elif c["type"] == "down":
            lines.append(
                f"📉 {c['provider']} {c['config']}: "
                f"¥{c['old_price']} → ¥{c['new_price']} (↓¥{c['diff']})"
            )
        else:  # up
            lines.append(
                f"📈 {c['provider']} {c['config']}: "
                f"¥{c['old_price']} → ¥{c['new_price']} (↑¥{c['diff']})"
            )
    
    return "\n".join(lines)


def fetch_activity_page(url):
    """抓取活动页面内容（带重试机制）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            print(f"  ⚠️ 请求超时 ({attempt+1}/{max_retries}): {url}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
        except requests.exceptions.SSLError as e:
            print(f"  ⚠️ SSL 错误 ({attempt+1}/{max_retries}): {url} - {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️ 请求失败 ({attempt+1}/{max_retries}): {url} - {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(2)
    
    print(f"  ❌ 抓取失败（已重试 {max_retries} 次）: {url}")
    return None


def extract_activity_info(html, provider):
    """从 HTML 中提取活动信息"""
    if not html:
        return []
    
    activities = []
    
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # 移除脚本和样式
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        # 查找所有包含活动关键词的文本
        keywords = ["优惠", "特惠", "促销", "活动", "HOT", "折扣", "免费", "体验", "领券", "秒杀"]
        
        # 查找链接中的活动
        links = soup.find_all("a", href=True)
        for link in links[:50]:  # 最多检查 50 个链接
            text = link.get_text(strip=True)
            if any(kw in text for kw in keywords) and len(text) < 100:
                # 去重
                if not any(a["title"] == text for a in activities):
                    activities.append({
                        "title": text,
                        "provider": provider,
                        "url": link.get("href", ""),
                    })
        
        # 如果没找到，尝试查找标题
        if not activities:
            titles = soup.find_all(["h1", "h2", "h3", "h4", "h5"])
            for title in titles[:20]:
                text = title.get_text(strip=True)
                if any(kw in text for kw in keywords) and len(text) < 100:
                    if not any(a["title"] == text for a in activities):
                        activities.append({
                            "title": text,
                            "provider": provider,
                        })
    
    except Exception as e:
        print(f"解析活动页面失败 {provider}: {e}")
    
    return activities[:10]  # 最多返回 10 个活动


def check_activity_changes():
    """检查活动页面变化（完整显示所有厂商状态）"""
    old_data = load_activities()
    old_activities = old_data.get("activities", {})
    
    new_activities = {}
    changes = []
    check_results = []  # 记录所有厂商的检查状态
    
    print(f"\n{'='*60}")
    print(f"📊 开始检查 {len(PROVIDERS)} 个云厂商活动页面...")
    print(f"{'='*60}")
    
    for provider, config in PROVIDERS.items():
        activity_url = config.get("activity_url")
        if not activity_url:
            check_results.append(f"  ⚪ {config['name']}: 跳过（无活动 URL）")
            continue
        
        print(f"\n🔍 检查 {config['name']}...")
        html = fetch_activity_page(activity_url)
        
        if html:
            # 生成页面内容哈希
            page_hash = hashlib.md5(html.encode()).hexdigest()
            old_hash = old_activities.get(provider, {}).get("hash")
            
            # 提取活动信息
            activity_list = extract_activity_info(html, provider)
            
            new_activities[provider] = {
                "hash": page_hash,
                "url": activity_url,
                "activities": activity_list,
                "last_check": datetime.now().isoformat(),
            }
            
            # 检测变化
            if old_hash != page_hash:
                changes.append({
                    "provider": config["name"],
                    "url": activity_url,
                    "type": "updated",
                    "activities": activity_list[:3],  # 只显示前 3 个
                })
                status = f"  ⚠️ {config['name']}: 有更新！"
                if activity_list:
                    status += f"\n     └─ {activity_list[0]['title'][:50]}"
                check_results.append(status)
            else:
                check_results.append(f"  ✅ {config['name']}: 无变化")
        else:
            check_results.append(f"  ❌ {config['name']}: 抓取失败")
    
    # 打印完整检查结果
    print(f"\n{'='*60}")
    print("📋 检查结果汇总:")
    print(f"{'='*60}")
    for result in check_results:
        print(result)
    
    # 保存新数据
    save_activities({
        "activities": new_activities,
        "last_check": datetime.now().isoformat(),
    })
    
    return changes, check_results


def generate_activity_message(changes, check_results=None):
    """生成活动变动通知"""
    lines = ["\n\n🎉 **活动页面监控报告**\n"]
    
    if changes:
        lines.append("**📢 更新提醒:**\n")
        for c in changes:
            lines.append(f"\n**{c['provider']}**: {c['url']}")
            for act in c["activities"]:
                lines.append(f"  • {act['title']}")
    else:
        lines.append("本次活动页面检查无更新。\n")
    
    # 添加完整检查状态
    if check_results:
        lines.append("\n**📋 完整检查状态:**\n")
        for result in check_results:
            lines.append(result)
    
    return "\n".join(lines)


def send_telegram_message(message, split_long=False):
    """发送 Telegram 消息（支持分段发送长消息）"""
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️ 未配置 TELEGRAM_BOT_TOKEN，跳过消息发送")
        return False
    
    # Telegram 消息长度限制：4096 字符
    MAX_LENGTH = 4000  # 留一些余量
    
    if split_long and len(message) > MAX_LENGTH:
        # 分段发送
        parts = []
        current_part = ""
        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 > MAX_LENGTH:
                if current_part:
                    parts.append(current_part)
                current_part = line
            else:
                current_part = current_part + '\n' + line if current_part else line
        if current_part:
            parts.append(current_part)
        
        print(f"📤 消息过长 ({len(message)} 字符)，分段发送 {len(parts)} 条...")
        success_count = 0
        for i, part in enumerate(parts):
            header = f"**({i+1}/{len(parts)})**\n" if len(parts) > 1 else ""
            if send_single_message(header + part):
                success_count += 1
            import time
            time.sleep(0.5)  # 避免频率限制
        print(f"✅ 成功发送 {success_count}/{len(parts)} 条消息")
        return success_count > 0
    else:
        return send_single_message(message)


def send_single_message(message):
    """发送单条 Telegram 消息"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
        }
        response = requests.post(url, json=data, timeout=30)
        response.raise_for_status()
        print("✅ Telegram 消息发送成功")
        return True
    except Exception as e:
        print(f"❌ 发送消息失败：{e}")
        return False


def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始价格监控...")
    
    # === 价格监控 ===
    old_data = load_prices()
    old_prices = old_data.get("prices", [])
    old_hash = old_data.get("hash", "")
    
    new_prices = fetch_all_prices()
    new_hash = get_data_hash(new_prices)
    
    price_changes = compare_prices(old_prices, new_prices)
    
    save_prices({"prices": new_prices, "hash": new_hash, "updated": datetime.now().isoformat()})
    
    history = load_history()
    history["records"].append({
        "timestamp": datetime.now().isoformat(),
        "hash": new_hash,
        "changes_count": len(price_changes),
        "changes": price_changes,
    })
    history["records"] = history["records"][-100:]
    save_history(history)
    
    # === 活动页面监控 ===
    print(f"[{datetime.now()}] 检查活动页面...")
    activity_changes, check_results = check_activity_changes()
    
    # === 生成并发送消息 ===
    table_msg = generate_price_table(new_prices)
    
    if price_changes or activity_changes:
        # 有变化，发送详细通知
        msgs = []
        
        if price_changes:
            price_msg = generate_change_message(price_changes)
            msgs.append(price_msg)
        
        if activity_changes or check_results:
            activity_msg = generate_activity_message(activity_changes, check_results)
            msgs.append(activity_msg)
        
        full_msg = "\n\n".join(msgs) + f"\n\n{table_msg}"
        send_telegram_message(full_msg, split_long=True)
        print(f"发现 {len(price_changes)} 处价格变动，{len(activity_changes)} 个活动页面更新，已发送通知")
    else:
        # 无变化，发送定期检查报告（包含完整检查状态）
        report_lines = [
            f"📋 **定时价格检查**",
            f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "\n本次检查无价格变动。",
        ]
        if check_results:
            report_lines.append("\n**📋 活动页面检查状态:**\n")
            report_lines.extend(check_results)
        report_msg = "\n".join(report_lines) + f"\n\n{table_msg}"
        send_telegram_message(report_msg, split_long=True)
        print("无价格变动，已发送定期报告")
    
    print(f"[{datetime.now()}] 价格监控完成")


if __name__ == "__main__":
    main()
