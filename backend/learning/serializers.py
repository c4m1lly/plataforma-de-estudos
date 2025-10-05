from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Course, Module, Lesson, Video, Enrollment, Progress, VideoViewEvent
)

User = get_user_model()

class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["uuid", "title", "file", "external_url", "duration_seconds", "transcoding_status", "thumbnail_url", "created_at"]

class LessonSerializer(serializers.ModelSerializer):
    video = VideoSerializer(read_only=True)
    video_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Lesson
        fields = ["uuid", "module", "title", "description", "order", "expected_duration_seconds", "video", "video_uuid", "created_at"]

    def create(self, validated_data):
        video_uuid = validated_data.pop("video_uuid", None)
        if video_uuid:
            try:
                video = Video.objects.get(pk=video_uuid)
                validated_data["video"] = video
            except Video.DoesNotExist:
                pass
        return super().create(validated_data)

class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    class Meta:
        model = Module
        fields = ["uuid", "course", "title", "order", "lessons", "created_at"]

class CourseSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        fields = ["uuid", "title", "slug", "description", "is_published", "owner", "owner_email", "modules", "created_at"]
        read_only_fields = ["slug", "owner"]

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["uuid", "user", "course", "created_at"]

class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ["uuid", "user", "lesson", "completed", "watch_time_seconds", "last_position_seconds", "updated_at"]

class VideoViewEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoViewEvent
        fields = ["uuid", "user", "lesson", "seconds_watched", "position_seconds", "client_ts", "created_at"]