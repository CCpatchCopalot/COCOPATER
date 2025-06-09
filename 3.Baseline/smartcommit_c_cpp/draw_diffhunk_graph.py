import difflib
import json
import os
from re import L
import os
import subprocess
from openai import timeout
import pandas as pd
from tqdm import tqdm
import json
import cpu_heater
import format_code
import hunkmap
import joern
import networkx as nx
import pandas as pd
import tqdm
from codefile import CodeFile, create_code_tree
from loguru import logger
from networkx import core_number
from patch import Patch
from project import Method, Project
from tqdm import tqdm
from ast_parser import ASTParser
from common import Language, Mode
from diffparser import AddHunk, DelHunk, Hunk, ModHunk, get_patch_hunks
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from clustering_graph import get_clustering_commit


def export_joern_graph(
    pre_dir: str,
    post_dir: str,
    need_cdg: bool,
    language: Language,
    multiprocess: bool = True,
    overwrite: bool = True,
):
    logger.info(f"🔄  pre-patch, post-patch CPG PDG ")
    worker_args = [
        (f"{pre_dir}/code", pre_dir, language, overwrite, need_cdg),
        (f"{post_dir}/code", post_dir, language, overwrite, need_cdg),
    ]
    if multiprocess:
        cpu_heater.multiprocess(
            joern.export_with_preprocess_and_merge,
            worker_args,
            max_workers=2,
            show_progress=False,
        )
    else:
        joern.export_with_preprocess_and_merge(*worker_args[0])
        joern.export_with_preprocess_and_merge(*worker_args[1])
    logger.info(f"✅ pre-patch, post-patch CPG PDG ")


    
def get_pre_post_methods(
    patch, pre_post_projects: tuple[Project, Project], signature: str
):
    pre_project, post_project = pre_post_projects

    pre_method = pre_project.get_method(signature)
    if signature in patch.change_method_map_dict.keys():
        post_method = post_project.get_method(
            patch.change_method_map_dict[signature][0]
        )
    else:
        post_method = post_project.get_method(signature)
    pre_method.counterpart = post_method
    post_method.counterpart = pre_method
    if pre_method is None:
        logger.warning(f"❌ Pre-Patch Method does not exist: {signature}")
        return
    if post_method is None:
        logger.warning(f"❌ Post-Patch Method does not exist: {signature}")
        return
    return pre_method, post_method

def get_diff_hunk(diff: str):
    hunks_content = ""
    iter = re.finditer(r"@@.*?@@", diff)
    indices = [m.start(0) for m in iter]
    for i, v in enumerate(indices):
        if i == len(indices) - 1:
            hunks_content += diff[v:]
        else:
            hunks_content += diff[v : indices[i + 1]]
    
    hunks_content = hunks_content.split("\n")[1:]
    return "\n".join(hunks_content)

def get_str_sim(string1, string2):

    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3)) 


    corpus = [string1, string2]
    tfidf_matrix = vectorizer.fit_transform(corpus)

    similarity_s1_s2 = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similarity_s1_s2[0][0]

def draw_diffhunk_graph(cve_id: str, repo_path: str, pre_commit: str, post_commit: str, language: Language):
    errors = {}
    errors[cve_id] = {}
    try:
        logger.info(f"🔄 analysis{cve_id}...")
        patch = Patch(repo_path, pre_commit.replace(" ","").replace("\n",""), post_commit.replace(" ","").replace("\n",""),  language)
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "patch error"
        return errors
    
    pre_line_hunk_map = {}
    post_line_hunk_map = {}
    diff_hunk_id_map = {}
    hunk_graph = nx.DiGraph()
    logger.info(f"✅ Patch Finish")

    try:
        pre_code_files = patch.pre_analysis_files
        post_code_files = patch.post_analysis_files

        logger.info(f"{cve_id} pre-patch code files: {len(pre_code_files)}")
        pre_dir = os.path.join(f"results_cache/{cve_id}", "pre")
        post_dir = os.path.join(f"results_cache/{cve_id}", "post")
        create_code_tree(pre_code_files, pre_dir)
        create_code_tree(post_code_files, post_dir)
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "code tree error"
        return errors
    logger.info(f"✅ patch")
    try:
        export_joern_graph(
            pre_dir,
            post_dir,
            need_cdg=True,
            language=Language.C,
            overwrite=False,
            multiprocess=True,
        )
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "joern graph error"
        return errors
    

    logger.info(f"🔄 Project Joern Graph")
    try:
        assert patch is not None
        patch.pre_project.load_joern_graph(f"{pre_dir}/cpg", f"{pre_dir}/pdg")
        patch.post_project.load_joern_graph(
        f"{post_dir}/cpg", pdg_dir=f"{post_dir}/pdg"
        )
        logger.info(f"✅ Project Joern Graph")
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "joern graph parse error"
        return errors

    try:    
        pre_post_projects = (patch.pre_project, patch.post_project)
        diff_hunks = []

        node_id = 0
        for method in patch.changed_methods:
            pre_method, post_method = get_pre_post_methods(patch, pre_post_projects, method)
            for hunks in pre_method.patch_hunks:
                if hunks not in diff_hunks:    
                    diff_hunks.append(hunks)
                if type(hunks) == AddHunk:
                    diff_hunk_id_map[f"{hunks.b_startline}-{hunks.b_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.b_startline, hunks.b_endline+1):
                        post_line_hunk_map[f"{post_method.file.name}:{line}"] = hunks
                elif type(hunks) == ModHunk:
                    diff_hunk_id_map[f"{hunks.a_startline}-{hunks.a_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.a_startline, hunks.a_endline+1):
                        pre_line_hunk_map[f"{pre_method.file.name}:{line}"] = hunks
                    for line in range(hunks.b_startline, hunks.b_endline+1):
                        post_line_hunk_map[f"{post_method.file.name}:{line}"] = hunks
                elif type(hunks) == DelHunk:
                    diff_hunk_id_map[f"{hunks.a_startline}-{hunks.a_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.a_startline, hunks.a_endline+1):
                        pre_line_hunk_map[f"{pre_method.file.name}:{line}"] = hunks            
            for hunks in post_method.patch_hunks:
                if hunks not in diff_hunks:    
                    diff_hunks.append(hunks)
                else:
                    continue
                if type(hunks) == AddHunk:
                    diff_hunk_id_map[f"{hunks.b_startline}-{hunks.b_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.b_startline, hunks.b_endline+1):
                        post_line_hunk_map[f"{post_method.file.name}:{line}"] = hunks
                elif type(hunks) == ModHunk:
                    diff_hunk_id_map[f"{hunks.a_startline}-{hunks.a_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.a_startline, hunks.a_endline+1):
                        pre_line_hunk_map[f"{pre_method.file.name}:{line}"] = hunks
                    for line in range(hunks.b_startline, hunks.b_endline+1):
                        post_line_hunk_map[f"{post_method.file.name}:{line}"] = hunks
                elif type(hunks) == DelHunk:
                    diff_hunk_id_map[f"{hunks.a_startline}-{hunks.a_endline}"] = node_id
                    hunk_graph.add_node(node_id, diff_content=get_diff_hunk(hunks.diff), diff_type=type(hunks))
                    node_id += 1
                    for line in range(hunks.a_startline, hunks.a_endline+1):
                        pre_line_hunk_map[f"{pre_method.file.name}:{line}"] = hunks
        # print(pre_line_hunk_map)
        # print(post_line_hunk_map)
            if pre_method is None or post_method is None:
                continue
            pre_slice_lines = pre_method.slice_by_diff_lines()
            post_slice_lines = post_method.slice_by_diff_lines()
            for line in pre_slice_lines:
                for pre_line in pre_slice_lines[line]:
                    if f"{pre_method.file.name}:{pre_line}" in pre_line_hunk_map:
                        from_hunk = pre_line_hunk_map[f"{pre_method.file.name}:{line}"]
                        to_hunk = pre_line_hunk_map[f"{pre_method.file.name}:{pre_line}"]
                        if type(from_hunk) == ModHunk:
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.a_startline}-{from_hunk.a_endline}"]
                        elif type(from_hunk) == AddHunk:
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.b_startline}-{from_hunk.b_endline}"]
                        elif type(from_hunk) == DelHunk:
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.a_startline}-{from_hunk.a_endline}"]
                        if type(to_hunk) == ModHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.a_startline}-{to_hunk.a_endline}"]
                        elif type(to_hunk) == AddHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.b_startline}-{to_hunk.b_endline}"]
                        elif type(to_hunk) == DelHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.a_startline}-{to_hunk.a_endline}"]
                        if from_hunk_id == to_hunk_id:
                            continue
                        if hunk_graph.has_edge(from_hunk_id, to_hunk_id) or hunk_graph.has_edge(to_hunk_id, from_hunk_id):
                            continue
                        hunk_graph.add_edge(from_hunk_id, to_hunk_id, label=pre_slice_lines[line][pre_line], weight=pre_slice_lines[line][pre_line])
            
            for line in post_slice_lines:
                for post_line in post_slice_lines[line]:
                    if f"{post_method.file.name}:{post_line}" in post_line_hunk_map:
                        from_hunk = post_line_hunk_map[f"{post_method.file.name}:{line}"]
                        to_hunk = post_line_hunk_map[f"{post_method.file.name}:{post_line}"]
                        if type(from_hunk) == ModHunk:  
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.a_startline}-{from_hunk.a_endline}"]
                        elif type(from_hunk) == AddHunk:
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.b_startline}-{from_hunk.b_endline}"]
                        elif type(from_hunk) == DelHunk:
                            from_hunk_id = diff_hunk_id_map[f"{from_hunk.a_startline}-{from_hunk.a_endline}"]
                        if type(to_hunk) == ModHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.a_startline}-{to_hunk.a_endline}"]
                        elif type(to_hunk) == AddHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.b_startline}-{to_hunk.b_endline}"]
                        elif type(to_hunk) == DelHunk:
                            to_hunk_id = diff_hunk_id_map[f"{to_hunk.a_startline}-{to_hunk.a_endline}"]
                        if from_hunk_id == to_hunk_id:
                            continue
                        if hunk_graph.has_edge(from_hunk_id, to_hunk_id) or hunk_graph.has_edge(to_hunk_id, from_hunk_id):
                            continue
                        hunk_graph.add_edge(from_hunk_id, to_hunk_id, label="hard link", weight=post_slice_lines[line][post_line])
        
        for diff_hunk1 in diff_hunks:
            for diff_hunk2 in diff_hunks:
                if diff_hunk1 == diff_hunk2:
                    continue
                str_sim = get_str_sim(get_diff_hunk(diff_hunk1.diff), get_diff_hunk(diff_hunk2.diff))
                ast_sim = get_str_sim(get_diff_hunk(diff_hunk1.ast_diff), get_diff_hunk(diff_hunk2.ast_diff))
                sim_all = (str_sim + ast_sim) / 2

                if sim_all >= 0.8:
                    if type(diff_hunk1) == ModHunk:
                        from_hunk_id = diff_hunk_id_map[f"{diff_hunk1.a_startline}-{diff_hunk1.a_endline}"]
                    elif type(diff_hunk1) == AddHunk:
                        from_hunk_id = diff_hunk_id_map[f"{diff_hunk1.b_startline}-{diff_hunk1.b_endline}"]
                    elif type(diff_hunk1) == DelHunk:
                        from_hunk_id = diff_hunk_id_map[f"{diff_hunk1.a_startline}-{diff_hunk1.a_endline}"]
                    if type(diff_hunk2) == ModHunk:
                        to_hunk_id = diff_hunk_id_map[f"{diff_hunk2.a_startline}-{diff_hunk2.a_endline}"]
                    elif type(diff_hunk2) == AddHunk:
                        to_hunk_id = diff_hunk_id_map[f"{diff_hunk2.b_startline}-{diff_hunk2.b_endline}"]
                    elif type(diff_hunk2) == DelHunk:
                        to_hunk_id = diff_hunk_id_map[f"{diff_hunk2.a_startline}-{diff_hunk2.a_endline}"]
                    if from_hunk_id == to_hunk_id:
                        continue
                    if hunk_graph.has_edge(from_hunk_id, to_hunk_id) or hunk_graph.has_edge(to_hunk_id, from_hunk_id):
                        continue
                    hunk_graph.add_edge(from_hunk_id, to_hunk_id, label=f"soft link", weight=sim_all)   
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "hunk graph error"
        return errors
            
    try:
        commit = get_clustering_commit(hunk_graph)
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "commit clustering error"
        return errors
    try:
        fp = open(f"results_cache/{cve_id}/commit.json", "w")
        json.dump(commit, fp, indent=4)
        fp.close()
        nx.nx_agraph.write_dot(hunk_graph, f"results_cache/{cve_id}/hunk_graph.dot")
        logger.info(f"✅ hunk ")
    except Exception as e:
        errors[cve_id]['details'] = str(e)
        errors[cve_id]['status'] = "hunk graph save error"
        return errors
    
    errors[cve_id]['status'] = "success"
    return errors

    
def clone_repo(repo_name, repo_dir, repohost=None):
    repo_path = os.path.join(repo_dir, repo_name)
    if not os.path.exists(repo_path):
        print(f"Cloning repo: {repo_name} from {'GitLab' if repohost else 'GitHub'}")

        if repohost == "gitlab":
            clone_url = f"https://gitlab.com/{repo_name.replace('@@', '/')}.git"
        elif repohost == "ghostscript":
      
            clone_url = f"	http://git.ghostscript.com/ghostpdl.git"
        else:
            clone_url = f"https://github.com/{repo_name.replace('@@', '/')}.git"

        subprocess.run(["git", "clone", clone_url, repo_path], check=True)

if __name__ == "__main__":
    fp = open(config.excel_path)
    dataset = json.load(fp)
    fp.close()
    language = Language.C
    work_list = []
    errors = {}
    repo_dir = "./gitrepo"
    for cve in tqdm(dataset):
        if os.path.exists(f"results_cache/{cve}/hunk_graph.dot"):
            continue
        os.system(f"rm -rf results_cache/{cve}")
        commits = dataset[cve]["patch"].split("\n")
        first_commit, last_commit = commits[0], commits[-1]
        if "ghostscript" in first_commit:
            repohost = "ghostscript"
        elif "gitlab" in first_commit:
            repohost = "gitlab"
        else:
            repohost = "github"
        
        
        if repohost == "gitlab":
            base_url = "https://gitlab.com/"
        elif repohost == "ghostscript":
            repo_name = "ghostscript@@ghostscript"
            pre_commit = first_commit.split("=")[-1]
            post_commit = first_commit.split("=")[-1]
        else:
            base_url = "https://github.com/"
        
        if repohost == "gitlab":
            split_token = "/-/commit/"
        elif repohost == "ghostscript":
            split_token = None
        else:
            split_token = "/commit/"
        
        if repohost != "ghostscript":
            repo_name = first_commit.replace(base_url, "").split(split_token)[0].replace("/", "@@")
            pre_commit = first_commit.split(split_token)[1].split("#diff")[0]
            post_commit = last_commit.split(split_token)[1].split("#diff")[0]


        cve_id = cve
        if repo_name.endswith("@@"):
            repo_name = repo_name[:-2]
        clone_repo(repo_name, repo_dir, repohost)
        if not os.path.exists(os.path.join(repo_dir, f"{repo_name}_{cve_id}")):
            os.makedirs(os.path.join(repo_dir, f"{repo_name}_{cve_id}"))
            os.system(f"cp -r {os.path.join(repo_dir, repo_name, '.git')} {os.path.join(repo_dir, f'{repo_name}_{cve_id}')}")
        if os.path.exists(os.path.join(repo_dir, f'{repo_name}_{cve_id}', '.git', 'config.lock')):
            os.system(f"rm -rf {os.path.join(repo_dir, f'{repo_name}_{cve_id}', '.git', 'config.lock')}")
        repo_path = os.path.join(repo_dir,  f'{repo_name}_{cve_id}')
        work_list.append((cve_id, repo_path, pre_commit, post_commit, language))
        # break
    results = cpu_heater.multiprocess(draw_diffhunk_graph, work_list, max_workers=32, show_progress=True, timeout=3600)
    for result in results:
        errors.update(result)
    with open("errors.json", "w") as fp:
        json.dump(errors, fp)