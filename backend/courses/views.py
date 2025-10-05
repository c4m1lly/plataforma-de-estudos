from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Course, Enrollment
from .serializers import CourseSerializer, EnrollmentSerializer
from .permissions import IsCourseOwnerOrReadOnly

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().select_related("owner")
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        if self.action in ["create"]:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsCourseOwnerOrReadOnly()]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        course = self.get_object()
        obj, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
        return Response(EnrollmentSerializer(obj).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def students(self, request, pk=None):
        qs = Enrollment.objects.filter(course_id=pk).select_related("user").order_by("-created_at")
        return Response(EnrollmentSerializer(qs, many=True).data)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]