# Quizzes App (independente com contenttypes)

Módulo Django para criar e aplicar **quizzes** desacoplados, podendo anexá-los a qualquer objeto
(`learning.Lesson`, `courses.Course`, etc.) via **contenttypes**.

## Recursos
- CRUD de **Quiz**, **Question**, **Option**
- **QuizAttempt** com avaliação automática (percentual)
- Endpoint para listar **minhas tentativas**
- Admin com listas/filtros úteis
- Totalmente independente: apenas requer `AUTH_USER_MODEL`

## Instalação
1) `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    "django.contrib.contenttypes",
    "rest_framework",
    "quizzes",
]
```

2) URLs do projeto:
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("quizzes/", include("quizzes.urls")),
]
```

3) Migrations:
```
python manage.py makemigrations quizzes
python manage.py migrate
```

## Como anexar um quiz a um objeto (ex.: lesson do app learning)
- O `Quiz` usa `content_type` por **model label** (ex.: `"lesson"` se o model se chama `Lesson`).
- Na criação via API, envie:
```json
{
  "title": "Quiz da Aula 1",
  "content_type": "lesson",
  "object_id": "UUID-ou-ID-da-aula",
  "questions": [
    {
      "text": "2+2?",
      "options": [
        {"text": "3", "is_correct": false},
        {"text": "4", "is_correct": true}
      ]
    }
  ]
}
```

## Envio de tentativa
`POST /quizzes/attempts/`:
```json
{
  "quiz": "uuid-do-quiz",
  "user": "uuid-do-usuario",
  "answers": [
    {"question": "uuid-da-pergunta", "selected_option": "uuid-da-opcao"}
  ]
}
```
- O backend computa `score` automaticamente (0–100).

## Minhas tentativas
- `GET /quizzes/attempts/my_attempts/` (autenticado)