# FDA Explorer Decisions

This records later user decisions without rewriting the original baseline plan or historical measurements. When requirements conflict, the latest explicit user decision governs.

## October 9, 2026: Performance Expectations

The two-second five-client target in the baseline plan was provisional, not an original CLI requirement, a correctness condition, or a hosting restriction. The original CLI performance requirement concerned a single invocation. The web concurrency test was an additional planning check.

The user accepts a relatively long wait provided the default, all-year overview achieves **warm request latency p95 strictly below 10 seconds with five simultaneous requesters**, while the application fits the available free computing power, memory, and storage. Hosting must remain **$0**. The previous two-second target is no longer a required acceptance threshold; do not pursue it at the expense of scope or unnecessary complexity.

The user explicitly clarified that the acceptance statistic is p95, not the maximum: **p95 < 10,000 ms**. Measure individual request response times under five-client concurrency, not the sum of five response times. Record individual completions, median, p95, and maximum for diagnosis, but a maximum above ten seconds alone does not fail this latency criterion. The user did not set a new hard threshold for every arbitrary filtered selection. Keep measuring those cases and flag severe delays, without silently imposing the old two-second target on them.

Service wake-up remains a separate, previously accepted condition, with a clearly labeled saved overview. A warm-request benchmark does not include wake-up. Future API/frontend measurements must include request handling, serialization, queue wait, and rendering/network context as appropriate; local SQLite-only tests do not prove actual hosted behavior. The real selected free host's limits must be verified before deployment. Earlier memory/payload targets are planning headroom, not provider limits or newly imposed user requirements.

### Existing Evidence

The final Slice 2 constrained default-overview measurements were median 10.10 seconds, p95 13.05 seconds, and maximum 17.20 seconds with five simultaneous readers. These remain unchanged historical results. The p95 of 13.05 seconds does not meet the revised p95-below-ten-seconds criterion; the maximum is diagnostic only. Other measured five-client cases had p95 below ten seconds. SQLite-only peak resident memory was 76.67 MiB; the database was 59.27 MiB. Neither measurement establishes that the whole eventual hosted application fits all provider limits.

### Recommended Next Step

Because this snapshot and its default filters are fixed, the versioned release already contains the complete default overview. First test reusing that prepared response for simultaneous default requests instead of recalculating it separately for each reader. Check release identity and labels; changing year/product filters must still return the correct selected result, never an unrelated default answer.

Profile this path under the same constraints and preserve filtered-query parity. This is a recommendation, not authorization to start another implementation slice, an API/frontend, or deployment. Existing Slice 2 correctness results and the three pre-existing upstream test-expectation failures are unaffected by the revised latency goal.
