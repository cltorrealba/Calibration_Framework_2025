# Prompt Codex — crear rama e integrar bundle

Usa modo Goal.

## GOAL

Integrar el bundle de gobernanza agéntica en una rama nueva de `cltorrealba/Calibration_Framework_2025`, validarlo y crear un único commit local. No iniciar desarrollo científico.

## CONTEXT

Repositorio:

```text
cltorrealba/Calibration_Framework_2025
base branch: mod_paper
new branch: article3-multiscale-transfer-pipeline
```

El bundle extraído está en:

```text
<BUNDLE_PATH>
```

Contiene `AGENTS.md`, `README_BUNDLE.md` y `docs/article3_multiscale/`.

## PREFLIGHT

1. Muestra:
   ```bash
   git status --short --branch
   git remote -v
   git rev-parse HEAD
   ```
2. Confirma que el repo corresponde a `Calibration_Framework_2025`.
3. Confirma que no hay cambios ajenos.
4. Si está dirty, no limpies ni descartes nada: detente y reporta.
5. Verifica que `mod_paper` existe local o remotamente.
6. Actualiza únicamente mediante fast-forward:
   ```bash
   git switch mod_paper
   git pull --ff-only origin mod_paper
   ```
   Si el pull no es posible, detente; no hagas merge automático.
7. Crea:
   ```bash
   git switch -c article3-multiscale-transfer-pipeline
   ```

## IMPLEMENTATION

Copia desde `<BUNDLE_PATH>`:

```text
AGENTS.md
README_BUNDLE.md
docs/article3_multiscale/
```

Reglas:

- no modificar contenido científico salvo corregir links/rutas manifiestamente rotos;
- no copiar ZIP dentro del repo;
- no tocar `WORKFLOW`, `RESULT ANALYSIS`, datos ni código;
- no modificar repositorios externos;
- no hacer push.

## VALIDATION

Ejecuta:

```bash
git diff --check
git status --short
```

Además:

- lista todos los archivos instalados;
- verifica que los 12 documentos de `docs/article3_multiscale/` existan;
- verifica que todos sean UTF-8;
- busca rutas absolutas privadas;
- verifica que `AGENTS.md` esté en la raíz;
- verifica links relativos del README.

Genera un reporte temporal fuera del repo o muéstralo en la respuesta; no agregues artefactos no solicitados.

## COMMIT

Revisa el diff completo. Luego:

```bash
git add AGENTS.md README_BUNDLE.md docs/article3_multiscale
git commit -m "docs(article3): add multiscale agentic development charter"
```

No hagas push.

## GATE

PASS si:

- rama creada desde `mod_paper`;
- bundle completo;
- diff limpio;
- commit local creado;
- ningún otro archivo cambió;
- no hubo push.

FAIL si cualquier condición no se cumple.

## STOP RULE

Detente después del commit. No crees scaffolding, no ejecutes Goal 0 y no edites código científico.

## FINAL REPORT

Entrega:

1. branch;
2. base SHA;
3. commit SHA;
4. archivos instalados;
5. validaciones;
6. `git status`;
7. confirmación explícita de no push.
