# Reglas Persistentes del Proyecto

1. Nunca escribas contraseñas reales en comandos, código, pruebas, documentación o logs. Ninguna contraseña o clave real puede escribirse en respuestas.
2. Nunca muestres el contenido de un `.env` real.
3. Usa `.env.example` únicamente con valores ficticios o vacíos.
4. `.env`, entornos virtuales, logs y archivos operativos deben quedar excluidos de Git.
5. No ejecutes `DROP`, `TRUNCATE`, eliminaciones masivas ni operaciones destructivas sin autorización expresa.
6. No modifiques nunca la base `sales_powerbi` ni la base `etl_automation`.
7. PostgreSQL será la única base de datos de la aplicación. No se permite usar SQLite como sustitución silenciosa en desarrollo, pruebas o CI. Este proyecto deberá utilizar posteriormente una base independiente.
8. No elimines, ocultes ni debilites pruebas para conseguir que Pytest o CI pasen. No se permite eliminar, omitir o debilitar pruebas para hacerlas pasar.
9. Si una prueba falla, identifica y corrige la causa real.
10. No instales software global ni modifiques el PATH del sistema.
11. Las dependencias deben instalarse exclusivamente dentro de `.venv`.
12. No publiques en GitHub, no configures remotos y no ejecutes `gh auth login` hasta recibir autorización.
13. No registres tareas de Windows ni servicios del sistema.
14. Antes de cada commit, ejecuta pruebas, Ruff, revisa secretos y muestra el estado de Git.
15. No se permite crear commits sin autorización expresa.
16. Mantén explicaciones y documentación en español; nombres técnicos y código pueden estar en inglés.
17. Debe existir un modelo de usuario personalizado antes de la primera migración.
18. Los roles se implementarán mediante `Group` y permisos de Django, no solamente mediante un campo de texto o enum en `User`.
19. Toda modificación de stock debe producirse a través de servicios de dominio y movimientos de inventario. No se permite editar directamente la existencia para procesar compras o ventas.
20. La confirmación de compras y ventas debe ser transaccional e idempotente.
21. La prevención de stock negativo debe considerar concurrencia mediante bloqueo de registros y transacciones.
22. El dinero debe almacenarse con `DecimalField`, nunca con float. Las cantidades deberán admitir unidades fraccionarias mediante `DecimalField`.
23. Las operaciones confirmadas no deben eliminarse; deben anularse o revertirse mediante operaciones trazables.
24. Seguridad, permisos y pruebas son requisitos de todas las fases, no únicamente de la fase final.
25. Bootstrap y Chart.js se utilizarán sin introducir React ni una API separada durante el MVP.

## Estado Operativo Actual

- Fase 1 completada.
- Fase 2 completada y verificada.
- Fase 3 es la siguiente etapa planificada y no debe iniciarse sin autorización expresa.
- Fase 4 y posteriores permanecen pendientes.
- Aplicaciones disponibles: `core`, `accounts`, `catalog`, `partners` e `inventory`.
- Estado de calidad: 91 pruebas aprobadas, cobertura actual del 100 % y umbral obligatorio del
  80 %.
- PostgreSQL es el único backend autorizado.
- Se mantienen vigentes todas las reglas de seguridad, PostgreSQL exclusivo y control de Git
  descritas arriba.
