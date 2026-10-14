# Loop progress

## Backlog

### P0: the app doesn't run

- [ ] `modules/ai_evaluator.py` uses `List` in a type hint without importing it. That raises NameError on import, so `main.py` can't start.
- [ ] `main.py` calls `logger.setLevel(logger.DEBUG)`, which raises AttributeError whenever `--verbose` is passed. Use `logging.DEBUG`.
- [ ] Model and SDK:
  - The code calls `gemini-1.5-flash` through `google-generativeai`. Gemini 1.5 has been retired and that SDK is deprecated.
  - Migrate to `google-genai` and pick a current model from the official docs. Keep the model ID configurable through `GEMINI_MODEL`.
  - Use JSON output mode with a response schema instead of stripping code fences.
- [ ] Dependencies have never been installed and pytest has never run. Install them, run `pytest` and fix every failure.
- [ ] There is no offline path.
  - Add `--plan PATH` to build a deck from a saved plan JSON without calling the API, and `--save-plan PATH` to write one.
  - Add `tests/fixtures/sample_plan.json`. It must use every visual type (image, chart, diagram, none) and include a long title and a 6-bullet slide.
- [ ] Add `scripts/render_preview.py`, which turns a deck into one PNG per slide (pptx to PDF to PNG) for the render check.

### P1: the decks don't look good yet

- [ ] Text overflow: 36pt titles in a 4.5" column and up to five 24pt bullets in fixed boxes overflow.
  - Fit the text, either by measuring wrapping or by shrinking within limits.
  - Cap bullets and words in the plan schema.
  - Use real bullets.
- [ ] Image failures put "[Image unavailable]" plus the exception text on the slide.
  - Never show errors on slides. Fall back to the text-only layout instead.
  - Handle WebP and SVG by converting or skipping them.
  - Fit images in both dimensions and keep the aspect ratio. Today only the width is constrained.
- [ ] Charts:
  - Coerce values to numbers.
  - Add data and axis labels and theme colors.
  - Hide the title with `chart.has_title = False`.
- [ ] Diagrams render as "[Diagram]" in italic text. Have the plan describe diagrams as structure (steps and nodes) and draw them with shapes and connectors.
- [ ] Visual system: one grid for margins and column widths, a title band or accent, one consistent font and a stronger title slide. Keep the PRD defaults.
- [ ] Plan schema: validate it with pydantic. The prompt, `_validate_plan` and the builder disagree on whether slide 0 is the title slide; make them agree.
- [ ] Judge the rendered slides:
  - Score the rendered PNGs with a multimodal call.
  - Before the AI judge runs, run deterministic lint for overflow, empty slides and bullet length.
  - Feed the findings back to the generator.
- [ ] Extraction keeps page boilerplate and truncates content at 8,000 characters. Use main-content extraction such as trafilatura or readability, and a much larger budget.
- [ ] Put the supporting detail from the source in each slide's speaker notes.

### P2: honesty and cleanup

- [ ] Dead options: `--config` does nothing, and rate limiting, caching and parallel downloads exist only as config fields. Implement or delete each one.
- [ ] The tqdm progress bar never advances during the feedback loop. Wire it to the loop or remove it.
- [ ] Console output mixes `INFO - …` log lines with the user-facing prints. Log WARNING and above to the console by default, and INFO and DEBUG only with `--verbose`.
- [ ] `AIEvaluator` hard-codes the threshold and attempt count, so `QUALITY_THRESHOLD` and `MAX_QUALITY_ATTEMPTS` have no effect. Read both from config.
- [ ] API-key lookup:
  - It is duplicated in `ai_generator.py` and `config.py`.
  - The `~/.zshrc` parser also matches commented-out lines.
- [ ] Validators:
  - The URL regex rejects valid URLs: TLDs longer than 6 characters, and any URL containing `..`.
  - The base-directory check uses string `startswith`, so `Input2/` passes. Use `Path.is_relative_to`.
- [ ] `ai_generator.py`, `ai_evaluator.py` and `pptx_builder.py` still use `print`. Route their output through the logger.
- [ ] Tests:
  - Replace the `AIza…` string in `tests/test_validators.py`.
  - Delete `test_imports.py`.
  - Add tests for the extractor (fixture HTML), the builder (every shape stays inside the slide bounds) and the feedback loop (mocked client).
- [ ] The docs and the last commit message overclaim, for example "80+ test cases", "multi-stage Dockerfile", rate limiting and caching.
  - Make README, DEPLOYMENT and ARCHITECTURE match the code.
  - The Dockerfile HEALTHCHECK does nothing.
  - docker-compose hard-codes example.com.
- [ ] Document where the model differs from the PRD, which specifies `gemini-1.5-flash`.

### P3: after everything above

- [ ] `.potx` template support (PRD roadmap)
- [ ] PDF and DOCX input (PRD roadmap)

## Iteration log

<!-- One line per iteration: date | item | evidence | commit -->
