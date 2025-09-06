import difflib
import clang.cindex as clang
import json
import re
import subprocess
import sys
import tempfile
from enum import Enum
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
sys.path.append('../..')
from ast_parser import ASTParser
from ast_similarity import multiset_jaccard_threshold, extract_nodes
from common import Language

class CodeMapper:
    def __init__(self, original_code, transformed_code):
        self.original_code = original_code
        self.transformed_code = transformed_code
        self.original_statements = self.extract_statements(original_code)
        self.transformed_statements = self.extract_statements(transformed_code)
        self.statement_map = self.map_statements()
    
    def extract_statements(self, code):
        index = clang.Index.create()
        tu = index.parse('tmp.c', args=['-xc', '-std=c99'], unsaved_files=[('tmp.c', code)], options=0)
        statements = []
        
        def visit(node):
            if node.kind.is_statement():
                statements.append((node.extent.start.line, node.spelling or node.kind.name))
            for child in node.get_children():
                visit(child)
        
        visit(tu.cursor)
        return statements
    
    def map_statements(self):
        matcher = difflib.SequenceMatcher(None, self.original_statements, self.transformed_statements)
        mapping = {}
        
        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == 'equal':
                for orig, trans in zip(self.original_statements[i1:i2], self.transformed_statements[j1:j2]):
                    mapping[orig] = trans
            elif opcode == 'replace':
                for orig, trans in zip(self.original_statements[i1:i2], self.transformed_statements[j1:j2]):
                    mapping[orig] = trans
            elif opcode == 'delete':
                for orig in self.original_statements[i1:i2]:
                    mapping[orig] = None
            elif opcode == 'insert':
                for trans in self.transformed_statements[j1:j2]:
                    mapping[None] = trans
        
        return mapping
    
    def mapping(self):
        return self.statement_map

    def transform_to_original(self, new_code):
        new_statements = self.extract_statements(new_code)
        reverse_map = {v: k for k, v in self.statement_map.items() if v is not None}
        transformed_statements = [reverse_map.get(stmt, stmt) for stmt in new_statements]
        
        return "\n".join([stmt[1] for stmt in transformed_statements])

class FaultType(Enum):
    SUCCESS = "SUCCESS"
    NO_FIX = "NO_FIX"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    AST_ERROR = "AST_ERROR"
    SEMANTIC_ERROR = "SEMANTIC_ERROR"

    
class Fault:
    def __init__(self, type: FaultType, description: str | None = None, key: str | None = None):
        self.key = key
        self.type = type
        self.description = description


def clang_tidy_report(code: str) -> list[str]:
    code_file = tempfile.NamedTemporaryFile(mode='w', suffix=".c")
    report_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml")
    code_file.write(code)
    code_file.flush()
    result = subprocess.run(
        ["clang-tidy", code_file.name, f"--export-fixes={report_file.name}", "--extra-arg=-ferror-limit=0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(report_file.name) as f:
        report = yaml.safe_load(f)
    error_messages = []
    if report is None:
        return error_messages
    for diag in report["Diagnostics"]:
        error_level = diag["Level"]
        if error_level != "Error":
            continue
        diag_message = diag["DiagnosticMessage"]["Message"]
        error_messages.append(diag_message)
    return error_messages

def clang_tidy_check(code: str, ignore_error_message: list[str] = []) -> Fault:
    code_file = tempfile.NamedTemporaryFile(mode='w', suffix=".c")
    report_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml")
    code_file.write(code)
    code_file.flush()
    result = subprocess.run(
        ["clang-tidy", code_file.name, f"--export-fixes={report_file.name}", "--extra-arg=-ferror-limit=0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with open(report_file.name) as f:
        report = yaml.safe_load(f)
    if report is None:
        return Fault(FaultType.SUCCESS)
    for diag in report["Diagnostics"]:
        error_level = diag["Level"]
        if error_level != "Error":
            continue
        diag_message = diag["DiagnosticMessage"]["Message"]
        if diag_message in ignore_error_message:
            continue
        if diag_message.startswith("use of undeclared identifier"):
            # check identifier is constant
            matches = re.findall(r"'(.*?)'", diag_message)
            if len(matches) != 0:
                identifier = matches[0]
                if identifier.isupper():
                    continue
        elif "too many errors emitted" in diag_message:
            continue
        diag_name = diag["DiagnosticName"]
        offset = diag["DiagnosticMessage"]["FileOffset"]
        line = code[:offset].count("\n") + 1
        desp = f"There is a syntax error in line {line}: {diag_message}"
        return Fault(FaultType.SYNTAX_ERROR, desp)
    return Fault(FaultType.SUCCESS)

class CodeBERTSimilarity:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.model = AutoModel.from_pretrained("microsoft/codebert-base")
        
    def get_embeddings(self, code_snippet):
        tokens = self.tokenizer(code_snippet, return_tensors="pt", padding=True, truncation=True)
        with torch.no_grad():
            outputs = self.model(**tokens)
        return outputs.last_hidden_state.mean(dim=1).numpy()
    
    def find_similar_statements(self, target_stmt, candidate_stmts, threshold=0.8):
        target_emb = self.get_embeddings(target_stmt)
        similar_stmts = []
        
        for stmt in candidate_stmts:
            stmt_emb = self.get_embeddings(stmt)
            similarity = np.dot(target_emb[0], stmt_emb[0]) / (np.linalg.norm(target_emb) * np.linalg.norm(stmt_emb))
            if similarity > threshold:
                similar_stmts.append(stmt)
                
        return similar_stmts

def find_syntatic_similar_statements(target_stmt, candidate_stmts, threshold=0.8): -> list[str]:
    similar_stmts = []
    for candidate_stmt in candidate_stmts:
        similarity = multiset_jaccard_threshold(target_stmt, candidate_stmt, Language.C)
        if similarity > threshold and candidate_stmt not in similar_stmts:
            similar_stmts.append(candidate_stmt)
    return similar_stmts

def checking_recovery(pa: str, pb: str, pc: list[str], pC: list[int] | None = None) -> str:
    """
    Enhanced recovery function that implements semantic similarity and compatibility mitigation
    
    Args:
        pa: Pre-patch code
        pb: Post-patch code 
        pc: Core sequence statements
        pC: Changed line numbers
    
    Returns:
        Recovered code
    """
    # Initialize CodeBERT for semantic similarity
    codebert = CodeBERTSimilarity()
    
    # Get base errors to ignore
    ignore_error_message = clang_tidy_report(pa)
    
    # Initialize recovery components
    Pool = []  # Pending recovery statements pool
    if pC:
        # Add core sequence statements to pool
        for idx in pC:
            Pool.append((pc[idx-1], 0))  # (statement, dependency_count)
            
        # Find semantically similar statements
        all_stmts = pc
        for idx in pC:
            similar_stmts = codebert.find_similar_statements(pc[idx-1], all_stmts)
            for stmt in similar_stmts:
                if stmt not in [x[0] for x in Pool]:
                    Pool.append((stmt, 0))
            similar_stmts = find_syntatic_similar_statements(pc[idx-1], all_stmts)
            for stmt in similar_stmts:
                if stmt not in [x[0] for x in Pool]:
                    Pool.append((stmt, 0))
    # Sort pool by dependencies and global declarations
    def get_priority(stmt_tuple):
        stmt, deps = stmt_tuple
        is_global = bool(re.match(r'^(extern|static|const|struct|#define)', stmt.strip()))
        return (-deps, -is_global)
    Pool.sort(key=get_priority)
    
    # Iterative recovery process
    recovered_pb = pb
    applied_pieces = []
    max_iterations = 100
    
    for iteration in range(max_iterations):
        if not Pool:
            break
        # Get next statement from pool
        stmt, _ = Pool.pop(0)
        applied_pieces.append(stmt)
        
        # Apply statement and check compatibility
        test_code = recovered_pb + "\n" + "\n".join(applied_pieces)
        current_fault = clang_tidy_check(test_code, ignore_error_message)
        
        if current_fault.type == FaultType.SUCCESS:
            recovered_pb = test_code
        else:
            # If error occurs, try to update dependencies
            for remaining_stmt, deps in Pool:
                if re.search(re.escape(stmt), remaining_stmt):
                    deps += 1
            Pool.sort(key=get_priority)
            
    return recovered_pb