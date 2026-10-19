# Run `findbox/main` is incomplete: 9 of 10 languages

The task (variant `besteffort`, spec `phi1`) was **stopped on 2026-10-19 at about 02:55**, after 5.5 h. The other
nine languages are complete and are unaffected (their records and box files were written when each task finished).

**Why it was stopped.** FindBox's `recon` step groups corner points by exact coordinate value using Python list
lookups. Its cost explodes when the corners have distinct floating-point coordinates, as they do with continuous
sampling. Measured on the same formula and setting (`results/logs/findbox_recon_scaling.log`):

| sample points | corners | recon time |
|---|---|---|
| 50 | 2,028 | 26 s |
| 100 | 4,034 | 72 s |
| 200 | 8,038 | 542 s |

At 1,000 points (about 40,000 corners), extrapolation gives 16–20 h or more for `recon` alone. The default (integer)
variant of φ1 finished in 73 min, because integer corners share coordinates.

**Consequences.**
- No best-effort φ1 language exists.
- `falsification/findbox_besteffort` therefore covers φ2–φ5 only, and `findbox_quality_main.md` covers 9 languages.
- The meta.json of this run has no "finished" entry, because the run was stopped.

**To complete it** (16–20 h or more):
`python experiments/run_findbox.py --config configs/findbox.yaml --run-id main --variants besteffort --specs phi1`
