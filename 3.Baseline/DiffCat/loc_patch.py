import shutil
import os
import subprocess
from diffparser import get_patch_hunks, HunkType


def get_patch_loc(project_path: str, pre_commit_id: str, post_commit_id: str):
    # Load essential elements
    diff_dict = {}
    if pre_commit_id is not None and post_commit_id is not None:
        # Create and clear the diff directory
        diff_dir = os.path.join("diff")
        if os.path.exists(diff_dir):
            shutil.rmtree(diff_dir)
        os.makedirs(diff_dir)
        
        os.chdir(project_path)
        
        diff_files = subprocess.run(
            ["git", "diff", "--name-only", pre_commit_id, post_commit_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ).stdout.decode().strip().split("\n")
        
        for file_path in diff_files:
            if not os.path.exists(file_path):
                continue
            subprocess.run(["git", "checkout", pre_commit_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pre_code = ""
            try:
                with open(file_path, 'r') as f:
                    pre_code = f.read()
            except:
                continue
            subprocess.run(["git", "checkout", post_commit_id], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            post_code = ""
            try:
                with open(file_path, 'r') as f:
                    post_code = f.read()
            except:
                continue
            hunks = get_patch_hunks(pre_code, post_code)
            
            for hunk in hunks:
                if hunk.type == HunkType.MOD:
                    if file_path not in diff_dict:
                        diff_dict[file_path] = {"add": [], "delete": []}
                    diff_dict[file_path]["delete"].append({
                        'start': hunk.a_startline,
                        'end': hunk.a_endline,
                        'code': hunk.a_code
                    })
                    diff_dict[file_path]["add"].append({
                        'start': hunk.b_startline,
                        'end': hunk.b_endline,
                        'code': hunk.b_code,
                        'insert_at': hunk.a_startline 
                    })
                elif hunk.type == HunkType.ADD:
                    if file_path not in diff_dict:
                        diff_dict[file_path] = {"add": [], "delete": []}
                    diff_dict[file_path]["add"].append({
                        'start': hunk.b_startline,
                        'end': hunk.b_endline,
                        'code': hunk.b_code,
                        'insert_at': hunk.insert_line
                    })
                elif hunk.type == HunkType.DEL:
                    if file_path not in diff_dict:
                        diff_dict[file_path] = {"add": [], "delete": []}
                    diff_dict[file_path]["delete"].append({
                        'start': hunk.a_startline,
                        'end': hunk.a_endline,
                        'code': hunk.a_code
                    })
    return diff_dict

def add_to_delete(diff_dict: dict):
    pass
