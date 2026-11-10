# Claude Agent SDK fixture privacy

This fixture is captured against the repository's local scripted model server,
using a temporary HOME, a fake API key and a loopback `ANTHROPIC_BASE_URL`.
No paid model or subscription is used. Attest 1.1 replaces Claude Code identity
values with placeholders (`device_id` → `{{device_1}}`, `session_id` →
`{{session_1}}`); `account_uuid` is empty. No raw identity values remain.

This recording was made with the published 1.1.0-rc.5 engine inside a macOS
`sandbox-exec` profile that permits only loopback networking. The stub received
exactly two Anthropic Messages requests: a tool call, then the final answer.

Older commits contain a Claude Code `device_id` in this example's fixture.
The owner has chosen not to rewrite Git history: removing it from the current
fixture does not erase old commits, forks or caches. Do not treat a checkout of
an older fixture as privacy-sanitized.
