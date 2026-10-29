# S0 Core — contexto de la plantilla

## Propósito y alcance

Esta plantilla permite compartir por Git el contexto, las especificaciones y los
cambios OpenSpec de un sistema. PO refina necesidades; DEV propone e implementa
en repositorios de código; QA deriva casos y verifica versiones identificadas.
El núcleo usa `spec-driven`, sin dependencia de Jira ni infraestructura adicional.
Las instrucciones comunes viven en `AGENTS.md` y los métodos PO/DEV/QA en
`.agents/skills/`. Codex y Claude consumen esas mismas fuentes; el modelo se
selecciona en cada cliente, sin cambiar el contexto ni las specs del sistema.

Al adoptar la plantilla se sustituye esta página por el contexto confirmado del
sistema: propósito, usuarios, alcance y límites, componentes, vocabulario y fuentes.
Cada instancia tiene identidad y repositorio Git propios y puede describir uno
o varios repositorios de código. No hay componentes de producto ni reglas de
negocio institucionales predefinidos.

## Componentes y fuentes

- Repositorio oficial de la plantilla:
  [`nuamx/nuam-ia-arq-sdd-openspec`, rama `development`](https://github.com/nuamx/nuam-ia-arq-sdd-openspec/tree/development).
- Requisitos vigentes: [openspec/specs/](../openspec/specs/), vacíos en la plantilla.
- Propuestas e historial: [openspec/changes/](../openspec/changes/).
- Necesidades de origen: texto aportado por el usuario, issue o HDU; Jira opcional.
- Código, contratos y tests: los repositorios consumidores que identifique cada
  sistema. Al adoptar, indica sus responsabilidades y URLs Git, sin rutas personales.
- El [catálogo compartido](../repositories.yaml) se entrega vacío. El equipo puede
  completar IDs, URLs Git y ramas de referencia para que cada integrante indique
  sus ubicaciones a `connect-project`; las rutas personales se recuerdan localmente.
  Su uso es opcional y no reemplaza este mapa de responsabilidades. OpenSpec no
  lo interpreta ni lo usa para conceder acceso o sincronizar código.
- Si un subsistema tiene otro S0, identifica su fuente canónica y el contrato de
  integración relevante. Sus requisitos internos permanecen en ese S0; aquí se
  describe el comportamiento y las dependencias que corresponden a este sistema.

## Vocabulario y límites

- **HDU:** historia o necesidad de usuario; puede recibirse como texto.
- **Store:** repositorio independiente con contexto, specs y cambios compartidos.
- **Consumidor:** repositorio de código con `store:` y sin specs/changes locales.
- **Caso preparado / test implementado / test ejecutado:** estados diferentes de QA.

Consultar no autoriza escribir. Las conexiones y el acceso a código dependen de
los permisos de la sesión. Los secretos y las configuraciones personales no se
versionan. Esta página referencia las specs; no las duplica.
