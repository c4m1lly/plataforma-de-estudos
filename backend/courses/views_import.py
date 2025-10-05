
from uuid import uuid4
from django.db import IntegrityError, transaction
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from learning.models import Course as LearningCourse, Module
from learning.youtube_import import import_playlist_into_module

class ImportYouTubeCourse(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        playlist_val = (
            request.data.get("playlist_id")
            or request.data.get("playlistId")
            or request.data.get("id")
            or request.data.get("playlist_url")
            or request.data.get("playlistUrl")
            or request.data.get("url")
            or request.data.get("playlist")
        )
        if not playlist_val:
            return Response({"detail": "playlist_id é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        base_title = request.data.get("title") or request.data.get("name") or "Curso importado do YouTube"
        description = request.data.get("description") or ""

        attempts = 0
        max_attempts = 10
        course = None
        while attempts < max_attempts:
            attempts += 1
            title_try = base_title if attempts == 1 else f"{base_title} - {uuid4().hex[:8]}"
            try:
                with transaction.atomic():
                    course = LearningCourse.objects.create(
                        owner=request.user,
                        title=title_try,
                        description=description,
                        is_published=False,
                    )
                break
            except IntegrityError:
                continue

        if not course:
            return Response({"detail": "Não foi possível gerar um slug único para o curso."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        module = Module.objects.create(course=course, title="Playlist", order=1)

        try:
            v_count, l_count = import_playlist_into_module(module, str(playlist_val).strip())
        except RuntimeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"Falha ao importar: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "course_uuid": str(course.uuid),
                "module_uuid": str(module.uuid),
                "videos_created": v_count,
                "lessons_created": l_count,
            },
            status=status.HTTP_201_CREATED,
        )
