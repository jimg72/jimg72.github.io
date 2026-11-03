# Frozen Tundra all-play calculator

Standalone Python 3.9+ command-line utility, using only the standard library.
No Jekyll, fantasy provider, lineup optimizer, or third-party package dependency.
Run commands from the repository root.

## Reproduce Week 7

```bash
python3 scripts/fantasy/all_play.py scripts/fantasy/examples/week7-checkpoint.json
```

This prints a weekly table and cumulative table ready to paste into a newsletter.
Use `--output report.md` to save Markdown. The supplied checkpoint includes the
12 owners, actual records, and all-play records through Week 7, plus the verified
Week 7 scores and matchups for display. Those scores are **not added again**.
The optional `checkpoint.last_week` is display-only and must use `matchups`.

Source: [October 27 Week 7 newsletter](../../_posts/2026-10-27-frozen-tundra-week-7.md).
The checkpoint transcribes its cumulative totals; it does not independently
reconstruct Weeks 1–6. Week 7 scores sum to **1,273.6**. Each cumulative record has
77 comparisons. Scott's 53–23–1 yields 4.9 expected wins and +2.1 luck.
No Week 8 scores or results are supplied.

## Add the next completed week

Copy `scripts/fantasy/examples/week7-scores.json` to a working file such as
`week8.json`. Replace the week number, **every score**, and all six matchup pairs
with final results for that week. Do not reuse Week 7 values as placeholders.
The utility checks completeness and consistency, but cannot determine whether
scores are final or match the league provider.

```bash
python3 scripts/fantasy/all_play.py \
  scripts/fantasy/examples/week7-checkpoint.json \
  --week week8.json \
  --output week8-tables.md \
  --save-checkpoint through-week8.json
```

Then use `through-week8.json --week week9.json` for the next completed week.
Saved checkpoints contain cumulative integer records without rounded metrics.
They omit old weekly scores; keep your weekly files if you need that history.
You can instead repeat `--week` in order, or place weekly objects inside the
season file's `weeks` array. Embedded weeks run first, followed by `--week` files.
A repeated, skipped, or out-of-order week is rejected rather than double-counted.
Output paths must differ from inputs and from each other.

## JSON contract

The sample files are complete runnable examples. All records are integer arrays
in `[wins, losses, ties]` order. Team names are stable identifiers; use the same
12 unique names everywhere. Scores may be JSON numbers or decimal strings;
strings preserve the exact supplied precision. Negative scores are supported.
Null, boolean, nonnumeric, and nonfinite scores are rejected.

A season contains:

- `teams`: the 12 owner names, in preferred order for equal all-play credit.
- `checkpoint` (optional): `through_week`, `actual_records`, and `all_play`,
  each record mapping containing exactly those 12 owners. Optional `last_week`
  can display the checkpoint's latest weekly scores without accumulating them.
- `weeks` (optional): an ordered array of completed weekly objects.

Without a checkpoint, processing starts at Week 1 with zero records. Every team
must play exactly one actual game and 11 all-play comparisons per week. Byes,
doubleheaders, median games, and changing league membership are not supported.

Each weekly object contains `week`, a `scores` mapping for all owners, and
**exactly one** of:

- `matchups`: six `[owner, opponent]` pairs, each owner appearing once. Actual
  wins/losses/ties are derived from the supplied scores; equal scores tie.
- `actual_records`: cumulative actual W–L–T records **through that week** for all
  12 owners, not weekly increments. The calculator subtracts the preceding
  records and requires exactly one new decision per owner, balanced league-wide.
  Use this when the provider resolves tied scores using a separate tiebreaker;
  all-play still treats equal scores as ties. These official records are trusted
  because this input mode does not specify opponents.

For record-based input, replace `matchups` with `actual_records` and copy the
mapping structure from the checkpoint, updating all values to current records.
The standalone `week7-scores.json` is a weekly object, not a season file; it is
included as a template and regression fixture, not an increment to Week 7.

## Calculations and presentation

Every score is compared to each of the other 11 scores. Equal decimal values
produce ties, with no rounding or floating-point tolerance before comparisons.
Weekly all-play records add to cumulative integer records.

- Expected wins = `(all_play_wins + 0.5 * all_play_ties) / 11`.
- Luck = `actual_wins - unrounded_expected_wins`.
- Actual matchup ties stay in the W–L–T record but do **not** receive half-win
  credit in luck. This intentionally follows the published newsletter formula.
  Consequently total luck need not be zero in weeks with actual matchup ties.
- Metrics round half up to one decimal for display only; negative zero is
  normalized. Scores and the weekly league total retain supplied precision.
- Tables sort by all-play win credit descending, then original roster order.
  This is not playoff seeding. Weekly tables use weekly actual results and luck;
  the cumulative table uses season totals. Checkpoint-only reports can display
  only the cumulative table when `last_week` is absent.

Validation checks record lengths and counts, balanced wins/losses, paired ties,
rosters, matchups, decimal values, duplicate JSON keys, and week continuity. It
cannot prove a historical checkpoint's full schedule from aggregate totals.
To correct an already-counted week, correct its source and rerun from an earlier
checkpoint (or the full season); do not append the same week again.

## Tests

```bash
python3 -m unittest discover -s scripts/fantasy/tests -v
```

Regressions cover all 12 Week 7 all-play ranks, the league total, all published
expected-win/luck figures, Scott and Phil's historical tie, checkpoint replay,
record-based input, checkpoint export, Markdown/CLI output, malformed input,
and synthetic tied-score scenarios. Synthetic cases use Week 1 and are not
presented as real league results.
