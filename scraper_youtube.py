import os
import time
from datetime import datetime, timezone, timedelta
import isodate
import pandas as pd
import urllib.parse
from pymongo import MongoClient
from googleapiclient.discovery import build
from dotenv import load_dotenv

WIB = timezone(timedelta(hours=7))

# Load environment variables (untuk run lokal)
load_dotenv()

# Setup API Key
API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    print("❌ Error: YOUTUBE_API_KEY tidak ditemukan di environment variables.")
    exit(1)
youtube = build("youtube", "v3", developerKey=API_KEY)

keywords = [
    "politik", "ekonomi", "teknologi", "terkini", "populer",
    "pendidikan", "viral", "hiburan", "wisata", "gaji",
    "pekerjaan", "hobi", "produktif", "kuliner", "pemerintah"
]

def is_short(duration_iso):
    """Double check: True jika durasi <= 60 detik"""
    try:
        seconds = isodate.parse_duration(duration_iso).total_seconds()
        return seconds <= 60
    except:
        return False

def get_channel_countries(channel_ids):
    """Cek country dari sekumpulan channel_id sekaligus (batch)"""
    if not channel_ids:
        return {}

    response = youtube.channels().list(
        part="snippet",
        id=",".join(channel_ids)
    ).execute()

    result = {}
    for item in response.get("items", []):
        channel_id = item["id"]
        country    = item["snippet"].get("country", "")
        result[channel_id] = country

    return result

def get_videos_by_keyword(keyword, max_results=20):
    videos = []
    try:
        search_response = youtube.search().list(
            part="snippet",
            q=keyword,
            type="video",
            regionCode="ID",
            relevanceLanguage="id",
            publishedAfter="2025-04-01T00:00:00Z",
            publishedBefore=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            order="viewCount",
            videoDuration="long",
            maxResults=max_results,
        ).execute()

        video_ids   = [item["id"]["videoId"]        for item in search_response.get("items", [])]
        channel_ids = [item["snippet"]["channelId"] for item in search_response.get("items", [])]

        if not video_ids:
            return []

        channel_country_map = get_channel_countries(list(set(channel_ids)))

        detail_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(video_ids),
        ).execute()

        for item in detail_response.get("items", []):
            snippet    = item["snippet"]
            stats      = item.get("statistics", {})
            content    = item.get("contentDetails", {})
            duration   = content.get("duration", "")
            channel_id = snippet.get("channelId", "")

            if is_short(duration):
                continue

            channel_country = channel_country_map.get(channel_id, "")
            if channel_country and channel_country != "ID":
                continue

            video_data = {
                "video_id":        item["id"],
                "keyword":         keyword,
                "title":           snippet.get("title", ""),
                "description":     snippet.get("description", "")[:500],
                "channel_name":    snippet.get("channelTitle", ""),
                "channel_id":      channel_id,
                "channel_country": channel_country or "tidak diset",
                "category_id":     snippet.get("categoryId", ""),
                "tags":            snippet.get("tags", []),
                "published_at":    snippet.get("publishedAt", ""),
                "view_count":      int(stats.get("viewCount", 0)),
                "like_count":      int(stats.get("likeCount", 0)),
                "comment_count":   int(stats.get("commentCount", 0)),
                "duration":        duration,
                "thumbnail_url":   snippet["thumbnails"]["high"]["url"],
                "scraped_at":      datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
            }
            videos.append(video_data)

    except Exception as e:
        print(f"  ⚠️ Error keyword '{keyword}': {e}")

    return videos


def main():
    all_data = []

    for kw in keywords:
        print(f"🔍 Scraping keyword: '{kw}'...")
        result = get_videos_by_keyword(kw, max_results=20)
        all_data.extend(result)
        print(f"   → {len(result)} video lolos filter")
        time.sleep(1)

    if not all_data:
        print("❌ Tidak ada data yang berhasil discrape.")
        return

    df = pd.DataFrame(all_data)
    df_unique = df.drop_duplicates(subset="video_id").reset_index(drop=True)

    print(f"\n✅ Total video terkumpul : {len(all_data)}")
    print(f"✅ Setelah hapus duplikat: {len(df_unique)} video unik")

    # Koneksi MongoDB menggunakan Environment Variable dari GitHub Actions / .env lokal
    mongo_user = os.getenv("MONGO_USER")
    mongo_pass = os.getenv("MONGO_PASS")
    mongo_cluster = os.getenv("MONGO_CLUSTER")
    mongo_db = os.getenv("MONGO_DB", "Capstone")
    mongo_coll = os.getenv("MONGO_COLLECTION_YT", "Data_Youtube_2")

    if not all([mongo_user, mongo_pass, mongo_cluster]):
        print("❌ Variabel MONGO di ENV tidak lengkap! Harap pastikan MONGO_USER, MONGO_PASS, dan MONGO_CLUSTER ada di .env atau GitHub Secrets.")
        return
        
    username = urllib.parse.quote_plus(mongo_user)
    password = urllib.parse.quote_plus(mongo_pass)
    uri = f"mongodb+srv://{username}:{password}@{mongo_cluster}/?retryWrites=true&w=majority"

    client = MongoClient(uri)
    db = client[mongo_db]
    collection = db[mongo_coll]

    # Simpan data ke MongoDB
    records = df_unique.to_dict('records')
    if records:
        try:
            # Menghapus semua video lama agar terganti dengan yang baru
            deleted = collection.delete_many({})
            print(f"🗑️ Menghapus {deleted.deleted_count} video lama dari MongoDB")
            
            # Memasukkan semua video terbaru
            collection.insert_many(records)
            print(f"✅ {len(records)} video terbaru berhasil dimasukkan ke MongoDB ({mongo_db}.{mongo_coll})")
        except Exception as e:
            print(f"❌ Error menyimpan ke MongoDB: {e}")
    else:
        print("❌ Tidak ada video yang berhasil diambil dari YouTube")

if __name__ == "__main__":
    main()
