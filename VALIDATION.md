# Validación del core

Referencia para mantener la plantilla: qué se comprobó, qué sigue pendiente y
cómo repetir las verificaciones. La instalación y el uso están en
[INSTALLATION.md](INSTALLATION.md) y [PLAYBOOK.md](PLAYBOOK.md).

## Estado y fuentes de evidencia

Última revisión del onboarding común y su traslado al Core oficial:
**2026-10-28**, descritos abajo.
Las suites anteriores conservan sus fechas y alcance. Los siguientes informes son
antecedentes de las entregas correspondientes, no resultados de la revisión actual:

| Informe | Publicación¹ | Revisión de entrega | Entorno declarado |
| --- | --- | --- | --- |
| [PR #6: organización de Discovery](https://github.com/fdelvalle01/s0-core-template/pull/6) | 2026-10-24 | [2b552cc](https://github.com/fdelvalle01/s0-core-template/commit/2b552cc819d031ca67f8710c85adb3560ae18105) | Windows; verificador Git/Python y comprobaciones estructurales |
| [PR #7: connect-project](https://github.com/fdelvalle01/s0-core-template/pull/7) | 2026-10-24 | [6d58fbd](https://github.com/fdelvalle01/s0-core-template/commit/6d58fbd88d79b6557e7b95b6212ed377dfcbd771) | OpenSpec 1.14.3; repositorios sintéticos, registros y preferencias aislados; catálogo Codex |

¹ Fechas de publicación en America/Santiago, no fechas exactas de ejecución.
Los PR contienen resúmenes de resultados, no logs completos. Los registros brutos
y fixtures se conservaron fuera de la plantilla y no están enlazados desde esos
informes. Tampoco se identifica allí el modelo ni todas las versiones de cliente.
Son antecedentes de esas entregas, no una certificación de cualquier revisión futura.

| Área | Resultado documentado | Fuente |
| --- | --- | --- |
| Verificador Discovery | 18 tests: 17 aprobados y 1 omitido por privilegios Windows para crear symlinks | PR #6 |
| Conexión local | S0 nuevo, monorepo y dos Git adicionales; resolución e integraciones correctas; borrador Discovery sin escritura | PR #7 |
| Reejecución y conflictos | Sin cambios innecesarios en archivos/estado Git/preferencias; planificación previa y asociaciones de registro conservadas | PR #7 |
| CLI y preferencias | Instalación real en prefijo npm desechable; selección de 1.14.3 frente a wrapper anterior simulado; herramientas ausentes simuladas; generación temporal con `delivery=both` | PR #7 |
| Catálogo e integraciones | Codex: 10 skills habilitadas, 0 errores, sin iniciar un turno de modelo; archivos oficiales del core conservados | PR #7 |
| Recorridos completos sin código y sin Python | **Pendientes**; los controles parciales no acreditan estos recorridos | PR #7 |
| Sesión real Claude Code y regresión semántica dual | **Pendientes**; catálogo, hashes y estructura no acreditan ejecución de los métodos | PR #6 / PR #7 |

En futuras validaciones registra fecha de ejecución, commit probado, sistema,
CLI, cliente/modelo cuando intervengan, resultado y enlace al informe o logs
accesibles al equipo. Conserva fallos y omisiones; no conviertas un caso omitido
en aprobado ni sobrescribas antecedentes con resultados de otro entorno.

<a id="official-core"></a>
### Incorporación en el Core oficial Nuam — 2026-10-28

Base oficial: `5e5ec4a3975d2ccb46f4145b0803ad6649d7e305` de
[`nuamx/nuam-ia-arq-sdd-openspec`, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
Se incorpora la implementación común del
[commit `3f5e67d`](https://github.com/fdelvalle01/s0-core-template/commit/3f5e67de5451d0d45f25f8755e7b759b913734c1).
Ese enlace conserva la procedencia histórica del trabajo. El origen vigente
para nuevas adopciones es el repositorio oficial y un commit publicado allí.

De los 44 archivos compartidos, 43 conservan exactamente los bytes de esa
implementación. Sólo cambia la redacción de `connect-project` para referirse al
repositorio maestro del Core sin exigir un nombre de repositorio particular.
Las guías identifican el origen oficial, seleccionan expresamente `development`
para crear una copia independiente y usan ese origen en el ejemplo de adopción.
El maestro no distribuye un `core-adoption.json` rellenado.

Comprobaciones ejecutadas en esta incorporación, en Windows con Git
2.25.0.windows.1 y Python 3.11.1:

- `quick_validate.py` aprobado para la skill canónica y su puente Claude.
- Comparador: 13 tests ejecutados, 12 aprobados y uno omitido por falta de
  privilegios para symlinks en Windows; el caso de junction fue aprobado.
- Enlaces locales de las guías y la skill: destinos de archivo comprobados;
  `git diff --check` sin errores.
- Comparación por bytes contra la base oficial: conservados los seis archivos
  de identidad, contexto, configuración, catálogo, specs e historial; los
  18 workflows oficiales y su marcador; y los dos archivos del Viewer.
  La identidad sigue siendo `s0-core`, el catálogo permanece vacío y el paquete
  Viewer mantiene su manifiesto y publisher originales.

La matriz CLI 1.13.2/1.14.3 y el ensayo independiente de agente descritos en la
sección siguiente corresponden a la implementación fuente. No se repitieron
durante el traslado, ni las suites históricas de Discovery o review-pr. Esta
incorporación no acredita nuevos ensayos de producto ni sesiones de Claude.

<a id="portable-onboarding"></a>
### Core común, acceso a fuentes y compatibilidad — 2026-10-28

Evidencia de la implementación fuente, incorporada aquí sin repetir los ensayos
CLI o de agente. Base: `5a54e24b540dc4bfbd71cf505da8e00c09ba57ca`, más la
ampliación publicada en `3f5e67de5451d0d45f25f8755e7b759b913734c1`.
Entorno: Windows, Git 2.25.0.windows.1, Python 3.11.1 y Node 22.18.0.
Se comprobaron las instalaciones npm de OpenSpec **1.13.2 y 1.14.3** con
registros y preferencias XDG aislados y repositorios sintéticos sin datos de
producto. Los ensayos de CLI usan la base citada; el ensayo de agente usa la
skill revisada y sus instrucciones actuales. No se cambiaron HOME ni CODEX_HOME.

| Comprobación | Resultado |
| --- | --- |
| Registrar una instancia nueva, resolverla y repetir el registro | Ambas versiones correctas; la repetición conserva el registro por bytes |
| `init --tools "claude,codex" --profile core --no-animation` con `store:` | 1.13.2 rechaza la operación con salida 1 y conserva archivos; 1.14.3 crea las integraciones y conserva el puntero |
| Repetir `init` con 1.14.3 | Archivos idénticos por bytes, sin specs ni changes locales |
| Crear cambio genérico, consultar instrucciones y validar estrictamente | Recorrido 1.14.3: 14 comandos y 26 comprobaciones correctos; no prueba implementar código |
| Consultar con 1.13.2 un consumidor integrado por 1.14.3 | `context`, `status`, `instructions apply` y validación estricta correctos; fixture y registro conservados |
| `actionContext.allowedEditRoots` desde el consumidor | 1.13.2 devuelve sólo S0; 1.14.3 devuelve consumidor y S0; mismo resultado con y sin `--store` |
| Fuente con otro store y trabajo pendiente | Puntero, archivos, índice y metadata conservados al consultar |
| Comparador Core/instancia | 13 tests: 12 aprobados y uno omitido por privilegios Windows para symlinks; caso de junction aprobado |

El rechazo de 1.13.2 es un límite comprobado, no un caso aprobado de integración.
No se retiró `store:` para sortearlo. La consulta correcta de un consumidor no
autoriza a ampliar las raíces de edición que declara el workflow. No se ejecutó
apply ni código de producto y no se certifican otras versiones o sistemas operativos.

Un agente independiente recibió la skill actual y una petición de preparar dos
fuentes, sin conocer los resultados esperados. La comparación externa de snapshots
confirmó una sola adición: el localizador Git del S0. Ambos consumidores, incluido
uno con otro store y trabajo pendiente, conservaron todos sus archivos y metadata,
ramas y HEAD; los registros y preferencias aislados y reales no cambiaron.
No necesitó ejecutar CLI ni registrar el S0 para esa preparación.

Una petición posterior al mismo agente autorizó integrar sólo el consumidor
compatible. Seleccionó 1.14.3, registró la identidad existente, generó integraciones
oficiales y alineó AGENTS/CLAUDE. `store doctor` no encontró problemas y `context`
resolvió el S0 correcto. La comparación externa confirmó únicamente esas escrituras,
el registro aislado y la configuración temporal de `delivery`; el otro consumidor
y los archivos globales permanecieron intactos. La reejecución del agente omitió
registro, init y escrituras, comprobando contenido y fechas de modificación
idénticos. No inició Discovery. El preflight dejó pendiente init hasta disponer
de lectura autorizada de los nombres de prompts globales; todos estaban ausentes.

Los hashes del registro, preferencias y prompts globales de la estación se
conservaron. La carpeta de prompts Codex globales no existía: el ensayo no prueba
una migración con legado. `init` de 1.14.3 puede limpiar esos prompts fuera de
XDG; la referencia de integración exige comprobarlos y dejar esa operación
pendiente si la limpieza no está dentro del alcance autorizado.

Los logs, snapshots y procedimientos del laboratorio se conservaron fuera de la
plantilla; no se distribuyen como evidencia accesible a otros equipos. Para
repetir la matriz, usa stores y consumidores sintéticos con XDG aislado, conserva
estado Git y hashes antes/después y ejecuta las operaciones de la tabla con cada
binario identificado. No uses productos ni el registro real para probar adopción.
El comparador se comprueba desde la raíz con:

```powershell
py -3 -B -m unittest discover -s scripts -p test_compare_core.py -v
```

La revisión independiente de las fuentes comprobó separación entre acceso e
integración y ausencia de reglas de producto en el maestro. Se corrigió el preflight de
prompts globales y la documentación de requisitos Git del comparador. Las suites
históricas de Discovery y review-pr no se repitieron: sus implementaciones no
cambiaron. Las sesiones reales en Claude y la regresión semántica dual continúan
pendientes; un ensayo de agente local no las acredita.

### Catálogo compartido y distribución — 2026-10-27

Base: `b4a6654ee18dba13ff05a0237cb0cc1ff627622c`, más esta ampliación.
Se incorpora `repositories.yaml` vacío (`version: 1`, `repositories: []`) y
se documenta la selección de sus entradas con ubicaciones personales.

- Validados YAML del catálogo y frontmatter de `connect-project` con el verificador
  de skills; comprobados enlaces locales y `git diff --check`.
- Revisión independiente de decisiones ante coordinador con componentes anidados,
  ruta explícita con otro clon recordado, remotos HTTPS/SSH, fork distinto y entorno
  cloud sin fuentes. Es una revisión del método, no una conexión real en Claude.
- Se conservan identidad, configuración oficial `spec-driven`, workflows de
  OpenSpec 1.14.3 y paquete Viewer 0.9.0 de la base anterior. El catálogo no contiene
  repositorios de un producto ni rutas personales.

No se ejecutaron nuevamente las suites históricas de Discovery o review-pr:
sus implementaciones no cambiaron. Conexiones y autenticación deben comprobarse
en cada estación; esta revisión no acredita acceso desde otros equipos.

### Fuentes locales, remotas y mixtas — 2026-10-25

Base: `2e9fd3dbeeca8e047ceedc04e84be0a4d22f2eb6`, más esta ampliación.
Fuente final: blob Git `d91dd0c7fe30d0ece7a0ee2a57a57a55b0f9ecb0`.
Las primeras conexiones y el caso sin código usaron candidatos intermedios;
actualización, recuperación y reejecución mixta se probaron sobre esta fuente final.
Entorno: Windows, Git **2.46.2.windows.1**, OpenSpec **1.14.3**, Python **3.13.3**.
Los agentes de esta sesión ejecutaron los procedimientos en repositorios sintéticos,
con registro y preferencias aislados. Un agente independiente recibió una petición
mixta y las skills locales sin adelantarle los resultados esperados. No se midieron
versión del cliente ni modelo; no fue una sesión real de Claude Code.

| Escenario ejecutado | Resultado |
| --- | --- |
| Conexión mixta: dos remotos, monorepo y otros Git | Cuatro consumidores conectados al S0 correcto; una raíz con planificación propia bloqueada e intacta; nombres de repositorio repetidos sin colisión |
| Sólo remoto; ramas explícita y predeterminada | Copias distintas para dos ramas del mismo URL; rama `trunk` resuelta sin asumir `main`; integraciones oficiales comprobadas |
| Actualización remota y desde una ruta local con upstream | Nuevas copias conectadas; anteriores preservadas en archivos, HEAD, rama, índice y configuración, incluido trabajo staged/unstaged |
| Actualización sin avance y reconexión | Sin otro clon, regeneración o entrada duplicada; reconexión sin consultar nuevas revisiones. Reejecución mixta: seis raíces, índice externo, registro y preferencias sin diferencias |
| Dos S0 en el mismo workspace | Mismo URL/rama/SHA con copias e índices independientes; consumidores resuelven su propio S0 |
| Conflicto de registro, rama ausente y remoto inaccesible | Bloqueos explícitos sin sustituir asociaciones ni descargas existentes |
| Recuperación e índice: nueve secuencias Git instrumentadas | Descargas pendientes recuperables; copias alteradas bloqueadas al reconectar; históricas conservadas; índices ajenos/inválidos y destinos dentro del S0 o con junction externa rechazados |
| Herramientas y preferencias | CLI real 1.14.3 seleccionada detrás de 1.13.2; ausencias simuladas con PATH aislado; preferencias persistentes conservadas |
| Sin código y entrega Discovery | Identidad preparada sin workspace/índice; borrador limitado al propósito. Snapshots posteriores a preparación, verificaciones de lectura sin violaciones y contexto sin escribir |
| Regresión del core | 37 archivos protegidos sin cambios; schema oficial sin overrides; 56 enlaces locales válidos; fuente común y puente válidos; sin artefactos de producto que validar |
| Suite existente de Discovery | 18 tests: 17 aprobados y 1 omitido por privilegios Windows para symlinks |

Los remotos HTTPS se redirigieron a Git bare locales. Esto prueba preparación Git,
no autenticación real de GitHub, GitLab, Bitbucket o SSH. No se instalaron runtimes
ni se ejecutaron productos. Los commits/push de preparación de fixtures afectaron
sólo remotos sintéticos; las operaciones de conexión no publicaron cambios.

Se conservaron los fallos de ensayo: escrituras CRLF del laboratorio requirieron
corregir únicamente las adiciones propias. Un `diff --check` de consumidor sigue
señalando whitespace preexistente, cuyos bytes e índice se preservaron; no se
presenta como verde. En las pruebas de recuperación se detectaron claves de editor
`vscode-merge-base` añadidas a Git; la repetición con una referencia estable pasó
sin excluir metadata del control. Los informes y registros brutos permanecen fuera del core,
en el laboratorio de esta entrega, no como nuevos archivos de la plantilla.
La ejecución real en Claude, la regresión semántica dual y el recorrido completo
sin Python siguen pendientes. Las ausencias simuladas no equivalen a probar
una máquina sin esas herramientas instaladas.

### Adaptación de review-pr — 2026-10-26

Base: `4455a9bbd748c14789bf5e2db9a8357fb58f7d9a`, más esta adaptación.
Fuente: `sdd-workspace`, rama `development`, commit
`3686a29a411b67192d26e47139e28fd154013a96`. Método adaptado: blob Git
`d01a0f857cc8bd0ec309c015d2d75ea10cd4cded`; verificador conservado sin cambios
de lógica: blob `2c2e25ecf91671b3845357688bef073fd9af5197`.
Entorno: Windows, Git **2.46.2.windows.1**, Node **24.19.0**, Python **3.13.3**,
OpenSpec **1.14.3** mediante ejecutable explícito; el wrapper anterior de PATH
devolvía 1.13.2 y no se utilizó para validar. No se cambió PATH permanente.

| Comprobación ejecutada | Resultado |
| --- | --- |
| Verificador importado | Sintaxis correcta y 20 tests aprobados, sin fallos ni omisiones; identidad, anclas, evidencia, diffs malformados, renombres, CLI, BOM y límite de tamaño |
| Entradas de skill y enlaces | Fuente común y puente válidos, frontmatter coincidente, 45 enlaces locales comprobados sin destinos ausentes; 11 entradas de skill por cliente |
| Revisión independiente de la adaptación | Sin pérdidas funcionales ni dependencias operativas del kit anterior; la comprobación de base, procedencia y semántica permanece a cargo del agente |
| Ejecución independiente con snapshot sintético | Detectó una regresión de autorización en el SHA del PR pese a una corrección local pendiente; contrastó la spec vigente con una propuesta sin aprobar y trató la instrucción de publicar incluida en el PR como dato |
| Evidencia y conservación del fixture | Tres casos ejecutados contra base/head; informe con un hallazgo y ancla válida; verificador correcto; HEAD, índice, cambios pendientes y archivo sin seguimiento conservados, sin publicación |
| Integridad del core | Configuración, identidad y workflows oficiales sin diferencias; OpenSpec no encontró artefactos que validar |

El agente de prueba recibió petición, snapshot, skill y fuentes del laboratorio
sin adelantarle el defecto esperado. El agente principal contrastó el informe,
los resultados y el estado Git con la referencia previa. No se registraron versión
del cliente ni modelo; no fue una sesión real de Claude Code.
En el primer informe del laboratorio se perdieron tildes al enviar texto por un
pipe PowerShell/Python. Se corrigió mediante escritura UTF-8 directa y se comprobó
el contenido por bytes; la incidencia quedó registrada con los resultados locales.

Los conteos de archivos no acreditan descubrimiento en el catálogo ni una sesión
real de Claude Code. La suite se ejecutó en Node 24.19.0, no en todas las versiones
admitidas. No se publicó una review remota ni se probó autenticación de proveedores.
Los fixtures de comprobación se conservan fuera de la plantilla.

### Localización de fuentes por estación — 2026-10-26

Base: `385fb8bea31f1dbffc0a446a52ac93fa9e7c59f0`, más esta ampliación.
Fuente final de `connect-project`: blob Git
`4c706dc213b5b78d61cbeaad9847232b9865f7cb`.
Entorno observado: Windows, Git **2.25.0.windows.1**, OpenSpec **1.14.3** y
Python **3.11.1**. Se usó el ejecutable comprobado y modo UTF-8 para el validador
de skills. Los scripts y evidencias de laboratorio quedaron fuera del core.

| Comprobación | Resultado |
| --- | --- |
| Skills y enlaces | Cuatro skills propias válidas; 71 enlaces locales comprobados entre maestro e instancia; fuentes comunes iguales |
| Incorporación a S0 existente | Dos Git en carpetas distintas conectados con registro y preferencias aislados; identidad, contexto, spec y cinco artefactos del cambio preexistente conservados por hash |
| Reejecución | Sin repetir registro ni init; archivos, estado Git, punteros y localizador conservados, incluido el mtime del JSON |
| Revisión actual y fuentes inválidas | Cambios de rama/HEAD admitidos con árbol sucio; ruta ausente, origin distinto y propietario ajeno identificados sin reparar ni sustituir entradas |
| Conexión mixta | Una copia remota sintética quedó en el índice externo `version: 1` con estado `connected`; el localizador conservó sólo las fuentes locales. Reejecución sin duplicados ni cambios de hashes/mtime |
| Instancia existente | Trece raíces locales verificadas; sesión independiente encontró dos componentes sin recibir sus rutas y declaró sus revisiones actuales |
| Integridad | Schema efectivo del paquete, sin overrides; configuración, identidad, skills oficiales y artefactos de planificación conservados en las instancias reales revisadas |

La primera prueba detectó que `status` sin selección falla cuando existen cambios
activos. Se corrigió la invocación de la skill propia a `status --all`, opción
oficial comprobada también con inventario vacío; no se modificó la CLI.
En el fixture, `init` oficial añadió `openspec/changes/archive/.gitkeep`; conservar
los artefactos anteriores no equivale a que la inicialización no añada archivos.
Discovery verificó su referencia y dejó sólo un borrador, sin publicar contexto.
El laboratorio registró 40 comprobaciones de conservación aprobadas; son controles
de conexión y lectura, no tests del producto ni una certificación general del agente.

El remoto del caso mixto se redirigió por comando Git a un bare local, sin cambios
de configuración global. Estas pruebas no ejecutaron producto ni autenticación remota. No acreditan una
sesión real de Claude Code. La validación de estación usa evidencia local y no
convierte el localizador en configuración OpenSpec o en inventario compartido.

<a id="viewer"></a>
## OpenSpec Viewer Base 0.9.0 — distribución del 2026-10-26

El paquete `tools/openspec-viewer/openspec-viewer-0.9.0.vsix` y su manifiesto
provienen del repositorio [sdd-openspec-view](https://github.com/fdelvalle01/sdd-openspec-view),
rama `development`. El manifiesto identifica commit y árbol fuente, lockfile,
versión de Node, archivos inspeccionados y SHA-256 del VSIX. La identidad
`fdelvalle01.openspec-viewer` y los ajustes anteriores se conservan.

Fuente confirmada: `f156c7c986408a7d8eefe9d8043559586495e806`. SHA-256 del VSIX:
`172997393f78072523b40cffcd644f71611b5f1d77367b32bff57a7b01ef5bc1`. El mismo binario y manifiesto se copiaron sin reconstruir
a ambas plantillas; sus hashes se contrastaron después de la copia.

| Comprobación ejecutada | Resultado |
| --- | --- |
| Fuente y dependencias | Commit f156c7c986408a7d8eefe9d8043559586495e806 limpio; lockfile con npm ci; Node 22.18.0 y npm 10.9.3. |
| Suite principal | 218 aprobadas, 0 fallidas y 1 omitida por permisos de symlink de archivo en Windows. |
| Interfaz y catálogo visual | 50 y 12 comprobaciones aprobadas; mapa Markdown y YAML opcional consultables sin inventario generado. |
| Regresión de registro de watchers | 26 pruebas de layout/controlador y 56 de extensión aprobadas; recuperación de archivos creados durante el registro de nuevas raíces. |
| Separación de productos | 8 pruebas y renderer Base real aprobados; sin asistente ni puente Desktop. |
| Inspección del VSIX | 43 entradas permitidas, documentación explícita y procedencia verificada; sólo se distribuye Base 0.9.0. |
| Instalación y host del paquete final | Install from VSIX en perfil aislado; versión 0.9.0 confirmada y 26 comprobaciones del paquete instalado aprobadas. |
| Core, consumidor y compatibilidad | Lectura de contexto, búsqueda, grafo, enlaces y watchers; consumidor resuelto con OpenSpec 1.14.3 antes de la ruta recordada; fixtures antiguos conservados. |
| Preservación de archivos | Lectura conservó 49 archivos de cada plantilla y 54 de NXT; los 54 hashes de NXT también coinciden antes y después del host del VSIX instalado. |
| Procedencia del motor | Seis módulos locales verificados; árbol histórico y adaptación local registrados por separado. |

Una prueba de symlink de archivo quedó omitida por EPERM; el rechazo de una junction externa sí se comprobó.
El grafo conserva diagnósticos de enlaces a documentos raíz fuera del índice y de algunas anclas HTML de skills que no reconoce.
En la estación de validación el primer OpenSpec de PATH es 1.13.2. Se utilizó 1.14.3 sólo en el entorno de prueba; con una CLI incompatible sigue disponible la selección manual del S0.
El primer candidato de validación no se distribuyó; el candidato final incorpora la reconciliación de watchers y pasó el host instalado.
No se instalaron extensiones en el perfil habitual ni se publicaron paquetes AI/Desktop. Las regresiones compartidas no equivalen a una nueva aceptación Desktop ni a una aceptación real de Jira OAuth.

La documentación de instalación explica selección directa y por consumidor,
actualización manual y la limitación de Workspace Trust. El empaquetado usa un
inventario explícito de documentación distribuible; diseños, auditorías,
diagnósticos privados, fuentes y servicios IA permanecen fuera del VSIX Base.
`*.vsix binary` evita normalización de finales de línea sobre el paquete Git.

La instalación aislada, las pruebas automáticas, la lectura real y la aceptación
manual son evidencias distintas. Jira OAuth y la aceptación funcional humana no
se acreditan por compilar, pasar fixtures o distribuir este paquete. Los
artefactos OpenSpec y las skills de esta plantilla conservan su contenido.

## Comprobaciones reproducibles

Trabaja en copias aisladas con datos sintéticos. Usa Git y OpenSpec **1.14.3**;
para Discovery, Python **>=3.10** y su biblioteca estándar. Comprueba primero el
ejecutable efectivo según [la referencia de CLI](INSTALLATION.md#cli-setup).

### Estructura y resolución

Desde la raíz de la copia de prueba, usando la CLI comprobada:

```powershell
openspec --version
openspec schema which spec-driven --json
openspec status
openspec validate --all --strict --no-interactive
openspec doctor
git diff --check
```

El schema efectivo debe ser el oficial del paquete, sin overrides. La plantilla
sin requisitos o cambios puede devolver inventarios vacíos. Comprueba enlaces,
fuentes propias y puentes Claude; verifica catálogo y ejecución por separado.

Para repetir la conexión, sigue estos escenarios con `connect-project`:

| Escenario | Comprobar |
| --- | --- |
| Instancia nueva, monorepo y varios Git | ID propio; `context --json` desde cada consumidor resuelve el mismo S0; sin specs/changes locales paralelos |
| Segunda ejecución | Identidad, punteros, instrucciones, HEAD, índice y preferencias conservados; sin generación redundante |
| Registro en conflicto o planificación previa | Bloqueo explícito, contenido y asociaciones preservados, resultados parciales identificados |
| CLI ausente, PATH antiguo o requisito ausente | Instalación/selección de versión según herramientas disponibles; requisito pendiente explícito; preferencias persistentes conservadas |
| Sin código o sin Python | Preparación posible y borrador limitado; sin arquitectura inventada ni escritura de contexto sin comprobaciones |
| Remoto o mixto, rama omitida y varias ramas | SHA realmente preparado; selección predeterminada correcta; copias sin colisiones ni conexiones por inferencia |
| Reejecución o actualización explícita | Reutilización sin avance implícito; nueva copia cuando corresponda y anterior intacta, también al actualizar desde una ruta local |
| Índice, descargas pendientes y varios S0 | Propietario y rutas comprobados; recuperación sin borrar copias; discrepancias de una copia verificada bloquean reconexión |
| Fuentes locales recordadas y estación nueva | S0 con contexto/specs/cambios conservados; rutas propias fuera del contenido versionado; sesión posterior encuentra código sin recibirlas otra vez |
| Lectura del localizador | Rama/HEAD actuales sin fijarlos; raíces ausentes, remotos distintos y propietario ajeno se informan sin reparar ni sustituir fuentes |

El cierre deja diffs locales sin stage, commit, push ni PR. Captura la referencia
de Discovery después de la preparación técnica y verifica lectura sin cambios
antes de presentar su borrador.

### Verificador y comportamiento de Discovery

Desde la raíz, sin generar caches Python en la plantilla:

```powershell
py -3 -B -m unittest discover -s .agents/skills/project-discovery/scripts -p test_project_discovery_scope.py -v
```

La suite cubre cambios previos, rutas permitidas exactas, archivos protegidos,
HEAD/índice, permisos y enlaces. Aunque usa carpetas temporales, hereda la
configuración y variables Git del entorno: hooks, firma o plantillas personales
pueden afectar su reproducibilidad. Ese aislamiento sigue pendiente de mejorar.

Para comprobar el método completo, usa dos o tres Git sintéticos con documentación
contradictoria y una dependencia desconocida. Pide un borrador a un agente sin
adelantar conclusiones; revisa fuentes, hechos/inferencias y cobertura. Comprueba
lectura sin cambios y, tras aprobar contenido y rutas, publicación limitada a ese
contexto contra la misma referencia. El [contrato de Discovery](.agents/skills/project-discovery/SKILL.md#scope-checks)
define las operaciones y límites exactos.

### Verificador y comportamiento de review-pr

Desde la raíz, con Node.js >=20 y sin instalar dependencias npm:

```powershell
node --test .agents/skills/review-pr/scripts/verify-report.test.mjs
```

Para probar el método, prepara un PR sintético con objetos base/head, diff y
contexto S0. Entrega el snapshot a un agente independiente usando la skill local,
sin adelantarle las conclusiones. Contrasta el informe con el código del SHA, las
specs vigentes y las propuestas; verifica que conserva trabajo local y que no
atribuye vigencia remota ni publicación a una captura suministrada. Ejecuta el
verificador sobre los artefactos finales y revisa aparte la semántica: pasar la
comprobación de anclas no demuestra que el hallazgo sea correcto.

### Regresión funcional en Codex y Claude

En copias equivalentes, fija revisión, CLI, schema, cliente, modelo y necesidad;
aísla registros y preferencias. Conserva hashes de configuración, identidad y
archivos oficiales para comprobar que Discovery no los modifica.
Compara una propuesta nativa antes y después de Discovery aprobado: conserva los
artefactos, valida con la CLI y revisa requisitos observables, decisiones de diseño
y tareas comprobables. Repite en cada cliente sin sustituirlo por el otro.
No se espera identidad textual; registra diferencias de significado, fallos y
fuentes. Este recorrido sigue pendiente según la tabla de estado.

## Límites de lo comprobado

El verificador detecta diferencias de archivos y estado Git; no acredita aprobación
humana, veracidad del texto ni escrituras transitorias revertidas. El análisis puede
ser selectivo, pero las huellas cubren los archivos incluidos de cada raíz capturada:
la arquitectura multirrepositorio no equivale a un benchmark de rendimiento.
Validación estructural, archivo de cambios y catálogo de skills no prueban aceptación
funcional, ejecución del producto ni permisos de otros clientes o conectores.
