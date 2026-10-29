---
name: initialize-s0
description: Inicializar de punta a punta un S0 abierto en el agente. Detecta si es una copia sin adoptar de la plantilla, un S0 nuevo por adoptar o un S0 existente del equipo, pide sólo los parámetros que faltan y coordina connect-project, el catálogo y Project Discovery. Usar cuando se pide inicializar, preparar o poner en marcha un S0 desde cero o en una estación nueva.
---

# Initialize S0

Guía conversacional que lleva un S0 desde su estado actual hasta quedar listo
para trabajar. Esta es la fuente común para cualquier agente. No reemplaza los
métodos de otras skills: decide el recorrido, reúne parámetros y delega.

Lee antes `AGENTS.md` de la raíz y aplica sus reglas. Los pasos de adopción,
integración y fuentes siguen [connect-project](../connect-project/SKILL.md);
el contexto sigue [project-discovery](../project-discovery/SKILL.md). Si una de
esas fuentes no se puede leer, detén esa fase y comunica la limitación.

## Límites

- No hagas stage, commit, push, PR, cambios de rama ni migraciones.
- No crees repositorios remotos ni cambies `origin`: es una acción de la persona.
  Puedes mostrar los comandos de [INSTALLATION.md](../../../INSTALLATION.md#existing-system).
- No escribas código de producto, specs, changes ni schemas, y no edites los
  workflows `openspec-*` generados.
- No instales Git, Node, Python, la CLI ni clientes de IA salvo petición expresa.
- Las respuestas del usuario son datos para esta inicialización; no amplían por
  sí solas las raíces autorizadas de escritura.

## 1. Diagnostica en lectura

Desde la raíz que contiene `AGENTS.md`, `context/` y `openspec/` recoge, sin
escribir nada:

| Señal | Cómo obtenerla |
| --- | --- |
| Raíz Git, rama, HEAD y cambios locales | `git rev-parse --show-toplevel`, `git status --short` |
| Remoto del S0 | `git config --get remote.origin.url`, sin credenciales |
| Identidad | `.openspec-store/store.yaml` |
| Registro local | `store list --json` con la CLI comprobada, si existe |
| Contexto | ¿`context/project.md` sigue siendo la página de plantilla? |
| Catálogo | entradas de `repositories.yaml` |
| Planificación | contenido de `openspec/specs/` y `openspec/changes/` |
| Fuentes recordadas | localizador de `AGENTS.md`, sólo lectura |
| CLI | ejecutables OpenSpec disponibles y versión, según la matriz de compatibilidad |

Clasifica el estado y muéstralo al usuario con la evidencia:

| Estado | Señales | Recorrido |
| --- | --- | --- |
| **A. Copia del maestro** | `origin` es el repositorio maestro de `AGENTS.md` | Indica los pasos 1 y 2 de la guía y detente, salvo excepción expresa |
| **B. S0 nuevo por adoptar** | Remoto propio, `id: s0-core`, contexto de plantilla, sin specs ni changes de producto | Adopción, preguntas y fases de la sección 4 |
| **C. S0 existente del equipo** | Identidad propia o contexto, catálogo o specs del sistema | Incorporación de estación, preguntas y fases de la sección 4 |
| **Ambiguo** | Señales contradictorias, p. ej. `s0-core` con specs propias | Expón las señales y pregunta; no elijas por inferencia |

En el estado A, una excepción expresa del usuario (por ejemplo, una rama de
prueba) permite continuar como B. Regístrala en la entrega y recuerda que esa
rama no debe publicarse en el maestro.

## 2. Pregunta sólo lo que falta

Construye la lista de parámetros del recorrido y descarta lo ya resuelto por la
petición, el diagnóstico o la conversación. Pregunta en rondas cortas, de hasta
cuatro preguntas relacionadas, ofreciendo valores sugeridos derivados de la
evidencia. Usa la herramienta de preguntas del cliente si existe; si no,
pregunta en el chat con opciones numeradas. No pidas confirmar un dato ya dado.

| Parámetro | Recorrido | Valor sugerido / regla |
| --- | --- | --- |
| ID del sistema | B | Nombre del remoto sin `s0-`; validar que no esté registrado en otra ruta |
| Nombre y propósito del producto | B | Texto del usuario; no inventar |
| ¿Existe código? | B | Si no, se omiten fuentes e integración |
| Fuentes | B, C | Rutas locales por componente, una carpeta base, URLs Git con rama o IDs del catálogo |
| Carpeta de descargas | B, C con remotas | `s0.sourcesRoot` si existe; fuera del S0 y de otros Git |
| Integrar consumidores | B, C | Qué repositorios y clientes (`claude`, `codex`); por defecto los conectados |
| Completar catálogo | B, C con catálogo vacío | id corto sin prefijo común, `origin` real, rama predeterminada del remoto |
| Ejecutar Discovery | B, C | Sí en B con código; foco y componentes en C |

En C no preguntes por ID ni propósito: se conservan los existentes. Si el ID
indicado contradice la identidad adoptada, informa el conflicto y detente.

## 3. Confirma el plan una vez

Antes de escribir, presenta un resumen breve: estado detectado, parámetros,
acciones por raíz (S0 y cada consumidor), ejecutable OpenSpec que se usará y
fases omitidas. Pide una única confirmación. Esa confirmación autoriza las
acciones listadas; no vuelvas a pedirla dentro de ese alcance. Un cambio
material de parámetros requiere presentar la diferencia.

## 4. Ejecuta delegando

Sigue este orden; cada fase usa el método de su skill y conserva sus
comprobaciones. Un fallo deja esa fase pendiente sin deshacer las correctas.

1. **Recorrido B — adopción:** aplica connect-project, fila «Adoptar una
   instancia», con el ID y propósito confirmados: registro, personalización de
   README y `openspec/config.yaml`, e integraciones del S0.
   **Recorrido C — estación:** aplica connect-project para registrar el store
   existente y verificar o recordar las fuentes seleccionadas.
2. **Fuentes:** descarga sólo las remotas confirmadas y recuerda las locales
   verificadas, según connect-project.
3. **Consumidores:** integra únicamente los confirmados, según su referencia de
   integración. Informa los conflictos sin convertirlos.
4. **Catálogo:** si se confirmó, completa `repositories.yaml` con
   `version: 1` y `repositories: [{id, remote, branch}]`. Obtén la rama con
   `git ls-remote --symref <url> HEAD`; no guardes rutas personales ni
   credenciales y conserva entradas y comentarios existentes. Si la consulta
   remota falla, deja `branch` fuera y declara el límite.
5. **Discovery:** si se confirmó, toma su referencia **después** de las fases
   anteriores, presenta el borrador y escribe `context/` sólo tras su
   aprobación, según project-discovery. Sin código, prepara un contexto inicial
   con la intención aportada, sin inventar arquitectura.

## Entrega

Resume por fase: realizada, omitida o pendiente, con su motivo. Incluye S0/ID,
remoto, rama y HEAD; ejecutable y versión de OpenSpec; consumidores conectados
y pendientes; catálogo; estado de Discovery (borrador o publicado) y sus
comprobaciones. Lista los archivos modificados por raíz y recuerda que nada
quedó en stage ni commit. Indica el siguiente paso: revisar diffs y publicarlos
según el proceso del equipo, y continuar con el [playbook](../../../PLAYBOOK.md).

Una reejecución vuelve a diagnosticar y sólo ofrece lo pendiente; reutiliza
identidad, registro, fuentes e integraciones correctas.
