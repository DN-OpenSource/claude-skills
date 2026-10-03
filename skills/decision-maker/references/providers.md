# Providers

Providers are named `{base_url, path, model, api_key | api_key_env}` entries. They live in `~/.config/decision-maker/providers.json` (override the location with `$DECISION_MAKER_CONFIG`), which is outside every repo and is written with mode 600.

| Want | Command |
|---|---|
| Add any provider/gateway | `provider add NAME --base-url URL --api-key-env VAR [--model M] [--path /v1/systemone] [--default]` |
| Change its base URL / key / model | `provider edit NAME --base-url URL` · `--api-key-env VAR` · `--api-key KEY` · `--model M` |
| Switch the default | `provider use NAME` (or `$DECISION_MAKER_PROVIDER`, or `--provider NAME` per call) |
| Remove | `provider remove NAME` (presets can be edited, not removed) |
| Check what a provider serves | `models --provider NAME` |

Prefer `--api-key-env`, which stores only the variable's name. Use `--api-key` only when the user asks to store the key itself. **Never** write a key into the repo, a SKILL/README example, or a commit. `provider list` masks stored keys. A provider qualifies if it speaks the System One wire format (`POST {base_url}/v1/systemone`, Bearer auth). TypeSafe direct, OpenRouter, OpenJEV (`provider use openjev` + `OPENJEV_API_KEY`) and LiteLLM's `/typesafe` pass-through are verified presets. See `api.md` for the request and response shapes, limits, and errors.
