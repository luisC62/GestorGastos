# MEMORY.md — Gestor de gastos
Memoria breve del proyecto entre sesiones. Máximo ~50 líneas.
## Estado actual
- API en `main.py`: POST `/gastos`, GET `/gastos`, DELETE `/gastos/{id}`,
  DELETE `/gastos` (borra todos) y GET `/gastos/total-semanal` y
  GET `/gastos/total-mensual`.
- `nuevosgastos.csv` contiene 25 gastos de ejemplo con fechas ISO de noviembre de 2026
  (además de la cabecera); ids `0` como en los registros existentes.
- Web completa en `index.html`, `styles.css` y `app.js` (HTML/CSS/JS puro, sin build):
  alta de gastos, lista del más reciente al más antiguo, borrado por selección y
  totales semanal y mensual en dos tarjetas sobre el formulario.
- La web habla con `http://127.0.0.1:8000` (constante `URL_API` en `app.js`).
- `main.py` usa `CORSMiddleware` (`allow_origins=["*"]`): sin él, el navegador bloquea
  las peticiones de `index.html` abierto con doble clic (origen "null").
- El usuario ya usa la web con datos reales: no borrar ni "limpiar" `misgastos.db`.
- Scripts `exportarcsv.py` / `importarcsv.py` usan la API (`URL_API` en cada script),
  no tocan `misgastos.db` directo. Requieren el servidor arrancado. Exporta con GET
  `/gastos`; importa validando el CSV en local y creando cada gasto con POST `/gastos`.
## Decisiones (y por qué)
- Totales: solo frontend, sin tocar `main.py`; se reutilizan `llamarAPI`, `formatoEuros`
  y `formatearFecha`. Peticiones secuenciales (más simples de leer que `Promise.all`).
- Tarjetas de totales: franja arriba (todo el ancho), etiquetas «Esta semana»/«Este mes»,
  rango de fechas debajo; sin título visible, solo `aria-label` en la sección.
- Se refrescan al abrir la página, tras crear y tras borrar; con la página abierta no se
  recalculan al cambiar de semana/mes (sin temporizadores: "haz solo lo que se pide").
- Alta de gastos pide la cantidad en euros aunque el prompt no la listaba: la API la exige.
- Borrado: se marca el gasto en la lista y se pulsa «Eliminar seleccionado», con `confirm()`.
- Fechas siempre en hora local: `hoyLocal()` con `getFullYear/getMonth/getDate` y
  `new Date(fecha + "T00:00")` para pintar. Nunca `toISOString()` (es UTC).
- Euros con `Intl.NumberFormat("es-ES", {style:"currency", currency:"EUR"})`.
- Validación del formulario con atributos HTML (`required`, `min`, `maxlength`); sin JS extra.
- Si falla la conexión con el servidor, la web muestra un aviso con el comando de arranque.
- Diseño: verde "dinero" sobre papel claro, tipografía del sistema (sin fuentes externas),
  dos columnas desde 760px, animación solo al añadir (respeta `prefers-reduced-motion`).
- Backend: fecha `date` ISO obligatoria; `cantidad` > 0; conexión por petición con
  `contextmanager`; DELETE responde 200 con JSON; totales semana (lunes-domingo) y mes
  natural con `BETWEEN` inclusivo y `COALESCE(SUM(cantidad), 0)`.
- CSV: cabecera, coma, UTF-8 con BOM; export incluye `id`, import lo ignora y valida todo.
  Scripts usan `urllib` (sin deps nuevas) contra la API; import valida todo antes de enviar
  y, si falla a mitad, avisa cuántos gastos se crearon antes del fallo (sin rollback HTTP).
- Borrado total: `DELETE /gastos` vacía la tabla (`DELETE FROM gastos`), no borra el
  fichero ni reinicia ids; responde 200 con el número de borrados y es idempotente.
  No hay botón en la web (regla en `AGENTS.md`).
## Aprendizajes y errores a evitar
- La consola de Windows muestra mal los acentos, pero SQLite/JSON/CSV guardan UTF-8 correcto.
- `input type="date"` solo acepta "AAAA-MM-DD"; para mostrar fechas al usuario se
  formatean con `toLocaleDateString("es-ES")`.
- Antes de arrancar uvicorn, comprobar si el puerto 8000 ya está ocupado: el usuario
  suele dejar su servidor arrancado (no hay que parárselo).
- Totales verificados contra el listado real: los números de la API cuadran con la suma
  de los gastos del periodo.
## Próximos pasos
- Sin peticiones pendientes.
