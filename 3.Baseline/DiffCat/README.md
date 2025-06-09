# DiffCat

> **DiffCat** is a tool that pin‑points the *non‑essential* (i.e., cosmetic and behaviour‑preserving) changes in code changes.

---


## 1  How DiffCat is worked

| Module | What it does |
|---------|--------------|
| **Patch Change Parser** | Scans a patch and splits each hunk into *added* and *deleted* lines, then aligns the two sets so every addition is paired with its corresponding deletion. |
| **First‑Preprocess** | Applies consistent formatting, and strips superfluous comments and blank lines. |
| **AST Builder** | Generates abstract‑syntax trees for the cleaned C/C++ files, giving later analyses a precise, language‑aware view of the code. |
| **Rename Detector** | Uses the ASTs to spot pairs of added/deleted lines that are simply the same symbol (function, variable, type) renamed. |
| **Non‑essential Classifier** | Labels a change as *non‑essential* when, after reversing any rename operations, the resulting code fragment is identical to the original. |


## 2  Using DiffCat

### 2.1  Input

* A **change set**: the list of files changed in one commit. 

### 2.2  Output
The output consists of two parts: the set of essential changes in the patch and the set of non‑essential changes in the patch.
