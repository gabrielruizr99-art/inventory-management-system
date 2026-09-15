# Plan de Proyecto y Arquitectura

## Arquitectura Modular (Aplicaciones Django)

El proyecto se estructurará en las siguientes aplicaciones que se crearán progresivamente, no todas durante la primera fase:

- `core`: utilidades compartidas, clases base y página inicial.
- `accounts`: usuario personalizado, autenticación, grupos, permisos y acceso por ubicación.
- `catalog`: categorías y productos.
- `partners`: clientes y proveedores.
- `inventory`: ubicaciones, existencias y movimientos.
- `purchases`: compras y entradas de inventario.
- `sales`: ventas y salidas de inventario.
- `dashboard`: indicadores y alertas.
- `audit`: auditoría de acciones importantes.
- `reports`: consultas y exportaciones CSV.

## Decisiones de Dominio

### A. USUARIOS Y PERMISOS

- `User` será un modelo personalizado basado en `AbstractUser`.
- Los roles se implementarán con grupos de Django:
  - Administrador
  - Vendedor
  - Almacén
- Los permisos se asignarán por grupo.
- Posteriormente los usuarios podrán limitarse a ubicaciones autorizadas.

### B. CATÁLOGO

- `Category`.
- `Product`.
- SKU único y obligatorio.
- Código de barras opcional.
- Precio de venta con `DecimalField`.
- Unidad de medida.
- Estado activo/inactivo.
- Los productos utilizados en transacciones no deberán eliminarse físicamente.

### C. UBICACIONES E INVENTARIO

Utiliza una única entidad `Location` para el MVP, con tipos:
- `BRANCH`
- `WAREHOUSE`

Define:
- `InventoryBalance`: existencia de un producto en una ubicación.
- Restricción única para `product + location`.
- `quantity` como Decimal.
- `minimum_quantity` por producto y ubicación.
- `StockMovement`: libro operativo e inmutable de entradas, salidas, ajustes, transferencias y reversiones.

Aclara que `StockMovement` no reemplaza la auditoría de usuarios.
No utilices una `GenericForeignKey` como decisión definitiva. Las referencias a documentos de compra, venta, ajuste o transferencia deberán conservar integridad y trazabilidad mediante relaciones explícitas o un diseño de referencia revisado antes de implementar el motor de inventario.

### D. COMPRAS Y VENTAS

Define:
- `Supplier`.
- `Customer`.
- `Purchase` y `PurchaseItem`.
- `Sale` y `SaleItem`.

Estados mínimos de compras y ventas:
- `DRAFT`
- `CONFIRMED`
- `CANCELLED`

Reglas:
- Un documento en borrador no modifica stock.
- Confirmarlo modifica stock exactamente una vez.
- Una venta no puede confirmarse si produciría stock negativo.
- La confirmación debe ejecutarse dentro de `transaction.atomic`.
- Para modificar existencias deben bloquearse los balances correspondientes con `select_for_update`.
- Los totales deben calcularse desde los detalles y no confiar en valores enviados por el navegador.
- La anulación de un documento confirmado debe generar movimientos de reversión.
- No se deben borrar documentos confirmados.

### E. AUDITORÍA

Define `AuditEvent` de forma separada a `StockMovement`.
Debe permitir registrar:
- usuario
- acción
- entidad afectada
- identificador
- fecha
- información segura del cambio

No deben almacenarse contraseñas, tokens ni datos sensibles en auditoría.

## F. FASES VERIFICABLES

**Fase 1 — Base técnica y autenticación:**
- `.venv`.
- Django 5.2 LTS.
- PostgreSQL.
- configuración por entorno;
- `core` y `accounts`;
- custom user antes de la primera migración;
- login y logout;
- grupos y permisos;
- Pytest;
- Ruff;
- GitHub Actions con PostgreSQL;
- pruebas iniciales.

**Fase 2 — Catálogo, socios y ubicaciones:**
- categorías;
- productos;
- clientes;
- proveedores;
- ubicaciones;
- CRUD;
- permisos;
- pruebas.

**Fase 3 — Motor de inventario:**
- balances;
- movimientos;
- ajustes;
- transferencias;
- transacciones;
- concurrencia;
- prevención de stock negativo;
- pruebas de invariantes.

**Fase 4 — Compras:**
- encabezado y detalles;
- borrador, confirmación y anulación;
- entradas de inventario;
- pruebas.

**Fase 5 — Ventas:**
- encabezado y detalles;
- borrador, confirmación y anulación;
- salidas de inventario;
- comprobación de disponibilidad;
- pruebas.

**Fase 6 — Dashboard, alertas y reportes:**
- indicadores;
- Chart.js;
- stock mínimo;
- filtros;
- exportación CSV;
- pruebas.

**Fase 7 — Auditoría, seguridad y experiencia:**
- eventos de auditoría;
- revisión integral de permisos;
- manejo seguro de errores;
- diseño responsive;
- optimización de consultas;
- pruebas.

**Fase 8 — Documentación y publicación:**
- README final;
- instalación reproducible;
- capturas;
- datos de demostración seguros;
- revisión de secretos;
- CI verde;
- publicación autorizada;
- release `v1.0.0`.

*Seguridad, permisos, Ruff y pruebas se validarán en todas las fases.*

## G. DEPENDENCIAS PREVISTAS

Dependencias de ejecución:
- Python 3.13.
- Django limitado a la rama 5.2 LTS mediante `Django~=5.2.0`.
- Psycopg 3 con soporte binario.
- django-environ.

Dependencias de desarrollo:
- pytest.
- pytest-django.
- pytest-cov.
- Ruff.

Notas sobre dependencias:
- Las versiones exactas se resolverán y registrarán desde un entorno virtual limpio.
- No deben utilizarse rangos abiertos como única estrategia de reproducibilidad.
- Bootstrap y Chart.js no son dependencias de pip.
- No se instalará React.
- No se añadirá Django REST Framework durante el MVP.
