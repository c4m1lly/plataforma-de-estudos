from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Quiz, Question, Option, QuizAttempt, AttemptAnswer
from .serializers import (
    QuizSerializer, QuestionSerializer, OptionSerializer,
    QuizAttemptSerializer, AttemptAnswerSerializer
)
from .permissions import IsAuthenticatedOrReadOnly

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().prefetch_related("questions__options")
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().prefetch_related("options")
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

class OptionViewSet(viewsets.ModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    permission_classes = [IsAuthenticated]

class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all().select_related("quiz", "user")
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def my_attempts(self, request):
        qs = self.queryset.filter(user=request.user).order_by("-created_at")
        return Response(self.get_serializer(qs, many=True).data)

class AttemptAnswerViewSet(viewsets.ModelViewSet):
    queryset = AttemptAnswer.objects.all().select_related("attempt", "question", "selected_option")
    serializer_class = AttemptAnswerSerializer
    permission_classes = [IsAuthenticated]