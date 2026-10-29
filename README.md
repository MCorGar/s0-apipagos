# S0 Core — distribución Nuam

S0 Core permite crear repositorios independientes de contexto y especificaciones
basados en OpenSpec. Cada S0 representa un sistema con uno o varios repositorios
de código y comparte skills para PO, DEV y QA. El equipo prepara el sistema una
vez y publica sus cambios por Git; después, sus integrantes utilizan ese mismo S0.

La fuente oficial de los métodos comunes es
[`nuamx/nuam-ia-arq-sdd-openspec`, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
Su catálogo se entrega vacío para completar al adoptar cada sistema.
La procedencia de entregas anteriores se conserva en [VALIDATION.md](VALIDATION.md).

## Elige tu recorrido

| Tu situación | Siguiente paso |
| --- | --- |
| Recibiste el S0 que tu equipo ya preparó | [Obtén la revisión y empieza a usarlo](INSTALLATION.md#join-team); no crees otro S0 |
| Vas a adoptar S0 en un producto existente | [Crea desde plantilla, clona y conecta el código](INSTALLATION.md#existing-system) |
| Vas a comenzar un producto sin código | [Prepara el S0 y define el contexto inicial](INSTALLATION.md#new-system) |

Si este repositorio ya corresponde a un sistema preparado, comienza por
`context/project.md` y el [playbook de PO, DEV y QA](PLAYBOOK.md).
PO y QA pueden leer, refinar y preparar casos desde el S0 sin instalar OpenSpec
ni descargar todos los repositorios de código.
Para consultar código existente, [verifica o recuerda sus fuentes](INSTALLATION.md#source-access).
Instalar integraciones en un consumidor es una acción explícita. OpenSpec 1.13.2
y 1.14.3 conviven según [las capacidades comprobadas](INSTALLATION.md#cli-compatibility).

## Visor incluido para VS Code

El repositorio incluye [OpenSpec Viewer Base 0.9.0](tools/openspec-viewer/openspec-viewer-0.9.0.vsix)
y su [manifiesto de procedencia](tools/openspec-viewer/openspec-viewer-0.9.0.manifest.json).
Permite consultar contexto, mapa documental de componentes, specs y cambios.
La instalación es manual mediante **Instalar desde VSIX…**; consulta
[instalación, actualización y selección del S0](INSTALLATION.md#viewer).
`connect-project` sigue dedicado a conectar proyectos y no instala extensiones.

## Conectar un S0 recién clonado

Después de [crear tu copia independiente desde el Core oficial](INSTALLATION.md#existing-system),
abre su raíz con el agente y escribe en el chat:

```text
Lee AGENTS.md y usa la skill connect-project de este S0.
Este S0 corresponde a [nombre y propósito del sistema].
Puedes configurar este S0 y estos repositorios: [rutas locales o URLs Git con rama opcional].
Para las descargas, usa [carpeta de trabajo fuera del S0].
Continúa con Project Discovery hasta presentar el borrador de contexto.
```

Esta petición autoriza la adopción e integración. El agente configura las copias
locales y descarga los remotos indicados; puedes
combinar ambos. Sólo pide carpeta de descargas cuando hace falta y la recuerda
en esta máquina. Reconectar conserva las revisiones; actualizarlas requiere una
petición explícita. Revisa el borrador antes de que Discovery guarde contexto y
publica los diffs según el proceso de tu equipo.
Los [requisitos y pasos completos](INSTALLATION.md#requirements) están en la guía.

Cuando el equipo ya preparó el sistema, puede mantener sus URLs Git en
[repositories.yaml](repositories.yaml). Cada integrante indica sus clones sin
editar ese catálogo compartido:

```text
Usa connect-project de este S0 para verificar y recordar todos los repositorios del catálogo.
Mis clones están en [carpeta base]. Conserva sus ramas y cambios.
Informa los que falten; no los descargues.
```

También puedes seleccionar IDs e indicar rutas por componente. La skill verifica
y recuerda esas ubicaciones sólo en tu estación; consulta
[catálogo y rutas personales](INSTALLATION.md#repository-catalog).

## Qué contiene el S0

- `context/`: conocimiento del sistema y fuentes, con `project.md` como índice.
- `repositories.yaml`: catálogo compartido inicialmente vacío; el equipo completa
  IDs, URLs Git y ramas de referencia, sin rutas personales.
- `openspec/specs/` y `openspec/changes/`: comportamiento vigente, propuestas e historial.
- `AGENTS.md`, `.agents/` y `.claude/`: instrucciones e integraciones para agentes.
- `.openspec-store/store.yaml` y `openspec/config.yaml`: identidad y configuración.
- `core-manifest.json` y `scripts/compare-core.py`: clasificación y comparación
  de los archivos compartidos frente a una revisión concreta del maestro.

El código y sus tests permanecen en los repositorios consumidores. Cada S0 tiene
su propio historial; las mejoras de la plantilla se adoptan de forma selectiva.
Jira es opcional y no se exigen documentos adicionales por rol.

El template es la fuente de los métodos comunes; cada instancia conserva sus
datos y reglas particulares. Al incorporar una revisión, registra su commit y
las excepciones intencionales en `core-adoption.json`. El
[procedimiento de mantenimiento](INSTALLATION.md#core-maintenance) compara sin
copiar archivos ni actualizar repositorios automáticamente.

<a id="trabajar-con-las-skills"></a>
## Uso y referencias

Codex y Claude utilizan las mismas fuentes propias; otros agentes pueden leerlas.
El cliente y el modelo se eligen aparte. Consulta las [invocaciones de las
skills](PLAYBOOK.md#skills) y cómo [seleccionar la copia local](INSTALLATION.md#local-skills).

| Documento | Para qué leerlo |
| --- | --- |
| [INSTALLATION.md](INSTALLATION.md) | Preparar el entorno, incorporarse al equipo o diagnosticar la conexión |
| [PLAYBOOK.md](PLAYBOOK.md) | Trabajar por rol, elegir skills y revisar resultados |
| [VALIDATION.md](VALIDATION.md) | Mantener el core: comprobaciones, evidencia y pendientes |
| [CORE_OVERVIEW.md](CORE_OVERVIEW.md) | Compartir con otra IA un resumen fechado de arquitectura, capacidades y límites |

Las reglas operativas comunes están en [AGENTS.md](AGENTS.md) y cada método en
su `SKILL.md`. El overview es una fotografía de la revisión que indica, no otro
procedimiento que debas seguir para instalar o usar el S0.
