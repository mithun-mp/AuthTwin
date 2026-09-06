# Non-Negotiable Project Boundaries & Assumptions

1. **NO FAKE VULNERABILITY FINDINGS**: Do not generate dummy security findings or claims of "IDOR Found" or "Access Granted" in Milestone 1. Shadow workflows are structural clones only.
2. **NO CREDENTIAL LEAKAGE**: Source identity authentication tokens, cookies, and secret headers MUST NEVER be copied into alternate identity shadow workflows.
3. **NO UNSANCTIONED REPLAY**: Replaying requests against target APIs is explicitly disabled in Milestone 1.
4. **NO PROPRIETARY BLACK-BOX AI DECISIONS**: Core workflow reconstruction, dependency mapping, and state graph generation MUST be 100% deterministic and evidence-backed.
5. **REAL BACKEND CONTRACTS**: The UI MUST display real data returned from backend API endpoints and SQLite database queries—never hardcoded mock statistics pretending to be live system state.
