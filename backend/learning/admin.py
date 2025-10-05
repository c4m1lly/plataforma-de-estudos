from django.contrib import admin
from .models import (
    Course, Module, Lesson, Video, Enrollment, Progress, VideoViewEvent
)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "is_published", "created_at")
    search_fields = ("title", "description", "owner__email")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__title")

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order", "video", "created_at")
    list_filter = ("module",)
    search_fields = ("title", "module__title")

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "duration_seconds", "transcoding_status", "created_at")
    search_fields = ("title",)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "created_at")
    list_filter = ("course",)

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "watch_time_seconds", "last_position_seconds", "updated_at")
    list_filter = ("lesson__module__course", "completed")

@admin.register(VideoViewEvent)
class VideoViewEventAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "seconds_watched", "position_seconds", "client_ts", "created_at")
    list_filter = ("lesson__module__course",)