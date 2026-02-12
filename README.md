# Secure Login - Sistema de Autenticación con 2FA

> Sistema fullstack de autenticación segura con autenticación de dos factores (2FA) obligatoria utilizando TOTP (Time-based One-Time Password), compatible con Microsoft Authenticator y Google Authenticator.

---

## 📋 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura y Metodología](#-arquitectura-y-metodología)
- [Patrones SOLID Aplicados](#-patrones-solid-aplicados)
- [Diagramas](#-diagramas)
- [Guía de Despliegue Local](#-guía-de-despliegue-local)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Documentación Adicional](#-documentación-adicional)

---

## 🎯 Descripción General

Este proyecto implementa un sistema de autenticación seguro con las siguientes características:

- **Autenticación de dos factores (2FA) obligatoria** usando TOTP
- **Backend RESTful** con FastAPI y PostgreSQL
- **Frontend moderno** con Next.js 14 (App Router)
- **Seguridad robusta** con JWT, bcrypt y rate limiting
- **Roles de usuario** (ADMIN y CLIENT) con control de acceso
- **Arquitectura en capas** siguiendo principios SOLID

---

## 🏗️ Arquitectura y Metodología

### Metodología: Arquitectura en Capas (Layered Architecture)

El proyecto sigue una **arquitectura en capas** que separa las responsabilidades del sistema en diferentes niveles, permitiendo:

- ✅ **Mantenibilidad**: Cambios aislados en cada capa
- ✅ **Escalabilidad**: Fácil adición de nuevas funcionalidades
- ✅ **Testabilidad**: Pruebas unitarias por capa
- ✅ **Reutilización**: Componentes desacoplados

### Capas del Backend

```
┌─────────────────────────────────────────┐
│  Presentation Layer (Routers)          │  ← Endpoints HTTP, validación de entrada
├─────────────────────────────────────────┤
│  Business Logic Layer (Services)       │  ← Lógica de negocio, reglas de autenticación
├─────────────────────────────────────────┤
│  Data Access Layer (Repositories)      │  ← Operaciones CRUD, queries a la BD
├─────────────────────────────────────────┤
│  Database Layer (PostgreSQL)           │  ← Persistencia de datos
└─────────────────────────────────────────┘
```

#### 1. **Presentation Layer** (`routers/`)
- Recibe peticiones HTTP
- Valida datos de entrada con Pydantic
- Delega lógica de negocio a los servicios
- Retorna respuestas HTTP estandarizadas

#### 2. **Business Logic Layer** (`services/`)
- Contiene toda la lógica de negocio
- Orquesta operaciones entre repositorios
- Implementa reglas de autenticación y autorización
- Gestiona tokens JWT y TOTP

#### 3. **Data Access Layer** (`repositories/`)
- Implementa el **patrón Repository**
- Abstrae las operaciones de base de datos
- Proporciona una interfaz limpia para el acceso a datos
- Maneja transacciones y queries SQL

#### 4. **Database Layer**
- PostgreSQL como base de datos relacional
- Migraciones con Alembic
- Modelos SQLAlchemy

### Patrón Repository

El **patrón Repository** actúa como una capa de abstracción entre la lógica de negocio y el acceso a datos:

```python
# Beneficios del patrón Repository:
- Centraliza las queries de base de datos
- Facilita el testing con mocks
- Permite cambiar el ORM sin afectar servicios
- Mejora la mantenibilidad del código
```

---

## 🎨 Patrones SOLID Aplicados

El proyecto implementa los cinco principios SOLID para garantizar un código limpio, mantenible y escalable:

### 1. **S - Single Responsibility Principle (SRP)**

> Cada clase o módulo debe tener una única responsabilidad.

**Implementación:**
- **`UserRepository`**: Solo maneja operaciones CRUD de usuarios
- **`AuthService`**: Solo gestiona lógica de autenticación
- **`TOTPService`**: Solo gestiona operaciones TOTP
- **`auth.py` (router)**: Solo maneja endpoints HTTP de autenticación

```python
# ✅ Correcto: Cada clase tiene una responsabilidad única
class UserRepository:
    """Solo operaciones de base de datos"""
    def create(self, email: str, password: str) -> User: ...
    def get_by_email(self, email: str) -> User: ...

class AuthService:
    """Solo lógica de autenticación"""
    def register_user(self, email: str, password: str) -> User: ...
    def authenticate_user(self, email: str, password: str) -> User: ...
```

### 2. **O - Open/Closed Principle (OCP)**

> Las entidades deben estar abiertas para extensión pero cerradas para modificación.

**Implementación:**
- Los servicios pueden extenderse sin modificar código existente
- Uso de interfaces y abstracciones
- Inyección de dependencias permite cambiar implementaciones

```python
# ✅ Correcto: Extensible mediante inyección de dependencias
class AuthService:
    def __init__(self, user_repository: UserRepository, totp_service: TOTPService):
        self.user_repository = user_repository  # Se puede inyectar cualquier implementación
        self.totp_service = totp_service
```

### 3. **L - Liskov Substitution Principle (LSP)**

> Los objetos deben poder ser reemplazados por instancias de sus subtipos sin alterar el comportamiento.

**Implementación:**
- Uso de abstracciones (Session de SQLAlchemy)
- Los repositorios y servicios pueden ser mockeados en tests
- Respeto a los contratos de interfaz

```python
# ✅ Correcto: Cualquier Session de SQLAlchemy puede usarse
def get_db() -> Session:
    """Generador de sesiones de base de datos"""
    # Se puede reemplazar con una sesión de test sin problemas
```

### 4. **I - Interface Segregation Principle (ISP)**

> Los clientes no deben depender de interfaces que no usan.

**Implementación:**
- **Schemas Pydantic específicos** para cada operación
- `UserRegisterRequest`, `UserLoginRequest`, `TOTPVerifyRequest`, etc.
- Cada endpoint recibe solo los datos que necesita

```python
# ✅ Correcto: Schemas específicos para cada operación
class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    phone_number: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: str
    password: str
    # No incluye campos innecesarios para login
```

### 5. **D - Dependency Inversion Principle (DIP)**

> Depender de abstracciones, no de implementaciones concretas.

**Implementación:**
- **Inyección de dependencias** con FastAPI `Depends()`
- Los servicios reciben repositorios, no crean instancias directamente
- Fácil reemplazo en tests con mocks

```python
# ✅ Correcto: Inyección de dependencias
@router.post("/register")
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db)  # Inyección de dependencia
):
    user_repo = get_user_repository(db)
    auth_service = get_auth_service(user_repo, totp_service)
    # El endpoint no conoce los detalles de implementación
```

### Beneficios de SOLID en el Proyecto

| Principio | Beneficio en el Proyecto |
|-----------|-------------------------|
| **SRP** | Facilita debugging y testing unitario |
| **OCP** | Permite añadir nuevos métodos de autenticación sin modificar código |
| **LSP** | Testing con mocks de BD sin cambiar lógica |
| **ISP** | Validación de datos precisa y documentación clara de APIs |
| **DIP** | Fácil cambio de librerías (JWT, hashing, ORM) sin refactorizar |

---

## 📊 Diagramas

### Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                      (Next.js 14)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Login   │  │ Register │  │ Setup 2FA│  │Dashboard │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTP/REST
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Presentation Layer (Routers)             │  │
│  │  /auth/register  /auth/login  /auth/verify-2fa      │  │
│  └───────────────────────┬──────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐  │
│  │         Business Logic Layer (Services)              │  │
│  │  ┌──────────────┐        ┌──────────────┐           │  │
│  │  │ AuthService  │◄───────┤ TOTPService  │           │  │
│  │  └──────┬───────┘        └──────────────┘           │  │
│  └─────────┼──────────────────────────────────────────┘  │
│            │                                              │
│  ┌─────────▼──────────────────────────────────────────┐  │
│  │       Data Access Layer (Repositories)             │  │
│  │         ┌──────────────────────┐                   │  │
│  │         │   UserRepository     │                   │  │
│  │         └──────────┬───────────┘                   │  │
│  └────────────────────┼────────────────────────────────┘  │
│                       │                                   │
└───────────────────────┼───────────────────────────────────┘
                        │ SQLAlchemy ORM
                        ↓
            ┌───────────────────────┐
            │   PostgreSQL 16       │
            │   (Docker Container)  │
            └───────────────────────┘
```

### Diagrama de Flujo de Autenticación 2FA

```
┌─────────┐                                              ┌─────────┐
│ Usuario │                                              │ Sistema │
└────┬────┘                                              └────┬────┘
     │                                                        │
     │  1. POST /auth/register                               │
     │  (email, password, name, phone)                       │
     ├──────────────────────────────────────────────────────►│
     │                                                        │
     │  2. Usuario creado (2FA pendiente)                    │
     │◄───────────────────────────────────────────────────────┤
     │                                                        │
     │  3. POST /auth/setup-2fa                              │
     ├──────────────────────────────────────────────────────►│
     │                                                        │
     │  4. QR Code + Secret                                  │
     │◄───────────────────────────────────────────────────────┤
     │                                                        │
     ├──┐                                                     │
     │  │ 5. Escanea QR con                                  │
     │  │    Microsoft Authenticator                         │
     │◄─┘                                                     │
     │                                                        │
     │  6. POST /auth/verify-2fa                             │
     │  (email, password, totp_code)                         │
     ├──────────────────────────────────────────────────────►│
     │                                                        │
     │                                       ┌────────────────┤
     │                                       │ 7. Valida TOTP │
     │                                       └────────────────┤
     │                                                        │
     │  8. JWT Access Token + Refresh Token                  │
     │◄───────────────────────────────────────────────────────┤
     │                                                        │
     │  9. Acceso a rutas protegidas                         │
     │  (Authorization: Bearer <token>)                      │
     ├──────────────────────────────────────────────────────►│
     │                                                        │
```

### Diagrama de Entidad-Relación (Base de Datos)

```
┌─────────────────────────────────────────────────────┐
│                    USERS TABLE                      │
├─────────────────────────────────────────────────────┤
│ PK  id                UUID                          │
│     email             VARCHAR(255)  UNIQUE          │
│     hashed_password   TEXT                          │
│     name              VARCHAR(255)                  │
│     phone_number      VARCHAR(20)   NULLABLE        │
│     role              VARCHAR(20)   DEFAULT='CLIENT'│
│     totp_secret       TEXT          NULLABLE        │
│     totp_verified     BOOLEAN       DEFAULT=FALSE   │
│     failed_attempts   INTEGER       DEFAULT=0       │
│     locked_until      TIMESTAMP     NULLABLE        │
│     created_at        TIMESTAMP                     │
│     updated_at        TIMESTAMP                     │
└─────────────────────────────────────────────────────┘

Índices:
- UNIQUE INDEX ON email
- INDEX ON role
- INDEX ON totp_verified
```

---

## 🚀 Guía de Despliegue Local

Esta sección proporciona instrucciones detalladas para desplegar el proyecto completo en tu entorno local.

### Prerrequisitos

Antes de comenzar, asegúrate de tener instalado:

- **Docker** y **Docker Compose** (para la base de datos)
- **Python 3.11+** (para el backend)
- **Node.js 18+** (para el frontend)
- **Git** (para clonar el repositorio)

### 1️⃣ Clonar el Repositorio

```bash
git clone https://github.com/MrBowis/secure-login.git
cd secure-login
```

---

### 2️⃣ Configurar y Levantar la Base de Datos (Docker Compose)

#### Paso 1: Navegar al directorio del backend

```bash
cd backend
```

#### Paso 2: Crear archivo de variables de entorno

Crea un archivo `.env` en el directorio `backend/` con la siguiente configuración:

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/secure_login_db
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

> **Nota**: Para desarrollo local, puedes usar los valores por defecto. En producción, **cambia el `SECRET_KEY`** por uno seguro.

#### Paso 3: Levantar PostgreSQL con Docker Compose

El archivo `docker-compose.yml` ya está configurado. Ejecuta:

```bash
# Levantar contenedor en modo detached (en background)
docker-compose up -d
```

#### Paso 4: Verificar que PostgreSQL está corriendo

```bash
# Ver logs del contenedor
docker-compose logs -f postgres

# Verificar que el contenedor está activo
docker ps
```

Deberías ver un contenedor llamado `backend-postgres-1` o similar en estado `Up`.

#### Paso 5: Crear las tablas de la base de datos

Las tablas se crean automáticamente al iniciar la aplicación FastAPI (ver `database.py`).

---

### 3️⃣ Configurar y Ejecutar el Backend (FastAPI con Uvicorn)

#### Paso 1: Crear un entorno virtual (venv)

Desde el directorio `backend/`:

**Linux/macOS:**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
venv\Scripts\activate.bat
```

#### Paso 2: Instalar dependencias de Python

Con el entorno virtual activado:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Paso 3: Iniciar el servidor FastAPI con Uvicorn

```bash
# Modo desarrollo con auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Paso 4: Verificar que el backend está corriendo

Abre tu navegador y accede a:

- **API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Docs (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/](http://localhost:8000/)

Si ves la documentación interactiva de FastAPI, ¡el backend está funcionando correctamente! 🎉

---

### 4️⃣ Configurar y Ejecutar el Frontend (Next.js)

#### Paso 1: Abrir una nueva terminal

Mantén el backend corriendo y abre una **segunda terminal**.

#### Paso 2: Navegar al directorio del frontend

```bash
cd frontend
```

#### Paso 3: Instalar dependencias de Node.js

```bash
# Con npm
npm install

# O con yarn
yarn install

# O con pnpm
pnpm install
```

#### Paso 4: Crear archivo de variables de entorno (opcional)

Crea un archivo `.env.local` en el directorio `frontend/` si necesitas configurar la URL del backend:

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> **Nota**: El frontend ya tiene configurado un proxy en `src/proxy.ts` que apunta a `http://localhost:8000` por defecto.

#### Paso 5: Iniciar el servidor de desarrollo de Next.js

```bash
# Modo desarrollo
npm run dev
```

#### Paso 6: Verificar que el frontend está corriendo

Abre tu navegador y accede a:

- **Aplicación**: [http://localhost:3000](http://localhost:3000)

Deberías ver la página de inicio del sistema de autenticación. 🎉

---

### 5️⃣ Probar el Sistema Completo

#### Paso 1: Registrar un nuevo usuario

1. Ve a [http://localhost:3000/auth/register](http://localhost:3000/auth/register)
2. Completa el formulario:
   - Email: `test@example.com`
   - Password: `Password123!`
   - Name: `Test User`
   - Phone: `+1234567890` (opcional)
3. Haz clic en "Registrar"

#### Paso 2: Configurar 2FA

1. Serás redirigido a la página de configuración 2FA
2. Abre **Microsoft Authenticator** o **Google Authenticator** en tu móvil
3. Escanea el código QR mostrado
4. El código TOTP de 6 dígitos aparecerá en tu app

#### Paso 3: Verificar 2FA e iniciar sesión

1. Ve a [http://localhost:3000/auth/login](http://localhost:3000/auth/login)
2. Ingresa tu email y password
3. Ingresa el código TOTP de 6 dígitos de tu app
4. Haz clic en "Iniciar Sesión"

#### Paso 4: Acceder al Dashboard

Una vez autenticado, serás redirigido al dashboard correspondiente a tu rol:
- **CLIENT**: `/dashboard/client`
- **ADMIN**: `/dashboard/admin`

---

### 6️⃣ Comandos Útiles

#### Base de Datos

```bash
# Detener contenedor de PostgreSQL
docker-compose down

# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar contenedor
docker-compose restart

# Eliminar contenedor y volúmenes (⚠️ borra todos los datos)
docker-compose down -v
```

#### Backend

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Desactivar entorno virtual
deactivate

# Instalar nuevas dependencias
pip install <paquete>
pip freeze > requirements.txt

# Ejecutar con variables de entorno específicas
SECRET_KEY=mi-clave uvicorn app.main:app --reload
```

#### Frontend

```bash
# Instalar nueva dependencia
npm install <paquete>

# Build de producción
npm run build

# Iniciar servidor de producción
npm run start

# Linting
npm run lint
```

---

### 7️⃣ Solución de Problemas Comunes

#### ❌ Error: "Connection refused" al conectar a PostgreSQL

**Solución:**
1. Verifica que Docker Compose está corriendo: `docker ps`
2. Revisa los logs: `docker-compose logs postgres`
3. Asegúrate de que el puerto 5432 no esté ocupado: `lsof -i :5432` (Linux/macOS) o `netstat -ano | findstr :5432` (Windows)

#### ❌ Error: "ModuleNotFoundError" en Python

**Solución:**
1. Asegúrate de estar en el entorno virtual: `source venv/bin/activate`
2. Reinstala las dependencias: `pip install -r requirements.txt`

#### ❌ Error: "EADDRINUSE: address already in use :::3000"

**Solución:**
1. Otro proceso está usando el puerto 3000
2. Cierra la aplicación que esté usando ese puerto o cambia el puerto:
   ```bash
   npm run dev -- -p 3001
   ```

#### ❌ Error: "Invalid TOTP code"

**Solución:**
1. Asegúrate de que la hora de tu dispositivo esté sincronizada
2. Verifica que estés usando el código correcto del authenticator
3. Los códigos TOTP expiran cada 30 segundos, prueba con un código nuevo

---

## 📁 Estructura del Proyecto

```
secure-login/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Punto de entrada FastAPI
│   │   ├── config.py            # Configuración y variables de entorno
│   │   ├── database.py          # Conexión a BD y sesiones
│   │   ├── dependencies.py      # Dependencias compartidas (auth, permisos)
│   │   ├── models/              # Modelos SQLAlchemy
│   │   │   ├── __init__.py
│   │   │   └── user.py          # Modelo User
│   │   ├── repositories/        # Capa de acceso a datos (Patrón Repository)
│   │   │   ├── __init__.py
│   │   │   └── user_repository.py
│   │   ├── routers/             # Endpoints HTTP (Capa de Presentación)
│   │   │   ├── __init__.py
│   │   │   └── auth.py          # Rutas de autenticación
│   │   ├── schemas/             # Schemas Pydantic (DTOs)
│   │   │   ├── __init__.py
│   │   │   └── auth.py          # Request/Response schemas
│   │   └── services/            # Lógica de negocio
│   │       ├── __init__.py
│   │       ├── auth_service.py  # Servicio de autenticación
│   │       └── totp_service.py  # Servicio TOTP (2FA)
│   ├── docker-compose.yml       # PostgreSQL con Docker
│   ├── requirements.txt         # Dependencias Python
│   └── README.md                # Documentación del backend
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # App Router de Next.js 14
│   │   │   ├── layout.tsx       # Layout principal
│   │   │   ├── page.tsx         # Página de inicio
│   │   │   ├── auth/            # Páginas de autenticación
│   │   │   │   ├── login/
│   │   │   │   ├── register/
│   │   │   │   ├── setup-2fa/
│   │   │   │   └── verify-2fa/
│   │   │   └── dashboard/       # Dashboards por rol
│   │   │       ├── admin/
│   │   │       └── client/
│   │   ├── components/          # Componentes React reutilizables
│   │   │   └── ui/              # Componentes de UI (shadcn/ui)
│   │   ├── lib/                 # Utilidades y configuración
│   │   │   ├── api.ts           # Cliente API (fetch wrapper)
│   │   │   ├── types.ts         # TypeScript types
│   │   │   └── utils.ts         # Funciones auxiliares
│   │   └── proxy.ts             # Configuración de proxy
│   ├── public/                  # Archivos estáticos
│   ├── package.json             # Dependencias Node.js
│   ├── tsconfig.json            # Configuración TypeScript
│   ├── next.config.ts           # Configuración Next.js
│   └── README.md                # Documentación del frontend
│
└── README.md                    # Documentación principal (este archivo)
```

---

## 🛠️ Tecnologías Utilizadas

### Backend

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Python** | 3.11+ | Lenguaje principal |
| **FastAPI** | 0.115+ | Framework web asíncrono |
| **PostgreSQL** | 16 | Base de datos relacional |
| **SQLAlchemy** | 2.0+ | ORM para Python |
| **Pydantic** | 2.10+ | Validación de datos |
| **PyJWT** | 2.10+ | Tokens JWT |
| **pyotp** | 2.9+ | Generación de TOTP |
| **pwdlib** | 0.2+ | Hashing de contraseñas (Argon2) |
| **Uvicorn** | Latest | Servidor ASGI |

### Frontend

| Tecnología | Versión | Propósito |
|-----------|---------|-----------|
| **Next.js** | 14+ | Framework React |
| **React** | 19+ | Librería UI |
| **TypeScript** | 5+ | Type safety |
| **Tailwind CSS** | 3+ | Estilos |
| **shadcn/ui** | Latest | Componentes UI |
| **react-hook-form** | Latest | Manejo de formularios |
| **zod** | Latest | Validación de esquemas |

---

## Casos de Uso

```mermaid
graph TD

%% ==== Estilos de alto contraste ====
classDef actor fill:#7b1fa2,color:#ffffff,stroke:#4a148c,stroke-width:2px
classDef system fill:#0d47a1,color:#ffffff,stroke:#002171,stroke-width:2px
classDef secure fill:#b71c1c,color:#ffffff,stroke:#7f0000,stroke-width:2px

%% ==== Actores ====
User((Usuario)):::actor
Admin((Admin)):::actor
AuthApp["App Autenticadora"]:::actor

%% ==== Sistema ====
subgraph SecureLogin["Sistema Secure Login"]

    Register["Registrar Usuario"]:::system
    Login["Iniciar Sesión"]:::system

    subgraph Security["Autenticación Fuerte"]
        Validate["Validar Credenciales"]:::secure
        Check2FA{"¿Tiene 2FA?"}:::secure
        VerifyTOTP["Verificar Código TOTP"]:::secure
        Setup2FA["Configurar 2FA (QR)"]:::secure
    end

    Dashboard["Dashboard"]:::system
end

%% ==== Relaciones ====
User --> Register
User --> Login

Login --> Validate
Validate --> Check2FA

Check2FA -- No --> Setup2FA
Check2FA -- Sí --> VerifyTOTP

Setup2FA <--> AuthApp
VerifyTOTP -- "Código OK" --> Dashboard

Admin --> Login
```

---

## 📝 Notas Importantes

- ⚠️ **Este proyecto es una demostración educativa**. Para producción, revisa:
  - Configuración de CORS
  - Secrets management (usar servicios como AWS Secrets Manager)
  - Rate limiting más estricto
  - HTTPS obligatorio
  - Logs y monitoreo
  - Backup de base de datos

- 🔐 **Seguridad**:
  - Cambia `SECRET_KEY` en producción
  - Usa contraseñas fuertes para PostgreSQL
  - Nunca subas archivos `.env` a Git
  - Habilita HTTPS en producción
---

## 👨‍💻 Autores

**Bowis**  
GitHub: [Alejandro Andrade](https://github.com/MrBowis)
GitHub: [Alex Trejo](https://github.com/Alex-Trejo)
GitHub: [Allan Panchi](https://github.com/AllanPanchi)

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.
