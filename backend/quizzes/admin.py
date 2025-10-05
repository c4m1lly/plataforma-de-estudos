from django.contrib import admin
from .models import Quiz, Question, Option, QuizAttempt, AttemptAnswer

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "content_type", "object_id", "created_at")
    list_filter = ("content_type",)
    search_fields = ("title", "object_id")

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz")
    search_fields = ("text",)

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text",)

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("quiz", "user", "score", "created_at")
    list_filter = ("quiz",)

@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "selected_option")