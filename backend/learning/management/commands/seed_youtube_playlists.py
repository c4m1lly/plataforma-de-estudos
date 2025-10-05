from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
from learning.models import Course, Module, Lesson, Video
import requests, re
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


def parse_iso8601_duration(iso: str) -> int:
    m = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', iso or '')
    if not m: return 0
    h = int(m.group(1) or 0); mn = int(m.group(2) or 0); s = int(m.group(3) or 0)
    return h*3600 + mn*60 + s

def extract_playlist_id(url: str) -> str:
    if "list=" in url:
        return url.split("list=")[1].split("&")[0]
    return url

def fetch_playlist_title(playlist_id: str, api_key: str) -> str:
    base = "https://www.googleapis.com/youtube/v3/playlists"
    r = requests.get(base, params={"part":"snippet", "id": playlist_id, "key": api_key}, timeout=20)
    if r.status_code != 200:
        return f"Playlist {playlist_id}"
    items = r.json().get("items", [])
    if not items:
        return f"Playlist {playlist_id}"
    return items[0]["snippet"]["title"][:180]

class Command(BaseCommand):
    help = "Cria cursos e módulos a partir de 5 playlists pré-definidas (usa YOUTUBE_API_KEY)."

    def add_arguments(self, parser):
        parser.add_argument("--owner-email", type=str, help="Email do dono dos novos cursos (opcional).")

    @transaction.atomic
    def handle(self, *args, **opts):
        api_key = "AIzaSyCcOtrjqrB4SCsOF5vpofATfLmXLg2HDjA"
        if not api_key:
            raise CommandError("YOUTUBE_API_KEY não configurada no settings/env.")

        User = get_user_model()
        owner = None
        if opts.get("owner_email"):
            owner = User.objects.filter(email=opts["owner_email"]).first()
            if not owner:
                raise CommandError(f"Usuário com email {opts['owner_email']} não encontrado.")
        else:
            owner = User.objects.order_by("-is_superuser","-is_staff","date_joined").first()
            if not owner:
                raise CommandError("Nenhum usuário encontrado para ser dono dos cursos. Crie um usuário primeiro.")

        created_courses = []

        base_api = "https://www.googleapis.com/youtube/v3"
        for url in PLAYLISTS:
            pid = extract_playlist_id(url)
            title = fetch_playlist_title(pid, api_key)
            course = Course.objects.create(owner=owner, title=title, description=f"Importado da playlist {pid}")
            module = Module.objects.create(course=course, title=f"Playlist: {title}", order=Module.objects.filter(course=course).count()+1)

            nextPageToken = None
            total_created = 0
            while True:
                params = {"part":"contentDetails,snippet", "playlistId": pid, "maxResults": 50, "key": api_key}
                if nextPageToken: params["pageToken"] = nextPageToken
                r = requests.get(f"{base_api}/playlistItems", params=params, timeout=20)
                r.raise_for_status()
                items = r.json().get("items", [])
                if not items:
                    break
                video_ids = [it.get("contentDetails",{}).get("videoId") for it in items if it.get("contentDetails")]
                if not video_ids:
                    break
                r2 = requests.get(f"{base_api}/videos", params={"part":"contentDetails,snippet", "id": ",".join(video_ids), "key": api_key}, timeout=20)
                r2.raise_for_status()
                vids = {v["id"]: v for v in r2.json().get("items", [])}

                order = Lesson.objects.filter(module=module).count()
                for it in items:
                    vid = vids.get(it.get("contentDetails",{}).get("videoId"))
                    if not vid: continue
                    vtitle = vid["snippet"]["title"]
                    duration = parse_iso8601_duration(vid["contentDetails"].get("duration"))
                    thumb = (vid["snippet"].get("thumbnails") or {}).get("medium",{}).get("url")
                    vobj = Video.objects.create(
                        external_url=f"https://www.youtube.com/watch?v={vid['id']}",
                        title=vtitle,
                        duration_seconds=duration or 0,
                        thumbnail_url=thumb,
                    )
                    order += 1
                    Lesson.objects.create(module=module, title=vtitle, order=order, video=vobj, expected_duration_seconds=duration or 0)
                    total_created += 1

                nextPageToken = r.json().get("nextPageToken")
                if not nextPageToken: break

            created_courses.append((course.uuid, title, total_created))

        self.stdout.write(self.style.SUCCESS("Playlists importadas com sucesso."))
        for cid, title, n in created_courses:
            self.stdout.write(f"- {title} ({cid}) -> {n} vídeos")
