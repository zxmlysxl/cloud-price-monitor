#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云服务器价格爬虫 - 各厂商独立函数
抓取失败返回空列表，不做兜底
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict

# 尝试 Playwright
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

USD_TO_CNY = 7.2  # 仅用于显示


def _http_get(url: str, headers: dict = None, timeout: int = 30) -> str:
    """HTTP GET"""
    try:
        resp = requests.get(url, headers=headers or {"User-Agent": "Mozilla/5.0"}, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    [HTTP] {url} 失败: {e}")
        return ""


def _playwright_get(url: str, wait_selector: str = None, timeout: int = 45) -> str:
    """Playwright GET"""
    if not HAS_PLAYWRIGHT:
        return ""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=15000)
                except Exception:
                    pass
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"    [Playwright] {url} 失败: {e}")
        return ""


# ============== 腾讯云轻量 ==============
def fetch_tencent() -> List[Dict]:
    """腾讯云轻量 - 不做兜底"""
    url = "https://cloud.tencent.com/product/lighthouse"
    print(f"  → 抓取腾讯云轻量价格…")

    html = _playwright_get(url, wait_selector=".price-list, .lighthouse-item, table", timeout=45)
    if not html:
        print(f"    [腾讯云] 无法访问页面")
        return []

    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)

    found = {}
    monthly_prices = re.findall(r'(\d+)\s*元\s*/\s*月', text)
    if monthly_prices:
        sorted_prices = sorted(set([int(p) for p in monthly_prices if 30 <= int(p) <= 500]))
        if len(sorted_prices) >= 3:
            found = {"2G": sorted_prices[0], "4G": sorted_prices[1], "8G": sorted_prices[2]}
        elif len(sorted_prices) >= 1:
            found["2G"] = sorted_prices[0]

    if not found:
        print(f"    [腾讯云] 未匹配到价格")
        return []

    configs = [
        {"config": "2 核 2G", "cpu": 2, "memory": "2G", "storage": "50GB SSD", "bandwidth": "30Mbps", "traffic": "2000GB/月"},
        {"config": "2 核 4G", "cpu": 2, "memory": "4G", "storage": "80GB SSD", "bandwidth": "30Mbps", "traffic": "3000GB/月"},
        {"config": "4 核 8G", "cpu": 4, "memory": "8G", "storage": "100GB SSD", "bandwidth": "30Mbps", "traffic": "4000GB/月"},
    ]
    prices = []
    for cfg in configs:
        mem = cfg["memory"]
        if mem not in found:
            continue
        p = found[mem]
        prices.append({
            **cfg, "price_monthly": p, "price_yearly": p * 10,
            "currency": "CNY", "region": "香港", "source": "scraper",
            "provider": "tencent", "provider_name": "腾讯云轻量", "url": url,
        })
    return prices


# ============== 阿里云轻量 ==============
def fetch_aliyun() -> List[Dict]:
    """阿里云轻量 - 不做兜底"""
    url = "https://www.aliyun.com/product/swas"
    print(f"  → 抓取阿里云轻量价格…")

    html = _playwright_get(url, wait_selector=".price, table, .sku-list", timeout=45)
    if not html:
        print(f"    [阿里云] 无法访问页面")
        return []

    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    found = {}
    configs = [
        {"cpu": 2, "memory": "2G"}, {"cpu": 2, "memory": "4G"}, {"cpu": 4, "memory": "8G"},
    ]
    for cfg in configs:
        pattern = rf"{cfg['cpu']}\s*核\s*{cfg['memory']}.*?[¥￥]\s*(\d+)"
        m = re.search(pattern, text)
        if m:
            found[cfg["memory"]] = int(m.group(1))

    if not found:
        print(f"    [阿里云] 未匹配到价格")
        return []

    storage_map = {"2G": "60GB SSD", "4G": "80GB SSD", "8G": "120GB SSD"}
    bw_map = {"2G": "5Mbps", "4G": "6Mbps", "8G": "8Mbps"}
    traffic_map = {"2G": "1500GB/月", "4G": "2000GB/月", "8G": "3000GB/月"}
    prices = []
    for cfg in configs:
        mem = cfg["memory"]
        if mem not in found:
            continue
        p = found[mem]
        prices.append({
            "config": f"{cfg['cpu']} 核 {mem}", "cpu": cfg["cpu"], "memory": mem,
            "storage": storage_map[mem], "bandwidth": bw_map[mem], "traffic": traffic_map[mem],
            "price_monthly": p, "price_yearly": p * 10,
            "currency": "CNY", "region": "香港", "source": "scraper",
            "provider": "aliyun", "provider_name": "阿里云轻量", "url": url,
        })
    return prices


# ============== 华为云 HECS ==============
def fetch_huawei() -> List[Dict]:
    """华为云 HECS - 不做兜底"""
    url = "https://www.huaweicloud.com/product/hecs.html"
    print(f"  → 抓取华为云 HECS 价格…")

    html = _playwright_get(url, wait_selector="table, .price-list", timeout=45)
    if not html:
        print(f"    [华为云] 无法访问页面")
        return []

    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    found = {}
    configs = [
        {"cpu": 2, "memory": "2G"}, {"cpu": 2, "memory": "4G"}, {"cpu": 4, "memory": "8G"},
    ]
    for cfg in configs:
        pattern = rf"{cfg['cpu']}\s*[vV]\s*[cC][pP][uU].*?{cfg['memory']}.*?[¥￥]\s*(\d+)"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            found[cfg["memory"]] = int(m.group(1))

    if not found:
        print(f"    [华为云] 未匹配到价格")
        return []

    storage_map = {"2G": "40GB SSD", "4G": "60GB SSD", "8G": "100GB SSD"}
    bw_map = {"2G": "1Mbps", "4G": "2Mbps", "8G": "3Mbps"}
    prices = []
    for cfg in configs:
        mem = cfg["memory"]
        if mem not in found:
            continue
        p = found[mem]
        prices.append({
            "config": f"{cfg['cpu']} 核 {mem}", "cpu": cfg["cpu"], "memory": mem,
            "storage": storage_map[mem], "bandwidth": bw_map[mem], "traffic": "按量",
            "price_monthly": p, "price_yearly": p * 10,
            "currency": "CNY", "region": "香港", "source": "scraper",
            "provider": "huawei", "provider_name": "华为云 HECS", "url": url,
        })
    return prices


# ============== AWS Lightsail ==============
def fetch_aws() -> List[Dict]:
    """AWS Lightsail - 不做兜底"""
    url = "https://aws.amazon.com/lightsail/pricing/"
    print(f"  → 抓取 AWS Lightsail 价格…")

    html = _http_get(url, headers={"Accept-Language": "en-US,en;q=0.9"})
    if not html:
        print(f"    [AWS] 无法访问页面")
        return []

    found = {}
    bundle_idx = html.find('id="Bundles"')
    if bundle_idx > 0:
        end_idx = html.find('id="Block_storage"', bundle_idx + 1000)
        if end_idx < 0:
            end_idx = html.find('id="CDN_distributions"', bundle_idx + 1000)
        if end_idx < 0:
            end_idx = html.find('id="Managed_databases"', bundle_idx + 1000)
        if end_idx < 0:
            end_idx = bundle_idx + 50000
        bundle_html = html[bundle_idx:end_idx]

        soup = BeautifulSoup(bundle_html, "html.parser")
        for col in soup.find_all("div", class_="lb-xbcol"):
            col_text = col.get_text(" ", strip=True)
            price_match = re.search(r'\$\s*(\d+(?:\.\d+)?)\s+[^$]+?USD\s*/\s*mo', col_text)
            if not price_match:
                continue
            price_usd = float(price_match.group(1))
            mem_match = re.search(r'(\d+)\s*GB\s*Memory', col_text)
            if not mem_match:
                continue
            mem_gb = int(mem_match.group(1))
            if mem_gb in [2, 4, 8]:
                found[f"{mem_gb}G"] = int(price_usd * USD_TO_CNY)
                print(f"    AWS {mem_gb}GB = ${price_usd}/mo = ¥{int(price_usd * USD_TO_CNY)}")

    if not found:
        print(f"    [AWS] 未匹配到价格")
        return []

    configs = [
        {"config": "1 核 2G", "cpu": 1, "memory": "2G", "storage": "80GB SSD", "bandwidth": "1Gbps", "traffic": "100GB/月"},
        {"config": "2 核 4G", "cpu": 2, "memory": "4G", "storage": "120GB SSD", "bandwidth": "1Gbps", "traffic": "100GB/月"},
        {"config": "2 核 8G", "cpu": 2, "memory": "8G", "storage": "240GB SSD", "bandwidth": "1Gbps", "traffic": "200GB/月"},
    ]
    prices = []
    for cfg in configs:
        mem = cfg["memory"]
        if mem not in found:
            continue
        cny = found[mem]
        prices.append({
            "provider": "aws", "provider_name": "AWS Lightsail",
            "config": cfg["config"], "cpu": cfg["cpu"], "memory": mem,
            "storage": cfg["storage"], "bandwidth": cfg["bandwidth"], "traffic": cfg["traffic"],
            "price_monthly": cny, "price_yearly": cny * 12,
            "currency": "CNY", "region": "Asia Pacific (Hong Kong)",
            "url": url, "source": "scraper",
            "note": f"按 1 USD = {USD_TO_CNY} CNY 换算",
        })
    return prices


# ============== Vultr (有 API!) ==============
def fetch_vultr() -> List[Dict]:
    """Vultr - 不做兜底"""
    print(f"  → 通过 Vultr API 抓取价格…")

    prices = []
    try:
        resp = requests.get("https://api.vultr.com/v2/plans", timeout=30,
                            headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        plans = data if isinstance(data, list) else data.get("plans", [])

        for plan_data in plans:
            plan_type = plan_data.get("type", "")
            if "vc2" not in plan_type.lower() and "cloud compute" not in plan_type.lower():
                continue
            vcpu = plan_data.get("vcpu_count", 0)
            ram_mb = plan_data.get("ram", plan_data.get("memory", 0))
            ram_gb = round(ram_mb / 1024)
            if ram_gb not in [2, 4, 8]:
                continue
            usd_monthly = plan_data.get("monthly_cost", plan_data.get("price_per_month", 0))
            cny_monthly = int(usd_monthly * USD_TO_CNY)
            bandwidth_gb = plan_data.get("bandwidth", 0)
            prices.append({
                "provider": "vultr", "provider_name": "Vultr",
                "config": f"{vcpu} 核 {ram_gb}G",
                "cpu": vcpu, "memory": f"{ram_gb}G",
                "storage": f"{plan_data.get('disk', 0)}GB SSD",
                "bandwidth": f"{bandwidth_gb / 1024:.1f}TB/月" if bandwidth_gb >= 1024 else f"{bandwidth_gb}GB/月",
                "traffic": f"{bandwidth_gb}GB/月",
                "price_monthly": cny_monthly,
                "price_yearly": cny_monthly * 12,
                "currency": "CNY", "region": "Hong Kong",
                "url": "https://www.vultr.com/products/cloud-compute/",
                "source": "api",
                "note": f"Vultr API 实时: ${usd_monthly}/月 ({plan_type})",
            })
        prices.sort(key=lambda x: (x["memory"], x["price_monthly"]))
    except Exception as e:
        print(f"    [Vultr API] 失败: {e}")
        return []

    if not prices:
        print(f"    [Vultr] API 返回空")
    return prices


# ============== 聚合函数 ==============
def fetch_all_prices() -> List[Dict]:
    """抓取所有厂家价格 - 失败的不返回"""
    all_prices = []
    scrapers = [
        ("腾讯云", fetch_tencent),
        ("阿里云", fetch_aliyun),
        ("华为云", fetch_huawei),
        ("AWS", fetch_aws),
        ("Vultr", fetch_vultr),
    ]
    for name, scraper in scrapers:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 抓取 {name}…")
        try:
            prices = scraper()
            if prices:
                all_prices.extend(prices)
                print(f"  ✓ {name}: 获取 {len(prices)} 条")
            else:
                print(f"  ⚠ {name}: 未获取到价格")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
        time.sleep(2)
    return all_prices


if __name__ == "__main__":
    prices = fetch_all_prices()
    print(f"\n共 {len(prices)} 条价格")