# Courses App (Cursos + Matrículas)

App Django independente para gerenciamento de **cursos** e **matrículas**.

## Recursos
- CRUD de **Course**
- **Enroll** (`POST /courses/{id}/enroll/`) para matricular o usuário logado
- Listagem de **students** do curso
- Admin com filtros úteis

## Instalação
1) `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "courses",
]
```

2) URLs do projeto:
```python
from django.urls import path, include

urlpatterns = [
    # ...
    path("courses/", include("courses.urls")),
]
```

3) Migrations:
```
python manage.py makemigrations courses
python manage.py migrate
```

4) Requisitos:
```
pip install djangorestframework
```