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
- `catalog`: categorías y productos.
- `partners`: proveedores y clientes.
- `inventory`: ubicaciones; el motor de existencias se implementará en la Fase 3.
- `config`: configuración principal del proyecto Django.
- `requirements/`: archivos de dependencias exactas (`base.txt` y `dev.txt`).
- `.github/workflows/`: configuración de CI para GitHub Actions.

## Estado Actual del Proyecto
La **Fase 1 está completada** y la **Fase 2 está completada y verificada**. La Fase 3 es la
siguiente fase planificada, pero su implementación todavía no ha comenzado.

La Fase 2 incorpora:

- modelos `Category`, `Product`, `Supplier`, `Customer` y `Location`;
- CRUD con plantillas Django y Bootstrap;
- búsqueda, filtros validados y paginación;
- activación y desactivación mediante operaciones POST;
- eliminación administrativa segura, con manejo de relaciones protegidas;
- autorización por grupos y permisos efectivos de Django;
- 91 pruebas aprobadas y cobertura actual del 100 %.

La cobertura puede variar a medida que el proyecto crezca. El umbral obligatorio se mantiene
en 80 %. La Fase 3 y las fases posteriores permanecen pendientes.

### Matriz resumida de roles

- **Administrador:** acceso completo a catálogo, socios y ubicaciones, incluida la eliminación
  administrativa.
- **Vendedor:** consulta categorías, productos y ubicaciones; administra clientes.
- **Almacén:** administra categorías, productos y proveedores; consulta ubicaciones.

La autorización de cada endpoint se comprueba mediante permisos Django, no únicamente por el
nombre del grupo ni por la visibilidad de la navegación.

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
.venv\Scripts\python.exe -m pytest
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
