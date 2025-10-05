
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .youtube_import import fetch_playlist_items, fetch_videos_durations, _parse_playlist_id

class YouTubePlaylistItemsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, playlist_id: str):
        pid = _parse_playlist_id(playlist_id)
        items = list(fetch_playlist_items(pid))
        if not items:
            return Response({"items": [], "count": 0})
        durations = fetch_videos_durations([i["videoId"] for i in items])
        data = []
        for it in items:
            vid = it["videoId"]
            data.append({
                "video_id": vid,
                "title": it["title"],
                "thumbnail_url": it["thumbnail_url"],
                "duration_seconds": durations.get(vid, 0),
                "watch_url": f"https://www.youtube.com/watch?v={vid}",
            })
        return Response({"items": data, "count": len(data)})
