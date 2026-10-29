# Captura e informes de review-pr

Mantén `input.json`, `report.json` y `review.md` juntos en el destino elegido por
el método. Escribe UTF-8 mediante serialización JSON; no interpolación de shell.
Los ejemplos siguientes son ilustrativos, no evidencia de un PR real.

## input.json

```json
{
  "repository": "owner/repository",
  "number": 123,
  "headOid": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "baseOid": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "url": "https://github.com/owner/repository/pull/123",
  "title": "Título obtenido del PR",
  "capturedAt": "2026-10-26T12:00:00Z",
  "source": "remote",
  "sourceVerification": "Archivos leídos por API al headOid; base/head estables tras capturar",
  "files": [{ "path": "src/example.js" }],
  "diff": "diff --git a/src/example.js b/src/example.js\n--- a/src/example.js\n+++ b/src/example.js\n@@ -1 +1 @@\n-return oldValue;\n+return newValue;\n"
}
```

- `repository`: identidad `owner/repository`; el número solo no basta.
- `number`: entero positivo. `headOid` y `baseOid`: SHA completos obtenidos de la
  fuente, no abreviados ni inventados. Para un snapshot incompleto declara lo que
  falta y limita la revisión; no copies valores ilustrativos.
- `files`: lista completa de rutas relativas del PR, con `/`, sin `..` ni rutas
  absolutas. En renombres usa la ruta actual; en eliminaciones, la ruta anterior.
- `diff`: texto unificado íntegro. Comprueba archivos/paginación con la fuente;
  un truncamiento entre archivos completos puede ser invisible para el parser.
- `source`: `remote` o `supplied`; registra la vigencia remota como no comprobada
  en un snapshot suministrado sin acceso. Describe en `sourceVerification` cómo
  comprobaste código, identidad y cobertura. Conserva los metadatos adicionales
  disponibles; no atribuyas una comprobación a estos campos por estar presentes.

El verificador exige `repository`, `number`, `headOid`, `files` y `diff`.
El agente contrasta `baseOid`, la procedencia y los demás metadatos; el esquema
por sí solo no acredita la captura ni comprueba la base.

## report.json

```json
{
  "repository": "owner/repository",
  "number": 123,
  "headOid": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "baseOid": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "comments": [{
    "path": "src/example.js",
    "line": 1,
    "side": "RIGHT",
    "body": "[P1] Título concreto. Disparador, consecuencia y evidencia verificable del fallo.",
    "evidence": "return newValue;"
  }]
}
```

La identidad debe coincidir con la captura, incluido `baseOid` si existe. Cada
comentario requiere ruta de la lista de archivos, número de línea positivo, lado,
cuerpo no vacío y fragmento literal no vacío de esa misma línea modificada.
Una línea de contexto sin cambios no es un ancla admitida por este verificador.
Para renombres, usa la ruta actual también al anclar en `LEFT`. No fabriques
anclas para binarios, submódulos ni hallazgos que sólo puedan explicarse fuera del
diff: van en `review.md`. Una lista vacía no representa una review `APPROVE`.

Ordena por impacto y usa la escala del equipo si está documentada. Sin escala
propia, `P0` indica un bloqueo crítico generalizado, `P1` un fallo grave que debe
corregirse pronto, `P2` un defecto de impacto acotado y `P3` uno menor. Explica
siempre las condiciones; la etiqueta no sustituye la evidencia.

## review.md y resultado de verificación

El informe narrativo debe permitir reproducir el razonamiento:

- Identidad del PR y SHA base/head; fuente y fecha de captura, vigencia comprobada
  o desconocida; S0 y repositorios consultados con sus revisiones/cambios locales.
- Alcance revisado y fuentes de requisitos. Distingue specs vigentes, propuestas
  activas y ausencia de HDU vinculada.
- Hallazgos con severidad, ruta/líneas, disparador, consecuencia y evidencia.
  Separa defectos previos, preguntas y recomendaciones de las regresiones.
- Pruebas/comandos ejecutados y resultados, evidencias suministradas y comprobaciones
  pendientes. Identifica versión, entorno y omisiones sin presentar lo planeado
  como ejecutado.
- Resultado real del verificador y sus límites. Indica si el informe es un
  borrador no verificado; no atribuyas aceptación humana o publicación.

La CLI devuelve JSON con `ok`, errores o identidad, cantidad de comentarios y
`diffSha256`; usa código de salida `0` al validar y `1` al fallar. El hash identifica
el texto examinado, sin certificar su origen. Reejecuta sobre los archivos finales
si cambian después de validar. El límite es 32 MiB por JSON, incluido el diff
serializado; un archivo mayor requiere resolver la limitación sin truncarlo.
