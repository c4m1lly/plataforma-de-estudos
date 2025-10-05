import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Course(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="courses")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    is_published = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Module(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=180)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} / {self.title}"

class Video(TimeStampedModel):
    TRANSCODE_CHOICES = (
        ("n/a", "Not applicable"),
        ("pending", "Pending"),
        ("done", "Done"),
        ("failed", "Failed"),
    )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to="learning/videos/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    title = models.CharField(max_length=180, default="")
    duration_seconds = models.PositiveIntegerField(default=0)
    transcoding_status = models.CharField(max_length=10, choices=TRANSCODE_CHOICES, default="n/a")
    thumbnail_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.title or (self.external_url or str(self.uuid))

class Lesson(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=1)
    video = models.ForeignKey(Video, on_delete=models.SET_NULL, null=True, blank=True, related_name="lessons")
    expected_duration_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.module.title} / {self.title}"

class Enrollment(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} -> {self.course}"

class Progress(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    watch_time_seconds = models.PositiveIntegerField(default=0)
    last_position_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "lesson")

class VideoViewEvent(TimeStampedModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_events")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="video_events")
    seconds_watched = models.PositiveIntegerField(default=0)
    position_seconds = models.PositiveIntegerField(default=0)
    client_ts = models.DateTimeField(default=timezone.now)