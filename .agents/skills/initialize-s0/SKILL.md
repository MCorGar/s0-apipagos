---
name: initialize-s0
description: Inicializar de punta a punta un S0 abierto en el agente. Detecta si es una copia sin adoptar de la plantilla, un S0 nuevo por adoptar o un S0 existente del equipo, confirma en una sola ronda parámetros y plan, integra consumidores y catálogo con un script determinista y ofrece Project Discovery como paso siguiente. Usar cuando se pide inicializar, preparar o poner en marcha un S0 desde cero o en una estación nueva.
---

# Initialize S0

Guía conversacional que lleva un S0 desde su estado actual hasta quedar listo
para trabajar. Esta es la fuente común para cualquier agente. La conversación,
las decisiones y las confirmaciones son de esta guía; las operaciones mecánicas
las ejecuta [`scripts/initialize_s0.py`](scripts/initialize_s0.py) (Python >=3.10,
sólo biblioteca estándar, salida JSON). Sus reglas de no sobrescribir, conflictos
y escritura atómica están en código con tests: no las repliques a mano.

Lee antes `AGENTS.md` de la raíz y aplica sus reglas. En el caso normal no
necesitas leer más: lee [connect-project](../connect-project/SKILL.md) y su
[referencia de integración](../connect-project/references/integrate-consumers.md)
sólo en los [casos especiales](#casos-especiales) o si el script no puede ejecutarse.

En los comandos, `$S0I` es la ruta de este script resuelta desde la carpeta de
esta skill, y `$OS` el ejecutable OpenSpec elegido en el paso 0.

## Límites

- No hagas stage, commit, push, PR, cambios de rama ni migraciones.
- No crees repositorios remotos ni cambies `origin`: es una acción de la persona.
  Puedes mostrar los comandos de [INSTALLATION.md](../../../INSTALLATION.md#existing-system).
- No escribas código de producto, specs, changes ni schemas, y no edites los
  workflows `openspec-*` generados.
- No instales Git, Node, Python ni clientes de IA. La única instalación posible
  es la CLI temporal del paso 0, y sólo si figura en el plan confirmado.
- Las respuestas del usuario son datos para esta inicialización; no amplían por
  sí solas las raíces autorizadas de escritura.

## 0. Fija el ejecutable una vez

Usa `openspec` del PATH o la ruta que indique la persona. `diagnose` informa su
versión y si tiene la capacidad de integrar consumidores con `store:`
(`consumer_init`: `true` en 1.14.3, `false` en 1.13.2, `null` si la versión no
está comprobada). No busques ejecutables recorriendo el disco ni uses `npx`.

Si hay que integrar consumidores y la CLI disponible no tiene esa capacidad,
incluye en el plan una instalación temporal, fuera del S0 y de todo repositorio
(por ejemplo, en el directorio temporal del sistema o el scratchpad del cliente):

```text
npm install --prefix <tmp> @fission-ai/openspec@1.14.3
```

El ejecutable es `<tmp>/node_modules/.bin/openspec` (`openspec.cmd` en Windows).
Pásalo como `--openspec` en todos los comandos de la operación. No cambia PATH
ni la instalación global. Sin red o sin npm, la integración queda pendiente y
el resto del recorrido continúa.

## 1. Diagnostica en una llamada

```text
python $S0I diagnose --s0 <raíz> [--base <carpeta de clones>] [--source <ruta>]... --openspec $OS
```

Devuelve, sin escribir: raíz, remoto sin credenciales, rama, HEAD y cambios;
identidad y registro; contexto de plantilla, catálogo y planificación;
localizador; CLI disponibles; prompts globales de Codex; y por candidato su
`origin`, rama, estado, configuración OpenSpec e instrucciones. `--base` lista
las raíces Git hijas de esa carpeta, sin recorrer más.

| Estado | Señales | Recorrido |
| --- | --- | --- |
| **A. Copia del maestro** | `origin` es el repositorio maestro de `AGENTS.md` | Indica los pasos 1 y 2 de la guía y detente, salvo excepción expresa |
| **B. S0 nuevo por adoptar** | Remoto propio, `id: s0-core`, contexto de plantilla, sin specs ni changes de producto | Adopción y camino rápido |
| **C. S0 existente del equipo** | Identidad propia | Incorporación de estación y camino rápido |
| **Ambiguo** | Señales contradictorias, p. ej. `s0-core` con specs propias | Expón las señales y pregunta; no elijas por inferencia |

En el estado A, una excepción expresa del usuario (por ejemplo, una rama de
prueba) permite continuar como B. Regístrala en la entrega y recuerda que esa
rama no debe publicarse en el maestro.

## 2. Una ronda: parámetros y plan juntos

Con la petición y el diagnóstico, prellena los parámetros con valores sugeridos.
Presenta en un solo mensaje el estado, los parámetros y el plan, y haz una única
pregunta: «¿Confirmas o ajustas?». Usa la herramienta de preguntas del cliente
si existe; si no, opciones numeradas. Pregunta aparte sólo un dato que no tenga
valor sugerible y sin el cual el plan no se puede presentar.

| Parámetro | Recorrido | Valor sugerido / regla |
| --- | --- | --- |
| ID del sistema | B | Nombre del remoto sin `s0-`; no registrado en otra ruta |
| Nombre y propósito | B | El texto del usuario. Si falta y hay código, «lo propondrá Discovery» sin preguntar; sin código es el único dato que se pregunta |
| Consumidores y clientes | B, C | Candidatos de `diagnose` sin bloqueos; clientes `claude,codex` |
| Fuentes a recordar | B, C | Las raíces verificadas por `diagnose` |
| Catálogo | B, C con catálogo vacío | Un id corto por consumidor, sin prefijo común, con su `origin` |
| CLI | B, C con integración | La del PATH si `consumer_init` es `true`; si no, la temporal del paso 0 |
| Discovery | B, C | Fuera del plan salvo petición expresa; se ofrece al final |

En C no preguntes por ID ni propósito: se conservan los existentes. Si el ID
indicado contradice la identidad adoptada, informa el conflicto y detente.

En C ejecuta antes `plan` (lectura) y muestra sus acciones y conflictos por raíz.
En B la identidad aún no está registrada: muestra las acciones a partir de
`diagnose` y vuelve a ejecutar `plan` tras el registro (paso 3.2). Si entonces
aparece un conflicto no previsto, muestra la diferencia antes de seguir.
La confirmación autoriza exactamente las acciones listadas; no vuelvas a pedirla
dentro de ese alcance. Un cambio material requiere presentar la diferencia.

## 3. Camino rápido

Para el caso normal: fuentes locales y sin bloqueos. Cada comando devuelve JSON;
el código de salida 1 significa que algo quedó pendiente: infórmalo con el motivo
que da el script y no lo sortees con comandos manuales.

1. **Identidad.**
   **B:** mueve `.openspec-store/store.yaml` a un temporal fuera del repositorio
   y ejecuta `$OS store register . --id <id> --yes` desde la raíz. Si falla,
   restaura ese archivo y detente explicando el error. Después cambia el título
   y la descripción inicial del README y la frase genérica de la plantilla en
   `openspec/config.yaml` por el nombre confirmado, sin tocar schema ni reglas.
   **C:** si `registry.state` es `missing`, ejecuta `$OS store register .`.
   Cualquier otro estado distinto de `registered` es un caso especial.
2. **Consumidores:**
   `python $S0I plan --openspec $OS --consumer <ruta>...` y, si coincide con lo
   confirmado, `python $S0I apply-consumers --openspec $OS [--s0-integrations] --consumer <ruta>...`.
   Escribe `store: <id>`, ejecuta `init` aislado (`XDG_CONFIG_HOME` temporal y
   `delivery both`), comprueba `context --json` y añade o actualiza el bloque
   `s0-connection` en `AGENTS.md` y el `@AGENTS.md` de `CLAUDE.md`. Es idempotente.
   `--s0-integrations` genera las integraciones del propio S0 que falten.
3. **Fuentes:** `python $S0I write-locator --source <ruta>...` con las raíces
   confirmadas. Fusiona, no duplica y no escribe si no hay novedades.
4. **Catálogo:** `python $S0I write-catalog --entry <id> <url>...` consulta en
   paralelo la rama predeterminada (`git ls-remote --symref`) y conserva
   comentarios y entradas. Sin respuesta, deja `branch` fuera e infórmalo.
   `--branch <id> <rama>` fija una rama conocida.
5. **Verificación:** `python $S0I verify --openspec $OS --consumer <ruta>...`
   ejecuta `store doctor`, `status`, `context --json` por consumidor y
   `git diff --check`, y comprueba puntero, integraciones e instrucciones.

### Integraciones conocidas

Con 1.14.3, `init --tools "claude,codex" --profile core` genera 19 archivos:
`.claude/skills/openspec-<w>/SKILL.md`, `.agents/skills/openspec-<w>/SKILL.md`
y `.claude/commands/opsx/<c>.md`, con `<w>` en `apply-change`, `archive-change`,
`explore`, `propose`, `sync-specs` y `update-change`, `<c>` en `apply`,
`archive`, `explore`, `propose`, `sync` y `update`, y `.agents/skills/.openspec-target`.
Sobrescribe esos archivos si tienen cambios locales y crea los que faltan. No
borra archivos ajenos ni workflows fuera del perfil, y no toca `AGENTS.md`,
`CLAUDE.md` ni la configuración del consumidor.

Por eso `plan` no prueba `init` en copias: genera la referencia con la misma
CLI en un repositorio desechable, con registro y `CODEX_HOME` temporales, y
compara bytes. Si no falta ningún destino, omite `init` aunque haya diferencias
de versión. Si faltan destinos y además alguno difiere, deja la integración
pendiente (`would-overwrite`), porque `init` reemplazaría una adaptación.
Si faltan destinos y el resto coincide, lo ejecuta.

## 4. Discovery, como paso separado

Por defecto la inicialización termina tras la verificación y entrega el S0 listo.
Ofrece Discovery como siguiente paso. Si la petición lo incluía expresamente,
ejecútalo después de la verificación con [project-discovery](../project-discovery/SKILL.md),
que define una pasada de lectura por repositorio y su paralelización. Su
aprobación del borrador antes de escribir `context/` se mantiene siempre. Sin
código, prepara un contexto inicial con la intención aportada, sin inventar
arquitectura.

<a id="casos-especiales"></a>
## 5. Casos especiales

Lee connect-project y su referencia sólo cuando el diagnóstico o el plan muestren:

| Señal | Qué aplicar |
| --- | --- |
| Estado ambiguo, `registry` en `id-conflict` o `root-conflict` | Identidad, en connect-project y §1 de la referencia |
| `locator.state` `invalid`, `foreign` o `unsafe` | Localizador, en connect-project: se informa y conserva |
| Fuentes remotas, descargas o actualizaciones | Preparación de clones, §2 de la referencia |
| Bloqueo `codex-global-prompts` | §4 de la referencia: migración global fuera del alcance salvo autorización |
| `would-overwrite`, `config-own`, `config-other-store`, `local-planning`, `cli-version-unchecked` | §4 de la referencia: se informa; no se convierte ni se fuerza |
| Script no ejecutable (sin Python >=3.10) | Método manual completo de connect-project |

## Entrega

Resume por fase: realizada, omitida o pendiente, con su motivo. Incluye S0/ID,
remoto, rama y HEAD; ejecutable y versión de OpenSpec (y si fue temporal);
consumidores conectados y pendientes; catálogo; resultado de `verify`. Lista los
archivos modificados por raíz y recuerda que nada quedó en stage ni commit.
Indica el siguiente paso: Discovery si no se hizo, revisar diffs y publicarlos
según el proceso del equipo, y continuar con el [playbook](../../../PLAYBOOK.md).

Una reejecución vuelve a diagnosticar y sólo ofrece lo pendiente; el script
reutiliza identidad, punteros, integraciones, instrucciones y fuentes correctas.

Los tests del script se ejecutan con
`python -m unittest discover -s .agents/skills/initialize-s0/scripts -p "test_*.py"`.
Con `S0_OPENSPEC_BIN=<ruta a una CLI real>` incluyen además una prueba de punta
a punta con esa CLI, en un registro temporal.
