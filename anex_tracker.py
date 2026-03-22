#!/usr/bin/env python3
"""
Anex Flo & Eli Price Tracker
Магазини: Hotline, Antoshka, Karapuzov, MA.com.ua, Rozetka
"""

import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

BOT_TOKEN    = os.environ.get("BOT_TOKEN", "")
CHAT_ID      = os.environ.get("CHAT_ID", "")
PRICES_FILE  = "prices_history.json"
WEBSITE_FILE = "docs/prices.json"

PAGES = [

    # ══════════════════════════════════════════════════════
    # HOTLINE — мінімальна ціна по всіх магазинах
    # ══════════════════════════════════════════════════════
    {
        "name": "Anex Flo 2в1 — Hotline",
        "model": "Anex Flo 2в1", "store": "Hotline",
        "url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557565/",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557565/",
        "selector": "[class*='price']",
    },
    {
        "name": "Anex Eli No.5 — Hotline",
        "model": "Anex Eli No.5", "store": "Hotline",
        "url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557629/",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557629/",
        "selector": "[class*='price']",
    },
    {
        "name": "Anex Eli Secret — Hotline",
        "model": "Anex Eli Secret", "store": "Hotline",
        "url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558179/",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558179/",
        "selector": "[class*='price']",
    },
    {
        "name": "Anex Eli Muse — Hotline",
        "model": "Anex Eli Muse", "store": "Hotline",
        "url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558180/",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558180/",
        "selector": "[class*='price']",
    },
    {
        "name": "Anex Eli Midnight — Hotline",
        "model": "Anex Eli Midnight", "store": "Hotline",
        "url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558181/",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21558181/",
        "selector": "[class*='price']",
    },

    # ══════════════════════════════════════════════════════
    # ANTOSHKA — реальний URL бренду
    # ══════════════════════════════════════════════════════
    {
        "name": "Anex Flo 2в1 — Antoshka",
        "model": "Anex Flo 2в1", "store": "Antoshka",
        "url": "https://antoshka.ua/uk/brand/anex/?q=flo",
        "store_url": "https://antoshka.ua",
        "selector": "[class*='price'], [class*='Price'], .product-price",
    },
    {
        "name": "Anex Eli 2в1 — Antoshka",
        "model": "Anex Eli (всі моделі)", "store": "Antoshka",
        "url": "https://antoshka.ua/uk/brand/anex/?q=eli",
        "store_url": "https://antoshka.ua",
        "selector": "[class*='price'], [class*='Price'], .product-price",
    },

    # ══════════════════════════════════════════════════════
    # KARAPUZOV — офіційний дилер
    # ══════════════════════════════════════════════════════
    {
        "name": "Anex Flo 2в1 — Karapuzov",
        "model": "Anex Flo 2в1", "store": "Karapuzov",
        "url": "https://karapuzov.com.ua/uk/anex-flo/",
        "store_url": "https://karapuzov.com.ua",
        "selector": "[class*='price'], .price, [class*='Price']",
    },
    {
        "name": "Anex Eli 2в1 — Karapuzov",
        "model": "Anex Eli (всі моделі)", "store": "Karapuzov",
        "url": "https://karapuzov.com.ua/uk/anex-eli/",
        "store_url": "https://karapuzov.com.ua",
        "selector": "[class*='price'], .price, [class*='Price']",
    },

    # ══════════════════════════════════════════════════════
    # MA.COM.UA (babyshop)
    # ══════════════════════════════════════════════════════
    {
        "name": "Anex Flo 2в1 — MA.com.ua",
        "model": "Anex Flo 2в1", "store": "MA.com.ua",
        "url": "https://ma.com.ua/ua/ulitsa/kolyaski/stroller_type=2-v-1/brand=anex/stroller_series=flo",
        "store_url": "https://ma.com.ua",
        "selector": "[class*='price'], .price",
    },
    {
        "name": "Anex Eli 2в1 — MA.com.ua",
        "model": "Anex Eli (всі моделі)", "store": "MA.com.ua",
        "url": "https://ma.com.ua/ua/ulitsa/kolyaski/stroller_type=2-v-1/brand=anex/stroller_series=eli",
        "store_url": "https://ma.com.ua",
        "selector": "[class*='price'], .price",
    },

    # ══════════════════════════════════════════════════════
    # ROZETKA
    # ══════════════════════════════════════════════════════
    {
        "name": "Anex Flo 2в1 — Rozetka",
        "model": "Anex Flo 2в1", "store": "Rozetka",
        "url": "https://rozetka.com.ua/ua/search/?text=anex+flo+2+in+1&section_id=80003",
        "store_url": "https://rozetka.com.ua",
        "selector": "span.goods-tile__price-value",
    },
    {
        "name": "Anex Eli 2в1 — Rozetka",
        "model": "Anex Eli (всі моделі)", "store": "Rozetka",
        "url": "https://rozetka.com.ua/ua/search/?text=anex+eli+2+in+1&section_id=80003",
        "store_url": "https://rozetka.com.ua",
        "selector": "span.goods-tile__price-value",
    },
]


def extract_price(text: str) -> int | None:
    digits = re.sub(r"[^\d]", "", text.strip())
    if digits and 5000 < int(digits) < 300000:
        return int(digits)
    return None


def parse_all_prices() -> dict:
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="uk-UA",
        )
        page = context.new_page()

        for item in PAGES:
            print(f"\n🔍 {item['name']}...")
            try:
                page.goto(item["url"], wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2500)

                price = None

                # CSS селектор
                try:
                    els = page.query_selector_all(item["selector"])
                    for el in els:
                        price = extract_price(el.inner_text())
                        if price:
                            break
                except Exception:
                    pass

                # Fallback — regex по HTML
                if not price:
                    content = page.content()
                    for m in re.findall(r"(\d[\d\s]{3,7}\d)\s*(?:₴|грн)", content):
                        p_val = extract_price(m)
                        if p_val:
                            price = p_val
                            break

                if price:
                    print(f"  ✅ {price:,} ₴".replace(",", " "))
                    results[item["name"]] = {
                        "name":      item["name"],
                        "model":     item["model"],
                        "price":     price,
                        "store":     item["store"],
                        "url":       item["url"],
                        "store_url": item["store_url"],
                        "date":      datetime.now().strftime("%Y-%m-%d"),
                    }
                else:
                    print(f"  ⚠️  Ціну не знайдено")

            except Exception as e:
                print(f"  ❌ Помилка: {e}")

        browser.close()
    return results


def send_telegram(message: str):
    if not BOT_TOKEN or not CHAT_ID:
        print("  ⚠️  BOT_TOKEN або CHAT_ID не задано")
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": message,
                  "parse_mode": "HTML", "disable_web_page_preview": False},
            timeout=10,
        )
        if resp.json().get("ok"):
            print("  📬 Telegram надіслано")
    except Exception as e:
        print(f"  ❌ Telegram: {e}")


def fmt(p: int) -> str:
    return f"{p:,}".replace(",", " ") + " ₴"


def load_history() -> dict:
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data: dict):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run():
    print(f"\n{'='*60}")
    print(f"  🛒 Anex Tracker | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*60}")

    history = load_history()
    today   = parse_all_prices()
    alerts  = []

    for name, data in today.items():
        new_p     = data["price"]
        old_entry = history.get(name)
        old_p     = old_entry.get("price") if old_entry else None
        old_date  = old_entry.get("date", "?") if old_entry else None

        if old_p and new_p < old_p:
            diff = old_p - new_p
            pct  = round((diff / old_p) * 100)
            print(f"  🟢 ЗНИЖКА! {fmt(old_p)} → {fmt(new_p)} (-{pct}%)")
            alerts.append({
                "name": name, "model": data["model"], "store": data["store"],
                "old_price": old_p, "new_price": new_p,
                "diff": diff, "pct": pct,
                "url": data["url"], "old_date": old_date,
            })
        elif old_p and new_p > old_p:
            print(f"  🔴 Зросла: {fmt(old_p)} → {fmt(new_p)}")
        else:
            print(f"  ➖ {fmt(new_p)}")

    if alerts:
        for a in alerts:
            send_telegram(
                f"🟢 <b>ЗНИЖКА НА КОЛЯСКУ!</b>\n\n"
                f"🛒 <b>{a['model']}</b>\n"
                f"📍 {a['store']}\n\n"
                f"Вчора ({a['old_date']}): <s>{fmt(a['old_price'])}</s>\n"
                f"Сьогодні: <b>{fmt(a['new_price'])}</b> (-{a['pct']}%)\n"
                f"💰 Економія: <b>{fmt(a['diff'])}</b>\n\n"
                f"🔗 <a href=\"{a['url']}\">Переглянути →</a>"
            )
    else:
        lines = "\n".join(
            f"  • {d['model']} ({d['store']}): <b>{fmt(d['price'])}</b>"
            for d in today.values()
        ) if today else "  Дані не отримано"
        send_telegram(
            f"ℹ️ <b>Перевірка цін {datetime.now().strftime('%d.%m.%Y %H:%M')}</b>\n\n"
            f"Знижок не виявлено.\n\n"
            f"<b>Поточні ціни:</b>\n{lines}"
        )

    merged = {**history, **today}
    save_history(merged)

    os.makedirs("docs", exist_ok=True)
    website_data = {
        "updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "prices": [
            {
                "name":       name,
                "model":      data.get("model", name),
                "price":      data["price"],
                "store":      data.get("store", ""),
                "url":        data.get("url", ""),
                "date":       data.get("date", ""),
                "prev_price": history.get(name, {}).get("price"),
                "prev_date":  history.get(name, {}).get("date"),
            }
            for name, data in merged.items()
        ]
    }
    with open(WEBSITE_FILE, "w", encoding="utf-8") as f:
        json.dump(website_data, f, ensure_ascii=False, indent=2)

    print(f"\n🌐 docs/prices.json збережено")
    print(f"✅ Готово! Знижок: {len(alerts)}\n")


if __name__ == "__main__":
    run()
