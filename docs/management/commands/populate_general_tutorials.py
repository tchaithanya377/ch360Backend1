from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate general getting-started tutorials for the Docs app'

    def handle(self, *args, **options):
        self.stdout.write('Creating general Docs tutorials...')

        category, _ = Category.objects.get_or_create(
            slug='getting-started',
            defaults={
                'name': 'Getting Started',
                'description': 'How to use the documentation and APIs effectively',
                'icon': 'fas fa-rocket',
                'color': '#1abc9c',
                'order': 0,
                'is_active': True,
            },
        )

        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        tutorials = [
            {
                'slug': 'using-the-tutorials',
                'title': 'How to Use Tutorials Effectively',
                'desc': 'Filters, search, difficulty levels, and reading steps/code blocks.',
                'steps': [
                    ('Browse & filter', 'Use the left sidebar to filter by Category and Difficulty.'),
                    ('Search', 'Use the top search bar to find tutorials or APIs instantly.'),
                    ('Follow the steps', 'Each tutorial has Overview, Step-by-Step, and Code Examples sections.'),
                ],
                'code': [],
                'order': 1,
            },
            {
                'slug': 'react-vite-quickstart',
                'title': 'React + Vite Client Quickstart',
                'desc': 'Create a tiny React client to call CampusHub APIs.',
                'steps': [
                    ('Create app', 'Run `npm create vite@latest ch360-client -- --template react` then `cd ch360-client && npm install && npm install axios`.'),
                    ('API helper', 'Create `src/api.js` and paste the Axios instance below. Set token after login.'),
                    ('Test call', 'Use the example component to call any endpoint (e.g., Students List).'),
                ],
                'code': [
                    ('javascript', "// src/api.js\nimport axios from 'axios';\nexport const api = axios.create({ baseURL: 'http://127.0.0.1:8000' });\nexport function setToken(token){ api.defaults.headers.common.Authorization = `Bearer ${token}`;}"),
                    ('javascript', "// src/App.jsx\nimport { useState } from 'react';\nimport { api } from './api';\nexport default function App(){\n  const [rows, setRows] = useState([]);\n  async function load(){ const {data} = await api.get('/api/v1/students/students/'); setRows(data);}\n  return (<div style={{padding:20}}><button onClick={load}>Load Students</button><pre>{JSON.stringify(rows,null,2)}</pre></div>);\n}"),
                ],
                'order': 2,
            },
        ]

        for spec in tutorials:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 8,
                    'tags': 'getting-started,react,vite,docs',
                    'author': author,
                    'order': spec['order'],
                    'featured': True,
                },
            )
            Step.objects.filter(tutorial=tut).delete()
            for idx, (title, content) in enumerate(spec['steps'], start=1):
                Step.objects.create(tutorial=tut, title=title, content=content, order=idx)
            CodeExample.objects.filter(tutorial=tut).delete()
            for idx, (lang, code) in enumerate(spec['code'], start=1):
                CodeExample.objects.create(tutorial=tut, language=lang, code=code, title=f'Example {idx}', order=idx)

        self.stdout.write(self.style.SUCCESS('General Docs tutorials ready. Visit /docs/tutorials/'))

