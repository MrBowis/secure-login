# Secure Login - Proyecto Fullstack

Este proyecto implementa un sistema de autenticación seguro con 2FA (TOTP) usando **FastAPI** (backend) y **Next.js** (frontend).

## 📁 Estructura del Proyecto

```
secure-login/
├── backend/    # API FastAPI + PostgreSQL
└── frontend/   # Next.js (React)
```

---

## 🏗️ Metodología y Arquitectura

### Enfoque de Desarrollo

Este proyecto sigue una **arquitectura en capas (Layered Architecture)** combinada con el **patrón Repository** y **principios SOLID**. Esta metodología fue elegida por las siguientes razones:

#### 1. **Arquitectura en Capas**
Separa las responsabilidades en capas bien definidas:
- **Capa de Presentación (Routers)**: Maneja HTTP requests/responses
- **Capa de Lógica de Negocio (Services)**: Implementa reglas de negocio
- **Capa de Acceso a Datos (Repositories)**: Gestiona operaciones con la base de datos
- **Capa de Modelos**: Define la estructura de datos

**Ventajas**:
- ✅ Separación clara de responsabilidades
- ✅ Facilita testing unitario de cada capa
- ✅ Permite cambiar implementaciones sin afectar otras capas
- ✅ Código más mantenible y escalable

#### 2. **Patrón Repository**
Abstrae el acceso a datos, proporcionando una interfaz limpia para operaciones CRUD:
- Centraliza las consultas a la base de datos
- Facilita el cambio de proveedor de base de datos
- Simplifica el testing con repositorios mock

#### 3. **Inyección de Dependencias**
Utiliza el sistema `Depends` de FastAPI para:
- Gestionar el ciclo de vida de las dependencias
- Facilitar el testing
- Reducir acoplamiento entre componentes

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│                     (Next.js + React)                       │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Login   │  │ Register │  │  Setup   │  │Dashboard │  │
│  │  Page    │  │   Page   │  │   2FA    │  │   Page   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│         │              │              │            │       │
└─────────┼──────────────┼──────────────┼────────────┼───────┘
          │              │              │            │
          └──────────────┴──────────────┴────────────┘
                              │
                         HTTP/HTTPS
                              │
┌─────────────────────────────┼─────────────────────────────┐
│                        BACKEND                             │
│                    (FastAPI + Python)                      │
│                             │                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │              CAPA DE ROUTERS                       │   │
│  │   ┌─────────────┐                                  │   │
│  │   │  auth.py    │  ← Endpoints HTTP                │   │
│  │   └─────────────┘                                  │   │
│  └──────────┬─────────────────────────────────────────┘   │
│             │ Depends()                                    │
│  ┌──────────▼─────────────────────────────────────────┐   │
│  │         CAPA DE SERVICIOS                          │   │
│  │   ┌──────────────┐     ┌──────────────┐           │   │
│  │   │AuthService   │◄────┤TOTPService   │           │   │
│  │   └──────────────┘     └──────────────┘           │   │
│  │         │                     │                    │   │
│  │    Lógica 2FA          Genera códigos TOTP        │   │
│  └──────────┬──────────────────────────────────────────┘  │
│             │ Depends()                                    │
│  ┌──────────▼─────────────────────────────────────────┐   │
│  │        CAPA DE REPOSITORIOS                        │   │
│  │   ┌──────────────────┐                             │   │
│  │   │ UserRepository   │  ← Operaciones CRUD         │   │
│  │   └──────────────────┘                             │   │
│  └──────────┬──────────────────────────────────────────┘  │
│             │ SQLAlchemy ORM                               │
│  ┌──────────▼─────────────────────────────────────────┐   │
│  │         CAPA DE MODELOS                            │   │
│  │   ┌──────────┐                                     │   │
│  │   │ User     │  ← Modelo ORM                       │   │
│  │   └──────────┘                                     │   │
│  └──────────┬──────────────────────────────────────────┘  │
└─────────────┼──────────────────────────────────────────────┘
              │
              ▼
    ┌────────────────────┐
    │    PostgreSQL      │
    │   (Base de Datos)  │
    └────────────────────┘
```

### Flujo de Autenticación con 2FA

```
┌─────────┐                                          ┌─────────┐
│ Usuario │                                          │ Sistema │
└────┬────┘                                          └────┬────┘
     │                                                    │
     │  1. POST /auth/register                            │
     │  {email, password, name, phone}                    │
     ├───────────────────────────────────────────────────►│
     │                                                    │
     │  ✓ Usuario creado (2FA pendiente)                 │
     │◄───────────────────────────────────────────────────┤
     │                                                    │
     │  2. POST /auth/setup-2fa                           │
     │  {email, password}                                 │
     ├───────────────────────────────────────────────────►│
     │                                                    │
     │  ✓ QR Code + Secret (totp_secret guardado)        │
     │◄───────────────────────────────────────────────────┤
     │                                                    │
     │  [Usuario escanea QR con Microsoft Authenticator]  │
     │                                                    │
     │  3. POST /auth/verify-2fa                          │
     │  {email, password, totp_code}                      │
     ├───────────────────────────────────────────────────►│
     │                                                    │
     │  ✓ 2FA verificado (totp_verified = true)          │
     │◄───────────────────────────────────────────────────┤
     │                                                    │
     │  4. POST /auth/login                               │
     │  {email, password, totp_code}                      │
     ├───────────────────────────────────────────────────►│
     │                                                    │
     │  ✓ JWT Token                                       │
     │◄───────────────────────────────────────────────────┤
     │                                                    │
     │  5. GET /auth/me                                   │
     │  Authorization: Bearer {token}                     │
     ├───────────────────────────────────────────────────►│
     │                                                    │
     │  ✓ Datos del usuario                               │
     │◄───────────────────────────────────────────────────┤
     │                                                    │
```

---

## 🎯 Principios SOLID Aplicados

Este proyecto implementa los cinco principios SOLID de forma rigurosa. A continuación, se justifica cada uno con ejemplos del código:

### 1. **Single Responsibility Principle (SRP)**
*"Una clase debe tener una sola razón para cambiar"*

#### ✅ Implementación:

**UserRepository** (`backend/app/repositories/user_repository.py`):
- **Única responsabilidad**: Operaciones CRUD con la base de datos
- No maneja autenticación, hashing de contraseñas ni lógica de negocio
```python
class UserRepository:
    """Solo gestiona acceso a datos de usuarios"""
    def create(self, email, password, name, phone_number, role) -> User
    def get_by_email(self, email) -> Optional[User]
    def get_by_id(self, user_id) -> Optional[User]
    def update(self, user) -> User
```

**AuthService** (`backend/app/services/auth_service.py`):
- **Única responsabilidad**: Lógica de autenticación y generación de JWT
- No accede directamente a la base de datos
```python
class AuthService:
    """Solo maneja autenticación y tokens"""
    def register_user(self, email, password, name, phone_number, role)
    def verify_password(self, plain_password, hashed_password)
    def create_access_token(self, user_id, role)
    def decode_access_token(self, token)
```

**TOTPService** (`backend/app/services/totp_service.py`):
- **Única responsabilidad**: Generación y verificación de códigos TOTP
- Implementación RFC 6238 aislada
```python
class TOTPService:
    """Solo maneja operaciones TOTP/2FA"""
    def generate_secret(self) -> str
    def generate_qr_uri(self, email, secret) -> str
    def verify_totp(self, secret, code) -> bool
```

### 2. **Open/Closed Principle (OCP)**
*"Abierto para extensión, cerrado para modificación"*

#### ✅ Implementación:

El sistema permite **agregar nuevos tipos de autenticación** sin modificar código existente:

**Ejemplo**: Si quisiéramos agregar autenticación con SMS:
```python
# Crear nuevo servicio SIN modificar código existente
class SMSService:
    def send_code(self, phone_number: str) -> str:
        """Envía código por SMS"""
        pass
    
    def verify_code(self, phone_number: str, code: str) -> bool:
        """Verifica código SMS"""
        pass

# Usar en AuthService mediante inyección de dependencias
class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        totp_service: TOTPService,
        sms_service: Optional[SMSService] = None  # ← Extensión
    ):
        self.sms_service = sms_service
```

**Los routers son extensibles**:
- Nuevos endpoints se agregan sin modificar los existentes
- Cada endpoint es independiente y usa dependencias inyectadas

### 3. **Liskov Substitution Principle (LSP)**
*"Los objetos de una subclase deben poder reemplazar a los de la clase base"*

#### ✅ Implementación:

**Repositorios intercambiables**:
```python
# Se podría crear un MockUserRepository para testing
class MockUserRepository:
    """Repositorio en memoria para pruebas"""
    def __init__(self):
        self.users = {}
    
    def create(self, email, password, name, phone_number, role):
        """Misma interfaz que UserRepository"""
        user = User(email=email, ...)
        self.users[email] = user
        return user

# El AuthService funcionaría igual con cualquiera
auth_service = AuthService(
    user_repository=MockUserRepository(),  # ← Sustituible
    totp_service=TOTPService()
)
```

**Dependency Injection permite sustitución**:
- `get_current_user` vs `get_current_active_user` vs `require_admin`
- Cada uno extiende el anterior sin romper compatibilidad

### 4. **Interface Segregation Principle (ISP)**
*"Los clientes no deberían depender de interfaces que no usan"*

#### ✅ Implementación:

**Schemas específicos** (`backend/app/schemas/auth.py`):
```python
# Cada operación tiene su propio schema
class UserRegisterRequest(BaseModel):
    """Solo campos necesarios para registro"""
    email: EmailStr
    password: str
    name: str
    phone_number: Optional[str] = None
    role: Optional[str] = "CLIENT"

class UserLoginRequest(BaseModel):
    """Solo campos necesarios para login"""
    email: EmailStr
    password: str
    totp_code: str  # ← 2FA obligatorio

class TOTPSetupRequest(BaseModel):
    """Solo campos para setup 2FA"""
    email: EmailStr
    password: str

class TOTPVerifyRequest(BaseModel):
    """Solo campos para verificar 2FA"""
    email: EmailStr
    password: str
    totp_code: str
```

**Ventajas**:
- Cada endpoint recibe solo lo que necesita
- No hay campos innecesarios en los requests
- Validación específica por operación

### 5. **Dependency Inversion Principle (DIP)**
*"Depender de abstracciones, no de implementaciones concretas"*

#### ✅ Implementación:

**Inyección de Dependencias en FastAPI**:
```python
# Router NO instancia directamente servicios
@router.post("/login")
async def login(
    request: UserLoginRequest,
    db: Session = Depends(get_db)  # ← Abstracción
):
    # Obtener dependencias (Factory Pattern)
    user_repository = get_user_repository(db)  # ← No new()
    auth_service = get_auth_service(user_repository)  # ← No new()
    
    # Usar servicios
    token = auth_service.login(...)
```

**AuthService depende de abstracciones**:
```python
class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,  # ← Abstracción
        totp_service: TOTPService  # ← Abstracción
    ):
        # No crea instancias, recibe dependencias
        self.user_repository = user_repository
        self.totp_service = totp_service
```

**Beneficios**:
- Fácil testing con mocks
- Componentes desacoplados
- Posibilidad de cambiar implementaciones

---

## 🚀 Guía Completa de Despliegue Local

Esta guía te permitirá ejecutar el proyecto completo en tu máquina local, tanto en **Linux/macOS** como en **Windows**.

### Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

| Herramienta | Versión Mínima | Verificación |
|-------------|----------------|--------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| PostgreSQL | 16+ | `psql --version` |
| Docker (opcional) | 20+ | `docker --version` |
| Git | 2.0+ | `git --version` |

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/MrBowis/secure-login.git
cd secure-login
```

### Paso 2: Configurar el Backend

#### 2.1 Navegar al directorio backend

```bash
cd backend
```

#### 2.2 Crear entorno virtual

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

#### 2.3 Instalar dependencias de Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.4 Configurar PostgreSQL

**Opción A: Con Docker (Recomendado)**

```bash
# Iniciar contenedor PostgreSQL
docker-compose up -d

# Verificar que esté corriendo
docker ps
```

El archivo `docker-compose.yml` ya está configurado con:
- Usuario: `postgres`
- Contraseña: `postgres`
- Base de datos: `secure_login`
- Puerto: `5432`

**Opción B: PostgreSQL Local**

1. Instalar PostgreSQL en tu sistema
2. Crear la base de datos:

```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE secure_login;

# Salir
\q
```

#### 2.5 Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env
```

Editar `.env` con tus valores:

```env
# Base de datos
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/secure_login

# JWT (IMPORTANTE: Cambiar en producción)
JWT_SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Configuración de la aplicación
DEBUG=True
APP_NAME=Secure Login API
```

**⚠️ Importante**: Para producción, genera una clave secreta fuerte:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2.6 Iniciar el backend

```bash
# Asegúrate de estar en el directorio backend con el entorno virtual activado
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verificar que funciona**:
- API: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- Flujo de autenticación: http://localhost:8000/flow

### Paso 3: Configurar el Frontend

#### 3.1 Abrir una nueva terminal

Mantén el backend corriendo y abre una nueva terminal.

#### 3.2 Navegar al directorio frontend

```bash
cd secure-login/frontend
```

#### 3.3 Instalar dependencias de Node.js

```bash
# Con npm (recomendado)
npm install

# O con yarn
yarn install

# O con pnpm
pnpm install
```

#### 3.4 Configurar variables de entorno (si es necesario)

Crear archivo `.env.local` (opcional):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3.5 Iniciar el frontend

```bash
npm run dev
```

**Verificar que funciona**:
- Aplicación: http://localhost:3000

### Paso 4: Probar el Flujo Completo

#### 4.1 Registro de Usuario

1. Abre http://localhost:3000
2. Ve a la página de registro
3. Completa el formulario:
   - Email: `test@example.com`
   - Contraseña: `SecurePass123!`
   - Nombre: `Test User`
   - Teléfono: `+1234567890` (opcional)
   - Rol: `CLIENT` (o `ADMIN`)

#### 4.2 Configurar 2FA

1. Después del registro, configura 2FA
2. Escanea el código QR con **Microsoft Authenticator**:
   - iOS: [App Store](https://apps.apple.com/app/microsoft-authenticator/id983156458)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=com.azure.authenticator)
3. O ingresa el código manualmente en la app

#### 4.3 Verificar 2FA

1. Ingresa el código de 6 dígitos mostrado en Microsoft Authenticator
2. Verifica que el 2FA esté activado

#### 4.4 Iniciar Sesión

1. Ve a la página de login
2. Ingresa tu email y contraseña
3. Ingresa el código TOTP actual de Microsoft Authenticator
4. ¡Listo! Deberías estar autenticado

### Paso 5: Pruebas con curl (Opcional)

```bash
# 1. Registrar usuario
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "SecurePass123!",
    "name": "Curl User",
    "phone_number": "+1234567890",
    "role": "CLIENT"
  }'

# 2. Setup 2FA
curl -X POST "http://localhost:8000/auth/setup-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "SecurePass123!"
  }'

# 3. Verificar 2FA (usar código de Authenticator)
curl -X POST "http://localhost:8000/auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "SecurePass123!",
    "totp_code": "123456"
  }'

# 4. Login (usar código actual)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "curl@example.com",
    "password": "SecurePass123!",
    "totp_code": "123456"
  }'

# 5. Acceder a endpoint protegido
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer {tu_token_aqui}"
```

### Solución de Problemas Comunes

#### Backend no inicia

**Error**: `No module named 'app'`
- **Solución**: Asegúrate de estar en el directorio `backend/` y tener el entorno virtual activado

**Error**: `Connection refused` (PostgreSQL)
- **Solución**: Verifica que PostgreSQL esté corriendo:
  ```bash
  docker ps  # Si usas Docker
  # o
  sudo systemctl status postgresql  # Linux
  ```

**Error**: `database "secure_login" does not exist`
- **Solución**: Crea la base de datos:
  ```bash
  docker exec -it <container_id> psql -U postgres -c "CREATE DATABASE secure_login;"
  ```

#### Frontend no inicia

**Error**: `EADDRINUSE: address already in use`
- **Solución**: El puerto 3000 está ocupado. Usa otro puerto:
  ```bash
  npm run dev -- -p 3001
  ```

**Error**: `Cannot connect to backend`
- **Solución**: Verifica que el backend esté corriendo en http://localhost:8000

#### Problemas con 2FA

**Error**: Código TOTP inválido
- **Solución**: 
  - Verifica que la hora de tu sistema esté sincronizada
  - El código tiene 30 segundos de validez
  - Intenta con el siguiente código generado

### Detener el Proyecto

1. **Backend**: Presiona `Ctrl+C` en la terminal del backend
2. **Frontend**: Presiona `Ctrl+C` en la terminal del frontend
3. **PostgreSQL (Docker)**: 
   ```bash
   cd backend
   docker-compose down
   ```

### Estructura Final de Directorios

```
secure-login/
├── backend/
│   ├── venv/                 # Entorno virtual (no se commitea)
│   ├── app/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── routers/
│   │   └── schemas/
│   ├── .env                  # Variables de entorno (no se commitea)
│   ├── requirements.txt
│   └── docker-compose.yml
└── frontend/
    ├── node_modules/         # Dependencias (no se commitea)
    ├── src/
    ├── public/
    ├── package.json
    └── .env.local            # Variables de entorno (no se commitea)
```

---

## 📚 Documentación

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

---

## 📝 Notas

- Asegúrate de que el backend esté corriendo antes de usar el frontend.
- Configura correctamente las variables de entorno en ambos proyectos.
- Para producción, sigue las recomendaciones de seguridad de los READMEs internos.
- El sistema requiere 2FA obligatorio para todos los usuarios.
- Los códigos TOTP son válidos por 30 segundos.

---
