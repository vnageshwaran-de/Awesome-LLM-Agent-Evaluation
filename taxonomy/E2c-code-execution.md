# E2c — Code execution environments

**Pillar:** III — WHERE it is tested (Environment Topologies; dynamic E2)

**Definition.** Repository- or interpreter-backed environments that execute the agent's edits against a real test suite (bug fixing, feature implementation, test satisfaction).

**Strength.** The topology where programmatic scoring (H1) is most defensible — the test suite is an objective, pre-existing oracle.

**Limitation.** Partiality of test coverage (passing tests is necessary but not sufficient for correctness); contamination risk for public repositories whose issues and fixes appear in training data.

**Benchmarks:** SWE-bench (Dockerized GitHub repos); AgentBench (code/DB environments).
