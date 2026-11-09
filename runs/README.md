# Runs log

`runs_log.jsonl` is appended by every backtest run (`crt_robot.backtest.runlog`):
one JSON object per line with the run id, git commit, strategy, parameters,
engine config, data span, whether the locked holdout was used, and the summary.
Commit it: it is the record of every parameter combination tried (BUILD_PLAN 3.3).
