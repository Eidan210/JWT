# Campus API segura

API REST construida con **FastAPI** que implementa registro de usuarios, inicio de sesión y rutas protegidas mediante **JWT** (JSON Web Tokens). Las contraseñas se almacenan hasheadas con **Argon2**.

> ⚠️ Proyecto educativo: los usuarios se guardan en memoria (`usuarios_db`), por lo que se pierden al reiniciar el servidor.

## Características

- Registro de usuarios con validación (`username` 3–50 caracteres, `password` 6–100).
- Hash de contraseñas con `pwdlib` + Argon2.
- Autenticación con tokens JWT (HS256) que expiran a los 60 minutos.
- Rutas públicas y rutas protegidas por `Authorization: Bearer <token>`.
- Documentación interactiva automática (Swagger UI y ReDoc).

## Stack

| Componente | Librería |
|---|---|
| Framework web | `fastapi[standard]` |
| JWT | `PyJWT` |
| Hash de contraseñas | `pwdlib[argon2]` |
| Variables de entorno | `python-dotenv` |

## Estructura

```
despliegue/
├── main.py           # Aplicación FastAPI (modelos, auth y endpoints)
├── requirements.txt  # Dependencias
├── .env.example      # Plantilla de variables de entorno
└── .gitignore
```

## Instalación

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell/CMD)
# source venv/bin/activate     # Linux / macOS

# 2. Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` a `.env` y define la clave secreta usada para firmar los tokens:

```env
JTW_SECRET_KEY=tu_clave_secreta_larga_y_aleatoria
```

> El nombre de la variable en `main.py` es `JTW_SECRET_KEY` (sí, con `JTW`). Debe coincidir exactamente o la app falla al arrancar con `RuntimeError`.

Genera una clave segura con:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Nunca subas `.env` al repositorio (ya está en `.gitignore`).

## Ejecución

```bash
fastapi dev main.py
# o
uvicorn main:app --reload
```

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

## Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/publico` | No | Mensaje de bienvenida |
| POST | `/usuarios/registro` | No | Registra un usuario (201; 409 si ya existe) |
| POST | `/token` | No | Inicia sesión y devuelve un JWT (401 si credenciales inválidas) |
| GET | `/perfil` | Bearer | Devuelve el usuario autenticado |
| GET | `/cursos` | Bearer | Lista de cursos (`Python`, `Java`, `FastAPI`) |

### Ejemplo de uso

```bash
# Registro
curl -X POST http://127.0.0.1:8000/usuarios/registro \
  -H "Content-Type: application/json" \
  -d '{"username": "eidan", "password": "secreto123"}'

# Login (el cuerpo es JSON, no form-data)
curl -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" \
  -d '{"username": "eidan", "password": "secreto123"}'
# -> {"access_token": "<jwt>", "token_type": "bearer"}

# Ruta protegida
curl http://127.0.0.1:8000/perfil -H "Authorization: Bearer <jwt>"
```

## Errores de autenticación

| Código | Causa |
|---|---|
| 401 | Credenciales incorrectas, token inválido o expirado |
| 404 | El usuario del token ya no existe |
| 409 | Nombre de usuario ya registrado |

## Limitaciones y mejoras pendientes

- Persistencia: reemplazar el diccionario en memoria por una base de datos (PostgreSQL, SQLite + SQLAlchemy).
- `/usuarios/registro` devuelve el `password_hash` en la respuesta; conviene eliminarlo.
- `/token` recibe JSON (`UsuarioRegistro`), por lo que el botón *Authorize* de Swagger (que envía form-data OAuth2) no funciona; usar `OAuth2PasswordRequestForm` lo resolvería.
- Imports sin uso en `main.py` (`opentelemetry.trace.Status`, `OAuth2PasswordRequestForm`) y typo en el mensaje de `/publico` ("Bienvenkido").
- Añadir tests, rate limiting y refresh tokens.
