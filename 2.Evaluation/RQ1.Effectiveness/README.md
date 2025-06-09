We assessed Copalot using the ground truth, and compared its performance with baseline approaches. See [RQ1 results](results.json).
- The raw results of `PRIMEVUL` is shown in [prime_vul_results](prime_vul_results), the raw results of `PRIMEVUL++` is shown in [results_prevul++](results_prevul++), and the raw results of `Copalot` is shown in [results_cocopater](results_cocopater)
- For  `PRIMEVUL`, just run `python get_baseline_results.py` to get the function-level effectiveness of it.
- For other baseline and `cocopater`:
    - To get the patch-level results, just run in the following steps:
        1. modify the result directory path in the line 7 of `get_diff.py` and run `python get_diff.py` to format the results.
        2. modify the repository directory and result directory path in the line 25 and 27 of `get_results_post.py` and run `python get_results_post.py` to get the characterics of the generated patch.
        3. run `python get_baseline_results.py` to get the function-level effectiveness of them.
    - To get the statement-level effectiveness, just modify the repository directory and result directory path in the line 25 and 27 of `get_baseline_results_stmt_level.py` and run `python get_baseline_results_stmt_level.py`
