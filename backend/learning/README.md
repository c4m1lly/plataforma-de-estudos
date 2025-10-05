# Learning App (sem quizzes)

Recursos principais:
- CRUD de **Course / Module / Lesson / Video**.
- Upload de **Video** (multipart), link externo opcional.
- **Enrollment** do aluno no curso.
- Registro de **Progress** por aula, com endpoint `progress/tick/` para player.
- **Analytics** rápidos: `/courses/{id}/stats/` e `/courses/{id}/students/`.

Instalação:
- Adicione `learning` ao `INSTALLED_APPS`.
- Inclua `path("learning/", include("learning.urls"))` nas URLs do projeto.
- `python manage.py makemigrations learning && python manage.py migrate`