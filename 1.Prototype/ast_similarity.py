from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple
from tree_sitter import Node
from ast_parser import ASTParser
from common import Language

# ---------- 工具函数 ----------
_IDENT_RE = re.compile(r"[A-Za-z_]\w+|\d+")

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

def tokenize_text(s: str):
    return set(t.lower() for t in _IDENT_RE.findall(s))

def jaccard_tokens(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)

# ---------- 节点特征 ----------
@dataclass(frozen=True)
class NodeFeat:
    typ: str
    tokens: frozenset[str]

def extract_nodes(code: str, lang: Language = Language.CPP, max_text_len: int = 160) -> List[NodeFeat]:
    parser = ASTParser(code, lang)
    tree = parser.get_root()
    src = code.encode("utf-8")

    feats: List[NodeFeat] = []

    def node_text(n: Node) -> str:
        raw = src[n.start_byte:n.end_byte].decode("utf-8", errors="ignore")
        return normalize_space(raw)[:max_text_len]

    def walk(n: Node):
        txt = node_text(n)
        toks = tokenize_text(txt)
        feats.append(NodeFeat(n.type, frozenset(toks)))
        for i in range(n.named_child_count):
            walk(n.named_children[i])

    walk(tree)
    return feats

# ---------- 节点相似度 ----------
def node_similarity(a: NodeFeat, b: NodeFeat, alpha: float = 0.7) -> float:
    type_eq = 1.0 if a.typ == b.typ else 0.0
    token_sim = jaccard_tokens(a.tokens, b.tokens)
    return alpha * type_eq + (1 - alpha) * token_sim

# ---------- 阈值多重集 Jaccard ----------
def multiset_jaccard_threshold(code1: str, code2: str,
                               lang: Language = Language.CPP,
                               alpha: float = 0.7,
                               tau: float = 0.85) -> float:
    A = extract_nodes(code1, lang)
    B = extract_nodes(code2, lang)

    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0

    matched = 0
    used = [False] * len(B)

    for a in A:
        best_j = -1
        best_s = 0.0
        for j, b in enumerate(B):
            if used[j]:
                continue
            s = node_similarity(a, b, alpha)
            if s > best_s:
                best_s, best_j = s, j
        if best_s >= tau and best_j >= 0:
            used[best_j] = True
            matched += 1

    union = max(len(A), len(B))
    return matched / union if union else 1.0

# ---------- 示例 ----------
if __name__ == "__main__":
    pass
