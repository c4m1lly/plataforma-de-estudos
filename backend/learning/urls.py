from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, ModuleViewSet, LessonViewSet, VideoViewSet,
    EnrollmentViewSet, ProgressViewSet
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"modules", ModuleViewSet, basename="module")
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"videos", VideoViewSet, basename="video")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")
router.register(r"progress", ProgressViewSet, basename="progress")

urlpatterns = [
    path("", include(router.urls)),
]