from django.db.models import Sum, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.conf import settings
from urllib.parse import urlparse, parse_qs
import os
import re
import requests

from .models import (
    Course, Module, Lesson, Video,
    Enrollment, Progress, VideoViewEvent
)
from .serializers import (
    CourseSerializer, ModuleSerializer, LessonSerializer, VideoSerializer,
    EnrollmentSerializer, ProgressSerializer, VideoViewEventSerializer
)
from .permissions import IsCourseOwnerOrReadOnly

User = get_user_model()


# -----------------------
# Helpers
# -----------------------
ISO8601_DURATION_RE = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$")

def parse_iso8601_duration(iso: str) -> int:
    """
    Converte 'PT#H#M#S' para segundos.
    """
    m = ISO8601_DURATION_RE.match(iso or "")
    if not m:
        return 0
    h = int(m.group(1) or 0)
    mn = int(m.group(2) or 0)
    s = int(m.group(3) or 0)
    return h * 3600 + mn * 60 + s


def extract_yt_playlist_id(playlist_url: str) -> str | None:
    """
    Extrai o 'list' de URLs do YouTube (playlist). Ex:
    https://www.youtube.com/playlist?list=PLabc...
    https://www.youtube.com/watch?v=XXX&list=PLabc...
    """
    try:
        parsed = urlparse(playlist_url)
        q = parse_qs(parsed.query)
        return (q.get("list") or [None])[0]
    except Exception:
        return None


# -----------------------
# ViewSets
# -----------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related("owner")
    serializer_class = CourseSerializer

    def get_permissions(self):
        # Público para listar/consultar curso e a rota aninhada de módulos
        if self.action in ["list", "retrieve", "modules"]:
            return [AllowAny()]
        if self.action in ["create"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsCourseOwnerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # --- Matrícula do usuário no curso ---
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        obj, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
        return Response(EnrollmentSerializer(obj).data, status=status.HTTP_200_OK)

    # --- Estatísticas (agregadas) do curso ---
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def stats(self, request, pk=None):
        lessons = Lesson.objects.filter(module__course_id=pk)
        prog = Progress.objects.filter(lesson__in=lessons)
        completed = prog.filter(completed=True).count()
        total = prog.count() or 1
        rate = completed / total
        watch_time = prog.aggregate(s=Sum("watch_time_seconds")).get("s") or 0
        return Response({
            "lessons_count": lessons.count(),
            "progress_records": total,
            "completed_records": completed,
            "avg_lesson_completion_rate": round(float(rate) * 100.0, 2),
            "total_watch_time_seconds": int(watch_time),
        }, status=200)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="in-progress")
    def in_progress(self, request):
        user = request.user

        lessons_per_course = (
            Lesson.objects
            .values("module__course_id")
            .annotate(total=Count("uuid"))
        )
        total_map = {row["module__course_id"]: row["total"] for row in lessons_per_course}

        done_per_course = (
            Progress.objects
            .filter(user=user, completed=True)
            .values("lesson__module__course_id")
            .annotate(done=Count("uuid"))
        )
        done_map = {row["lesson__module__course_id"]: row["done"] for row in done_per_course}

        data = []
        for c in Course.objects.all().select_related("owner"):
            total = total_map.get(c.uuid, 0)
            done = done_map.get(c.uuid, 0)
            pct = round((done / total) * 100.0, 2) if total else 0.0
            data.append({
                "id": str(c.uuid),
                "title": c.title,
                "description": c.description,
                "progress": pct,
            })
        return Response(data, status=200)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="user-progress")
    def user_progress(self, request, pk=None):
        user = request.user
        lessons = Lesson.objects.filter(module__course_id=pk).values_list("uuid", flat=True)
        user_prog = (
            Progress.objects
            .filter(user=user, lesson__uuid__in=list(lessons))
            .values("lesson_id", "completed", "watch_time_seconds", "last_position_seconds")
        )
        return Response(list(user_prog), status=200)

    @action(detail=True, methods=["get"], permission_classes=[AllowAny], url_path="modules")
    def modules(self, request, pk=None):
        ordering = request.query_params.get("ordering") or "order"
        qs = Module.objects.filter(course_id=pk)
        try:
            qs = qs.order_by(ordering, "title")
        except Exception:
            qs = qs.order_by("order", "title")
        return Response(ModuleSerializer(qs, many=True).data, status=200)

class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_permissions(self):
        # Público pode ver; alterações exigem auth
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        course = self.request.query_params.get("course")
        if course:
            qs = qs.filter(course_id=course)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            try:
                qs = qs.order_by(ordering, "title")
            except Exception:
                qs = qs.order_by("order", "title")
        else:
            qs = qs.order_by("order", "title")
        return qs


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all().select_related("module", "video")
    serializer_class = LessonSerializer

    def get_permissions(self):
        # Público pode ver; alterações exigem auth
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        module = self.request.query_params.get("module")
        if module:
            qs = qs.filter(module_id=module)
        ordering = self.request.query_params.get("ordering")
        if ordering:
            try:
                qs = qs.order_by(ordering, "title")
            except Exception:
                qs = qs.order_by("order", "title")
        else:
            qs = qs.order_by("order", "title")
        return qs


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    # Importar playlist do YouTube e criar (Module -> Lessons -> Video)
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="import-youtube")
    def import_youtube(self, request):
        """
        body:
          {
            "playlist_url": "...",
            "course_id": "<uuid do course>",
            "module_title": "opcional (default: Playlist YouTube)"
          }
        """
        # 1) API key
        api_key = getattr(settings, "YOUTUBE_API_KEY", None) or os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return Response({"detail": "YOUTUBE_API_KEY não configurada"}, status=400)

        # 2) Params obrigatórios
        playlist_url = (request.data.get("playlist_url") or "").strip()
        course_id = request.data.get("course_id")
        module_title = (request.data.get("module_title") or "Playlist YouTube").strip()
        if not course_id:
            return Response({"detail": "course_id é obrigatório"}, status=400)

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({"detail": "Curso não encontrado"}, status=404)

        playlist_id = extract_yt_playlist_id(playlist_url)
        if not playlist_id:
            return Response({"detail": "URL de playlist inválida (parâmetro 'list' não encontrado)"}, status=400)

        # 3) Cria módulo
        module = Module.objects.create(course=course, title=module_title, order=(Module.objects.filter(course=course).count() + 1))

        # 4) Busca itens da playlist e cria vídeos/lessons
        base = "https://www.googleapis.com/youtube/v3"
        next_page = None
        order = Lesson.objects.filter(module=module).count()

        while True:
            params = {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": 50,
                "pageToken": next_page or "",
                "key": api_key,
            }
            r = requests.get(f"{base}/playlistItems", params=params, timeout=20)
            if r.status_code != 200:
                try:
                    err = r.json()
                except Exception:
                    err = {"status": r.status_code, "text": r.text[:200]}
                return Response({"detail": "Falha YouTube playlistItems", "error": err}, status=502)

            items = r.json().get("items", [])
            video_ids = [it.get("contentDetails", {}).get("videoId") for it in items if it.get("contentDetails")]
            if not video_ids:
                break

            r2 = requests.get(f"{base}/videos", params={"part": "contentDetails,snippet", "id": ",".join(video_ids), "key": api_key}, timeout=20)
            if r2.status_code != 200:
                try:
                    err2 = r2.json()
                except Exception:
                    err2 = {"status": r2.status_code, "text": r2.text[:200]}
                return Response({"detail": "Falha YouTube videos", "error": err2}, status=502)

            vids = {v["id"]: v for v in r2.json().get("items", [])}
            for it in items:
                vid_id = (it.get("contentDetails") or {}).get("videoId")
                if not vid_id or vid_id not in vids:
                    continue
                vid = vids[vid_id]
                title = vid["snippet"]["title"]
                duration = parse_iso8601_duration((vid["contentDetails"] or {}).get("duration"))
                thumb = ((vid["snippet"] or {}).get("thumbnails") or {}).get("medium", {}).get("url")

                vobj = Video.objects.create(
                    external_url=f"https://www.youtube.com/watch?v={vid_id}",
                    title=title,
                    duration_seconds=duration or 0,
                    thumbnail_url=thumb,
                )
                order += 1
                Lesson.objects.create(
                    module=module,
                    title=title,
                    order=order,
                    video=vobj,
                    expected_duration_seconds=duration or 0,
                )

            next_page = r.json().get("nextPageToken")
            if not next_page:
                break

        return Response({"detail": "Playlist importada com sucesso", "module_id": str(module.uuid)}, status=201)


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]


class ProgressViewSet(viewsets.ModelViewSet):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    permission_classes = [IsAuthenticated]

    # Registrar progresso de vídeo/lesson (tick)
    # POST /learning/progress/tick/
    # body: {"lesson": "<uuid>", "seconds": 30, "position": 120}
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated], url_path="tick")
    def tick(self, request):
        user = request.user
        lesson_id = request.data.get("lesson")
        seconds = int(request.data.get("seconds", 0))
        position = int(request.data.get("position", 0))

        if not lesson_id:
            return Response({"detail": "lesson é obrigatório"}, status=400)

        try:
            lesson = Lesson.objects.get(pk=lesson_id)
        except Lesson.DoesNotExist:
            return Response({"detail": "Aula não encontrada"}, status=404)

        prog, _ = Progress.objects.get_or_create(user=user, lesson=lesson)
        prog.watch_time_seconds = (prog.watch_time_seconds or 0) + max(0, seconds)
        prog.last_position_seconds = max(prog.last_position_seconds or 0, position)
        if lesson.expected_duration_seconds and prog.watch_time_seconds >= lesson.expected_duration_seconds * 0.9:
            prog.completed = True
        prog.save()

        VideoViewEvent.objects.create(
            user=user,
            lesson=lesson,
            seconds_watched=max(0, seconds),
            position_seconds=max(0, position),
        )

        return Response(ProgressSerializer(prog).data, status=200)
