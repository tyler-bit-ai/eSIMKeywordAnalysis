# Development Guidelines

## Repository Scope

### Current Source Of Truth

- Treat this repository as a minimal workspace until new files are actually added.
- Reference `shrimp-rules.md` before making any change in this repository.
- Reference `.codex/config.toml` before changing MCP, task-manager, or workspace configuration.
- Treat `.shrimp-data/` as runtime data owned by `shrimp-task-manager`; inspect it before cleanup or migration tasks.
- Reference `pyproject.toml`, `config/`, `docs/`, and `src/keyword_analysis/` before changing the Python workflow structure.

### Current Verified Structure

- Assume only these project-specific paths exist unless a fresh recursive scan proves otherwise:
  - `shrimp-rules.md`
  - `.codex/config.toml`
  - `.shrimp-data/`
- Current verified top-level implementation paths also include:
  - `pyproject.toml`
  - `README.md`
  - `config/`
  - `docs/`
  - `src/`
  - `outputs/`
- Re-scan the repository with a recursive file listing before proposing changes that mention `src`, `docs`, `README`, tests, build files, or package managers.
- Do not describe or rely on any application architecture that is not present on disk.

## Configuration Rules

### `.codex/config.toml`

- Keep `mcp_servers."shrimp-task-manager"` settings consistent with the local workspace.
- When modifying `DATA_DIR`, verify that the new path matches the actual task data location and update any related operational instructions in `shrimp-rules.md` in the same change.
- Do not change `command`, `args`, or `transport` unless the task explicitly requires reconfiguring the `shrimp-task-manager` integration.

### `.shrimp-data/`

- Treat `.shrimp-data/` as generated task state, not as a place for source code.
- Do not manually create feature files inside `.shrimp-data/`.
- Do not delete or rewrite `.shrimp-data/` as part of unrelated code changes.
- If a task requires resetting task state, state that the change affects `shrimp-task-manager` data and isolate it from source edits.

### Python Workflow Files

- Keep Python packaging metadata in `pyproject.toml`.
- Keep reusable workflow code under `src/keyword_analysis/`.
- Keep collection defaults and environment-like knobs under `config/`.
- Keep planning, methodology, and validation documents under `docs/`.
- Keep generated artifacts under `outputs/` and avoid treating them as hand-authored source.

## Change Workflow

### Before Editing

- Run a fresh recursive scan of the repository before any non-trivial implementation task.
- Base every file reference on files that currently exist on disk.
- Update `shrimp-rules.md` first when the repository structure, key config paths, or multi-file coordination rules change.
- When adding a new top-level source, config, or docs path, update `shrimp-rules.md` in the same task.

### When Adding New Project Files

- Add new rules to `shrimp-rules.md` immediately after introducing a new top-level source area, documentation area, or build/config file.
- Record exact coordination rules once multiple files must change together.
- Use concrete path pairs in rules after they exist. Example:
  - Do: "When modifying `docs/index.md`, also review `README.md`."
  - Do not: "Update all related docs" without naming files.

## Multi-file Coordination

### Currently Required Coordination

- When editing `.codex/config.toml`, review whether `shrimp-rules.md` must be updated to reflect new workspace or task-manager rules.
- When creating any new top-level directory or root-level config file, update `shrimp-rules.md` in the same task.
- When editing `pyproject.toml`, review `README.md` and `shrimp-rules.md` for dependency or structure drift.
- When editing research methodology in `docs/`, review whether matching implementation defaults in `config/` or `src/keyword_analysis/` must change too.

### Coordination That Is Not Yet Valid

- Do not claim that `README.md`, `docs/`, `src/`, `tests/`, `package.json`, or `pyproject.toml` require synchronized updates unless those files are created and verified in the repository.

## AI Decision Rules

### Priority Order

- Prefer observed files over assumptions.
- Prefer configuration safety over convenience when touching `.codex/config.toml`.
- Prefer updating `shrimp-rules.md` over leaving new repository structure undocumented.

### Ambiguity Handling

- If a request mentions files or modules that do not exist, verify by scanning the repository before acting.
- If the scan shows the target does not exist, either create only the explicitly requested file or limit the work to existing files.
- Do not infer a framework, language, or build system from the repository name alone.

## Prohibited Actions

### Never Do These

- Do not invent project structure that is not present on disk.
- Do not write rules based on generic best practices with no repository-specific anchor.
- Do not store source code, docs, or manual notes under `.shrimp-data/`.
- Do not modify task-manager configuration without checking its file-path consequences.
- Do not mention synchronized file updates unless the exact files are verified.

### Examples

- Do: verify `.codex/config.toml` before changing task-manager behavior.
- Do: update `shrimp-rules.md` when adding a new root file like `README.md`.
- Do not: assume a `src/` directory exists because the repository will "probably" grow.
- Do not: create documentation coordination rules for files that have not been added yet.
