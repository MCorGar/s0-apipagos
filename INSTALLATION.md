# Preparar o incorporarse a un S0

El maestro oficial es
[`nuamx/nuam-ia-arq-sdd-openspec`, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
Para consultar o clonar esta base, selecciona expresamente `development`: la rama
predeterminada de este remoto es `production`. El recorrido siguiente obtiene
`development` y conecta la copia al repositorio independiente de tu sistema.

Elige el recorrido que corresponde a tu situación:

| Situación | Recorrido |
| --- | --- |
| Vas a adoptar S0 en un producto existente, con uno o varios repositorios | [1. Conectar el sistema](#existing-system) |
| Vas a comenzar un proyecto sin código | [2. Preparar un S0 nuevo](#new-system) |
| El equipo ya preparó el S0 y vas a utilizarlo | [3. Incorporarte al equipo](#join-team) |
| Sólo necesitas comprobar o recordar fuentes | [Acceso a fuentes existentes](#source-access) |

La plantilla maestra crea instancias independientes. Cada S0 comparte contexto,
specs y cambios de un sistema; sus repositorios de código son los consumidores.
Los ejemplos usan nombres y rutas ficticios. Los prompts van en el chat del agente.

<a id="requirements"></a>
## Herramientas según tu tarea

| Tarea | Qué necesitas |
| --- | --- |
| Crear el repositorio independiente del S0 | Cuenta con acceso al Core y permisos para crear el repositorio del sistema |
| Clonar o verificar clones | Git y agente con acceso a las carpetas |
| Adoptar S0 e integrar consumidores | CLI con `store`, `context` e `init`; versiones y alcance comprobados en la matriz de compatibilidad |
| Descargar fuentes remotas | Acceso Git HTTPS o SSH a esos repositorios y una carpeta de trabajo externa al S0 |
| Leer, refinar historias o preparar casos desde el S0 | Editor o agente con acceso al S0; no requiere CLI OpenSpec |
| Ejecutar workflows oficiales | CLI con los comandos y campos que necesita el workflow y acceso a las fuentes pertinentes |
| Guardar contexto mediante Discovery | Git y Python >=3.10 para verificar el alcance |
| Revisar PR | Acceso al PR o snapshot y código de su revisión; Node.js >=20 para verificar los informes; CLI con `context` si se resuelve un store desde un consumidor |
| Ejecutar producto o sus tests | Herramientas, entorno, datos y permisos del producto |

Cuando la petición incluye instalar herramientas, puede instalarse la versión
recomendada 1.14.3 mediante npm con Node.js >=20.19.0. Una instalación 1.13.2
compatible con la tarea puede reutilizarse. El binario autónomo no requiere Node.
La skill no instala Git, Node, Python ni clientes de IA. Si falta una herramienta,
indica qué fase queda pendiente.

Instaladores oficiales: [Git](https://git-scm.com/install/windows),
[Node.js](https://nodejs.org/en/download), [OpenSpec](https://openspec.dev/docs/installation),
[Codex](https://learn.chatgpt.com/docs/quickstart) y
[Claude Code](https://code.claude.com/docs/en/quickstart).

<a id="existing-system"></a>
## 1. Conectar un sistema existente

**Crear repositorio → copiar el Core oficial → pedir adopción e integración → revisar diffs.**
Si ya creaste y clonaste tu S0 independiente, continúa en el paso 3.

### Paso 1. Crea el S0 en GitHub

1. Consulta la revisión de [Core oficial, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
2. Crea un repositorio vacío para tu sistema con el propietario, nombre
   (por ejemplo, `s0-my-system`) y visibilidad correspondientes.
3. No inicialices README, licencia ni `.gitignore`: recibirán los del Core.

La persona realiza esta acción. Si usas **Use this template**, comprueba antes
que copiará la revisión oficial elegida; copiar sólo la rama predeterminada
actual toma `production`, no la base `development` de esta guía.

### Paso 2. Obtén el Core y conecta el repositorio nuevo

En una carpeta separada del código, sustituye la URL de ejemplo por la del
repositorio vacío recién creado. En PowerShell:

```powershell
git clone --branch development --single-branch https://github.com/nuamx/nuam-ia-arq-sdd-openspec.git s0-my-system
Set-Location s0-my-system
git remote set-url origin https://github.com/your-team/s0-my-system.git
git push -u origin development
```

Esta copia conserva el historial del Core y continúa en un repositorio
independiente. Configura `development` como rama predeterminada del nuevo S0
según el proceso del equipo. Las mejoras futuras del maestro se incorporan
selectivamente; `origin` corresponde desde ahora al sistema.

### Paso 3. Abre el S0 y pide la conexión

Abre con tu agente la raíz que contiene `AGENTS.md`, `context/` y `openspec/`.
En el chat, sustituye nombre, propósito y fuentes. Si ya tienes el código local:

```text
Usa la skill connect-project para adoptar este S0 como my-system.
El producto es [nombre y propósito]. Instala las integraciones OpenSpec para
Codex y Claude en D:\my-system-web y D:\my-system-api.
Continúa con el borrador de contexto de Project Discovery.
```

Para un monorepo indica una sola raíz Git, aunque contenga varios servicios.
Para varios Git, enumera las raíces o una carpeta que los agrupe; el agente
identifica los repositorios dentro de ese límite. Puedes conectar más después.

Si el código está en GitHub, GitLab o Bitbucket, proporciona sus URLs Git:

```text
Usa la skill connect-project para adoptar este S0 e integrar estos consumidores:
- Web: https://github.com/your-team/web.git, rama development.
- API: git@gitlab.com:your-team/api.git, rama main.
Descarga las copias en D:\workspaces y presenta el borrador de Project Discovery.
```

También puedes mezclar fuentes en una petición:

```text
Usa la skill connect-project para adoptar este S0 e instalar las integraciones
en D:\my-system-api y https://github.com/your-team/web.git, rama development.
Descarga lo necesario en D:\workspaces y continúa con el borrador de Discovery.
```

Elige una carpeta de descargas fuera del S0 y que no esté dentro de otro Git.
El agente recuerda ese destino en este clon del S0. Usa el acceso Git disponible;
no necesita tokens en el chat. En una fuente nueva, si omites la rama, resuelve la
predeterminada del remoto. No busca copias por todo el equipo ni descarga fuentes
no solicitadas.

Esta petición de adopción e integración prepara identidad, registro, punteros e
integraciones oficiales para Codex/Claude. Conserva cambios locales y una identidad ya adoptada. Si encuentra
otro store o planificación OpenSpec previa incompatible, informa el conflicto
sin borrarla ni migrarla. Los resultados parciales deben identificar lo pendiente.

### Paso 4. Revisa el contexto y comparte la preparación

Después de configurar, el agente informa las copias, ramas, SHA y cambios locales
observados. Cuando se pidió Discovery, toma entonces su referencia y presenta un borrador con fuentes
y archivos destino. Revisa ese contenido antes de aprobar su escritura. **Sin Python/Git o
una referencia válida, entrega sólo el borrador en conversación y no escribe
archivos de contexto.** Las fuentes inaccesibles se declaran como limitaciones.

Revisa los diffs del S0 y de sus consumidores. `connect-project` deja los cambios
locales, sin stage, commit, push ni PR. Publícalos mediante el proceso del equipo;
después comparte la URL del S0, su ID y el [recorrido de incorporación](#join-team).

<a id="source-access"></a>
### Acceso a fuentes existentes

Si el S0 ya existe y sólo necesitas consultar código, pide verificar o preparar
sus fuentes. La skill distingue esa acción de instalar integraciones en productos:

```text
Usa connect-project para verificar el acceso a [rutas o repositorios y referencias].
Quiero consultar esas fuentes desde este S0. Informa qué archivos y revisiones
puedes leer y cuáles faltan.
```

La verificación sola es de lectura. Para reutilizar ubicaciones locales en otra
sesión, añade «recuerda estas fuentes en este clon del S0». Se guardan en metadata
Git, conservando archivos, ramas y asociaciones OpenSpec de los productos.
Un repositorio con otro store puede ser una fuente de código de este análisis.
La lectura remota usa el acceso autorizado del cliente y no requiere clon ni CLI.
Las URLs y archivos disponibles deben comprobarse en la referencia seleccionada;
no se sustituyen silenciosamente por otra rama o copia.

Preparar fuentes es opcional cuando ya están accesibles. Descargas, actualización
Git, registro del S0 e instalación de integraciones se realizan cuando la petición
incluye esas acciones. Discovery también se solicita, y puede incluirse en la
misma petición sin una confirmación adicional de inicio.

<a id="connect-code"></a>
### Añadir repositorios o actualizar fuentes

Pide a `connect-project` verificar o recordar nuevas fuentes; si quieres instalar
integraciones en ellas, indícalo. Conserva el ID existente; la reejecución reutiliza conexiones correctas y completa lo pendiente
sin buscar automáticamente nuevas revisiones.

Para trabajar con código remoto más reciente, solicítalo expresamente:

```text
Usa la skill connect-project de este S0 para actualizar la fuente Web conectada,
rama development.
Conserva mi copia actual y prepara la revisión reciente en el workspace recordado.
Continúa con Project Discovery hasta presentar el borrador.
```

La actualización prepara otra copia si corresponde y conserva íntegramente la
anterior. Si la revisión no cambió y la copia sigue siendo válida, la reutiliza e
informa sus cambios locales. No hace pull, reset ni cambios de rama sobre tu trabajo.
Para actualizar desde una ruta local necesita un remoto y una rama inequívocos.
Las copias no se eliminan automáticamente; un cambio manual de rama o HEAD en una
copia registrada se informa, sin repararlo silenciosamente.

<a id="repository-catalog"></a>
### Compartir URLs Git y configurar rutas personales

El equipo mantiene [repositories.yaml](repositories.yaml), inicialmente vacío,
con `version: 1` y `repositories: [{id, remote, branch}]`. `id` identifica al
repositorio, `remote` es su URL Git HTTPS/SSH sin credenciales y `branch` es opcional.
Las responsabilidades y relaciones se documentan en `context/project.md`.
Ejemplo ficticio para sustituir por los repositorios reales de la instancia:

```yaml
version: 1
repositories:
  - id: web
    remote: https://example.com/organizacion/web.git
    branch: development
  - id: api
    remote: git@example.com:organizacion/api.git
    branch: main
```

Cada persona puede conectar las entradas que seleccione mediante sus rutas:

```text
Usa connect-project de este S0 para verificar y recordar todos los repositorios del catálogo.
Mis clones están en [carpeta base], incluidos los componentes dentro del coordinador.
Conserva sus ramas y cambios. Informa los que falten; no los descargues.
```

Puedes sustituir «todos» por IDs concretos. Si un componente está en otra ubicación,
indica «Recuerda web del catálogo; mi clon está en [ruta de Web]». La ruta por
componente prevalece; una base indicada limita la búsqueda de los restantes.
Sin base, la skill reutiliza conexiones recordadas válidas y pide ubicación sólo
para las que falten. Si hay varias copias sin selección inequívoca, pide elegir.

Comprueba cada raíz y su remoto, reconociendo HTTPS/SSH del mismo repositorio.
Los componentes seleccionados pueden estar dentro de un coordinador que también
sea Git; no se conectan otros repositorios anidados por inferencia. Las ubicaciones
verificadas se recuerdan en metadata Git local, sin editar el catálogo compartido.

Si faltan clones y quieres obtenerlos, pide «Descarga y recuerda [IDs o todos] del
catálogo en [carpeta fuera del S0 y de otros Git]». Instalar sus integraciones es
una acción adicional que puedes incluir expresamente. La rama del catálogo orienta
nuevas descargas; una rama expresa tiene prioridad. Conectar copias existentes
conserva sus ramas y revisiones. Una petición sólo local no descarga faltantes.

En cloud, usa las copias accesibles o la lectura remota autorizada en ese entorno;
el catálogo no transfiere rutas ni credenciales del PC. Usar el catálogo es opcional:
siguen admitiéndose rutas o URLs expresas. OpenSpec no lo interpreta ni conecta
repositorios por su mera presencia.

<a id="new-system"></a>
## 2. Comenzar un proyecto nuevo, sin código

Crea y clona el S0 siguiendo los pasos 1 y 2 anteriores. Abre su raíz y escribe:

```text
Usa la skill connect-project de este S0.
Adopta y registra este S0 para my-system. El objetivo inicial es [problema y usuarios].
Todavía no hay código ni consumidores. Prepara un borrador de contexto inicial
para revisar, distinguiendo intención de implementación existente.
```

Revisa el borrador y sus destinos antes de guardarlo, con los mismos requisitos
de comprobación del paso 4. Publica la preparación por Git y continúa con el
[playbook](PLAYBOOK.md). No necesitas crear servicios o repositorios vacíos.
Cuando exista código, conecta sus repositorios al mismo S0. Discovery es opcional y
no constituye un requisito previo de OpenSpec.

<a id="join-team"></a>
## 3. Usar un S0 que el equipo ya preparó

1. Obtén la URL del **S0 del sistema** y la rama o revisión que debes consultar.
2. Clona ese repositorio, o descarga su ZIP si sólo necesitas los archivos.
3. Conserva `.agents/` y `.claude/` y abre la raíz que contiene `AGENTS.md`.
4. Continúa con las [skills y recorridos del playbook](PLAYBOOK.md#skills).

Para leer, refinar historias y preparar casos desde esa raíz no necesitas crear
otro S0, registrar el store, instalar OpenSpec ni descargar todos los servicios.
Para clonar una rama concreta puedes usar `git clone --branch branch-to-review URL`,
sustituyendo ambos valores. Con ZIP descarga la revisión acordada; no incluye Git.

Los cambios deben estar publicados para que otros los reciban. Comprueba la
rama/commit al revisar; un clon o ZIP no se actualiza solo. Recibe nuevas revisiones
conservando tu trabajo local.

Si eres DEV y necesitas resolver el store desde código en esta máquina, pide
integrar esos consumidores con `connect-project` desde el S0 con su ID existente
y las rutas o URLs pertinentes.
Para conectar usa un clon Git del S0. Preparará lo que falte conservando su
identidad, contexto, specs y cambios existentes. Por ejemplo:

```text
Usa connect-project para registrar este S0 e instalar las integraciones en
D:\my-system-web y D:\my-system-api. Conserva el contexto y la planificación existentes.
```

Las rutas se recuerdan sólo en tu clon; las de otro desarrollador no viajan con
Git. Conecta una vez por estación y repite al añadir o reubicar fuentes, no antes
de cada historia. Para consultar código basta el recorrido de acceso a fuentes.
Si solicitas un borrador Discovery, se revisa antes de guardarlo.
Si el equipo completó el [catálogo compartido](#repository-catalog), basta
seleccionar sus IDs e indicar tu carpeta base o las rutas particulares.

<a id="local-skills"></a>
## Si el agente encuentra otra skill

Comprueba que usa la entrada del repositorio bajo `.agents/skills/` o su puente
`.claude/skills/`. Una skill personal del mismo nombre puede ser otra versión.
Si no aparece la local, pide leer su `SKILL.md` explícitamente. Por ejemplo,
`connect-project` está en `.agents/skills/connect-project/SKILL.md`, con ruta
relativa a la raíz de ese S0. El descubrimiento y la prioridad dependen del
cliente; otros agentes pueden leer los archivos, pero su integración debe
comprobarse.

Desde un consumidor, `store:` no instala las skills propias ni carga por sí solo
las instrucciones del S0. Resuelve `openspec context --json` y lee `AGENTS.md`,
`context/project.md` y la skill pertinente bajo `root.path`.

<a id="project-discovery"></a>
## Actualizar el contexto después

Pide `project-discovery` con las fuentes y el foco que necesitas revisar.
Documenta propósito, mapa, arquitectura, tecnologías, interfaces e infraestructura
según la evidencia disponible. `context/project.md` es el índice; los demás
archivos son opcionales y se separan sólo cuando aportan valor.

El método de lectura, borrador y aprobación se define en
[Project Discovery](.agents/skills/project-discovery/SKILL.md), junto con la
[organización del contexto](.agents/skills/project-discovery/SKILL.md#context-content)
y sus comprobaciones. El código observado no se convierte automáticamente en specs.

<a id="daily-work"></a>
Para trabajar con historias, cambios y pruebas, continúa en [PLAYBOOK.md](PLAYBOOK.md).

<a id="cli-setup"></a>
## Referencia técnica avanzada

Estos comandos sirven para diagnóstico o configuración manual deliberada.
La primera conexión con el agente sigue el recorrido anterior. Usa el ejecutable
compatible comprobado y la raíz indicada en cada sección.

### Localizar los repositorios locales

Desde el S0, `git rev-parse --git-path s0-local-sources.json` indica el localizador
que `connect-project` mantiene para las raíces locales verificadas. Vive en la
metadata Git, admite repositorios en carpetas distintas y no se publica ni requiere
un inventario compartido. Su contrato y las comprobaciones de lectura están en
[AGENTS.md](AGENTS.md#fuentes-locales-de-esta-estación).

Las ramas y commits pueden cambiar durante el trabajo: el agente comunica la
revisión que consulta. Si mueves un repositorio, conecta su nueva ruta; una ruta
ausente se informa y no se reemplaza silenciosamente. La ausencia del localizador
no impide trabajar con contexto y specs. Es una extensión local de S0, no un
archivo o mecanismo interpretado por OpenSpec.

### Localizar las copias remotas

Cuando se solicitan descargas, `connect-project` recuerda el destino en la configuración Git local del S0:
`git config --local --get s0.sourcesRoot`. Bajo ese workspace mantiene
`.s0-connections/<store-id>.json` con la instancia, fuentes, ramas, rutas, SHA y
estado de sus copias. Es un índice local que el agente contrasta con Git, no
configuración OpenSpec ni evidencia suficiente del contexto. No se publica con
el S0; las fuentes y revisiones pertinentes sí acompañan al contexto aprobado.

### Comprobar la CLI

```powershell
openspec --version
Get-Command openspec -All | Select-Object Source
$s0NpmPrefix = (npm prefix -g).Trim()
& (Join-Path $s0NpmPrefix 'openspec.cmd') --version
```

El prefijo npm aplica si utilizas esa distribución. Si falta la CLI y ya tienes
Node/npm compatibles: `npm install -g @fission-ai/openspec@1.14.3`.
Si el ejecutable efectivo carece de una capacidad necesaria, usa otra instalación
comprobada por su ruta. Para priorizarla sólo en esa terminal:

```powershell
$env:Path = "$s0NpmPrefix;$env:Path"
openspec --version
```

Esto no cambia permanentemente PATH ni afecta procesos ya abiertos. Comprueba
el ejecutable efectivo al comenzar una nueva sesión, según [AGENTS.md](AGENTS.md).

<a id="cli-compatibility"></a>
### Compatibilidad por capacidades

El equipo puede usar 1.13.2 y 1.14.3 según las operaciones comprobadas en
[VALIDATION.md](VALIDATION.md#portable-onboarding). 1.14.3 se recomienda para
nuevas instalaciones; otra versión no se rechaza sólo por su número. Comprueba
las opciones y campos que requiere la tarea cuando no estén verificados, y
mantén el mismo ejecutable durante la operación.

| Necesidad | Criterio |
| --- | --- |
| Leer fuentes, refinar o preparar casos desde S0 | Sin CLI; acceso efectivo a archivos y referencias |
| Resolver stores y consultar planificación | `context`, `store`, `list`, `status`, `instructions` y JSON esperado |
| Registrar un S0 | Registro e identidad comprobados con 1.13.2 y 1.14.3 |
| Instalar integraciones en un consumidor con `store:` | Comprobado con 1.14.3; 1.13.2 rechaza ese `init`, aunque puede consultar consumidores ya integrados |
| Ejecutar un workflow | Cumplir sus comandos, campos y límites de `actionContext`; un campo ausente no concede permisos |
| Validar artefactos | Registrar versión, comando y revisión; los diagnósticos pueden diferir entre versiones |
| Resolver automáticamente S0 desde Viewer 0.9.0 | CLI >=1.14.3 y <2.0.0; con 1.13.2 seleccionar manualmente la carpeta S0 |

Los workflows distribuidos conservan `generatedBy: "1.14.3"` como procedencia.
Alternar ejecutables no requiere regenerarlos ni permite editarlos manualmente.
Una validación satisfactoria en una versión no borra observaciones de otra ni
acredita aceptación funcional. Para reproducir una evidencia usa su versión.
Si sólo está disponible 1.13.2, conserva el puntero y deja pendiente la instalación
de integraciones; puedes continuar con las consultas compatibles. Si existe otra
CLI que soporte esa operación, selecciónala antes de preparar el consumidor.
No retires `store:` ni crees planificación local para sortear el rechazo.
En el consumidor de prueba, `status` de 1.13.2 limita `allowedEditRoots` al S0;
1.14.3 incluye también el consumidor. Resolver correctamente el store no basta
para implementar en el producto: comprueba ese alcance y selecciona una CLI que
admita la operación solicitada, además de contar con autorización sobre el código.

### Registrar una identidad existente

Desde la raíz de un S0 ya adoptado:

```powershell
Get-Content -LiteralPath .openspec-store/store.yaml
openspec store list
openspec store register .
```

Un ID resuelve una ruta por registro. Ante un conflicto, conserva la asociación
existente. `register --id` no renombra un store que ya tiene otra identidad.

Sólo en un clon nuevo comprobado de la plantilla, con remoto propio y sin contenido
de producto, puede retirarse el marcador heredado para crear la identidad oficial.
Conserva antes una copia del marcador fuera del repositorio y comprueba que el ID
está disponible; restaura esa copia si falla el registro:

```powershell
$s0Id = 'my-system'
Remove-Item -LiteralPath .openspec-store/store.yaml
openspec store register . --id $s0Id --yes
openspec store doctor $s0Id
```

### Conectar un consumidor sin planificación previa

Desde su raíz Git, con el S0 registrado. Una configuración o planificación previa
requiere revisión; este bloque no la migra:

```powershell
if ((Test-Path openspec/config.yaml) -or (Test-Path openspec/config.yml) -or
    (Test-Path openspec/specs) -or (Test-Path openspec/changes)) {
    throw 'Existe OpenSpec previo: requiere revisión.'
}
New-Item -ItemType Directory -Path openspec -Force | Out-Null
Set-Content -LiteralPath openspec/config.yaml -Value 'store: my-system' -Encoding utf8
openspec init --tools "claude,codex" --profile core --no-animation
openspec context --json
```

Conserva las comillas en PowerShell. La preferencia `delivery` controla skills y
comandos; `openspec config get delivery` permite consultarla. `connect-project`
usa preferencias temporales para generar ambos sin cambiar las persistentes.
La raíz resuelta debe ser el S0; no deben aparecer specs/changes en el consumidor.
`members: []` es normal sin Worksets. Revisa también instrucciones raíz y anidadas:
`init` no reconcilia sus referencias antiguas por ti.

<a id="viewer"></a>
## Visor de contexto, specs y cambios

Incluimos [OpenSpec Viewer Base 0.9.0](tools/openspec-viewer/openspec-viewer-0.9.0.vsix),
con identidad `fdelvalle01.openspec-viewer`, y su
[manifiesto](tools/openspec-viewer/openspec-viewer-0.9.0.manifest.json).
Su fuente se mantiene en [sdd-openspec-view](https://github.com/fdelvalle01/sdd-openspec-view).
Es un paquete Base de lectura, sin asistente IA. Requiere VS Code de escritorio
1.110.0 o posterior; leer el S0 directamente no requiere Git ni CLI OpenSpec.

1. En VS Code abre **Extensiones → … → Instalar desde VSIX…** y selecciona
   `tools/openspec-viewer/openspec-viewer-0.9.0.vsix` de tu copia del S0.
2. Ejecuta **Developer: Reload Window** al instalar o actualizar. La actualización
   conserva los comandos y las preferencias `sddWorkspaceViewer`.
3. Abre la raíz del S0 y ejecuta **OpenSpec Viewer: Abrir visor**. Desde otra
   carpeta, usa **Elegir carpeta S0** o **Abrir S0 por ruta**.

El proyecto entra por `context/project.md`; su mapa de componentes permanece
documentado en Markdown. No se exige inventario JSON. El visor conserva `docs/`
y descriptores de S0 anteriores; `repositories.yaml`, `jira.md` y `revision.md`
son opcionales. Las casillas marcadas no acreditan pruebas ni aceptación.

Desde un consumidor con `store:`, el visor consulta `openspec context --json`
con una CLI compatible, después de comprobar su versión, y exige un workspace
confiable para ejecutar esa consulta. Viewer 0.9.0 admite CLI >=1.14.3 y <2.0.0
para esa resolución; con 1.13.2 puedes elegir manualmente la carpeta S0.
Varios consumidores del mismo S0 se agrupan; si hay varios sistemas, selecciona
el que quieres leer. Si falta la CLI, es incompatible o no resuelve el store,
el visor explica la limitación y permite elegir manualmente el S0. En modo
restringido puedes continuar con la lectura directa.

Para verificar el archivo antes de instalarlo, ejecuta desde la raíz del S0:

```powershell
$viewerManifest = Get-Content tools/openspec-viewer/openspec-viewer-0.9.0.manifest.json -Raw | ConvertFrom-Json
$viewerHash = (Get-FileHash tools/openspec-viewer/openspec-viewer-0.9.0.vsix -Algorithm SHA256).Hash.ToLowerInvariant()
if ($viewerHash -ne $viewerManifest.package.sha256) { throw 'El hash del VSIX no coincide con su manifiesto.' }
```

La instalación sigue siendo una acción manual. `connect-project` no instala ni
actualiza extensiones. El visor sólo consulta archivos; los workflows OpenSpec
y el código continúan en sus herramientas habituales. Consulta los resultados
y límites registrados en [VALIDATION.md](VALIDATION.md#viewer).

<a id="maintenance"></a>
## Mantenimiento

<a id="core-maintenance"></a>
### Incorporar una revisión del maestro

El [maestro oficial en `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development)
mantiene las capacidades comunes. [core-manifest.json](core-manifest.json)
clasifica los archivos para actualizar cada instancia con una comparación explícita:

| Clase | Tratamiento |
| --- | --- |
| `shared` | Skills, workflows, puentes, herramientas y archivos de soporte comunes; las diferencias requieren explicación o actualización |
| `review` | Instrucciones, guías y configuración que combinan reglas comunes y personalización; revisar sus diferencias antes de incorporar |
| `instance` | Identidad, contexto, catálogo, specs e historial; su contenido pertenece al sistema |

1. Prepara y valida la mejora común en el Core oficial, sin datos de un producto.
2. Identifica su commit publicado en `development` y comprueba el estado local de la instancia.
3. Compara y revisa los cambios, conservando contenido propio y trabajo previo.
4. Incorpora sólo lo acordado y registra el commit y las excepciones intencionales
   en `core-adoption.json` de la instancia. Comprueba otra vez el resultado.

El registro tiene este formato; sustituye el commit por los 40 caracteres de la
revisión realmente incorporada. No se distribuye un registro de adopción rellenado
desde el maestro ni se incluyen rutas personales:

```json
{
  "version": 1,
  "source": {
    "repository": "https://github.com/nuamx/nuam-ia-arq-sdd-openspec",
    "commit": "<SHA completo de la revisión incorporada>"
  },
  "overrides": []
}
```

Una excepción usa `{ "path": "ruta/relativa", "reason": "motivo de la adaptación" }`.
Debe identificar un archivo concreto: no declara equivalente su contenido ni
oculta la diferencia. Revisa si sigue siendo necesaria al adoptar otra revisión.
Las diferencias en documentos `review` también requieren revisión humana.

El comparador es de lectura y requiere Python >=3.10 y Git. Ambas rutas deben
ser raíces Git exactas con al menos un commit. Desde la copia del Core,
sustituye rutas y `CORE_COMMIT`:

```powershell
py -3 -B scripts/compare-core.py --core C:\sources\nuam-ia-arq-sdd-openspec --instance D:\systems\s0-my-system --revision CORE_COMMIT --json
```

Sin `--revision` compara los archivos actuales del maestro y declara ese origen;
no los presenta como una revisión publicada. Informa archivos iguales, modificados,
ausentes, adicionales y excepciones. Código 0: sin divergencias compartidas no
declaradas; 1: hay divergencias compartidas; 2: entrada o metadata inválida.
Ninguno acredita pruebas funcionales ni sustituye la revisión de documentos.
El comando no descarga, copia, registra ni sincroniza repositorios.

Adopta mejoras del maestro mediante un PR selectivo, conservando identidad,
contexto, specs e historial del sistema. `git pull` recibe cambios del repositorio;
`openspec update` regenera integraciones oficiales. Revisa primero
`openspec update --dry-run`; no edites los workflows generados a mano.

Al migrar nombres antiguos, usa `context/project.md`, `refine-user-story`,
`prepare-tests`, `repositories.yaml` y `VALIDATION.md`; ajusta puentes y enlaces
conservando los datos propios. No hace falta crear un inventario para migrar.

Consulta [VALIDATION.md](VALIDATION.md) para comprobar una actualización y conocer
lo pendiente. Referencias oficiales: [Stores](https://openspec.dev/docs/stores),
[CLI](https://openspec.dev/docs/cli), [Profiles](https://openspec.dev/docs/profiles) y
[configuración](https://openspec.dev/docs/configuration/config-yaml).
