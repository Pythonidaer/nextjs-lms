# Next.js App Router: From routing to production

Course: https://pythonidaer.github.io/nextjs-lms/

A self-paced static LMS built from the official **Next.js 16.3.8** documentation. Includes **501 source chapters, 503 lesson decks, 3,906 slides, five module quizzes and a 23-question final assessment**. The final reviews the 23 questions from the module checks; it is not an independent exam.

## Included content

- App Router: getting started, guides, glossary and complete API reference
- Shared architecture, community and overview pages
- 209 relevant Markdown troubleshooting/error pages
- Guided App Router exercises with worked self-checks, a study strategy and a learning-dashboard capstone

292 App Router/shared documentation pages and 209 relevant troubleshooting pages are mapped in `source-manifest.json`. All 164 Pages Router documentation pages and 44 Pages-specific errors are excluded; the manifest records each exclusion. Shared `source:` aliases are resolved and App Router conditional content is selected. Original examples, warnings, tables and version histories are retained. Code displays filenames and package-manager labels. Visual references link to official assets and require connectivity.

Scope is the release's App Router/shared docs and relevant errors. Pages Router lesson tracks and quizzes are removed. App Router migration/comparison guidance remains in its original context. The separate nextjs.org/learn tutorial, blogs, vendor material and historical versions are outside this course. Later releases require an explicit source refresh. Experimental and deprecated features retain their upstream notices. See `THIRD_PARTY_NOTICES.md` and `vendor/marked.LICENSE.md` for licenses.

## Study and run

Start with Orientation, then App Router Getting Started. Build the local practice project as you study; use the rest as a searchable reference. Reference sections start collapsed. Search matches titles and source text. All lessons are accessible by default. Turning off **Unlock all lessons and quizzes** in Settings applies the final gate: all lesson decks and module quizzes must be completed first. Quizzes pass at 80% with retakes enabled.

Run `python3 -m http.server 8000` in this folder and open http://localhost:8000. There is no install/build requirement for the LMS. All text, examples and quizzes are packaged in a compressed local JSON file; Markdown rendering is a local script. A current browser loads and decompresses the course once. They can be used locally without a documentation API; linked media and external sites need connectivity. The LMS does not execute Next.js examples: exercises require your own local Next.js project and manual review.

Notes, settings, completion and reports are specific to this course and browser. CSV reports export browser-local results. There is no authentication, shared instructor dashboard, server grading, verified certificate or SCORM/xAPI integration. Answers are visible in client files. Production multi-user reporting would require an authenticated backend.

## Maintain the course

`course.json.gz` is the tracked canonical full model, loaded by the browser. The generator also writes an editable local `course.json` that is excluded from git. Decompress the canonical model when editing without a source checkout. Stable IDs preserve progress. Changed lesson content resets that lesson's progress fingerprint.

To rebuild reproducibly, check out the official source at `v16.3.8` (commit `b0fad0d45eb4c4430fda5eeeb442e8a5af08a5f6`) with its docs and errors directories, install PyYAML, and run:

```bash
python3 scripts/build_course.py --source /absolute/path/to/next.js
```

Edit authored exercises and quizzes in `scripts/curriculum.json`. The generator deliberately rejects a different source revision. For manual local course.json changes, recompress it to course.json.gz before publishing; the parity test detects drift.

## Verification

```bash
node tests/course.test.cjs
python3 tests/source.test.py /absolute/path/to/next.js
node tests/browser.test.cjs
```

The Python checks require PyYAML and the last command requires Playwright plus its Chromium browser. `LMS_TEST_URL` optionally targets a deployed URL; otherwise the browser test starts its own temporary server. `CHROMIUM_EXECUTABLE` supports an alternative Chromium binary. `CHROMIUM_BUNDLE` optionally supplies a serverless Chromium package's argument configuration.

Verified: included/excluded source coverage and hashes, compressed/model parity, runtime validation without truncation, router selection and code preservation, all 3,906 slides, safe Markdown, 390/768/1440px layouts, outline search/toggle, notes/completion persistence, grading, skill reports, final gating and independent main scrolling.
