# CoCoPATER
## ⭐ New Update For Revision

We have added the [priliminary study](5.Priliminary/), new [approach component](1.Prototype/ast_parser.py), and corresponding [experiments](2.Evaluation/) for supporing Major Revision.


## ⭐ New Experiment and Results Update For Rebutall

Here is the additional experiment demonstrtated for [Rebuttal](https://github.com/CCpatchCopalot/COCOPATER/tree/main/4.Rebuttal).
------------------------------

With the rapid development of open-source software (OSS), the number of OSS vulnerabilities has been increasing rapidly. To mitigate such security risks, vulnerability patches are deployed across a wide range of security tasks. However, patches may contain noncritical changes. Such tangled patches can hurt the effectiveness and efficiency of these security tasks. Existing approaches of identifying critical changes often lack precise inter-procedural analysis, work at a coarse granularity, or do not scale well to large and complex patches, limiting their effectiveness.

To address these limitations, we propose a novel approach CoCoPATER to identify critical changes in a vulnerability patch at the statement level. CoCoPATER decompose critical changes identification into two phases, i.e., function-level and statement-level phases. CoCoPATER follows a filtering-then-recovering strategy in each phase to first pinpoint a necessary minimal set of critical changes by semantic-enhanced LLM, then recover any semantically similar and functionally related critical changes. Our evaluation demonstrates that CoCoPATER outperforms state-of-the-art approaches by at least 0.42 (95%) at F1-score. Moreover, by integrating CoCoPATER with tools of three downstream tasks (i.e., vulnerable version identification, patch backporting and recurring vulnerability detection), those tools show the improvement both in effectiveness and efficiency, underscoring the value of identifying critical changes in vulnerability patches.

This is source code and detaset of the tool `CoCoPATER` which can identifying critical changes in vulnerability patches.


# [1.Prototype](https://github.com/CCpatchCopalot/COCOPATER/tree/main/1.Prototype)

## Phase 1: Critical Functions Extraction

Phase 1 implements a "filtering-then-recovering" pipeline to isolate the most relevant functions responsible for the vulnerability fix.  We begin by normalizing each changed file via semantic equivalence transformations, stripping away purely syntactic edits to focus on meaningful changes. Next, we extract three complementary signatures: inter-procedural call graph summaries, intra-procedural statement flow around diff hunks, and vulnerability knowledge (descriptions and CWE) from CVE reports.  These signatures guide a semantic-enhanced LLM in filtering out non-critical functions, producing an initial core set.  To ensure completeness, we recover semantically similar variants using CodeBERT and then expand the set through backward and forward inter-procedural data-dependency analysis powered by Joern.  The result is one or more ordered critical function chains capturing both vulnerable logic and its propagation paths.

### 1.1 Semantic Equivalent Statements Transformation
In this step, we apply AST-based semantic equivalence transformations using curated patterns (e.g., arithmetic/logical simplifications, loop refactoring, macro expansion) to strip away syntactic noise and retain only meaningful semantic changes. The related file included `code_transformation.py` and `ast_parser.py`. The detailed file structures are:

- `code_transformation.py`
  - `operator_extraction`
  - `del_DeadCode`
  - `while_for_transformation`
  - `move_definition`
  - `split_define_assign`
  - `merge_control_blocks`
  - `split_control_blocks`
  - `del_qualifier`
  - `modify_if_else`
  - `code_transformation`
- `ast_parser.py`
  - `ASTParser`
### 1.2 Core Critical Functions Extraction
We aggregate inter-procedural call graph signatures, intra-procedural statement flow around diff hunks, and CVE-derived vulnerability knowledge to prompt the LLM for filtering and ranking the core critical functions. The related file included `function_clustering.py`, `vul_pat_cg.py`, `critical_vul_extract.py`, `callgraph_formatted` and `cg_path.py`. The detailed file structures are:

- `function_clustering.py`
  - `export_joern_graph`
  - `get_pre_post_call`
- `trigger_analysis/vul_pat_cg.py`
  - `extract_vuln_functions(desc, cg, pat)`
- `trigger_analysis/critical_vul_extract.py`
  - `find_called_functions(cg, llm_methods)`
  - `filter_call_data(cg, called_methods)`
- `callgraph_formatted.py`
  - `process_graph(graph_part, part_name, target)`
- `cg_path.py`
  - `func_path_extract(trigger_point, modified_point, cache_dir)`

### 1.3 Critical Function Chains Construction
By encoding F_core functions with CodeBERT to recover semantically similar variants and performing backward/forward data-dependency analysis on Joern-generated PDGs, we build ordered critical function chains that trace vulnerability propagation. The related file included `codebert.py`, `joern.py`, and `function_clustering.py`. The detailed file structures are:
- `codebert.py`
  - `codebert_sim(core_func_list, pre_function_dict, post_function_dict)`
- `joern.py`
  - `export_with_preprocess_and_merge(code_path, output_path, language, overwrite, cdg_need)`
  - `CPG` and `PDG` classes for graph construction and analysis
- `function_clustering.py`
  - Backward and forward inter-procedural data dependency analysis via Joern

## Phase 2: Critical Statements Extraction

Phase 2 drills down inside each critical function chain to identify the atomic statements that enact the vulnerability fix.  We extract fine-grained inter-procedural taint paths for changed variables, merging pre- and post-patch sequences to form candidate statement sequences.  These candidates, together with vulnerability knowledge, are presented to the LLM to filter for core critical statement sequences, honoring the same filtering-then-recovering ethos.  Semantic recovery leverages CodeBERT to include similar sequences, and a monitoring mechanism (static linting or compilation checks) iteratively reintroduces additional statements from the original patch until all compatibility errors are resolved.  The final output is a concise, semantically complete patch aligned with the vulnerability context.

### 2.1 Candidate Critical Statement Sequences Extraction
For each function chain, we extract backward and forward inter-procedural taint paths for changed variables, merging pre- and post-patch contexts into unified candidate statement sequences. The related file included `taint_analysis.py` and `merge_taint_path.py`. The detailed file structures are:

- `taint_analysis.py`
  - `taint_analysis_all`
  - `mapping_taint_path`
  - `taint_analysis`
- `merge_taint_path.py`
  - `process_string(s)`
  - `merge_string_lists(list1, list2)`

### 2.2 Core Critical Statement Sequences Extraction
The LLM is guided by vulnerability knowledge and candidate taint sequences to filter and select the top-ranked core critical statement sequences for precise remediation.

- `trigger_analysis/vul_pat_cg.py`
  - `extract_vuln_patch(desc, pat, taint_pats)`

### 2.3 Critical Statements Expansion
We recover semantic variants of core sequences via CodeBERT and iteratively reintroduce pending statements under a compatibility monitor (static lint or compile checks) until all errors are resolved, yielding the final concise and complete patch.
- `recovery.py`
- - `CodeBERTSimilarity`
  - `CodeMapper(original_code, transformed_code)`
  - `checking_recovery(pa, pb, pc, pC)`
- `get_ccpost.py`
  - `apply_diff_in_memory(repo_path, commit_hash, file_path, diff_path)`
  - 

# [2.Evaluation](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation)

## [Baselines](https://github.com/CCpatchCopalot/COCOPATER/tree/main/3.Baseline)
- [SmaretCommit](https://github.com/CCpatchCopalot/COCOPATER/tree/main/3.Baseline/smartcommit_c_cpp)
- [DiffCat](https://github.com/CCpatchCopalot/COCOPATER/tree/main/3.Baseline/DiffCat)
- PRIMEVUL
- [PRIMEVUL++](https://github.com/CCpatchCopalot/COCOPATER/tree/main/3.Baseline/PRIMEVUL%2B%2B)

## [GroundTruth](https://github.com/CCpatchCopalot/COCOPATER/tree/main/0.GroundTruth)

- Initial [1,553](https://github.com/CCpatchCopalot/COCOPATER/blob/main/0.GroundTruth/dataset_all.json) collected C/C++ vulnerability patches; 

- 203 CVEs with [Tangled Patches](https://github.com/CCpatchCopalot/COCOPATER/blob/main/0.GroundTruth/ccpatch_dataset.json), [CC Patches](https://github.com/CCpatchCopalot/COCOPATER/tree/main/0.GroundTruth/ccpatch) and their executable [PoCs](https://github.com/CCpatchCopalot/COCOPATER/tree/main/0.GroundTruth/poc_oracle) for verifying;


## [RQ1 Effectiveness](https://github.com/CCpatchCopalot/COCOPATER/tree/main/RQ1.Effectiveness)


We assessed CoCoPATER using the ground truth, and compared its performance with baseline approaches. See [RQ1 results](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ1.Effectiveness/results.json).

- the raw results of `CoCoPATER` is shown in [results_cocopater](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ1.Effectiveness/results_cocopater)
- The raw results of `PRIMEVUL` is shown in [prime_vul_results](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ1.Effectiveness/primevul_results)
- the raw results of `PRIMEVUL++` is shown in [results_prevul++](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ1.Effectiveness/results_prevul%2B%2B)
- the raw results of `SmartCommit` is shown in [results_SmartCommit](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ1.Effectiveness/results_SmartCommit)
- the raw results of `DiffCat` is shown in [results_diffcat](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ1.Effectiveness/results_diffcat)

For  `PRIMEVUL`, just run `python get_baseline_results.py` to get the function-level effectiveness of it.
For other baseline and `cocopater`:
  - To get the patch-level results, just run in the following steps:
      1. modify the result directory path in the line 7 of `get_diff.py` and run `python get_diff.py` to format the results.
      2. modify the repository directory and result directory path in the line 25 and 27 of `get_results_post.py` and run `python get_results_post.py` to get the characterics of the generated patch.
      3. run `python get_baseline_results.py` to get the function-level effectiveness of them.
  - To get the statement-level effectiveness, just modify the repository directory and result directory path in the line 25 and 27 of `get_baseline_results_stmt_level.py` and run `python get_baseline_results_stmt_level.py`


## [RQ2 Ablation](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ2.Ablation)
We created six ablated versions for CoCoPATER (See [RQ2 results](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ2.Ablation/results.json))

    (1) identifying critical functions using the LLM without the intra-/inter-procedural signatures extraction module (w/o Sig);

    (2) removing the critical function chains construction module (w/o FC); 

    (3) switching GPT-4o to GPT-3.5 [39] (w/GPT3.5);

    (4) removing the equivalent transformation module (w/o trans);

    (5) identifying critical statements using the LLM without the core statement sequence extraction module (w/o Seq);

    (6) removing the monitor module (w/o mon);

To get the results of the ablated versions, follow the similiar step of RQ1.


## [RQ3 Generality](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality)

**Generality Dataset Construction.** To demonstrate the generality of CoCoPATER in real-world scenarios, we constructed a new dataset containing both tangled patches and CC patches. 

We began by excluding our benchmark CVEs from the collected vulnerabilities in C/C++ projects, and then randomly sampled 781 CVEs with the corresponding patches with a confidence level of 99% and a margin of error of 3%. Two analysts independently tagged each patch as either a tangled or a CC.

Any disagreements were resolved by a third author, achieving [Kappa of 0.949](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/dataset/kappa) for tangled patch identification and 0.892 for CC patch construction. This process identified [227 tangled patches]((https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/dataset/generality_gt/generality_tangled_before)) and [554 CC patches](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/dataset/generality_gt/generality_clean) with 400 human-hours.


**Result.** To demonstrate the generality of CoCoPATER in real-world scenarios, we constructed a new dataset containing both tangled patches and CC patches. The results is in [RQ3 results](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results.json).

- the raw results of `CoCoPATER` is shown in [results_cocopater](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results_cocopater)
- The raw results of `PRIMEVUL` is shown in [results_primevul](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results_primevul)
- the raw results of `PRIMEVUL++` is shown in [results_privevul++](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results_privevul++)
- the raw results of `SmartCommit` is shown in [results_SmartCommit](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results_SmartCommit)
- the raw results of `DiffCat` is shown in [results_diffcat](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ3.Generality/results_diffcat)

To get the results of the baselines on the generality dataset, follow the similiar step of RQ1.


## [RQ4 Sensitivity](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ4.Sensitivity)

To analysis how do the configurable parameters affect the effectiveness of CoCoPATER, run the following command to analysis the sensitivity of topF and topS.
```
python Sensitivity_Func.py
```

```
python Sensitivity_Stmt.py
```


## [RQ5 Efficiency](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ5.Efficiency)

CoCOPATER takes 21.7 seconds to construct a CC patch on average, demonstrating its efficiency in real-world applications. The results is shown in [results.json](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ5.Efficiency/efficiency.json)

## [RQ6 Usefulness](https://github.com/CCpatchCopalot/COCOPATER/tree/main/2.Evaluation/RQ6.Usefulness)

### Vulnerable Version Identification

- GroundTruth Dataset: [Dataset](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ6.Usefulness/TASK_I/groundtruth.json)
- Baseline: [VSZZ](https://github.com/baolingfeng/V-SZZ)
- Result:  [Results](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ6.Usefulness/TASK_I/results.json)

### Patch BackPorting

- Baseline: [TSBPORT](https://sites.google.com/view/tsbport), [Cherry Pick](https://git-scm.com/docs/git-cherry-pick)
- Result: [Results](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ6.Usefulness/TASK_II/results.json)

### Recurring Vulnerability Detection

- GroundTruth Dataset: [Dataset](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ6.Usefulness/TASK_III/groundtruth.xlsx)
- Baseline: [VUDDY](https://github.com/squizz617/vuddy), [FIRE](https://github.com/CGCL-codes/FIRE)
- Result:  [Results](https://github.com/CCpatchCopalot/COCOPATER/blob/main/2.Evaluation/RQ6.Usefulness/TASK_III/results.json)

