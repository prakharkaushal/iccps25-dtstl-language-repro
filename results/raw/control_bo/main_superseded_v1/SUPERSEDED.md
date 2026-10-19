# Superseded run (kept for provenance; do not use)

This E6 run (2026-10-18 19:42-20:06) used plain RTAMT robustness of phi as BO's objective and success test
(rho >= 0). LangControl (E5) instead tests membership in the domain-bounded language (D19), which rejects
trajectories leaving the signal domain. With random references, over half of the tracked trajectories leave
the domain, so the two success tests differ strongly (e.g. phi3: 81.5 % vs 40.4 % of random references), which
made the BO-vs-LCW comparison unfair in BO's favour (it reported a BO/LCW ratio of 0.34).
Fix: BO now uses RTAMT robustness of (phi AND always(x in domain)), whose sign equals the language test
(tests/test_control.py::test_domain_bounded_robustness_matches_language_membership). Re-run as run-id `main`.
