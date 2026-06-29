# scraper.py

import os
import httpx
import asyncio
import pandas as pd
from selectolax.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import urllib.parse
import re

WIB = timezone(timedelta(hours=7))

# ========================
# LOAD .ENV
# ========================
load_dotenv()

# ========================
# CLEANING (RINGAN)
# ========================
def clean_text(text):
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)

    return text

async def fetch_detik(keyword):
    url = (
        f"https://www.detik.com/search/searchall?"
        f"query={keyword}"
        f"&sortby=time"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:

            response = await client.get(url, headers=headers)

            print(f"\nKeyword : {keyword}")
            print("Status  :", response.status_code)
            print("URL     :", response.url)

            response.raise_for_status()

            parser = HTMLParser(response.text)

            data = []

            for article in parser.css("article"):
                date_el = article.css_first(".media__date span")
                raw_date = (
                    date_el.attributes.get("title")
                    if date_el else ""
                )

                title_el = article.css_first("h3.media__title")
                link_el = article.css_first("a")

                title = title_el.text(strip=True) if title_el else ""
                link = link_el.attributes.get("href") if link_el else ""

                data.append({
                    "source": "detik",
                    "keyword": keyword,
                    "title": title,
                    "clean_title": clean_text(title),
                    "link": link,
                    "published_date": raw_date,
                    "scraped_at": datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                })

            print(f"Data ditemukan: {len(data)}")

            return data

    except Exception as e:
        print(f"\nERROR pada keyword '{keyword}'")
        print(type(e).__name__)
        print(e)
        return []

# ========================
# MAIN
# ========================
async def main():
    keywords = [
    "politik",
    "ekonomi",
    "teknologi",
    "terkini",
    "populer",
    "pendidikan",
    "viral",
    "hiburan",
    "wisata",
    "gaji",
    "pekerjaan",
    "hobi",
    "produktif",
    "kuliner",
    "pemerintah"]

    results = []

    for keyword in keywords:
        print(f"\n=== Mengambil keyword: {keyword} ===")

        data = await fetch_detik(keyword)
        results.append(data)

        await asyncio.sleep(2)   # jeda 2 detik agar tidak dianggap spam

    df = pd.DataFrame([item for sub in results for item in sub])

    print("Total data:", len(df))

    # ========================
    # MONGODB
    # ========================
    username = urllib.parse.quote_plus(os.getenv("MONGO_USER"))
    password = urllib.parse.quote_plus(os.getenv("MONGO_PASS"))
    cluster = os.getenv("MONGO_CLUSTER")

    uri = (
        f"mongodb+srv://{username}:{password}"
        f"@{cluster}/"
        "?retryWrites=true&w=majority&appName=Cluster0"
    )

    client = MongoClient(uri)

    db = client[os.getenv("MONGO_DB")]
    collection = db[os.getenv("MONGO_COLLECTION")]

    try:
        client.server_info()
        print("✅ MongoDB Connected")
    except Exception as e:
        print("❌ MongoDB Error:", e)
        return

    # ========================
    # LANJUT KE DATABASE
    # ========================
    db = client["Capstone"]
    collection = db["Data_Detik"]

    if not df.empty:
        new_data = df.to_dict("records")

        if new_data:
            try:
                # Menghapus semua data lama agar terganti dengan yang baru
                deleted = collection.delete_many({})
                print(f"🗑️ Menghapus {deleted.deleted_count} berita lama dari MongoDB")
                
                # Memasukkan semua data terbaru
                collection.insert_many(new_data)
                print(f"✅ {len(new_data)} berita terbaru berhasil dimasukkan ke MongoDB")
            except Exception as e:
                print(f"❌ Error saat menyimpan ke MongoDB: {e}")
    else:
        print("❌ Tidak ada data yang berhasil diambil dari Detik")


# ========================
# RUN
# ========================
if __name__ == "__main__":
    asyncio.run(main())