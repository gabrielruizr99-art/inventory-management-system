# Reglas Persistentes para Codex

- Trabaja sobre el repositorio existente y usa sus archivos reales como fuente de verdad.
- Mantén explicaciones y documentación en español; el código y los nombres técnicos pueden estar en inglés.
- Nunca leas, muestres, copies ni registres el contenido de `.env`, credenciales, claves, tokens o cadenas de conexión reales.
- Usa `.env.example` solamente con valores ficticios o vacíos y conserva `.env`, `.venv`, logs y archivos operativos fuera de Git.
- PostgreSQL es el único motor autorizado; no uses SQLite en desarrollo, pruebas ni CI.
- No accedas ni modifiques las bases `sales_powerbi` y `etl_automation`.
- No ejecutes `DROP`, `TRUNCATE`, eliminaciones masivas ni operaciones destructivas sin autorización expresa.
- Usa exclusivamente `.venv` para Python y dependencias; no instales globalmente ni modifiques el `PATH`.
- No elimines, omitas ni debilites pruebas o el umbral de cobertura para ocultar fallos; corrige siempre la causa real.
- Valida seguridad, permisos, Django Check, migraciones, Ruff, formato, Pytest y cobertura en cada fase.
- No hagas `git add`, commit, push, configuración de remotos ni autenticación con GitHub sin autorización expresa.
- No crees superusuarios, datos de demostración, tareas de Windows ni servicios del sistema sin autorización.
- No modifiques migraciones aplicadas salvo defecto crítico; detente e informa antes de hacerlo.
- Implementa los roles mediante grupos y permisos de Django.
- Al procesar inventario, usa servicios de dominio, movimientos trazables, transacciones e idempotencia; evita stock negativo con bloqueos.
- Almacena dinero y cantidades fraccionarias con `DecimalField`, nunca con `float`.
- No elimines operaciones confirmadas: anúlalas o reviértelas mediante operaciones trazables.
- Durante el MVP usa plantillas Django, Bootstrap, JavaScript mínimo y Chart.js; no añadas React ni una API separada.
- Avanza por las fases de `docs/project-plan.md`; no implementes fases posteriores sin autorización.
- Identifica explícitamente como ficticias todas las contraseñas usadas en pruebas o CI.

## Estado Operativo Actual

- Fase 1 completada.
- Fase 2 completada y verificada.
- Fase 3 es la siguiente etapa planificada; no iniciarla sin autorización expresa.
- Fase 4 y posteriores permanecen pendientes.
- Aplicaciones disponibles: `core`, `accounts`, `catalog`, `partners` e `inventory`.
- Verificación actual: 91 pruebas aprobadas y cobertura del 100 %; umbral obligatorio del 80 %.
- PostgreSQL es el único backend autorizado.
- Todo commit, push, merge, tag o release requiere autorización explícita.
