# Inventory Management System

Aplicación web profesional para la gestión de inventario, compras y ventas diseñada para pequeños negocios y almacenes.

## Objetivo del Sistema
Proveer un MVP robusto y mantenible que permita el control de existencias, el registro de entradas (compras) y salidas (ventas) de mercancía de forma concurrente y segura, ofreciendo un entorno administrativo para reportes e indicadores.

## Stack Previsto
- **Backend:** Python 3.13, Django 5.2 LTS, PostgreSQL
- **Frontend:** Plantillas Django, Bootstrap, Chart.js (JavaScript mínimo, sin React)
- **Calidad y Testing:** Pytest, Ruff
- **CI:** GitHub Actions

## Estructura Resumida
- `core`: utilidades compartidas, vistas globales y página inicial.
- `accounts`: custom user model y gestión de autenticación, grupos y permisos.
- `config`: configuración principal del proyecto Django.
- `requirements/`: archivos de dependencias exactas (`base.txt` y `dev.txt`).
- `.github/workflows/`: configuración de CI para GitHub Actions.

## Estado Actual del Proyecto
El proyecto ha completado la **Fase 1**. Se encuentra implementada la base técnica, entorno virtual, dependencias, proyecto Django, modelo de usuario personalizado, grupos de roles iniciales, interfaz base (Bootstrap 5), y las configuraciones de Pytest y Ruff, asegurado con CI en GitHub Actions. Aún no se ha desarrollado la lógica de catálogo, compras o ventas.

🔗 [Ver Plan de Proyecto y Fases](docs/project-plan.md)
🔗 [Ver Reglas del Proyecto](.agents/CONTEXT.md)

> **⚠️ Advertencia de Seguridad**
> Nunca almacene contraseñas reales ni valores de entorno críticos en el control de versiones. Se debe hacer uso exclusivo de `.env` (ignorado por Git) para configurar el acceso en cada entorno.

---

## Requisitos y Preparación

1. **Python 3.13** instalado en el sistema.
2. **PostgreSQL 18** (o versión compatible) instalado y en ejecución.

### Creación Manual del Rol y Base de Datos

Debido a restricciones de seguridad, crea manualmente el rol y la base de datos desde
pgAdmin. En la pestaña **General** define el nombre del rol; en **Definition** introduce la
contraseña mediante los campos protegidos de la interfaz; y en **Privileges** habilita inicio
de sesión. Después crea la base `inventory_management` y asigna ese rol como propietario.

El privilegio `CREATEDB` se permite solamente al rol local de desarrollo para que Pytest pueda
crear y eliminar su base temporal aislada. En producción debe retirarse y las pruebas deben
usar infraestructura separada.

### Configuración del Entorno (`.env`)

Crea un archivo llamado `.env` en la raíz del proyecto basándote en el archivo de ejemplo proporcionado:
```powershell
Copy-Item .env.example .env
```
Luego, edita `.env` agregando tu `DJANGO_SECRET_KEY` segura y el `DB_PASSWORD` que elegiste al crear el rol en PostgreSQL.

---

## Instalación en Windows PowerShell

1. **Crear el entorno virtual:**
```powershell
python -m venv .venv
```

2. **Activar e instalar dependencias:**
```powershell
.venv\Scripts\python.exe -m pip install -r requirements/dev.txt
```

3. **Ejecutar migraciones:**
```powershell
.venv\Scripts\python.exe manage.py migrate
```

4. **Ejecución local del servidor de desarrollo:**
```powershell
.venv\Scripts\python.exe manage.py runserver
```

---

## Pruebas y Calidad de Código

### Ejecutar Pruebas Automatizadas (Pytest)
```powershell
.venv\Scripts\pytest.exe
```

### Linter y Formato (Ruff)

Verificar reglas y formato sin modificar archivos:
```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

Aplicar formato intencionalmente:
```powershell
.venv\Scripts\python.exe -m ruff format .
```
