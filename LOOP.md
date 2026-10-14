# Improvement loop

Start it with:

```
/loop Run one iteration of the improvement loop defined in LOOP.md
```

## Goal

Turn this repo into an HTML-to-PowerPoint generator whose decks a designer would ship without edits. "Best in the world" means meeting the bar below. An item counts as done only when command output or a rendered slide image proves it.

## The bar (definition of done)

1. **It runs.** In a fresh venv, `pip install -r requirements.txt` succeeds, `python main.py --help` works, and `pytest` passes with no network access and no API key.
2. **It runs offline and live.** `python main.py --plan tests/fixtures/sample_plan.json` builds a deck without calling Gemini. With `GEMINI_API_KEY` set, `python main.py --html sample.html` works end to end.
3. **The slides look designed.** Check every slide of the rendered sample deck for these:
   - No text is clipped or runs past its box or the slide edge.
   - No error or placeholder text appears, such as "[Image unavailable]", "[Diagram]" or exception messages.
   - Margins and alignment follow one consistent grid.
   - Images keep their aspect ratio and fit inside their area.
   - Charts have readable labels.
   - Text contrast is readable.
   - No slide is a wall of text.
4. **The judge sees what the audience sees.** Quality scoring uses the rendered slide images (a multimodal call) plus deterministic checks (overflow, word counts, empty slides), not only the JSON plan.
5. **The docs are true.** Every feature, flag and env var named in README, DEPLOYMENT and ARCHITECTURE exists and works. Anything else is removed from the docs or the code.

## Each iteration

1. Read this file and `LOOP_PROGRESS.md`. Run `git status` and `git log --oneline -5`.
2. Take the highest-priority unchecked backlog item (P0, then P1, then P2). Do one item, or a few that touch the same code.
3. Reproduce the problem first with a failing test, a command that errors, or a rendered slide that shows the defect.
4. Fix it with the smallest correct change and match the existing code style. Prefer deleting dead code to adding infrastructure.
5. Verify:
   - Run `pytest -q`.
   - Whenever builder, plan or layout code changed, do the render check:
     1. Run `python main.py --plan tests/fixtures/sample_plan.json`.
     2. Convert the deck with `soffice --headless --convert-to pdf --outdir <scratch dir> <deck>.pptx`.
     3. Rasterize each page with `pdftoppm -png -r 60`. If poppler is missing, use PyMuPDF.
     4. Open every PNG with the Read tool and look at it. Write down what is wrong on each slide, if anything.
6. Update `LOOP_PROGRESS.md`:
   - Tick the item and record its evidence, either the command and its result or an observation such as "slide 4 PNG: title fits on one line".
   - Add any new defects to the backlog with a priority.
   - Add one line to the iteration log.
7. Commit with a message that says what changed and how it was verified. Push with `git push -u origin claude/html-to-pptx-generator-011eZF3RQerjPyckevXi6sUR`. On network errors, retry after 2s, 4s, 8s and 16s.
8. If every backlog item is checked and all five parts of the bar have recorded evidence, change nothing. Reply `LOOP COMPLETE` with a summary of the evidence.

## Rules

- Never mark anything done without evidence. Don't write "production-ready" or "enterprise-grade", and don't quote test counts you didn't count.
- Tests never touch the network or Gemini; mock the client. One opt-in live smoke test may exist, and it must skip when `GEMINI_API_KEY` is unset.
- Never print, log or commit an API key, or put one in a fixture. That includes fake-looking `AIza…` strings.
- Don't start P3 work until P0 through P2 are done.
- If an item fails two iterations in a row, mark it `BLOCKED:` with the reason and move on.
- Only work on and push to `claude/html-to-pptx-generator-011eZF3RQerjPyckevXi6sUR`.
- Keep the PRD defaults unless one of them causes a defect against the bar. The defaults are:
  - light blue background
  - 36pt bold dark-blue titles
  - 24pt body text
  - slide numbers on every slide except the title slide
  - timestamped output names

  If you change a default, record why in `LOOP_PROGRESS.md`.
