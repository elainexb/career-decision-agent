# Career Decision Agent — Minimal Runtime Package

One Hermes Agent composes nine task Skills through four Career tools. This package contains only the files needed for the current runtime and initial setup. Historical code, archives, test records, personal information, and credentials are excluded.

## Scope

- Actual resume PDF, text, or images → pending Evidence candidates.
- A new job description (JD) and one existing personal Evidence document → source extraction, requirement analysis, capability and industry/scenario comparisons, risk and career-value assessment, resume suggestions, and HTML/Markdown reports.
- Supplementary materials → Evidence or case-maintenance proposals. Generate and review a resume text draft when explicitly requested.
- Facts and formal IDs are not approved automatically, and maintenance proposals are not applied automatically. Company research is deferred. Visual layout review of PDF/Word resumes is outside this version's scope.
- Long-term career-preference storage and collection of unresolved preference expressions are not implemented. The runtime consumes only caller-confirmed, configured constraints; automatic preference memory is not available.

## File Responsibilities

| Location | Responsibility |
|---|---|
| `AGENTS.md` | Current runtime instructions and factual/permission boundaries, independent of historical context |
| `.agents/skills/` | Nine Skills, their referenced rules and schemas, and the Evidence validation helper |
| `plugins/career-decision/` | Hermes registration, tool adaptation, and image delivery |
| `harness/worker.py` + `CONTRACT.md` | Input snapshots, context, artifact dependencies, validation, state, and retained failures |
| `harness/report.py` + `report.template.html` | HTML and Markdown generation after validation |
| `harness/install_profile.py` | Initial configuration of an existing, empty dedicated profile |
| `requirements.txt` | Current dependency versions; PDF processing also requires the system `pdftoppm` executable |

## Initial Setup

An existing Hermes installation, a working `openai-codex` login, and access to `gpt-6.1-sol` are required. This package does not copy credentials or modify Hermes core. Do not rerun the installer against an already configured profile: it refuses to overwrite existing plugin configuration.

From the package root, prepare the Python environment and local data directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
mkdir -p data/private
```

Install Poppler's `pdftoppm` executable. Using Hermes's current profile commands, first create a dedicated `career-decision` profile with no configured plugins. Then run:

```bash
.venv/bin/python harness/install_profile.py \
  --profile-dir "$HOME/.hermes/profiles/career-decision" \
  --project-dir "$PWD" \
  --pdf-python "$PWD/.venv/bin/python" \
  --pdf-renderer "$(command -v pdftoppm)" \
  --input-root "$HOME/Downloads"
```

The installer generates the Git-ignored `data/private/hermes-config.local.json`, profile configuration, SOUL instructions, and a link to the plugin source. Input locations, the Evidence path, output storage, PDF tools, and confirmed constraints belong to local configuration rather than Skill instructions.

JD analysis requires one personal Evidence document conforming to `.agents/skills/resume-intake/schemas/evidence.schema.json`. Its default local location is `data/private/career-master.local.yaml`. Set `evidence_path` in the generated runtime configuration to your existing document to preserve a single authoritative source without copying old records. First intake can produce pending candidates without an existing Evidence document, but this version does not automatically promote candidates into authoritative personal data.

Start fresh tasks in this package. Historical project runs have different rule hashes and should not be imported or resumed.

## Starting the Agent and Providing Inputs

From the package root, run:

```bash
hermes -p career-decision --in "$PWD"
```

Provide the full paths to actual files in the conversation and describe the task. JD inputs can be JPG/PNG/WebP, PDF, or TXT. Resume review requires actual TXT content; PDF resumes can be used for intake. When providing multiple files, identify which contain the JD and which contain the resume. Each file is limited to 20 MB, PDFs to 10 pages, and oversized context fails explicitly.

For a new JD analysis, request use of the current Evidence document, requirement-level importance and support assessments, industry and business-scenario comparisons, work nature, risks, and resume suggestions. Ask for an HTML report using the existing template and the actual output file path.

Outputs are saved to the configured local `runs_dir`. The status `validated_pending_review` means deterministic checks passed. Fact confirmation, semantic review, and user acceptance remain separate steps.

## Publishing to Git

Commit only this package's source files. `.gitignore` excludes personal data, runtime configuration, outputs, credentials, and environments. Runtime data is not included, and the package contains no sample personal facts, historical reports, or automatically created preferences. Full verification records are stored separately from the package and are not Agent runtime dependencies.
