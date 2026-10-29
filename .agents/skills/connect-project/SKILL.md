---
name: connect-project
description: Preparar acceso a fuentes locales, remotas o mixtas de un S0, o adoptar una instancia e integrar consumidores cuando se solicita. Verifica referencias, recuerda rutas locales y distingue consultar código de instalar OpenSpec en los repositorios.
---

# Connect Project

Recibe un S0 identificado y las rutas, repositorios o entradas del catálogo que
interesan a la tarea. Esta es la fuente común para Codex, Claude y otros agentes.
Si las fuentes ya son accesibles, pueden consultarse sin repetir una conexión.
Lee `AGENTS.md` de la instancia y conserva su identidad y las reglas del sistema.

## Elige la acción según la petición

| Petición | Alcance |
| --- | --- |
| Consultar o verificar fuentes | Leer y comprobar archivos y referencias; no escribir configuración ni localizadores |
| Preparar acceso, conectar fuentes o recordar ubicaciones | Verificar las fuentes seleccionadas y recordar las rutas locales comprobadas cuando hay un S0 Git identificado |
| Registrar este S0 | Registrar su identidad existente con la CLI, conservando las asociaciones de otras copias |
| Adoptar una instancia, inicializar OpenSpec o instalar integraciones en consumidores | Seguir [la adopción e integración](references/integrate-consumers.md); puede preparar identidad, punteros e integraciones dentro de ese alcance |
| Descargar o actualizar fuentes | Obtener las copias expresamente solicitadas en el destino autorizado; no implica integrarlas con OpenSpec |

Una petición genérica de conectar fuentes prepara su acceso. Inicializar o
integrar consumidores requiere que esa intención esté expresada en la petición
o en el alcance ya acordado. No vuelvas a pedir una confirmación ya concedida.
Si una ambigüedad afecta a qué repositorios se escribirán, verifica lo accesible
y aclara esa parte antes de modificar consumidores.

La creación de la instancia y el clon inicial del S0 corresponden al usuario.
Trabaja sobre su instancia independiente; no conviertas el repositorio maestro
del Core en el S0 de un producto. Una consulta de fuentes no requiere
instalar CLI, registrar un store ni generar integraciones. Discovery es opcional
cuando se pide analizar o actualizar contexto; esta skill no lo inicia por sí sola.

No hagas stage, commits, push, PR, migraciones ni cambios de rama como efecto de
conectar. Conserva trabajo previo, configuración y planificación. No escribas
código de producto ni crees specs, cambios o schemas. Un archivo inaccesible o
una fuente incompatible queda pendiente; continúa con las fuentes válidas.

## Identifica el S0 y sus fuentes

Para un clon S0, comprueba raíz Git real, remoto, rama, HEAD y cambios locales.
Lee su identidad en `.openspec-store/store.yaml`; el ID no demuestra por sí solo
que un clon sea el maestro o una instancia descartable. Para un S0 remoto,
identifica repositorio y referencia y lee sus instrucciones en esa revisión.
No exijas un clon local para consultar archivos remotos.

Respeta la elección local, remota o mixta por componente. Una URL no es una orden
de descargar. Una ruta expresa selecciona esa copia. Ante una fuente inaccesible,
informa el límite sin sustituirla por otra rama, fork o ubicación silenciosamente.
Distingue archivos leídos de cobertura funcional: un README no acredita el código
completo ni su comportamiento. No ejecutes builds, tests, aplicaciones o scripts
del producto para verificar una ubicación.

### Catálogo compartido y ubicaciones personales

`repositories.yaml` es opcional: `version: 1`,
`repositories: [{id, remote, branch}]`, con `branch` opcional. Los IDs son únicos
y `remote` es una URL Git HTTPS/SSH sin credenciales. El catálogo no guarda rutas
personales ni acredita acceso al código. Conectar una estación no lo reescribe.
Usa sólo las entradas seleccionadas; un catálogo vacío no impide usar rutas o
URLs expresas. Un catálogo inválido se informa y conserva.

Para fuentes locales, prioriza rutas expresas por componente. Si se aporta una
carpeta base, limita la búsqueda y las entradas recordadas a ella; sin base,
reutiliza las entradas válidas del localizador y pide sólo las ubicaciones que
falten. No recorras el equipo entero, enlaces, metadata Git, dependencias o caches.
Al encontrar una raíz Git, úsala como unidad, sin convertir sus submódulos u otros
repositorios referenciados. Para componentes del catálogo seleccionados, puedes
comprobar carpetas homónimas bajo el coordinador indicado, aunque éste sea Git.
Una ruta expresa permite otras ubicaciones, sin ampliar la búsqueda a sus vecinas.
Las convenciones adicionales de carpetas y componentes pertenecen a cada instancia.

Comprueba raíz real y `origin`, no sólo nombres. Reconoce HTTPS/SSH del mismo
host y repositorio, omitiendo `.git` al comparar identidad; un fork u otro host
no es equivalente. Conserva el `origin` real sin credenciales. Una ruta ausente
o un remoto distinto queda pendiente. Dos copias válidas del mismo remoto siguen
siendo fuentes distintas; si no se seleccionó una, pide elegirla.

Excluye de los consumidores el propio S0, otros S0 y raíces que contengan al S0
o estén dentro de él. Un coordinador puede leerse como fuente operacional sin
convertirse en consumidor. El catálogo y las convenciones de una instancia no
amplían por sí solos las raíces autorizadas de escritura.

## Verifica el acceso disponible

### Fuentes locales

En cada raíz seleccionada lee sus instrucciones y observa rama, HEAD y cambios.
Conservar una copia no acredita que esté limpia ni actualizada. No cambies su
rama ni sus archivos para hacerla coincidir con el catálogo.

Para leer código no se exige un puntero `store:` ni se ejecuta `openspec init`.
Un repositorio con otro store o planificación propia puede ser una fuente de
código: conserva esa asociación y sus requisitos. Integrarlo con este S0 es otra
acción y exige las comprobaciones de [integración](references/integrate-consumers.md).
Las raíces resueltas y `actionContext` que requiere un workflow no se deducen de
haber verificado una fuente; no inventes permisos cuando falte esa información.

### Fuentes remotas

Usa las herramientas de lectura ya disponibles y autorizadas. Comprueba propietario,
repositorio, rama o commit y archivos de esa misma revisión. Prevalece la referencia
solicitada; después la del catálogo. Si no hay referencia, identifica la que el
proveedor realmente permite consultar y señala la limitación cuando sea necesario.
No sustituyas una rama solicitada por la predeterminada cuando falle.

Lee los archivos pertinentes y cita sus rutas y revisión cuando está expuesta.
Conocer una URL, listar metadata o recibir archivos sincronizados no demuestra
acceso vivo a todo el repositorio. No inventes SHA ni confundas blob con commit.
Si faltan permisos, referencia o contenido, identifica lo pendiente. Un 404 no
prueba por sí solo que un repositorio privado no exista.

No instales conectores, cambies cuentas o permisos ni pidas tokens en el chat como
efecto de verificar. El acceso remoto no se guarda como ruta local ni requiere
registro de store. En fuentes mixtas conserva la procedencia por componente y los
cambios locales observados. Una copia o credencial de otra estación no concede
acceso en un entorno cloud.

### Descargas y actualizaciones solicitadas

La consulta remota no descarga código. Si el usuario solicita copias o una
actualización, aplica [la preparación de clones](references/integrate-consumers.md#prepare-clones)
con una raíz S0 e identidad comprobadas. Ese apartado prepara fuentes y su índice;
no autoriza los pasos posteriores de integración. Una actualización no hace fetch,
pull, reset ni limpieza sobre el checkout existente: prepara una copia externa
y conserva lo anterior, salvo que el usuario haya elegido expresamente otro flujo.
Una reejecución sin petición de actualizar reutiliza lo ya verificado.

## Registro e integración cuando correspondan

Para registrar un S0 existente o integrar consumidores, identifica ejecutable y
versión según `AGENTS.md` y [la guía de instalación](../../../INSTALLATION.md).
Comprueba las capacidades y opciones necesarias; 1.13.2 y 1.14.3 no se descartan
por el número de versión. Mantén el mismo ejecutable durante la operación y
registra su versión con el resultado. Una instalación distinta en PATH no
justifica actualizar ni regenerar integraciones existentes.

Con `context` y `store` disponibles, ejecuta `context --json` desde la raíz S0
y comprueba `root.path`. Consulta `store list --json`; reutiliza la asociación
si ID y raíz coinciden. Para un registro solicitado que falte, usa
`store register .` conservando la identidad existente. Ante otra raíz o ID,
informa el conflicto sin sobrescribir, desregistrar ni elegir otro S0.
No cambies `defaultStore` global. Si falta CLI o una capacidad requerida, deja
pendiente esa operación; verificar fuentes desde una raíz explícita puede continuar.

Sólo la adopción nueva o integración solicitada sigue la referencia
[integrate-consumers](references/integrate-consumers.md). La comprobación de una
fuente con otro store no permite reasociarla. Conserva las restricciones del
workflow oficial y no copies integraciones entre proyectos para sortear la CLI.

<a id="recuerda-fuentes-locales"></a>
## Recuerda fuentes locales

Este paso corresponde a preparar o recordar fuentes, o a una integración
solicitada; se omite en una consulta de sólo lectura. Requiere una raíz Git S0
local con identidad comprobada. Si el S0 sólo es remoto, comunica el resultado
en la sesión sin crear un clon, store o archivo local como efecto secundario.
Un registro CLI pendiente no impide recordar fuentes de esa raíz explícita;
conserva el conflicto informado y no uses `--store` como si estuviera resuelto.

Usa el contrato de `AGENTS.md`: `version: 1`, `s0: {id, root}` y
`repositories: [{path, remote}]`. Obtén el destino desde el S0 con
`git rev-parse --git-path s0-local-sources.json`; resuelve una salida relativa
contra esa raíz. No presupongas que `.git` es una carpeta. Comprueba que el
destino pertenece a su metadata Git y no sigue un enlace fuera de ella.

Si existe, valida estructura, ID y raíz propietaria. Un localizador inválido o
ajeno queda intacto y pendiente; no adoptes sus rutas ni lo repares por inferencia.
Fusiona fuentes seleccionadas y verificadas por raíz real, preservando entradas
no seleccionadas. No retires rutas por estar temporalmente ausentes. Guarda
rutas absolutas reales y el remoto sin credenciales o `null` cuando no existe.
No guardes ramas, SHA, estado de trabajo, URLs remotas como rutas ni fuentes sin
verificar. Si no hay novedades, no reescribas el archivo ni dupliques entradas.
Sin fuentes verificadas no crees un localizador vacío.

Guarda UTF-8 mediante temporal y reemplazo dentro del mismo directorio. Ante un
fallo conserva lo anterior y declara la persistencia pendiente. El localizador
recuerda fuentes; no certifica que los consumidores estén integrados con OpenSpec.

## Entrega y continuación

Comprueba el estado Git, ramas y HEAD de las raíces inspeccionadas. En preparación
de acceso deben conservarse; en integración, identifica cada modificación
solicitada y conserva el resto. Entrega S0/ID, acción realizada, fuentes y
referencias comprobadas, cobertura y pendientes. Distingue fuente accesible,
localizador guardado, store registrado e integración de consumidor verificada.

Si también se pidió Discovery, lee [project-discovery](../project-discovery/SKILL.md)
y aplícalo a la selección accesible después de la preparación. Su snapshot incluye
los cambios técnicos ya realizados y su publicación conserva las revisiones de
esa skill. Si todavía no hay código, utiliza sólo el propósito aportado, sin
inventar arquitectura o componentes. No inicies `propose` o `apply` por conectar.
