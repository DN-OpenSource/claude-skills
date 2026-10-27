# AGENTS.md — shop

## Purpose
A tiny shop backend: `schema.sql`, `app.py` (SQLite) and `utils.py` helpers.

## Ownership
Root contract for the whole repo.

## Local Contracts
- Keep helpers in `utils.py` pure: no database access.
- Every change to `utils.py` keeps `test_utils.py` passing.

## Verification
`python -m pytest -q`

## Child DOX Index
_(none)_
