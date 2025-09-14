from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from docs.models import Category, Tutorial, Step, CodeExample, APIEndpoint


User = get_user_model()


class Command(BaseCommand):
    help = 'Populate Tutorials and API docs for Accounts endpoints (beginner friendly)'

    def handle(self, *args, **options):
        self.stdout.write('Creating Accounts documentation...')

        # Category for accounts/auth
        category, _ = Category.objects.get_or_create(
            slug='accounts',
            defaults={
                'name': 'Accounts',
                'description': 'User registration, login, tokens, and profile',
                'icon': 'fas fa-user-shield',
                'color': '#16a085',
                'order': 1,
                'is_active': True,
            },
        )

        # Author (fallback to first superuser or any user)
        author = User.objects.filter(is_staff=True).first() or User.objects.first()

        # Create the tutorial
        tutorial, _ = Tutorial.objects.get_or_create(
            slug='accounts-api-beginner-guide',
            defaults={
                'title': 'Accounts API: Beginner Step-by-Step Guide',
                'description': 'Learn how to Register, Login (JWT), use Refresh Token, check Me, and Logout. Includes Postman tests and a React + Vite example.',
                'content': (
                    'This tutorial explains the Accounts API in very simple English.\n\n'
                    'You will: register a user, get JWT tokens, call the profile endpoint, refresh tokens, and logout.\n'
                    'We also test in Postman and then call the same endpoints from a small React + Vite app.'
                ),
                'category': category,
                'difficulty': 'beginner',
                'estimated_time': 25,
                'prerequisites': 'Have the backend running locally at http://127.0.0.1:8000',
                'tags': 'accounts,auth,jwt,postman,react,vite',
                'author': author,
                'featured': True,
                'order': 1,
            },
        )

        # Steps content (plain text/markdown; keep simple language)
        steps_data = [
            (
                1,
                'Know the endpoints',
                'We will use these URLs:\n\n'
                '- Register: `POST /api/accounts/register/`\n'
                '- Login (email or roll/username): `POST /api/accounts/token/`\n'
                '- Refresh token: `POST /api/accounts/token/refresh/`\n'
                '- Me (get/update profile): `GET /api/accounts/me/` and `PUT/PATCH /api/accounts/me/`\n'
                '- Logout (blacklist refresh): `POST /api/accounts/logout/`',
            ),
            (
                2,
                'Register a user',
                'Send a POST to `/api/accounts/register/` with body:\n\n'
                '```json\n{\n  "username": "alice",\n  "email": "alice@example.com",\n  "password": "StrongPass123"\n}\n```\n\n'
                'Response contains the user. Now you can login with email or username.',
            ),
            (
                3,
                'Login and get JWT tokens',
                'POST to `/api/accounts/token/` with body:\n\n'
                '```json\n{\n  "username": "alice@example.com",\n  "password": "StrongPass123"\n}\n```\n\n'
                'You receive `access` and `refresh` tokens. Keep `refresh` safe. Use `access` in Authorization header: `Bearer ACCESS_TOKEN`.',
            ),
            (
                4,
                'Call Me endpoint',
                'Send `GET /api/accounts/me/` with header `Authorization: Bearer ACCESS_TOKEN`.\n'
                'You will get your profile. You can also update with `PUT` or `PATCH`.',
            ),
            (
                5,
                'Refresh the access token',
                'POST `/api/accounts/token/refresh/` with body:\n\n'
                '```json\n{\n  "refresh": "YOUR_REFRESH_TOKEN"\n}\n```\n\n'
                'You receive a new `access` token.',
            ),
            (
                6,
                'Logout',
                'POST `/api/accounts/logout/` with body containing your refresh token:\n\n'
                '```json\n{\n  "refresh": "YOUR_REFRESH_TOKEN"\n}\n```\n\n'
                'This blacklists the refresh token so it cannot be used again.',
            ),
            (
                7,
                'Test in Postman (quick)',
                '1) Create a new Collection.\n'
                '2) Add requests for each endpoint.\n'
                '3) After Login, save `access` and `refresh` to variables.\n'
                '4) Set Authorization header on requests: `Bearer {{access}}`.\n'
                '5) Use `{{refresh}}` in Refresh and Logout bodies.',
            ),
            (
                8,
                'React + Vite mini app',
                'Commands to create app:\n\n'
                '```bash\nnpm create vite@latest ch360-auth -- --template react\ncd ch360-auth\nnpm install\nnpm install axios\n```\n\n'
                'Add a small API helper and a login form. Example code is included below in Code Examples.',
            ),
        ]

        for order, title, content in steps_data:
            Step.objects.update_or_create(
                tutorial=tutorial,
                order=order,
                defaults={'title': title, 'content': content},
            )

        # Code examples: Postman curl, React axios
        CodeExample.objects.update_or_create(
            tutorial=tutorial,
            title='cURL: Login then call Me',
            defaults={
                'language': 'bash',
                'code': (
                    "curl -X POST 'http://127.0.0.1:8000/api/accounts/token/' -H 'Content-Type: application/json' "
                    "-d '{""username"": ""alice@example.com"", ""password"": ""StrongPass123""}'\n"
                    "# copy ACCESS from response then:\n"
                    "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/accounts/me/\n"
                ),
                'description': 'Quick local test with curl',
                'order': 1,
            },
        )

        CodeExample.objects.update_or_create(
            tutorial=tutorial,
            title='React Vite: simple auth client (Axios)',
            defaults={
                'language': 'javascript',
                'code': (
                    "// src/api.js\n"
                    "import axios from 'axios';\n\n"
                    "const api = axios.create({ baseURL: 'http://127.0.0.1:8000' });\n\n"
                    "export async function login(username, password) {\n"
                    "  const { data } = await api.post('/api/accounts/token/', { username, password });\n"
                    "  api.defaults.headers.common.Authorization = `Bearer ${data.access}`;\n"
                    "  return data;\n"
                    "}\n\n"
                    "export async function getMe() {\n"
                    "  const { data } = await api.get('/api/accounts/me/');\n"
                    "  return data;\n"
                    "}\n\n"
                    "// src/App.jsx\n"
                    "import { useState } from 'react';\n"
                    "import { login, getMe } from './api';\n\n"
                    "export default function App() {\n"
                    "  const [email, setEmail] = useState('alice@example.com');\n"
                    "  const [password, setPassword] = useState('StrongPass123');\n"
                    "  const [me, setMe] = useState(null);\n\n"
                    "  return (\n"
                    "    <div style={{ padding: 20 }}>\n"
                    "      <h2>CH360 Auth Demo</h2>\n"
                    "      <input value={email} onChange={e => setEmail(e.target.value)} placeholder='email or username'/>\n"
                    "      <input type='password' value={password} onChange={e => setPassword(e.target.value)} placeholder='password'/>\n"
                    "      <button onClick={async () => { await login(email, password); alert('Logged in'); }}>Login</button>\n"
                    "      <button onClick={async () => { const d = await getMe(); setMe(d); }}>Get Me</button>\n"
                    "      <pre>{me ? JSON.stringify(me, null, 2) : 'No data'}</pre>\n"
                    "    </div>\n"
                    "  );\n"
                    "}\n"
                ),
                'description': 'Drop-in snippets for a minimal React + Vite client',
                'order': 2,
            },
        )

        # APIEndpoint docs for each accounts route
        endpoints = [
            {
                'title': 'Register',
                'endpoint': '/api/accounts/register/',
                'method': 'POST',
                'description': 'Create a new user',
                'request_body': {
                    'username': {'type': 'string', 'required': True},
                    'email': {'type': 'string', 'required': True},
                    'password': {'type': 'string', 'required': True},
                },
                'status_codes': {'201': 'Created', '400': 'Validation error'},
                'authentication_required': False,
                'order': 1,
            },
            {
                'title': 'Login (JWT)',
                'endpoint': '/api/accounts/token/',
                'method': 'POST',
                'description': 'Obtain access and refresh tokens using email or username/roll',
                'request_body': {
                    'username': {'type': 'string', 'required': True},
                    'password': {'type': 'string', 'required': True},
                },
                'example_response': {'access': '...', 'refresh': '...'},
                'status_codes': {'200': 'OK', '401': 'Invalid credentials'},
                'authentication_required': False,
                'order': 2,
            },
            {
                'title': 'Refresh Token',
                'endpoint': '/api/accounts/token/refresh/',
                'method': 'POST',
                'description': 'Get a new access token using refresh token',
                'request_body': {'refresh': {'type': 'string', 'required': True}},
                'example_response': {'access': '...'},
                'status_codes': {'200': 'OK', '401': 'Invalid token'},
                'authentication_required': False,
                'order': 3,
            },
            {
                'title': 'Me (profile)',
                'endpoint': '/api/accounts/me/',
                'method': 'GET',
                'description': 'Get current user profile',
                'request_headers': {'Authorization': {'value': 'Bearer ACCESS', 'required': True}},
                'status_codes': {'200': 'OK', '401': 'Unauthorized'},
                'authentication_required': True,
                'order': 4,
            },
            {
                'title': 'Logout',
                'endpoint': '/api/accounts/logout/',
                'method': 'POST',
                'description': 'Blacklist refresh token to logout',
                'request_body': {'refresh': {'type': 'string', 'required': True}},
                'status_codes': {'205': 'Reset Content', '400': 'Invalid token', '401': 'Unauthorized'},
                'authentication_required': True,
                'order': 5,
            },
        ]

        for data in endpoints:
            APIEndpoint.objects.update_or_create(
                endpoint=data['endpoint'],
                method=data['method'],
                defaults={
                    **data,
                    'category': category,
                    'tags': 'accounts,auth,jwt',
                    'is_active': True,
                },
            )

        self.stdout.write(self.style.SUCCESS('Accounts documentation ready. Visit /docs/tutorials/'))

        # Additional per-endpoint detailed tutorials
        detailed_specs = [
            {
                'slug': 'accounts-register-detailed',
                'title': 'Register API – Step-by-step Guide',
                'desc': 'Create a new user account. Learn the body format, Postman testing, and React + Vite example.',
                'tags': 'accounts,register,signup,jwt',
                'order': 10,
                'steps': [
                    ('What this does', 'This endpoint creates a user in the system. No token is needed.'),
                    ('URL and method', 'POST `http://127.0.0.1:8000/api/accounts/register/`'),
                    ('Request body', 'JSON body:\n```json\n{\n  "username": "alice",\n  "email": "alice@example.com",\n  "password": "StrongPass123"\n}\n```'),
                    ('Postman test', 'Create a new Postman request (POST). Body -> raw -> JSON. Paste the body above. Send. You should get the user JSON back with id/email.'),
                    ('React + Vite', 'Example code below creates user and shows result.'),
                ],
                'code': [
                    ('bash', 'curl -X POST http://127.0.0.1:8000/api/accounts/register/ -H "Content-Type: application/json" -d "{\\"username\\":\\"alice\\",\\"email\\":\\"alice@example.com\\",\\"password\\":\\"StrongPass123\\"}"'),
                    ('javascript', "// src/register.js\nimport axios from 'axios';\nexport async function register(username, email, password){\n  const {data}=await axios.post('http://127.0.0.1:8000/api/accounts/register/',{username,email,password});\n  return data;\n}"),
                ],
            },
            {
                'slug': 'accounts-login-detailed',
                'title': 'Login API (JWT) – Step-by-step Guide',
                'desc': 'Obtain access and refresh tokens using email or username. Includes Postman and React examples.',
                'tags': 'accounts,login,jwt,tokens',
                'order': 11,
                'steps': [
                    ('What this does', 'Authenticates the user and returns two tokens: access and refresh.'),
                    ('URL and method', 'POST `http://127.0.0.1:8000/api/accounts/token/`'),
                    ('Request body', '```json\n{\n  "username": "alice@example.com",\n  "password": "StrongPass123"\n}\n```'),
                    ('Postman test', 'Create a POST request, set body to JSON above. Copy `access` and `refresh` from the response for later steps.'),
                    ('React + Vite', 'Use Axios to call the login API and store access token in memory for subsequent calls.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/accounts/token/ -H 'Content-Type: application/json' -d '{\"username\":\"alice@example.com\",\"password\":\"StrongPass123\"}'"),
                    ('javascript', "// src/auth.js\nimport axios from 'axios';\nexport async function login(username,password){\n  const {data}=await axios.post('http://127.0.0.1:8000/api/accounts/token/',{username,password});\n  axios.defaults.headers.common.Authorization = `Bearer ${data.access}`;\n  return data;\n}"),
                ],
            },
            {
                'slug': 'accounts-me-detailed',
                'title': 'Me API – Step-by-step Guide',
                'desc': 'Read the logged-in user profile using the access token.',
                'tags': 'accounts,me,profile,jwt',
                'order': 12,
                'steps': [
                    ('What this does', 'Returns the current authenticated user details. Requires access token.'),
                    ('URL and method', 'GET `http://127.0.0.1:8000/api/accounts/me/`'),
                    ('Headers', 'Add `Authorization: Bearer ACCESS_TOKEN`'),
                    ('Postman test', 'Set the header with the access token received from login and click Send.'),
                    ('React + Vite', 'Call the endpoint with Axios after setting default Authorization header during login.'),
                ],
                'code': [
                    ('bash', "curl -H 'Authorization: Bearer ACCESS_TOKEN' http://127.0.0.1:8000/api/accounts/me/"),
                    ('javascript', "// src/me.js\nimport axios from 'axios';\nexport async function getMe(){\n  const {data}=await axios.get('http://127.0.0.1:8000/api/accounts/me/');\n  return data;\n}"),
                ],
            },
            {
                'slug': 'accounts-refresh-detailed',
                'title': 'Refresh Token API – Step-by-step Guide',
                'desc': 'Use the refresh token to get a new access token when it expires.',
                'tags': 'accounts,refresh,jwt',
                'order': 13,
                'steps': [
                    ('What this does', 'Takes your refresh token and returns a fresh access token.'),
                    ('URL and method', 'POST `http://127.0.0.1:8000/api/accounts/token/refresh/`'),
                    ('Request body', '```json\n{\n  "refresh": "YOUR_REFRESH_TOKEN"\n}\n```'),
                    ('Postman test', 'Send the body above; copy the new `access` for subsequent requests.'),
                    ('React + Vite', 'Create a function to refresh and update Axios default Authorization header.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/accounts/token/refresh/ -H 'Content-Type: application/json' -d '{\"refresh\":\"YOUR_REFRESH_TOKEN\"}'"),
                    ('javascript', "// src/refresh.js\nimport axios from 'axios';\nexport async function refresh(refreshToken){\n  const {data}=await axios.post('http://127.0.0.1:8000/api/accounts/token/refresh/',{refresh:refreshToken});\n  axios.defaults.headers.common.Authorization = `Bearer ${data.access}`;\n  return data;\n}"),
                ],
            },
            {
                'slug': 'accounts-logout-detailed',
                'title': 'Logout API – Step-by-step Guide',
                'desc': 'Blacklist the refresh token so it can’t be used again.',
                'tags': 'accounts,logout,jwt',
                'order': 14,
                'steps': [
                    ('What this does', 'Invalidates the refresh token. Access token expires naturally later.'),
                    ('URL and method', 'POST `http://127.0.0.1:8000/api/accounts/logout/`'),
                    ('Request body', '```json\n{\n  "refresh": "YOUR_REFRESH_TOKEN"\n}\n```'),
                    ('Postman test', 'Send the body above. Expect HTTP 205 if success. Subsequent refresh with the same token should fail.'),
                    ('React + Vite', 'Call logout with the stored refresh token; then clear tokens in your app state.'),
                ],
                'code': [
                    ('bash', "curl -X POST http://127.0.0.1:8000/api/accounts/logout/ -H 'Content-Type: application/json' -d '{\"refresh\":\"YOUR_REFRESH_TOKEN\"}'"),
                    ('javascript', "// src/logout.js\nimport axios from 'axios';\nexport async function logout(refreshToken){\n  await axios.post('http://127.0.0.1:8000/api/accounts/logout/',{refresh:refreshToken});\n  delete axios.defaults.headers.common.Authorization;\n}"),
                ],
            },
        ]

        for spec in detailed_specs:
            tut, _ = Tutorial.objects.update_or_create(
                slug=spec['slug'],
                defaults={
                    'title': spec['title'],
                    'description': spec['desc'],
                    'content': spec['desc'],
                    'category': category,
                    'difficulty': 'beginner',
                    'estimated_time': 10,
                    'prerequisites': 'Backend running locally; have Postman installed',
                    'tags': spec['tags'],
                    'author': author,
                    'featured': False,
                    'order': spec['order'],
                },
            )

            # Steps
            Step.objects.filter(tutorial=tut).delete()
            for idx, (title, content) in enumerate(spec['steps'], start=1):
                Step.objects.create(tutorial=tut, title=title, content=content, order=idx)

            # Code examples
            CodeExample.objects.filter(tutorial=tut).delete()
            for idx, (lang, code) in enumerate(spec['code'], start=1):
                CodeExample.objects.create(tutorial=tut, language=lang, code=code, title=f'Example {idx}', order=idx)

        self.stdout.write(self.style.SUCCESS('Added per-endpoint detailed tutorials.'))


