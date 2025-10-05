from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Course, Enrollment

User = get_user_model()

class CourseSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Course
        fields = ["uuid", "title", "slug", "description", "is_published", "owner", "owner_email", "created_at"]
        read_only_fields = ["slug", "owner"]

class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["uuid", "user", "course", "created_at"]