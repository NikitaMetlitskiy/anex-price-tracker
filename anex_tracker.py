#!/usr/bin/env python3
"""
Anex Flo & Eli Price Tracker — з Playwright
Парсить JavaScript-сайти (Hotline, Rozetka) через headless браузер.
"""

import json
import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests

# ── КОНФІГ ──────────────────────────────────────────────────────────────────
BOT_TOKEN   = "8654506714:AAHaC6A4D_s-JXZWQUjZiMC8MmeowS0jhpM"
CHAT_ID     = "-1003762393572"
PRICES_FILE  = "prices_history.json"
WEBSITE_FILE = "docs/prices.json"   # GitHub Pages читає з папки /docs

# ── СТОРІНКИ ДЛЯ ПАРСИНГУ ───────────────────────────────────────────────────
PAGES = [
    {
        "name": "Anex Flo 2в1",
        "url":  "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557565/",
        "store": "Hotline (мін. ціна)",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557565/",
        "price_selector": ".price, [class*='price'], [class*='Price']",
    },
    {
        "name": "Anex Eli 2в1",
        "url":  "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557629/",
        "store": "Hotline (мін. ціна)",
        "store_url": "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557629/",
        "price_selector": ".price, [class*='price'], [class*='Price']",
    },
    {
        "name": "Anex Flo 2в1 — Rozetka",
        "url":  "https://rozetka.com.ua/ua/search/?text=anex+flo+2+in+1&section_id=80003",
        "store": "Rozetka",
        "store_url": "https://rozetka.com.ua",
        "price_selector": "span.goods-tile__price-value",
    },
    {
        "name": "Anex Eli 2в1 — Rozetka",
        "url":  "https://rozetka.com.ua/ua/search/?text=anex+eli+2+in+1&section_id=80003",
        "store": "Rozetka",
        "store_url": "https://rozetka.com.ua",
        "price_selector": "span.goods-tile__price-value",
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
            print(f"\n🔍 {item['name']} ({item['store']})...")
            try:
                page.goto(item["url"], wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(2000)

                price = None

                # Спочатку CSS селектор
                try:
                    els = page.query_selector_all(item["price_selector"])
                    for el in els:
                        txt = el.inner_text()
                        price = extract_price(txt)
                        if price:
                            break
                except Exception:
                    pass

                # Якщо не знайшли — regex по всьому HTML
                if not price:
                    content = page.content()
                    matches = re.findall(r"(\d[\d\s]{3,7}\d)\s*(?:₴|грн)", content)
                    for m in matches:
                        p_val = extract_price(m)
                        if p_val:
                            price = p_val
                            break

                if price:
                    print(f"  ✅ Ціна: {price:,} ₴".replace(",", " "))
                    results[item["name"]] = {
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


def send_telegram(message: str) -> bool:
    url     = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     message,
        "parse_mode":               "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.json().get("ok"):
            print("  📬 Telegram надіслано")
            return True
        else:
            print(f"  ❌ Telegram помилка: {resp.json()}")
    except Exception as e:
        print(f"  ❌ Telegram: {e}")
    return False


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
    print(f"\n{'='*55}")
    print(f"  🛒 Anex Tracker | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*55}")

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
            print(f"\n  🟢 ЗНИЖКА {name}: {fmt(old_p)} → {fmt(new_p)} (-{pct}%)")
            alerts.append({
                "name": name, "store": data["store"],
                "old_price": old_p, "new_price": new_p,
                "diff": diff, "pct": pct,
                "url": data["url"], "old_date": old_date,
            })
        elif old_p and new_p > old_p:
            print(f"\n  🔴 Зросла {name}: {fmt(old_p)} → {fmt(new_p)}")
        else:
            print(f"\n  ➖ {name} = {fmt(new_p)}")

    # ── Telegram ────────────────────────────────────────────────────────────
    if alerts:
        for a in alerts:
            msg = (
                f"🟢 <b>ЗНИЖКА НА КОЛЯСКУ!</b>\n\n"
                f"🛒 <b>{a['name']}</b>\n"
                f"📍 {a['store']}\n\n"
                f"Вчора ({a['old_date']}): <s>{fmt(a['old_price'])}</s>\n"
                f"Сьогодні: <b>{fmt(a['new_price'])}</b> (-{a['pct']}%)\n"
                f"💰 Економія: <b>{fmt(a['diff'])}</b>\n\n"
                f"🔗 <a href=\"{a['url']}\">Переглянути →</a>"
            )
            send_telegram(msg)
    else:
        date_str = datetime.now().strftime("%d.%m.%Y")
        lines = "\n".join(
            f"  • {n}: <b>{fmt(d['price'])}</b> ({d['store']})"
            for n, d in today.items()
        ) if today else "  Дані не отримано"
        msg = (
            f"ℹ️ <b>Перевірка цін {date_str}</b>\n\n"
            f"Знижок сьогодні не виявлено.\n\n"
            f"<b>Поточні ціни:</b>\n{lines}"
        )
        send_telegram(msg)

    merged = {**history, **today}
    save_history(merged)

    # Зберігаємо для сайту
    os.makedirs("docs", exist_ok=True)
    website_data = {
        "updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "prices": [
            {
                "name": name, "price": data["price"],
                "store": data.get("store",""), "url": data.get("url",""),
                "date": data.get("date",""),
                "prev_price": history.get(name,{}).get("price"),
                "prev_date": history.get(name,{}).get("date"),
            }
            for name, data in merged.items()
        ]
    }
    with open("docs/prices.json","w",encoding="utf-8") as f:
        json.dump(website_data, f, ensure_ascii=False, indent=2)
    print("🌐 docs/prices.json збережено")
    print(f"\n✅ Готово! Знайдено знижок: {len(alerts)}\n")


if __name__ == "__main__":
    run()
