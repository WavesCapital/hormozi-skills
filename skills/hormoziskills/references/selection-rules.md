# Hormozi Router Selection Rules

1. If the user already names a specific `hormozi-*` skill, do not interpose.
2. Return one primary skill and at most two supporting skills.
3. Use the narrowest child skill that matches the requested outcome.
4. Use supporting skills only when they materially change the output.
5. If a best-match skill is planned or missing, say so and use the declared fallback.
6. Do not route generic business or marketing prompts here unless the user explicitly asks for Hormozi-skill routing.
