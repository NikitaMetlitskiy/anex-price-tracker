#!/usr/bin/env python3
"""
Anex Flo & Eli Price Tracker
Щодня о 10:00 перевіряє ціни та надсилає сповіщення в Telegram при зниженні.
"""

import requests
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ── КОНФІГ ──────────────────────────────────────────────────────────────────
BOT_TOKEN = "8654506714:AAHaC6A4D_s-JXZWQUjZiMC8MmeowS0jhpM"
CHAT_ID   = "-1003762393572"
PRICES_FILE = "prices_history.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9",
}

# ── МАГАЗИНИ ДЛЯ ПАРСИНГУ ───────────────────────────────────────────────────
STORES = [
    # ── Anex FLO ──
    {
        "name": "Anex Flo — Karapuzov",
        "model": "Anex Flo 2в1",
        "url": "https://karapuzov.com.ua/uk/strollers/universal/anex-flo-2in1",
        "price_selector": ".price-current, .product-price, span.price",
        "store_url": "https://karapuzov.com.ua",
    },
    {
        "name": "Anex Flo — Rozetka",
        "model": "Anex Flo 2в1",
        "url": "https://rozetka.com.ua/ua/search/?text=anex+flo+2+in+1",
        "price_selector": "span.goods-tile__price-value",
        "store_url": "https://rozetka.com.ua",
    },
    {
        "name": "Anex Flo — MA.com.ua",
        "model": "Anex Flo 2в1",
        "url": "https://ma.com.ua/ua/ulitsa/kolyaski/brand=anex/stroller_series=flo",
        "price_selector": ".price, .product-price",
        "store_url": "https://ma.com.ua",
    },
    # ── Anex ELI ──
    {
        "name": "Anex Eli — Karapuzov",
        "model": "Anex Eli 2в1",
        "url": "https://karapuzov.com.ua/uk/strollers/universal/anex-eli-2in1",
        "price_selector": ".price-current, .product-price, span.price",
        "store_url": "https://karapuzov.com.ua",
    },
    {
        "name": "Anex Eli — Rozetka",
        "model": "Anex Eli 2в1",
        "url": "https://rozetka.com.ua/ua/search/?text=anex+eli+2+in+1",
        "price_selector": "span.goods-tile__price-value",
        "store_url": "https://rozetka.com.ua",
    },
    {
        "name": "Anex Eli — MA.com.ua",
        "model": "Anex Eli 2в1",
        "url": "https://ma.com.ua/ua/ulitsa/kolyaski/brand=anex/stroller_series=eli",
        "price_selector": ".price, .product-price",
        "store_url": "https://ma.com.ua",
    },
    {
        "name": "Anex Eli — Babymax",
        "model": "Anex Eli 2в1",
        "url": "https://babymax.com.ua/ukr/universalnaya-kolyaska-2-v-1---anex-eli-",
        "price_selector": ".price, .product-price, span[class*='price']",
        "store_url": "https://babymax.com.ua",
    },
]

# ── HOTLINE (агрегатор) ──────────────────────────────────────────────────────
HOTLINE_URL = "https://hotline.ua/ua/deti/detskie-kolyaski/313721-21557565-21557629/"


def extract_price(text: str) -> int | None:
    """Витягує числову ціну з рядка, напр. '34 999 грн' → 34999"""
    cleaned = re.sub(r"[^\d]", "", text)
    if cleaned and 1000 < int(cleaned) < 200000:
        return int(cleaned)
    return None


def parse_price(store: dict) -> int | None:
    """Парсить ціну з сайту магазину."""
    try:
        resp = requests.get(store["url"], headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for selector in store["price_selector"].split(", "):
            elements = soup.select(selector)
            for el in elements:
                price = extract_price(el.get_text())
                if price:
                    return price
    except Exception as e:
        print(f"  ⚠️  Помилка парсингу {store['name']}: {e}")
    return None


def send_telegram(message: str) -> bool:
    """Надсилає повідомлення в Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("ok"):
            print("  ✅ Telegram надіслано")
            return True
        else:
            print(f"  ❌ Telegram помилка: {data}")
    except Exception as e:
        print(f"  ❌ Telegram виключення: {e}")
    return False


def load_history() -> dict:
    if os.path.exists(PRICES_FILE):
        with open(PRICES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data: dict):
    with open(PRICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_price(p: int) -> str:
    return f"{p:,}".replace(",", " ") + " ₴"


def run():
    print(f"\n{'='*55}")
    print(f"  🛒 Anex Price Tracker | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*55}\n")

    history = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    alerts = []
    results = {}

    for store in STORES:
        print(f"🔍 {store['name']}...")
        price = parse_price(store)

        if price is None:
            print(f"  ⚠️  Не вдалось отримати ціну\n")
            # Зберігаємо стару ціну якщо є
            if store["name"] in history:
                results[store["name"]] = history[store["name"]]
            continue

        print(f"  💰 Поточна ціна: {format_price(price)}")

        old_entry = history.get(store["name"])
        old_price = old_entry.get("price") if old_entry else None
        old_date  = old_entry.get("date", "невідомо") if old_entry else None

        results[store["name"]] = {
            "model": store["model"],
            "price": price,
            "url":   store["url"],
            "store_url": store["store_url"],
            "date":  today,
        }

        if old_price and price < old_price:
            diff = old_price - price
            pct  = round((diff / old_price) * 100)
            print(f"  🟢 ЗНИЖКА! Вчора {format_price(old_price)} → Сьогодні {format_price(price)} (-{pct}%)")
            alerts.append({
                "store": store["name"],
                "model": store["model"],
                "old_price": old_price,
                "new_price": price,
                "diff": diff,
                "pct": pct,
                "url": store["url"],
                "old_date": old_date,
            })
        elif old_price and price > old_price:
            diff = price - old_price
            pct  = round((diff / old_price) * 100)
            print(f"  🔴 Зросла: {format_price(old_price)} → {format_price(price)} (+{pct}%)")
        else:
            print(f"  ➖ Без змін")
        print()

    # ── Надсилаємо зведення в Telegram ──────────────────────────────────────
    if alerts:
        for alert in alerts:
            msg = (
                f"🟢 <b>ЗНИЖКА НА КОЛЯСКУ!</b>\n\n"
                f"🛒 <b>{alert['model']}</b>\n"
                f"📍 {alert['store']}\n\n"
                f"Вчора ({alert['old_date']}): <s>{format_price(alert['old_price'])}</s>\n"
                f"Сьогодні: <b>{format_price(alert['new_price'])}</b> "
                f"<b>(-{alert['pct']}%)</b>\n"
                f"💰 Економія: <b>{format_price(alert['diff'])}</b>\n\n"
                f"🔗 <a href=\"{alert['url']}\">Переглянути на сайті →</a>"
            )
            send_telegram(msg)
    else:
        # Щоденне мовчазне підтвердження (надсилаємо тільки якщо нема знижок)
        date_str = datetime.now().strftime("%d.%m.%Y")
        prices_summary = "\n".join(
            f"  • {k}: <b>{format_price(v['price'])}</b>"
            for k, v in results.items()
            if "price" in v
        )
        msg = (
            f"ℹ️ <b>Перевірка цін {date_str}</b>\n\n"
            f"Знижок сьогодні не виявлено.\n\n"
            f"<b>Поточні ціни:</b>\n{prices_summary}"
        )
        send_telegram(msg)

    # ── Зберігаємо нові ціни ────────────────────────────────────────────────
    save_history(results)
    print(f"💾 Ціни збережено у {PRICES_FILE}")
    print(f"\n✅ Готово! Знайдено знижок: {len(alerts)}\n")


if __name__ == "__main__":
    run()
