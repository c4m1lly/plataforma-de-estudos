
import re
import requests
from typing import Dict, List, Iterable
from django.db import models

API_KEY = "AIzaSyCcOtrjqrB4SCsOF5vpofATfLmXLg2HDjA"
YOUTUBE_PLAYLIST_ITEMS = "https://www.googleapis.com/youtube/v3/playlistItems"
YOUTUBE_VIDEOS = "https://www.googleapis.com/youtube/v3/videos"

def _parse_playlist_id(url_or_id: str) -> str:
    m = re.search(r"[?&]list=([A-Za-z0-9_\-]+)", url_or_id or "")
    return m.group(1) if m else (url_or_id or "").strip()

def _parse_iso8601_duration_to_seconds(iso: str) -> int:
    import re as _re
    h = m = s = 0
    mt = _re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "PT0S")
    if mt:
        h = int(mt.group(1) or 0); m = int(mt.group(2) or 0); s = int(mt.group(3) or 0)
    return h*3600 + m*60 + s

def fetch_playlist_items(playlist_id: str, api_key: str = API_KEY) -> Iterable[dict]:
    params = {"key": api_key, "part": "snippet,contentDetails", "playlistId": playlist_id, "maxResults": 50}
    while True:
        resp = requests.get(YOUTUBE_PLAYLIST_ITEMS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items", []):
            snippet = item.get("snippet") or {}
            content = item.get("contentDetails") or {}
            vid = content.get("videoId")
            if not vid: continue
            thumbs = (snippet.get("thumbnails") or {})
            thumb = (thumbs.get("maxres") or thumbs.get("standard") or thumbs.get("high") 
                     or thumbs.get("medium") or thumbs.get("default") or {})
            yield {"videoId": vid, "title": snippet.get("title") or "", "thumbnail_url": thumb.get("url")}
        token = data.get("nextPageToken")
        if not token: break
        params["pageToken"] = token

def fetch_videos_durations(video_ids: List[str], api_key: str = API_KEY) -> Dict[str, int]:
    d: Dict[str,int] = {}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        params = {"key": api_key, "part": "contentDetails", "id": ",".join(chunk), "maxResults": 50}
        resp = requests.get(YOUTUBE_VIDEOS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for it in data.get("items", []):
            vid = it.get("id")
            iso = (it.get("contentDetails") or {}).get("duration", "PT0S")
            d[vid] = _parse_iso8601_duration_to_seconds(iso)
    return d

def import_playlist_into_module(module, playlist_url_or_id: str) -> tuple[int,int]:
    from .models import Video, Lesson
    pid = _parse_playlist_id(playlist_url_or_id)
    items = list(fetch_playlist_items(pid))
    if not items: return (0,0)
    durs = fetch_videos_durations([i["videoId"] for i in items])
    created_v = created_l = 0
    current_max = module.lessons.aggregate(m=models.Max("order")).get("order__max") or 0
    for idx, it in enumerate(items, start=1):
        vid = it["videoId"]; title = it["title"] or f"Vídeo {idx}"
        url = f"https://www.youtube.com/watch?v={vid}"
        thumb = it["thumbnail_url"]; dur = durs.get(vid, 0)
        video, v_new = Video.objects.get_or_create(
            external_url=url,
            defaults={"title": title, "thumbnail_url": thumb, "duration_seconds": dur, "transcoding_status": "n/a"}
        )
        if v_new: created_v += 1
        lesson, l_new = Lesson.objects.get_or_create(
            module=module, title=title,
            defaults={"order": current_max+idx, "expected_duration_seconds": dur or 0, "video": video}
        )
        if l_new: created_l += 1
        elif not getattr(lesson, "video_id", None):
            lesson.video = video; lesson.save(update_fields=["video"])
    return (created_v, created_l)
