from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuizViewSet, QuestionViewSet, OptionViewSet,
    QuizAttemptViewSet, AttemptAnswerViewSet
)

router = DefaultRouter()
router.register(r"quizzes", QuizViewSet, basename="quiz")
router.register(r"questions", QuestionViewSet, basename="question")
router.register(r"options", OptionViewSet, basename="option")
router.register(r"attempts", QuizAttemptViewSet, basename="attempt")
router.register(r"answers", AttemptAnswerViewSet, basename="answer")

urlpatterns = [
    path("", include(router.urls)),
]