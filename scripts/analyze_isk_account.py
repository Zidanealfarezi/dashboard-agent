import json
import re
from pathlib import Path
from collections import defaultdict

chunks_path = Path("/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46/raw_scraped_chunks.json")
chunks = json.loads(chunks_path.read_text(encoding="utf-8"))

parsed_videos = {}

pattern = re.compile(
    r"(00:\d{2})\n"
    r"([\s\S]+?)\n"
    r"(\d{1,2}\s+(?:Okt|Nov|Sep|Agu|Jul|Jun|Mei|Apr|Mar|Feb|Jan)[^\n]*|\d+\s+bln\s+lalu|\d+\s+hr\s+lalu)\n"
    r"(Semua orang|Hanya saya|Teman)\n"
    r"(\d+)\n"
    r"(\d+)\n"
    r"(\d+)"
)

for chunk in chunks:
    matches = pattern.findall(chunk)
    for dur, cap, date, priv, views, likes, comments in matches:
        clean_cap = re.sub(r"\s+", " ", cap).strip()
        # Deduplication key based on clean_cap[:40] and date
        key = f"{dur}_{clean_cap[:40]}_{date}"
        if key not in parsed_videos:
            hashtags = re.findall(r"#\w+", clean_cap)
            parsed_videos[key] = {
                "duration": dur,
                "caption": clean_cap,
                "hashtags": hashtags,
                "date": date,
                "privacy": priv,
                "views": int(views),
                "likes": int(likes),
                "comments": int(comments),
            }

videos_list = list(parsed_videos.values())
print(f"Total parsed unique videos: {len(videos_list)}")

# Classification into Product Pillars
def classify_pillar(caption, hashtags):
    c_lower = (caption + " " + " ".join(hashtags)).lower()
    if "paku cap keris" in c_lower or "paku" in c_lower:
        if "seng" in c_lower:
            return "Paku Seng / Asbes"
        return "Paku Cap Keris"
    elif "kawat duri" in c_lower:
        return "Kawat Duri Diamond"
    elif "kawat licin" in c_lower or "kawat" in c_lower:
        return "Kawat Licin Diamond"
    elif "kereta sorong" in c_lower or "five star" in c_lower or "kereta pasir" in c_lower:
        return "Kereta Sorong Five Star"
    elif "baja" in c_lower or "besi" in c_lower:
        return "Bahan Bangunan Baja/Besi"
    else:
        return "Corporate / Branding Umum"

for v in videos_list:
    v["pillar"] = classify_pillar(v["caption"], v["hashtags"])

# Aggregates by Pillar
pillar_stats = defaultdict(lambda: {"count": 0, "total_views": 0, "total_likes": 0, "total_comments": 0})
for v in videos_list:
    p = v["pillar"]
    pillar_stats[p]["count"] += 1
    pillar_stats[p]["total_views"] += v["views"]
    pillar_stats[p]["total_likes"] += v["likes"]
    pillar_stats[p]["total_comments"] += v["comments"]

for p, st in pillar_stats.items():
    st["avg_views"] = round(st["total_views"] / max(1, st["count"]), 1)
    st["avg_likes"] = round(st["total_likes"] / max(1, st["count"]), 2)
    st["engagement_rate"] = round(((st["total_likes"] + st["total_comments"]) / max(1, st["total_views"])) * 100, 2)

# Top Performing Videos
top_by_views = sorted(videos_list, key=lambda x: x["views"], reverse=True)
top_by_likes = sorted(videos_list, key=lambda x: x["likes"], reverse=True)

total_account_views = sum(v["views"] for v in videos_list)
total_account_likes = sum(v["likes"] for v in videos_list)
total_account_comments = sum(v["comments"] for v in videos_list)
avg_views_overall = round(total_account_views / max(1, len(videos_list)), 1)
overall_engagement_rate = round(((total_account_likes + total_account_comments) / max(1, total_account_views)) * 100, 2)

report_data = {
    "total_videos_analyzed": len(videos_list),
    "total_account_views": total_account_views,
    "total_account_likes": total_account_likes,
    "total_account_comments": total_account_comments,
    "avg_views_overall": avg_views_overall,
    "overall_engagement_rate": overall_engagement_rate,
    "pillar_stats": dict(pillar_stats),
    "top_10_views": top_by_views[:10],
    "top_5_likes": top_by_likes[:5],
    "bottom_5_views": top_by_views[-5:] if len(top_by_views) >= 5 else [],
    "all_videos": videos_list
}

out_file = Path("/Users/zidane/.gemini/antigravity/brain/08b02ca4-493f-4aa6-a15f-c792fb191e46/isk_account_analysis.json")
out_file.write_text(json.dumps(report_data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Analysis saved to {out_file}")

print("\n--- SUMMARY STATS ---")
print(f"Total Videos Analyzed: {len(videos_list)}")
print(f"Total Views: {total_account_views}")
print(f"Avg Views: {avg_views_overall}")
print(f"Total Likes: {total_account_likes}")
print(f"Overall Engagement Rate: {overall_engagement_rate}%")
print("\n--- PILLAR BREAKDOWN ---")
for p, s in pillar_stats.items():
    print(f"• {p}: {s['count']} video | Total Views: {s['total_views']} | Avg: {s['avg_views']} | Eng: {s['engagement_rate']}%")

print("\n--- TOP 5 VIDEOS BY VIEWS ---")
for i, v in enumerate(top_by_views[:5], 1):
    print(f"{i}. [{v['views']} views, {v['likes']} likes] ({v['pillar']}) {v['caption'][:90]}...")
