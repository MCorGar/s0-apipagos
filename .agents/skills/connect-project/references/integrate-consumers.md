# Adoptar un S0 e integrar consumidores

Lee esta referencia cuando la petición autorice adoptar la instancia,
inicializar OpenSpec o instalar integraciones en los consumidores identificados.
Aplica primero la selección y los límites de [connect-project](../SKILL.md).
Si sólo se solicitaron descargas, usa únicamente el apartado de preparación de
clones con el S0 y su identidad ya comprobados; no actives registro ni integración.

Comprueba en la CLI elegida `context`, `store`, `init`, `config` y las opciones
que vas a usar; registra su versión. En las instalaciones comprobadas, **1.13.2
registra y resuelve stores, pero rechaza `init` en un consumidor con `store:`**.
**1.14.3 sí genera esas integraciones conservando el puntero**. Para ese paso,
selecciona la CLI con esa capacidad antes de escribir en el consumidor. Si falta,
deja su integración pendiente y continúa con las consultas posibles. La existencia
de una opción en `--help` no acredita por sí sola este comportamiento. Nunca
retires el puntero ni crees specs locales para sortear ese rechazo.
Instalar o actualizar la CLI se limita al alcance autorizado; no es un efecto
de detectar una versión distinta.

## 1. Comprueba la identidad antes de preparar fuentes

Lee `.openspec-store/store.yaml`, el remoto del S0, su configuración y
`store list --json` usando la CLI comprobada. Conserva una identidad ya adoptada.
Si el ID solicitado contradice esa identidad, informa el conflicto antes de
conectar consumidores; esta skill no renombra sistemas existentes.

Sólo en una adopción nueva confirmada desde plantilla, con remoto propio,
contenido inicial genérico y sin specs ni cambios de producto, determina que el
marcador heredado puede sustituirse; no lo retires hasta el paso 3.
`id: s0-core` por sí solo no demuestra que sea descartable.
Deriva el ID del nombre del repositorio remoto quitando `s0-`, salvo que el usuario
lo haya indicado. Si no es válido o resulta ambiguo, pide ese dato.

Comprueba que el ID previsto no esté registrado en otra ruta ni la ruta bajo otro
ID. No desregistres asociaciones ajenas. Si hay un conflicto de identidad o el S0
es el maestro, detén la preparación antes de clonar o configurar consumidores.

<a id="prepare-clones"></a>
## 2. Prepara sólo las descargas o actualizaciones solicitadas

Si la petición no incluye descargar o actualizar fuentes, o todavía no hay
código, omite este paso: una URL por sí sola no autoriza un clon. No crees workspace
ni índice de descargas. Las fuentes locales verificadas se recuerdan al terminar
según el método de la skill. Para obtener copias, usa el destino indicado o
consulta `git config --local --get s0.sourcesRoot` desde el S0. Si falta, pide
una carpeta de trabajo una vez. Resuelve su ruta real: no puede estar dentro
del S0 ni de otra raíz Git. Puede contener las nuevas copias como hijas.
Comprueba enlaces y destinos antes de escribir; no atravieses una redirección
que salga del workspace autorizado. Recuerda el destino comprobado con
`git config --local s0.sourcesRoot <ruta>`; no cambies configuración Git global.

### Índice local de copias

Usa `<workspace>/.s0-connections/<store-id>.json`, fuera de todas las raíces
analizadas. Mantén JSON UTF-8 con `version: 1`, `s0: {id, root, remote}` y
`copies`: entradas `{remote, branch, path, base_sha, status}`. Los nombres de
claves son literales; los valores corresponden a la instancia y copias reales.
`status` es `pending`, `prepared`, `connected` o `blocked`; `base_sha` puede ser
null hasta verificar el clon. Conserva las entradas anteriores al añadir una
revisión. No conviertas este índice en inventario compartido ni snapshot Discovery.

Antes de reutilizarlo, valida versión, estructura, propietario (ID, raíz S0 y
remoto), rutas dentro del workspace y ausencia de destinos compartidos con otro
S0. Un índice inválido o ajeno bloquea la operación remota; no lo sobrescribas
ni adoptes sus rutas. Para la copia seleccionada verifica raíz Git exacta y URL de `origin`
(`git config --get remote.origin.url`, antes de posibles reglas `insteadOf`),
rama y HEAD contra su entrada. Las copias históricas no seleccionadas conservan
su registro aunque después alguien trabaje en ellas. No confíes sólo en el JSON
ni en el nombre del directorio. No guardes contraseñas o tokens en URLs, índice, logs o contexto;
usa las credenciales HTTPS/SSH ya disponibles. No cambies cuentas ni enumeres
otros repositorios del proveedor.

### Conectar o actualizar

1. **Reconectar una fuente conocida:** selecciona la entrada correspondiente a la
   URL y rama solicitadas; si hay varias revisiones y ninguna selección explícita,
   inspecciona la última entrada que corresponda, incluido su estado pendiente
   o bloqueado; no saltes a una revisión anterior para ocultar un fallo. Una rama
   omitida reutiliza la selección anterior sólo si es inequívoca. No consultes el remoto
   para actualizarla ni repitas un clon ya verificado. Si la entrada nunca fue
   verificada (`base_sha: null`), inspecciona la descarga: completa lo comprobable
   según el punto 5 o prepara una ruta libre conservando la incompleta. No compares
   HEAD contra null. Conserva y declara los cambios locales de una copia verificada.
   Si su rama, HEAD o remoto cambió, informa el bloqueo; no elijas otra copia a
   escondidas ni la repares. Una petición explícita de actualizar permite preparar
   otra. Una ruta local proporcionada sigue siendo una fuente local, no una orden
   de igualarla a su remoto.
2. **Fuente nueva o actualización explícita:** comprueba acceso con Git. Resuelve
   la rama predeterminada mediante `git ls-remote --symref <url> HEAD` sólo cuando
   no haya selección previa ni rama indicada; no asumas `main`. Comprueba la rama
   exacta con `git ls-remote --exit-code --heads <url> refs/heads/<rama>`.
   Valida la referencia y pasa URL, rama y destino como argumentos, sin construir
   comandos ejecutables a partir de sus textos. Una rama ausente o remoto vacío
   queda bloqueado; no selecciones otra rama silenciosamente.
3. **Actualizar una fuente local:** usa la URL y rama expresas o su upstream
   configurado si es inequívoco. Un remoto local `.` o una referencia sin URL/rama
   resoluble requiere esos datos. No hagas fetch, pull, checkout, reset o limpieza
   en ese checkout. La actualización prepara una copia externa y conserva tanto
   sus cambios de producto como sus integraciones; no los traslada automáticamente.
4. **Reutilizar o clonar:** si una actualización encuentra el mismo SHA base y una
   copia registrada válida para esa rama, reutilízala y declara su estado sucio.
   En otro caso reserva una ruta inexistente bajo el workspace, diferenciando S0,
   repositorio, rama y revisión; resuelve colisiones con un sufijo sin sobrescribir.
   Registra `pending` y ejecuta `git clone --single-branch --branch <rama> -- <url>
   <destino>` con argumentos separados. No uses cachés, worktrees, submódulos
   recursivos ni ejecutes código del producto. Sólo las copias nuevas seleccionan
   rama. Si se proporcionó una copia local para reutilizar, sigue el flujo local
   sobre esa raíz; no la adoptes por coincidencia de URL con otra entrada.
5. **Verificar la copia nueva:** comprueba raíz, remoto, rama y `rev-parse HEAD`;
   registra ese SHA realmente obtenido, que puede diferir de la consulta anterior
   si la rama avanzó. Es la revisión observada en esta preparación, no una promesa
   de actualidad permanente ni una captura atómica entre varios repositorios.
   Marca `prepared`. En fallo, conserva la ruta y marca `blocked`; una reejecución
   inspecciona lo existente y sólo completa lo verificable o usa una ruta libre.
   Nunca borres una copia parcial para reintentar. Declara contenido inaccesible,
   submódulos o LFS faltantes como límites de cobertura.

Conserva el índice válido al actualizarlo (escritura temporal y reemplazo dentro
de su directorio). Si falla su escritura, no sigas creando copias sin seguimiento.
No limpies copias antiguas automáticamente. Reúne las raíces preparadas y locales
autorizadas, elimina duplicados por raíz real y aplica las mismas comprobaciones
de instrucciones y exclusión de otros S0 antes de conectarlas. Los fallos de una
fuente no impiden trabajar con otras compatibles; identifica siempre lo pendiente.

## 3. Registra y personaliza el S0

Con la identidad comprobada, registra un store adoptado con `store register .`
si hace falta, conservando metadata. Sólo para la adopción nueva comprobada en
el paso 1, retira el marker heredado conservándolo temporalmente fuera del
repositorio y deja crear la identidad con `store register . --id <id> --yes`.
Si falla, restaura únicamente ese marker que acabas de retirar y explica el error;
no continúes suponiendo que quedó registrado. No uses `git init` ni edites el ID
a mano: conserva las comprobaciones de identidad de la CLI.

En una instancia recién adoptada, cambia el título/descripción inicial del README
y la frase genérica que identifica la plantilla en `openspec/config.yaml` por
el nombre confirmado del sistema. Preserva schema, reglas y demás propiedades;
no añadas instrucciones técnicas ni dupliques el contexto funcional. Conserva
descripciones propias existentes. Project Discovery prepara `context/` cuando se
solicita; la adopción técnica no inicia ese análisis automáticamente.

Comprueba también las integraciones oficiales del propio S0 con el procedimiento
de generación/verificación siguiente. Si faltan, ejecútalo desde su raíz,
conservando su configuración, specs, cambios y skills propias. El S0 mantiene
su raíz OpenSpec: no se sustituye su configuración por un puntero a sí mismo.

## 4. Integra cada consumidor compatible

En cada raíz Git seleccionada, aplica esta decisión antes de ejecutar `init`:

| Estado encontrado | Acción |
| --- | --- |
| Sin configuración ni specs/changes locales | Crea `openspec/config.yaml` con `store: <id>` |
| Configuración sólo de puntero al mismo S0 | Consérvala byte a byte y comprueba las integraciones |
| Otro store, configuración propia, YAML inválido o specs/changes locales | Informa el conflicto; no conviertas ni borres esa planificación |

Considera también `config.yml`; no crees un segundo archivo para ocultar el
existente. Detecta los conflictos antes de escribir en ese consumidor. Puedes
continuar con consumidores compatibles; el resultado debe distinguir los
conectados de los pendientes y nunca presentarse como completo si falta alguno.

Antes de ejecutar `init`, comprueba también la limpieza de integraciones antiguas
que realiza la CLI seleccionada. En 1.14.3 puede eliminar prompts OpenSpec globales
de Codex aunque `XDG_CONFIG_HOME` sea temporal: busca los nombres administrados
`opsx-{propose,explore,new,continue,apply,update,ff,sync,archive,bulk-archive,verify,onboard}.md`
en `prompts` bajo el `CODEX_HOME` efectivo o `~/.codex` cuando no esté definido.
No cambies `HOME` ni `CODEX_HOME` para sortear esta comprobación. Si existen y
su migración global no está dentro del alcance autorizado, o no puedes comprobarlo,
deja ese `init` pendiente antes de escribir el puntero del consumidor e informa
los archivos afectados. Una integración local no autoriza esa limpieza global.

Genera las integraciones que falten con la CLI oficial, desde esa raíz:

```powershell
openspec init --tools "claude,codex" --profile core --no-animation
```

En PowerShell conserva las comillas. En la ejecución real sustituye `openspec`
por el ejecutable compatible comprobado para esta operación. Entre las versiones
evaluadas, usa 1.14.3 para inicializar un consumidor con `store:`. No uses
`--force` ni `--language` sobre un consumidor. No crees `openspec/specs/` o
`openspec/changes/` allí.

Para obtener skills y comandos sin cambiar preferencias persistentes, ejecuta
`init` en un proceso con `XDG_CONFIG_HOME` temporal, inicialmente vacío y fuera
de los repositorios. En ese mismo entorno aislado ejecuta primero
`config set delivery both` con la CLI comprobada: no dependas del valor por
defecto, pues la migración puede inferirlo de integraciones existentes. Mantén
`XDG_DATA_HOME` y el registro del usuario que acabas de utilizar. Si modificas
variables en la sesión, conserva los valores originales y restáuralos con
`finally`, incluso ante un error. No cambies `delivery` o `defaultStore` en la
configuración persistente del usuario. El directorio temporal no se versiona.

En una reejecución, omite `init` si las integraciones existentes satisfacen el
perfil y los clientes solicitados, con sus instrucciones y capacidades verificadas.
Comprueba archivos y contenido, no sólo directorios. `generatedBy` identifica su
procedencia; una diferencia con la CLI efectiva no obliga a regenerar. No alternes
las integraciones al cambiar entre ejecutables compatibles. Si faltan archivos,
comprueba el efecto de `init` sobre los existentes antes de ejecutarlo; no prometas
que la CLI escribirá únicamente los ausentes. Conserva adaptaciones y cambios
locales. Si el comando reemplazaría contenido ajeno o una actualización no
solicitada, informa ese límite y deja pendiente la integración afectada.

## 5. Alinea las instrucciones y verifica

Aplica las escrituras de instrucciones sólo a consumidores compatibles cuya
conexión al S0 elegido esté comprobada. Los consumidores bloqueados conservan
también sus instrucciones, sin añadirles el bloque de otra conexión.
En el `AGENTS.md` de cada consumidor conectado incorpora este bloque,
reemplazando sólo el ID:

```text
<!-- s0-connection:start -->
El contexto y las especificaciones compartidas de este sistema están en el S0 <id>.
Comprueba el ejecutable OpenSpec y usa las capacidades que requiere la tarea.
Consulta la compatibilidad y las instrucciones vigentes del S0 resuelto.
Desde esta raíz, ejecuta openspec context --json y lee root.path.
Antes de planificar, lee AGENTS.md y context/project.md en esa raíz resuelta.
Mantén las specs y los artefactos OpenSpec allí; el código y sus tests van en
los repositorios afectados. Lee las skills propias desde la raíz S0 cuando
corresponda; registrar el store no las instala en este consumidor.
<!-- s0-connection:end -->
```

Créalo si falta, añade el bloque si no existe y actualiza sólo ese bloque en
reejecuciones. Conserva las convenciones, contenido y modificaciones ajenas.
Para Claude crea `CLAUDE.md` con `@AGENTS.md` si falta; si ya existe, preserva su
contenido y añade esa importación sólo si aún no carga las instrucciones locales.
Revisa las instrucciones anidadas pertinentes y corrige referencias de conexión
obsoletas dentro del alcance, sin reescribir reglas de producto por suposición.
Si un archivo inaccesible o un conflicto impide esa alineación, informa el límite.

Desde el S0 ejecuta `store doctor <id>` y `status --all --store <id>`. Desde cada
consumidor ejecuta `context --json` y `status --all`: la raíz debe ser exactamente el
S0 elegido. Comprueba los punteros conservados, las integraciones esperadas y
la ausencia de specs/changes locales. Revisa diferencias y archivos nuevos con
Git y `git diff --check`; no hagas stage para obtener el diff de archivos nuevos.
Actualiza el estado de las copias del índice: `connected` sólo tras verificar
su resolución e integraciones, `blocked` si la conexión está pendiente. Conserva
el SHA base y distingue los cambios de integración de otras modificaciones locales.


Al terminar, recuerda las fuentes verificadas según [el localizador común](../SKILL.md#recuerda-fuentes-locales) y entrega el estado por consumidor. Una segunda
ejecución reutiliza identidad, registro, punteros e instrucciones correctos.
Ante un fallo conserva las partes correctas y el trabajo previo; no hagas
rollback general ni elimines fuentes para obtener una comprobación verde.
Discovery se ejecuta sólo si también fue solicitado, después de esta preparación,
con sus propias reglas de revisión del contexto.
