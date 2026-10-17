
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from opentelemetry.trace import Status
from pwdlib import PasswordHash
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm    
from datetime import datetime, timedelta, timezone
import jwt


load_dotenv()

CLAVE_SECRETA = os.getenv("JTW_SECRET_KEY")
ALGORITMO = "HS256"
MINUTOS_EXPIRACION = 60

if not CLAVE_SECRETA:
    raise RuntimeError("La clave secreta no está definida en las variables de entorno.")

usuarios_db = {}

contexto_password = PasswordHash.recommended()

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="token")

class UsuarioRegistro(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class RespuestaToken(BaseModel):
    access_token: str
    token_type: str

def hashear_password(password: str)-> str:
    return contexto_password.hash(password)

def verificar_password(password: str, hash_guardado: str) -> bool:
    return contexto_password.verify(password, hash_guardado)

app = FastAPI(title = "Campus API segura")
    

@app.get("/publico")
def publico():
    return {"mensaje": "Bienvenkido a campus API segura, esta es una ruta pública"}

@app.post("/usuarios/registro", status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioRegistro):
    
    if usuario.username in usuarios_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya está en uso."
        )
    
    usuarios_db[usuario.username] = {
        "username": usuario.username,
        "password": hashear_password(usuario.password)
    }
    return {
        "mensaje": "Usuario registrado exitosamente.",
        "usuario": usuario.username,
        "password_hash": usuarios_db[usuario.username]["password"]
    }
    
def crear_token_acceso(username: str) -> str:
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_EXPIRACION)

    payload = {
        "sub": username,
        "exp": expiracion,
    }

    token = jwt.encode(payload, CLAVE_SECRETA, algorithm=ALGORITMO)
    return token

@app.post("/token", response_model=RespuestaToken)
def iniciar_sesion(formulario: UsuarioRegistro):
    usuario = usuarios_db.get(formulario.username)
    
    if not usuario or not verificar_password(formulario.password, usuario["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_acceso = crear_token_acceso(usuario["username"])
    return {"access_token": token_acceso, "token_type": "bearer"}

def obtener_usuario_actual(token: str = Depends(esquema_oauth2))-> dict:
    try:
        payload = jwt.decode(token, CLAVE_SECRETA, algorithms=[ALGORITMO])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    usuario = usuarios_db.get(username)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    
    return usuario
@app.get("/perfil")
def perfil(usuario: dict = Depends(obtener_usuario_actual)):
    return {"mensaje": "perfil autorizado", "usuario": usuario["username"]}

@app.get("/cursos")
def cursos(usuario: dict = Depends(obtener_usuario_actual)):
    return {"mensaje": ["Python", "Java", "FastAPI"], "usuario": usuario["username"]}