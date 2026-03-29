# Data-plane migration matrix (sprint-1)

| Domain | Status | Notes |
|---|---|---|
| users | implemented | Discovery + auto-match (XML_ID/email/login), ambiguous/unmatched queue, manual override, blocking semantics for downstream domains. |
| groups | partial | Mapping + create/reuse decision persistence + risk notes. Membership data accepted via payload, but external target write adapters are mocked through `MigratedRecord`. |
| projects | partial | Same as groups. |
| tasks | partial | Real dependency-checked migration over mapping layer with explicit blocked/partial statuses. External transport adapter is mocked in current sprint. |
| comments | partial | Parent task + author relation checks and migration report states are implemented. |
| file refs | partial | Metadata/reference migration implemented. Heavy payload copy intentionally not implemented (explicit partial verification status). |

## Execution order

`users -> groups -> projects -> tasks -> comments -> file_refs`

## Safety guarantees in sprint-1

- No cross-domain relation relies on source/target ID equality.
- Unresolved users prevent safe execution for dependent domains.
- Ambiguous/unmatched mappings are reviewable and must be resolved/overridden explicitly.
