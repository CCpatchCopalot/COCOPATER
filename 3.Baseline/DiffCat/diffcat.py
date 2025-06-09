from loc_patch import *

import json
import re
from typing import Dict, List, Tuple, Any

"""diffcat.py
A minimal, extensible Python implementation of a DIFFCAT‑style filter for C/C++ patch‑diffs.

The script expects a single JSON file on stdin *or* as a positional argument that contains
one root object whose keys are file paths and whose values are objects with two arrays:
    "add"   – array of inserted hunks
    "delete" – array of removed  hunks
(The exact schema mirrors the example in the prompt.)

It prints **two** JSON documents on stdout:
1. an array   "non_essential" – the hunks flagged as cosmetic / non‑essential
2. an object  "filtered_patch" – the original patch with the flagged hunks removed

The matching logic is intentionally lightweight:
    * whitespace / comment only edits
    * addition or removal of *const*, *inline*, *static*, *constexpr* qualifiers
    * simple namespace qualification changes (e.g., string -> std::string)

For deeper semantic reasoning (e.g., rename ripples) plug in libclang via the `ClangASTRule` stub.
"""

##############################
# Generic data structures
##############################

Hunk = Dict[str, Any]  # {start, end, code, ...}
FilePatch = Dict[str, List[Hunk]]  # {'add': [...], 'delete': [...]}
PatchDiff = Dict[str, FilePatch]  # {file path: {'add': [...], 'delete': [...]}}


class Rule:
    """Base class for a non‑essential‑difference detection rule."""

    def match(self, delete: Hunk, add: Hunk) -> bool:
        raise NotImplementedError


##############################
# Heuristic rules
##############################

def _strip_comments(code: str) -> str:
    """Very rough C/C++ comment stripper (// and /* */)."""
    code = re.sub(r"//.*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return code


class WhitespaceRule(Rule):
    """Only whitespace (and comment) changes."""

    def match(self, delete: Hunk, add: Hunk) -> bool:
        old = _strip_comments(delete["code"]).strip()
        new = _strip_comments(add["code"]).strip()
        return old == new


class ConstQualifierRule(Rule):
    """Addition or removal of const / storage qualifiers only."""
    _qualifiers = re.compile(r"\b(constexpr|const|static|inline|volatile|register)\b")

    def _without_qualifiers(self, s: str) -> str:
        return self._qualifiers.sub("", s)

    def match(self, delete: Hunk, add: Hunk) -> bool:
        old = self._without_qualifiers(delete["code"]).strip()
        new = self._without_qualifiers(add["code"]).strip()
        return old == new


class NamespaceQualificationRule(Rule):
    """Changes like string -> std::string (simple prefix swap)."""
    _ns_prefix = re.compile(r"\b([a-zA-Z_][\w:]*)::")

    def _strip_ns(self, s: str) -> str:
        return self._ns_prefix.sub("", s)

    def match(self, delete: Hunk, add: Hunk) -> bool:
        old = self._strip_ns(delete["code"]).strip()
        new = self._strip_ns(add["code"]).strip()
        return old == new


class ClangASTRule(Rule):
    """Placeholder – use libclang to detect rename‑induced reference updates."
    """

    def _tokenise(self, code: str) -> List[str]:
        TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\S")
        """Very light tokeniser: identifiers vs. every other single char."""
        return TOKEN_RE.findall(code)

    def match(self, delete: Hunk, add: Hunk) -> bool:
        IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
        if (delete["end"] != delete["start"] or
                add["end"] != add["start"]):
            return False

        old_line = delete["code"].strip()
        new_line = add["code"].strip()

        old_toks = self._tokenise(old_line)
        new_toks = self._tokenise(new_line)
        if len(old_toks) != len(new_toks):
            return False

        diff_pairs = [(o, n) for o, n in zip(old_toks, new_toks) if o != n]
        if len(diff_pairs) != 1:
            return False

        old_tok, new_tok = diff_pairs[0]
        return bool(IDENT_RE.fullmatch(old_tok) and IDENT_RE.fullmatch(new_tok))


##############################
# Core processing
##############################

RULES: List[Rule] = [WhitespaceRule(), ConstQualifierRule(), NamespaceQualificationRule(), ClangASTRule()]


def is_c_cpp_file(file_path: str) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    file_name = os.path.basename(file_path)
    BAN_FILE_NAME = {'error.cpp'}
    if file_name in BAN_FILE_NAME:
        return False
    c_cpp_exts = {'.c', '.cc', '.cpp', '.cxx', '.c++', '.cp'}
    return ext in c_cpp_exts


def is_valid_code(code: str) -> bool:
    if code is None or len(code.strip()) == 0:
        return False

    no_line_comments = re.sub(r'//.*', '', code)
    no_comments = re.sub(r'/\*.*?\*/', '', no_line_comments, flags=re.S)
    stripped = re.sub(r'\s+', '', no_comments)
    return len(stripped) != 0


def pair_hunks(deletes: List[Hunk], adds: List[Hunk]) -> List[Tuple[Hunk, Hunk]]:
    """Naïve pairing by identical start line; extend if needed."""
    add_map = {h["start"]: h for h in adds}
    pairs = []
    for d in deletes:
        a = add_map.get(d["start"])
        if a:
            pairs.append((d, a))
    return pairs


def classify_patch(patch: PatchDiff) -> Tuple[List[Hunk], PatchDiff]:
    """Return (non_essential_hunks, filtered_patch)."""
    non_essential: List[Hunk] = []
    filtered: PatchDiff = {}

    for file, changes in patch.items():
        if is_c_cpp_file(file):
            dels, adds = changes.get("delete", []), changes.get("add", [])
            pairs = pair_hunks(dels, adds)
            essential_dels, essential_adds = [], []

            for d, a in pairs:
                if any(rule.match(d, a) for rule in RULES):
                    non_essential.extend([d, a])
                else:
                    essential_dels.append(d)
                    essential_adds.append(a)

            # include unpaired hunks (pure insertions / deletions)
            paired_del_ids = {id(d) for d, _ in pairs}
            paired_add_ids = {id(a) for _, a in pairs}
            rest_dels = [h for h in dels if id(h) not in paired_del_ids]
            rest_adds = [h for h in adds if id(h) not in paired_add_ids]
            for d in rest_dels:
                if is_valid_code(d['code']):
                    essential_dels.append(d)
                else:
                    non_essential.append(d)
            for a in rest_adds:
                if is_valid_code(a['code']):
                    essential_adds.append(a)
                else:
                    non_essential.append(a)

            if essential_dels or essential_adds:
                filtered[file] = {
                    "delete": essential_dels,
                    "add": essential_adds,
                }
        else:
            dels, adds = changes.get("delete", []), changes.get("add", [])
            for a in adds:
                non_essential.append(a)
            for d in dels:
                non_essential.append(d)

    return non_essential, filtered


##############################
# CLI
##############################

def diffcat(patch: PatchDiff) -> None:
    non_ess, filtered = classify_patch(patch)
    result = {
        "non_essential": non_ess,
        "filtered_patch": filtered,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    pass
