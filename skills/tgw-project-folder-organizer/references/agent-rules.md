# Agent Rules Files

Generate thin bridge files. Do not duplicate long rules across files.

## Source Of Truth

`SOURCE_OF_TRUTH.md` is the path authority.

Include only:

```text
project name
quick path index
directory responsibilities
sensitive directory boundaries
path conflict log
last updated date
```

Do not include:

```text
long project history
full strategy documents
training manuals
complete file inventory
large tables of every file
```

## AGENTS.md

`AGENTS.md` is the project-level runtime rule file.

Include only:

```text
read SOURCE_OF_TRUTH first
which directories are sensitive
what not to delete or move
how to handle path conflicts
how to update index after changes
when to ask user before acting
```

Target length: under 80 lines.

## CLAUDE.md

`CLAUDE.md` is a Claude Code bridge.

It should point to:

```text
AGENTS.md
SOURCE_OF_TRUTH.md
```

Do not copy the whole AGENTS content into CLAUDE.md.

## Existing Files

If a project already has these files:

1. Read existing content.
2. Identify rules worth preserving.
3. Propose a replacement or patch.
4. Do not overwrite without explicit confirmation.

## Conflict Rule

If old rules and current files conflict:

```text
Do not silently fix.
Report:
- old rule
- observed path
- proposed authority
```
