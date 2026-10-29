# Instrucciones comunes de S0 Core

Este repositorio comparte contexto, especificaciones y cambios OpenSpec entre
personas y agentes. No fija un proveedor ni un modelo. Usa el mismo contenido y
las mismas reglas funcionales con cualquier cliente que pueda leer los archivos.

## Fuentes y raíz de trabajo

- Antes de ejecutar workflows OpenSpec, identifica el ejecutable y su versión.
  Usa las capacidades necesarias para la tarea según
  [la matriz de compatibilidad](INSTALLATION.md#cli-compatibility). 1.13.2 y 1.14.3
  pueden convivir; no actualices una instalación sólo por su número. Mantén el
  ejecutable elegido durante la operación y registra versión y comando junto al
  resultado. Si falta una capacidad, limita esa operación y usa una instalación
  compatible cuando esté disponible, sin cambiar PATH permanentemente.
- Leer, refinar o preparar casos desde un S0 explícitamente identificado no
  requiere CLI ni integración de los repositorios de código. Las fuentes pueden
  ser locales, remotas o mixtas; identifica revisión, archivos y límites de acceso.
- Lee `context/project.md` cuando la tarea requiera conocimiento del sistema.
  Las reglas y el schema están en `openspec/config.yaml`.
- Cada instancia S0 corresponde a un sistema con uno o varios repositorios de
  código. Usa el mapa de componentes del contexto y, cuando tenga entradas,
  `repositories.yaml` para identificar remotos y ramas de referencia. Consulta
  sólo las entradas pertinentes. Es una extensión opcional de S0, no
  configuración de OpenSpec ni autorización para clonar o modificar repositorios.
- `openspec/specs/` describe lo vigente; `openspec/changes/` contiene propuestas
  e historial. Distingue una propuesta activa de un requisito consolidado.
- Respeta el S0 canónico de cada subsistema. Si tiene otro S0, referencia sus
  requisitos o contratos y limita aquí el cambio al alcance de este sistema;
  no dupliques sus especificaciones internas. Un cambio en ambos S0 debe
  identificar sus fuentes, límites y acciones autorizadas.
- En un consumidor con `store:`, resuelve la raíz con `openspec context --json`.
  Lee el contexto y los artefactos de esa raíz. Si no se resuelve, comunica la
  limitación sin crear specs locales ni elegir un sistema vecino.
- Código y tests ejecutables viven en los repositorios consumidores autorizados.

## Fuentes locales de esta estación

El equipo mantiene IDs, URLs Git y ramas de referencia en `repositories.yaml`;
la plantilla entrega ese catálogo vacío. Cada persona indica a `connect-project`
la carpeta base de sus clones o rutas por componente. La skill verifica los remotos
y recuerda únicamente fuentes comprobadas cuando se solicita prepararlas. Las rutas expresas tienen prioridad;
si se indica una base, no elige copias recordadas fuera de ella. El catálogo no
guarda rutas personales, no cambia ramas locales ni acredita código actualizado.
Si faltan fuentes, identifica los IDs y remotos pertinentes; conocer una URL no
equivale a tener acceso a su código. En cloud la conexión se comprueba dentro de
ese entorno, sin reutilizar rutas de otra estación.

Cuando necesites código, usa las rutas expresas de la petición o consulta el
localizador opcional de este S0: `git rev-parse --git-path s0-local-sources.json`,
ejecutado desde su raíz. Resuelve una salida relativa desde esa misma raíz;
no presupongas que `.git` es una carpeta. Es metadata Git local de S0, no
configuración de OpenSpec ni contenido compartido con otros desarrolladores.

El JSON usa `version: 1`, `s0: {id, root}` y `repositories: [{path, remote}]`.
Las rutas son absolutas y reales; `remote` es el `origin` registrado sin
credenciales, o `null` cuando no existe. Comprueba estructura, ID y raíz del
propietario contra este S0 antes de usar sus entradas. Un archivo inválido o
ajeno se informa y conserva; no adoptes sus rutas ni lo repares al analizar.

Selecciona sólo los componentes pertinentes al alcance usando el mapa del contexto.
Para cada entrada comprueba raíz Git exacta y `origin`. Ser una fuente de código
no exige un puntero `store:` ni instalar integraciones. Comprueba la resolución
hacia este S0 con `openspec context --json` cuando se solicita integrar ese
consumidor; una asociación previa se conserva y puede impedir la integración
sin impedir la consulta del código. Compara rutas reales; dos clones del
mismo remoto siguen siendo fuentes distintas. Una ruta ausente o una identidad
distinta queda pendiente; continúa con las fuentes válidas sin sustituirla por
otro proyecto. Si la selección entre copias válidas es ambigua, pide la copia
que se quiere analizar.
Si no puedes comprobar el acceso o la integración solicitada, declara ese límite.

Rama, HEAD y cambios locales se observan al consultar código; no están fijados
por el localizador. Prioriza las copias locales verificadas: un error del proveedor
remoto no demuestra que falte el código local. Consultar no autoriza actualizar
Git, ejecutar producto ni escribir el localizador; su mantenimiento corresponde
a `connect-project`. Si falta, usa las rutas aportadas o pide ubicación sólo cuando
el código sea necesario. Refinamiento y QA pueden continuar con contexto y specs.

Las fuentes remotas se consultan con herramientas autorizadas que permitan
identificar repositorio, referencia y archivos. Una URL o un README no acredita
acceso al código completo. La lectura remota no exige un clon ni rutas ficticias
en el localizador. Descargar o actualizar fuentes requiere esa intención en la
petición; conectar acceso no instala OpenSpec en el producto.

## Capacidades compartidas

- Inicializar un S0 nuevo o existente con preguntas guiadas: [.agents/skills/initialize-s0/SKILL.md](.agents/skills/initialize-s0/SKILL.md).
- Conectar un proyecto: [.agents/skills/connect-project/SKILL.md](.agents/skills/connect-project/SKILL.md).
- Contextualización opcional: [.agents/skills/project-discovery/SKILL.md](.agents/skills/project-discovery/SKILL.md).
- Refinamiento PO: [.agents/skills/refine-user-story/SKILL.md](.agents/skills/refine-user-story/SKILL.md).
- Preparación QA: [.agents/skills/prepare-tests/SKILL.md](.agents/skills/prepare-tests/SKILL.md).
- Revisión de PR: [.agents/skills/review-pr/SKILL.md](.agents/skills/review-pr/SKILL.md).

Lee la skill correspondiente al realizar esa tarea, aunque el cliente no la
descubra automáticamente. Resolver un store no instala sus skills ni carga sus
instrucciones en una sesión iniciada en otro repositorio. Si no puedes leer la
fuente requerida, identifica el acceso faltante sin inventar su contenido.

Consultar o preparar casos no escribe ni ejecuta pruebas por defecto. Respeta
las acciones ya autorizadas por el usuario y sus destinos; Jira es opcional.
No atribuyas aprobaciones humanas ni ejecuciones a archivos o casos preparados.
Redacta en español y conserva trazabilidad con fuentes y revisiones identificables.

## Mantenimiento de la plantilla

El maestro oficial es
[`nuamx/nuam-ia-arq-sdd-openspec`, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
Las adopciones registran un commit publicado en ese repositorio. Las referencias
históricas de validación y la procedencia de herramientas externas no cambian
esa autoridad.

Usa inglés para nombres de carpetas, archivos propios, skills y claves de
inventario. Conserva los nombres oficiales de OpenSpec. El idioma de los nombres
técnicos no cambia la redacción en español de instrucciones y resultados.

Mantén las reglas comunes en este archivo y los métodos propios sólo en sus skills
canónicas de `.agents/skills/`. `CLAUDE.md` y las entradas propias de `.claude/`
son puentes a esas fuentes. No necesitan enlaces simbólicos ni scripts de copia.
`connect-project` distingue verificar o recordar fuentes de adoptar el S0 e
integrar consumidores. La integración usa la CLI oficial cuando forma parte de
la petición; la consulta conserva productos y asociaciones. Discovery se ejecuta
cuando se solicita, incluso si ya está incluido en la petición de preparación;
si no se solicitó, `initialize-s0` lo ofrece al terminar, sin ejecutarlo.
Project Discovery reúne su método completo y el verificador de `scripts/` en
`.agents/skills/project-discovery/`; Claude utiliza un puente a esa misma fuente.
Es independiente y no es un paso obligatorio de OpenSpec;
documentar contexto no autoriza cambiar configuración ni artefactos OpenSpec.
Los workflows `openspec-*` son generados por OpenSpec; actualízalos con la CLI
comprobada, sin editarlos a mano. Valida los artefactos con
`openspec validate --all --strict --no-interactive`; eso no ejecuta tests de producto.

El maestro define métodos reutilizables, no rutas, componentes ni políticas de
un producto. [core-manifest.json](core-manifest.json) distingue archivos comunes,
documentos que requieren revisión y datos de instancia. Las mejoras comunes se
preparan y validan primero en el maestro. Una instancia incorpora una revisión
concreta mediante diff selectivo y registra su procedencia y excepciones en
`core-adoption.json`, según [mantenimiento](INSTALLATION.md#core-maintenance).
Ese registro es documentación de adopción, no configuración de OpenSpec ni una
autorización para sobrescribir archivos. Conserva identidad, contexto, catálogo,
specs, historial y trabajo local; compara antes de actualizar y revisa las
excepciones declaradas. No propagues cambios automáticamente a otras instancias.
