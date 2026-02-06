# Secure Login - Proyecto Fullstack

Este proyecto implementa un sistema de autenticación seguro con 2FA (TOTP) usando **FastAPI** (backend) y **Next.js** (frontend).

## 📁 Estructura del Proyecto

```
secure-login/
├── backend/    # API FastAPI + PostgreSQL
└── frontend/   # Next.js (React)
```

---

## 🚀 Iniciar el Proyecto

### 1. Clonar el repositorio

```bash
git clone https://github.com/MrBowis/secure-login.git
cd secure-login
```

---

## 🖥️ Backend (FastAPI)

### Requisitos

- Python 3.11+
- PostgreSQL 16
- (Opcional) Docker y Docker Compose

### Instalación y Ejecución

#### Linux/macOS

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configura el archivo .env
cp .env.example .env
# Edita .env según tus credenciales

# Inicia PostgreSQL (opcional con Docker)
docker-compose up -d

# Ejecuta el backend
uvicorn app.main:app --reload
```

#### Windows

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Copia y edita .env
copy .env.example .env
# Edita .env con tus datos

# Inicia PostgreSQL (opcional con Docker)
docker-compose up -d

# Ejecuta el backend
uvicorn app.main:app --reload
```

La API estará disponible en: [http://localhost:8000](http://localhost:8000)

---

## 🌐 Frontend (Next.js)

### Requisitos

- Node.js 18+
- npm, yarn, pnpm o bun

### Instalación y Ejecución

#### Linux/macOS

```bash
cd frontend
npm install
npm run dev
```

#### Windows

```powershell
cd frontend
npm install
npm run dev
```

La app estará disponible en: [http://localhost:3000](http://localhost:3000)

---

## 📚 Documentación

- [Backend README](./backend/README.md)
- [Frontend README](./frontend/README.md)

---

## 📝 Notas

- Asegúrate de que el backend esté corriendo antes de usar el frontend.
- Configura correctamente las variables de entorno en ambos proyectos.
- Para producción, sigue las recomendaciones de seguridad de los READMEs internos.

---
