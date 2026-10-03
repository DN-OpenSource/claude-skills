# System One API — the facts decide.py relies on

Source: https://docs.typesafe.ai/api.md and /models.md (fetched 2026-10). The live docs win if they disagree — re-read them before writing integration code (index: https://docs.typesafe.ai/llms.txt).

## Endpoint

```http
POST {base_url}/v1/systemone
Authorization: Bearer <API_KEY>
Content-Type: application/json
```

`GET {base_url}/v1/models` lists model names. Model `jev-latest` (alias) → `jev-1.13.0` today; pin the versioned id once you've tuned thresholds against it.

## Request

```json
{
  "state": "text, or a JSON object/array",
  "model": "jev-latest",
  "questions": {
    "<your id>": { "type": "noul",   "instructions": "Yes/no question?", "criteria": {"true": "...", "false": "..."} },
    "<your id>": { "type": "choice", "instructions": "Which one?", "criteria": {"opt_a": "desc", "opt_b": null} },
    "<your id>": { "type": "score",  "instructions": "How much?",  "criteria": ["lowest level", "…", "highest level"] }
  }
}
```

- Question ids are for your code only; they are **not** sent to the model, so put the full meaning in `instructions`.
- `instructions` and `criteria` values may be strings, objects, or arrays. Refer to nested state with backticks: `` `ticket.messages[0].text` ``.
- Choice: 2–255 options (include a no-match option when nothing may fit). Score: 2–10 ordered, self-describing levels. Noul `criteria` is optional.
- All questions run in parallel against one ingest of `state` and cannot see each other's answers.

## Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_urgent":  { "type": "noul", "noul": 0.95 },
    "department": { "type": "choice", "choice": "billing",
                    "probabilities": {"billing": 0.88, "technical": 0.12, "sales": 0.0}, "confidence": 0.81 },
    "frustration":{ "type": "score", "score": 1.05, "legend": {"0": "Calm", "1": "Frustrated", "2": "Very angry"},
                    "probabilities": {"0": 0.0, "1": 0.95, "2": 0.05}, "confidence": 0.92 }
  },
  "usage": { "input_tokens": 304, "output_tokens": 18 }
}
```

Confidence (Choice/Score only) measures how concentrated the distribution is, not whether acting is safe. A Noul near 0.5 means "could be either", not "medium". `decide.py` adds `act: true|false` per answer from `--min-confidence` (Noul uses `max(p, 1-p)`).

## Limits & errors

- Context: 64k tokens per request (state + all questions); 32k for state + the longest single question. Text only.
- Price: per input token; output tokens are free. Rate limits are in tokens/s and requests/s.
- `401` bad key · `422` invalid body (details in body) · `429` rate limited · `529` overloaded. Retry 429/529 with exponential backoff and honor `retry-after` (decide.py does).

## Providers that speak this wire format

| Preset | base_url | model | key env |
|---|---|---|---|
| `typesafe` | `https://api.typesafe.ai` (or `$TYPESAFE_BASE_URL`) | `jev-latest` (or `$TYPESAFE_DEFAULT_MODEL`) | `TYPESAFE_API_KEY` |
| `openrouter` | `https://openrouter.ai/api` | `~typesafe/jev-latest` | `OPENROUTER_API_KEY` |
| `openjev` | `https://api.openjev.sh` | `openjev` (its default) | `OPENJEV_API_KEY` |
| `litellm` | `http://localhost:4000/typesafe` (your proxy URL + `/typesafe`) | `jev-latest` | `LITELLM_API_KEY` (virtual key) |

OpenJEV ([docs](https://openjev.sh/docs)) is an independent public gateway to Jev and is not affiliated with TypeSafe. It can return `503` when temporarily unavailable; decide.py retries that with backoff like 429/529.

Any other gateway that forwards `/v1/systemone` unchanged works too: `decide.py provider add <name> --base-url … --api-key-env …`.
