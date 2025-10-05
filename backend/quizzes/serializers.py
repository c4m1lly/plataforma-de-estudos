from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from .models import Quiz, Question, Option, QuizAttempt, AttemptAnswer

User = get_user_model()

class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = ["uuid", "text", "is_correct"]
        extra_kwargs = {"is_correct": {"write_only": True}}

class QuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    class Meta:
        model = Question
        fields = ["uuid", "text", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)
        for opt in options_data:
            Option.objects.create(question=question, **opt)
        return question

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)
    content_type = serializers.SlugRelatedField(slug_field="model", queryset=ContentType.objects.all())

    class Meta:
        model = Quiz
        fields = ["uuid", "title", "content_type", "object_id", "questions", "created_at"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        # map content_type by model label
        ct_label = validated_data.pop("content_type")
        ct = ContentType.objects.get(model=ct_label)
        quiz = Quiz.objects.create(content_type=ct, **validated_data)
        for qd in questions_data:
            options = qd.pop("options", [])
            q = Question.objects.create(quiz=quiz, **qd)
            for od in options:
                Option.objects.create(question=q, **od)
        return quiz

class AttemptAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptAnswer
        fields = ["uuid", "question", "selected_option"]

class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AttemptAnswerSerializer(many=True, write_only=True, required=False)
    class Meta:
        model = QuizAttempt
        fields = ["uuid", "quiz", "user", "score", "answers", "created_at"]
        read_only_fields = ["score"]

    def create(self, validated_data):
        answers_data = validated_data.pop("answers", [])
        attempt = QuizAttempt.objects.create(**validated_data)
        correct = 0
        total = 0
        for ans in answers_data:
            AttemptAnswer.objects.create(attempt=attempt, **ans)
            total += 1
            try:
                # verify correctness from selected_option
                if ans["selected_option"].is_correct:
                    correct += 1
            except Exception:
                pass
        attempt.score = (correct / total) * 100 if total else 0.0
        attempt.save(update_fields=["score"])
        return attempt