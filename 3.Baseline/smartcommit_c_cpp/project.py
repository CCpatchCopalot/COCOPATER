from __future__ import annotations

import ast
import json
import logging
import os
import subprocess
import sys
from collections import deque
from functools import cached_property
import code_transformation
import format_code
import joern
import networkx as nx
from networkx.drawing.nx_pydot import write_dot
from codefile import CodeFile
from diffparser import AddHunk, DelHunk, Hunk, ModHunk, get_patch_hunks
from joern import PDGNode
from json2dot import convert_to_dot
from loguru import logger
from tree_sitter import Node

import ast_parser
from ast_parser import ASTParser
from common import Language


def group_consecutive_ints(nums: list[int]):
    if len(nums) == 0:
        return []
    nums.sort()  
    result = [[nums[0]]]  # 
    for num in nums[1:]:
        if num == result[-1][-1] + 1:
            result[-1].append(num)  # 
        else:
            result.append([num])  
    return result


class ProjectJoern:
    def __init__(self, cpg_dir: str, pdg_dir: str):
        self.cpg = joern.CPG(cpg_dir)
        self.pdgs: dict[tuple[int, str, str], joern.PDG] = self.build_pdgs(pdg_dir)
        self.path = cpg_dir.replace("/cpg", "")

    def build_pdgs(self, pdg_dir: str):
        dot_names = os.listdir(pdg_dir)
        pdgs: dict[tuple[int, str, str], joern.PDG] = {}
        for dot in dot_names:
            dot_path = os.path.join(pdg_dir, dot)
            try:
                pdg = joern.PDG(pdg_path=dot_path)
            except Exception as e:
                logging.warning(f"❌ PDG loading failed: {dot_path}")
                logging.warning(e)
                continue
            try:
                if pdg.name is None or pdg.line_number is None or pdg.filename is None:
                    continue
            except:
                continue
            pdgs[(pdg.line_number, pdg.name, pdg.filename)] = pdg
        return pdgs

    def get_pdg(self, method: Method) -> joern.PDG | None:
        # print(self.pdgs)
        # print(method.start_line - 1, method.name, method.file.path)
        if self.pdgs.get((method.start_line, method.name, method.file.path)) is None:
            if (
                self.pdgs.get((method.start_line + 1, method.name, method.file.path))
                is None
            ):
                return self.pdgs.get(
                    (method.start_line - 1, method.name, method.file.path)
                )
            else:
                return self.pdgs.get(
                    (method.start_line + 1, method.name, method.file.path)
                )
        else:
            return self.pdgs.get((method.start_line, method.name, method.file.path))


class Project:
    def __init__(self, project_name: str, files: list[CodeFile], language: Language):
        self.project_name: str = project_name
        self.language: Language = language
        self.files: list[File] = []

        self.files_path_set: set[str] = set()
        self.imports_signature_set: set[str] = set()
        self.classes_signature_set: set[str] = set()
        self.methods_signature_set: set[str] = set()
        self.fields_signature_set: set[str] = set()

        for file in files:
            file = File(file.file_path, file.formated_code, self, language)
            self.files.append(file)
            self.files_path_set.add(file.path)
            if language == Language.JAVA:
                self.imports_signature_set.update(
                    [import_.signature for import_ in file.imports]
                )
                self.classes_signature_set.update(
                    [clazz.fullname for clazz in file.classes]
                )
                self.methods_signature_set.update(
                    [
                        method.signature
                        for clazz in file.classes
                        for method in clazz.methods
                    ]
                )
                self.fields_signature_set.update(
                    [
                        field.signature
                        for clazz in file.classes
                        for field in clazz.fields
                    ]
                )
            elif language == Language.C or language == Language.CPP:
                self.imports_signature_set.update(
                    [import_.signature for import_ in file.imports]
                )
                self.methods_signature_set.update(
                    [method.signature for method in file.methods]
                )

        self.joern: ProjectJoern | None = None

    def load_joern_graph(self, cpg_dir: str, pdg_dir: str):
        self.joern = ProjectJoern(cpg_dir, pdg_dir)

    def get_file(self, path: str) -> File | None:
        for file in self.files:
            if file.path == path:
                return file
        return None

    def get_import(self, signature: str) -> Import | None:
        for file in self.files:
            for import_ in file.imports:
                if import_.signature == signature:
                    return import_
        return None

    def get_class(self, fullname: str) -> Class | None:
        for file in self.files:
            for clazz in file.classes:
                if clazz.fullname == fullname:
                    return clazz
        return None

    def get_method(self, fullname: str) -> Method | None:
        if self.language == Language.JAVA:
            for file in self.files:
                for clazz in file.classes:
                    for method in clazz.methods:
                        if method.signature == fullname:
                            return method
        elif self.language == Language.C or self.language == Language.CPP:
            for file in self.files:
                for method in file.methods:
                    # if fullname == "src/H5Fsuper_cache.c#H5F__superblock_prefix_decode":
                    #     print(method.signature, fullname)
                    if method.signature == fullname:
                        return method
        return None

    def get_field(self, fullname: str) -> Field | None:
        for file in self.files:
            for clazz in file.classes:
                for field in clazz.fields:
                    if field.signature == fullname:
                        return field
        return None

    @cached_property
    def cpg(self):
        return self.joern.cpg.g  # type: ignore

    def get_callee(self, fullname: str):
        callees = []
        method = self.get_method(fullname)
        if method is None:
            logging.debug(f"Method{fullname} does not exist")
            return callees
        assert method is not None
        method_ids = method.line_number_pdg_map[0]
        line_map_method_nodes = method.line_number_pdg_map[1]
        call_ids = set()
        cpg = self.cpg
        for node in cpg.nodes:
            if (
                cpg.nodes[node]["label"] == "CALL"
                and int(cpg.nodes[node]["LINE_NUMBER"]) >= method.start_line
                and int(cpg.nodes[node]["LINE_NUMBER"]) <= method.end_line
            ):
                call_ids.add(node)

        for u, v, d in cpg.edges(data=True):
            try:
                if (
                    d["label"] == "CALL"
                    and (u in method_ids or u in call_ids)
                    and "LINE_NUMBER" in cpg.nodes[v].keys()
                ):  # type: ignore
                    if "label" in cpg.nodes[v] and cpg.nodes[v]["label"] == "METHOD":
                        line_number = next(
                            (
                                key
                                for key, value in line_map_method_nodes.items()
                                if u in value
                            ),
                            None,
                        )  # type: ignore
                        if line_number is None:
                            continue
                        callees.append(
                            {
                                "callee_linenumber": line_number,
                                "callee_method_name": f"{cpg.nodes[v]['FILENAME']}#{cpg.nodes[v]['NAME']}",
                                "method_line_number": cpg.nodes[v]["LINE_NUMBER"],
                            }
                        )  # type: ignore
            except:
                continue
            #     print(fullname, method_ids, method.start_line)
        return callees
    
class File:
    def __init__(
        self, path: str, content: str, project: Project | None, language: Language
    ):
        parser = ASTParser(content, language)
        self.language = language
        self.project = project
        self.parser = parser
        self.path = path
        self.name = os.path.basename(path)
        self.code = content

        if project is None:
            self.project = Project("None", [CodeFile(path, content)], language)
        else:
            self.project = project

    @cached_property
    def package(self) -> str:
        assert self.language == Language.JAVA
        package_node = self.parser.query_oneshot(ast_parser.TS_JAVA_PACKAGE)
        return package_node.text.decode() if package_node is not None else "<NONE>"  # type: ignore

    @cached_property
    def imports(self) -> list[Import]:
        if self.language == Language.JAVA:
            return [
                Import(import_node, self, self.language)
                for import_node in self.parser.query_all(ast_parser.TS_JAVA_IMPORT)
            ]
        elif self.language == Language.C or self.language == Language.CPP:
            return [
                Import(import_node, self, self.language)
                for import_node in self.parser.query_all(ast_parser.TS_C_INCLUDE)
            ]
        else:
            return []

    @cached_property
    def classes(self) -> list[Class]:
        if self.language == Language.JAVA:
            return [
                Class(class_node, self, self.language)
                for class_node in self.parser.query_all(ast_parser.TS_JAVA_CLASS)
            ]
        else:
            return []

    @cached_property
    def fields(self) -> list[Field]:
        return [field for clazz in self.classes for field in clazz.fields]

    @cached_property
    def methods(self) -> list[Method]:
        if self.language == Language.JAVA:
            return [method for clazz in self.classes for method in clazz.methods]
        elif self.language == Language.C or self.language == Language.CPP:
            methods: list[Method] = []
            query = ast_parser.TS_C_METHOD
            
            methods_dict = {}
            methods_intervals = []
            construction = {}
            # for child in  self.parser.root.children:
            #     if child.type == "ERROR":
            #         print("ERROR NODE", child.start_point[0])
            for method_node in self.parser.query_all(query):
                
                if method_node.text.decode().lstrip().startswith("namespace"):
                    continue
                
                elif method_node.text.decode().strip().startswith("class"):
                    sub_parser = ASTParser(method_node.text.decode(), Language.CPP)
                    sub_methods = sub_parser.query_all(ast_parser.TS_C_METHOD)
                    class_name = method_node.text.decode().strip().split(" ")[1].replace(":", "")
                    if "::" in class_name:
                        class_name.replace(" ","").split("::")[0]
                    
                    sts = set()
                    for sub_method in sub_methods:
                        sts.add(method_node.start_point[0]+sub_method.start_point[0]+1)
                        
                    
                    st = 0
                    ed = method_node.end_point[0]+1
                    for line in method_node.text.decode().split("\n"):
                        if line.strip().startswith("class"):
                            st += 1
                            continue
                        else:
                            if line.strip().startswith(class_name):
                                st = st+method_node.start_point[0]+1
                                break
                            st += 1
                    # print(method_node.text.decode(), class_name, st, ed, sts)
                    if st < method_node.start_point[0]:
                        methods_dict[
                        f"{method_node.start_point[0]}##{method_node.end_point[0]}"
                        ] = method_node
                        methods_intervals.append(
                            (method_node.start_point[0], method_node.end_point[0])
                        )
                        continue
                    for i in range(st, ed):
                        # print(i, st, ed, sts, class_name)
                        if i in sts:
                            while i > st and method_node.text.decode().split("\n")[i-method_node.start_point[0]-1].strip()=="\n":
                                i -= 1
                            ed = i
                            break
                    methods_dict[
                        f"{st-1}##{ed-1}"
                    ] = method_node
                    methods_intervals.append(
                        (st-1, ed-1)
                    )
                    construction[f"{st-1}##{ed-1}"] = "\n".join(method_node.text.decode().split("\n")[st-1:ed-1])
                else:
                    # print(method_node.text.decode())
                    methods_dict[
                        f"{method_node.start_point[0]}##{method_node.end_point[0]}"
                    ] = method_node
                    methods_intervals.append(
                        (method_node.start_point[0], method_node.end_point[0])
                    )
            methods_intervals = self.merge_intervals(methods_intervals)
            for st, ed in methods_intervals:
                # print(f"{st}##{ed}")
                
                if st == ed:
                    continue
                if f"{st}##{ed}" in methods_dict.keys():
                    if f"{st}##{ed}" in construction:
                        methods.append(
                            Method(methods_dict[f"{st}##{ed}"], None, self, self.language, st, ed, construction[f"{st}##{ed}"])
                        )
                    else:
                        methods.append(
                            Method(methods_dict[f"{st}##{ed}"], None, self, self.language)
                        )
                        
            return methods
        else:
            return []

    def merge_intervals(self, intervals):
        
        if not intervals:
            return []

        
        intervals.sort(key=lambda x: x[0])

        
        merged = [intervals[0]]

        for current in intervals[1:]:
            
            last = merged[-1]

            
            if current[0] <= last[1]:
                merged[-1] = [last[0], max(last[1], current[1])]
            else:
                
                merged.append(current)

        return merged


class Import:
    def __init__(self, node: Node, file: File, language: Language):
        self.file = file
        self.node = node
        self.code = node.text.decode()  # type: ignore
        self.signature = file.path + "#" + self.code


class Class:
    def __init__(self, node: Node, file: File, language: Language):
        self.language = language
        self.file = file
        self.code = node.text.decode()  # type: ignore
        self.node = node
        name_node = node.child_by_field_name("name")
        if name_node is None:
            logging.warning(f"❌ Class name parsing failed: {file.path}")
            return
        self.name = name_node.text.decode()  # type: ignore
        self.fullname = f"{file.package}.{self.name}"

    @cached_property
    def fields(self):
        file = self.file
        parser = file.parser
        class_node = self.node
        class_name = self.name
        fields: list[Field] = []
        
        query = f"""
        (class_declaration
            name: (identifier)@class.name
            (#eq? @class.name "{class_name}")
            body: (class_body
                (field_declaration)@field
            )
        )    
        """
        for field_node in parser.query_by_capture_name(query, "field", node=class_node):
            fields.append(Field(field_node, self, file))
        return fields

    @cached_property
    def methods(self):
        file = self.file
        parser = file.parser
        class_node = self.node
        class_name = self.name
        methods: list[Method] = []
        
        query = f"""
        (class_declaration
            name: (identifier)@class.name
            (#eq? @class.name "{class_name}")
            body: (class_body
                [(method_declaration)
                (constructor_declaration)]@method
            )
        )
        """
        for method_node in parser.query_by_capture_name(
            query, "method", node=class_node
        ):
            methods.append(Method(method_node, self, file, self.language))
        return methods


class Field:
    def __init__(self, node: Node, clazz: Class, file: File):
        self.name = (
            node.child_by_field_name("declarator")
            .child_by_field_name("name")
            .text.decode()
        )  # type: ignore
        self.clazz = clazz
        self.file = file
        self.code = node.text.decode()  # type: ignore
        self.signature = f"{self.clazz.fullname}.{self.name}"


class Method:
    def __init__(self, node: Node, clazz: Class | None, file: File, language: Language, st=-1, ed=-1, code = ""):
        self.language = language
        if language == Language.JAVA:
            name_node = node.child_by_field_name("name")
            assert name_node is not None and name_node.text is not None
            self.name = name_node.text.decode()
        else:
            name_node = node.child_by_field_name("declarator")
            while name_node is not None and name_node.type not in {
                "identifier",
                "operator_name",
                "type_identifier",
            }:
                # print("------------")
                # print(name_node.type, name_node.text)
                all_temp_name_node = name_node
                if (
                    name_node.child_by_field_name("declarator") is None
                    and name_node.type == "reference_declarator"
                ):
                    for temp_node in name_node.children:
                        if temp_node.type == "function_declarator":
                            name_node = temp_node
                            break
                if name_node.child_by_field_name("declarator") is not None:
                    name_node = name_node.child_by_field_name("declarator")
                # print(name_node.type, name_node.text)
                
                while name_node is not None and (
                    name_node.type == "qualified_identifier"
                    or name_node.type == "template_function"
                ):
                    temp_name_node = name_node
                    for temp_node in name_node.children:
                        # print(temp_node.type, temp_node.text)
                        if temp_node.type in {
                            "identifier",
                            "destructor_name",
                            "qualified_identifier",
                            "operator_name",
                            "type_identifier",
                            "pointer_type_declarator",
                        }:
                            name_node = temp_node
                            break
                    if name_node == temp_name_node:
                        break
                #     print(name_node.type, name_node.text)
                # print(name_node.type, name_node.text)
                
                if name_node is not None and name_node.type == "destructor_name":
                    for temp_node in name_node.children:
                        if temp_node.type == "identifier":
                            name_node = temp_node
                            break

                
                if (
                    name_node is not None
                    and name_node.type == "field_identifier"
                    and name_node.child_by_field_name("declarator") is None
                ):
                    break
                # print(name_node.type, name_node.text)
                if name_node == all_temp_name_node:
                    break

            assert name_node is not None and name_node.text is not None
            self.name = name_node.text.decode()
        self.clazz = clazz
        self.file = file
        self.node = node
        if st == -1:
            assert node.text is not None
            self.code = node.text.decode()
            self.start_line = node.start_point[0] + 1
            self.end_line = node.end_point[0] + 1
        else:
            self.code = code
            self.start_line = st+1
            self.end_line = ed+1

        self.lines: dict[int, str] = {
            i + self.start_line: line for i, line in enumerate(self.code.split("\n"))
        }

        self.abs_lines: dict[int, str] = {
            i + self.start_line: line
            for i, line in enumerate(self.abstract_code.split("\n"))
        }

        # print(self.name, self.lines, self.start_line)

        self._pdg: joern.PDG | None = None

        self.joern_path: str | None = None

        
        
        self.counterpart: Method | None = None
        self.method_dir: str | None = None
        self.html_base_path: str = ""
        self.method_file: str = ""
        self.diff_add_lines: list[tuple[int, int]] = []
        self.diff_del_lines: list[tuple[int, int]] = []

    @classmethod
    def init_from_file_code(cls, path: str, language: Language):
        with open(path, "r") as f:
            code = f.read()
        file = File(path, code, None, language)
        parser = ASTParser(code, language)
        method_node = parser.query_oneshot(ast_parser.TS_C_METHOD)
        assert method_node is not None
        return cls(method_node, None, file, language)

    @property
    def pdg(self) -> joern.PDG | None:
        assert self.file.project.joern is not None
        if self._pdg is None:
            self._pdg = self.file.project.joern.get_pdg(self)
        return self._pdg

    @cached_property
    def abstract_code(self):
        return code_transformation.abstract(self.code, self.language)

    @property
    def line_pdg_pairs(self) -> dict[int, joern.PDGNode] | None:
        line_pdg_pairs = {}
        if self.pdg is None:
            return None
        for node_id in self.pdg.g.nodes():
            node = self.pdg.get_node(node_id)
            if node.line_number is None:
                continue
            line_pdg_pairs[node.line_number] = node
        return line_pdg_pairs

    @property
    def rel_line_pdg_pairs(self) -> dict[int, joern.PDGNode] | None:
        rel_line_pdg_pairs = {}
        if self.pdg is None:
            return None
        for node_id in self.pdg.g.nodes():
            node = self.pdg.get_node(node_id)
            if node.line_number is None:
                continue
            rel_line_pdg_pairs[node.line_number - self.start_line + 1] = node
        return rel_line_pdg_pairs

    @cached_property
    def line_number_pdg_map(self):
        assert self.file.project.joern is not None
        pdg_dir = os.path.join(self.file.project.joern.path, "pdg")
        dot_names = os.listdir(pdg_dir)
        for dot in dot_names:
            dot_path = os.path.join(pdg_dir, dot)
            try:
                pdg = joern.PDG(pdg_path=dot_path)
            except Exception as e:
                logging.warning(f"❌ PDG loading failed: {dot_path}")
                logging.warning(e)
                continue
            if pdg.name is None or pdg.line_number is None or pdg.filename is None:
                continue
            if pdg.line_number == self.start_line and pdg.filename == self.file.path:
                method_nodes = []
                line_map_method_nodes = pdg.line_map_method_nodes_id
                for line in line_map_method_nodes:
                    if isinstance(line_map_method_nodes[line], int):
                        method_nodes.append(line_map_method_nodes[line])
                        line_map_method_nodes[line] = [line_map_method_nodes[line]]
                    else:
                        method_nodes.extend(line_map_method_nodes[line])
                return [method_nodes, line_map_method_nodes]
        return [-1, -1]

    @property
    def caller(self):
        callers = []
        assert self.file.project.joern is not None
        cpg_path = os.path.join(self.file.project.joern.path, "cpg", "export.dot")
        cpg: nx.MultiDiGraph = nx.nx_agraph.read_dot(cpg_path)
        method_ids = self.line_number_pdg_map[0]
        line_map_method_nodes = self.line_number_pdg_map[1]
        for u, v, d in cpg.edges(data=True):
            if d["label"] == "CALL" and v in method_ids:
                line_number = cpg.nodes[u]["LINE_NUMBER"]
                callers.append(line_number + "__split__" + u)

        return callers

    @property
    def callee(self):
        ## using joern so slow
        callees = set()
        # assert self.file.project.joern is not None # type: ignore
        # print(self.signature)
        # cpg_path = os.path.join(self.file.project.joern.path, "cpg", "export.dot") # type: ignore
        # cpg: nx.MultiDiGraph = nx.nx_agraph.read_dot(cpg_path)
        # method_ids = self.line_number_pdg_map[0]
        # line_map_method_nodes = self.line_number_pdg_map[1]
        # for u, v, d in cpg.edges(data=True):
        #     if d['label'] == "CALL" and u in method_ids and 'LINE_NUMBER' in cpg.nodes[v].keys():
        #         if 'label' in cpg.nodes[v] and cpg.nodes[v]['label'] == 'METHOD':
        #             line_number = next((key for key, value in line_map_method_nodes.items() if u in value), None) # type: ignore
        #             callees.append({"callee_linenumber":line_number, "callee_method_name":f"{cpg.nodes[v]['FILENAME']}#{cpg.nodes[v]['NAME']}", "method_line_number":cpg.nodes[v]['LINE_NUMBER']}) # type: ignore
        parser = ASTParser(self.code, self.language)

        call = parser.query_all(ast_parser.CPP_CALL)
        if len(call) == 0:
            return None

        for node in call:
            callees.add(node.text.decode())

        return callees

    @property
    def body_node(self) -> Node | None:
        return self.node.child_by_field_name("body")

    @property
    def body_start_line(self) -> int:
        if self.body_node is None:
            return self.start_line
        else:
            return self.body_node.start_point[0] + 1

    @property
    def body_end_line(self) -> int:
        if self.body_node is None:
            return self.end_line
        else:
            return self.body_node.end_point[0] + 1

    @property
    def diff_dir(self) -> str:
        assert self.method_dir is not None
        return f"{self.method_dir}/diff"

    @property
    def dot_dir(self) -> str:
        assert self.method_dir is not None
        return f"{self.method_dir}/dot"

    @property
    def rel_line_set(self) -> set[int]:
        return set(range(self.rel_start_line, self.rel_end_line + 1))

    @property
    def parameters(self) -> list[Node]:
        parameters_node = self.node.child_by_field_name("parameters")
        if parameters_node is None:
            return []
        parameters = ASTParser.children_by_type_name(
            parameters_node, "formal_parameter"
        )
        return parameters

    @property
    def parameter_signature(self) -> str:
        parameter_signature_list = []
        for param in self.parameters:
            type_node = param.child_by_field_name("type")
            assert type_node is not None
            if type_node.type == "generic_type":
                type_identifier_node = ASTParser.child_by_type_name(
                    type_node, "type_identifier"
                )
                if type_identifier_node is None:
                    type_name = ""
                else:
                    assert type_identifier_node.text is not None
                    type_name = type_identifier_node.text.decode()
            else:
                assert type_node.text is not None
                type_name = type_node.text.decode()
            parameter_signature_list.append(type_name)
        return ",".join(parameter_signature_list)

    @property
    def signature(self) -> str:
        if self.language == Language.JAVA:
            assert self.clazz is not None
            return f"{self.clazz.fullname}.{self.name}({self.parameter_signature})"
        else:
            return f"{self.file.path}#{self.name}"

    @property
    def signature_r(self) -> str:
        if self.language == Language.JAVA:
            assert self.clazz is not None
            fullname_r = ".".join(self.clazz.fullname.split(".")[::-1])
            return f"{self.name}({self.parameter_signature}).{fullname_r}"
        else:
            return f"{self.name}#{self.start_line}#{self.end_line}#{self.file.name}"

    @property
    def diff_lines(self) -> set[int]:
        lines = set()
        for hunk in self.patch_hunks:
            if type(hunk) == DelHunk:
                lines.update(range(hunk.a_startline, hunk.a_endline + 1))
            elif type(hunk) == ModHunk:
                lines.update(range(hunk.a_startline, hunk.a_endline + 1))
        return lines

    @property
    def rel_diff_lines(self) -> set[int]:
        return set([line - self.start_line + 1 for line in self.diff_lines])

    @property
    def diff_identifiers(self):
        assert self.counterpart is not None
        diff_identifiers = {}
        for hunk in self.patch_hunks:
            if type(hunk) == DelHunk:
                lines = set(range(hunk.a_startline, hunk.a_endline + 1))
                criteria_identifier_a = self.identifier_by_lines(lines)
                diff_identifiers.update(criteria_identifier_a)
            elif type(hunk) == ModHunk:
                a_lines = set(range(hunk.a_startline, hunk.a_endline + 1))
                b_lines = set(range(hunk.b_startline, hunk.b_endline + 1))
                criteria_identifier_a = self.identifier_by_lines(a_lines)
                criteria_identifier_b = self.counterpart.identifier_by_lines(b_lines)
                lines = a_lines.union(b_lines)
                for line in lines:
                    if (
                        line in criteria_identifier_a.keys()
                        and line in criteria_identifier_b.keys()
                    ):
                        diff_identifiers[line] = (
                            criteria_identifier_a[line] - criteria_identifier_b[line]
                        )
                    elif line in criteria_identifier_a.keys():
                        diff_identifiers[line] = criteria_identifier_a[line]
        return diff_identifiers

    @property
    def change_hunks(self):
        hunks = []
        # TODO
        return hunks

    @property
    def body_lines(self) -> set[int]:
        body_start_line = self.body_start_line
        body_end_line = self.body_end_line
        if self.lines[self.body_start_line].strip().endswith("{"):
            body_start_line += 1
        if self.lines[self.body_end_line].strip().endswith("}"):
            body_end_line -= 1
        return set(range(body_start_line, body_end_line + 1))

    @property
    def body_code(self) -> str:
        return "\n".join([self.lines[line] for line in sorted(self.body_lines)])

    @cached_property
    def patch_hunks(self) -> list[Hunk]:
        assert self.counterpart is not None
        hunks = get_patch_hunks(self.file.code, self.counterpart.file.code)
        for hunk in hunks.copy():
            if type(hunk) == ModHunk or type(hunk) == DelHunk:
                if not (
                    self.start_line <= hunk.a_startline
                    and hunk.a_endline <= self.end_line
                ):
                    hunks.remove(hunk)
            elif type(hunk) == AddHunk:
                if (
                    hunk.insert_line < self.start_line
                    or hunk.insert_line > self.end_line
                ):
                    hunks.remove(hunk)

        def sort_key(hunk: Hunk):
            if type(hunk) == AddHunk:
                return hunk.insert_line
            elif type(hunk) == ModHunk or type(hunk) == DelHunk:
                return hunk.a_startline
            else:
                return 0

        # sort hunks by start line
        hunks.sort(key=sort_key)
        return hunks

    @property
    def header_lines(self) -> set[int]:
        return set(range(self.start_line, self.body_start_line + 1))

    @property
    def body_lines(self) -> set[int]:
        body_start_line = self.body_start_line
        body_end_line = self.body_end_line
        while body_start_line not in self.lines.keys() or self.lines[body_start_line].strip().endswith("{"):
            body_start_line += 1
        while body_end_line not in self.lines.keys() or self.lines[body_end_line].strip().endswith("}"):
            body_end_line -= 1
        return set(range(body_start_line, body_end_line + 1))

    @property
    def body_code(self) -> str:
        return "\n".join([self.lines[line] for line in sorted(self.body_lines)])

    @property
    def comment_lines(self) -> set[int]:
        body_node = self.node.child_by_field_name("body")
        if body_node is None:
            return set()
        comment_lines = set()
        query = f"""
        (line_comment)@line_comment
        (block_comment)@block_comment
        """
        comment_nodes = self.file.parser.query_from_node(body_node, query)
        line_comments = [
            comment for comment in comment_nodes if comment[1] == "line_comment"
        ]
        block_comments = [
            comment for comment in comment_nodes if comment[1] == "block_comment"
        ]
        for comment_node in line_comments:
            line = comment_node.start_point[0] + 1
            if self.lines[line].strip() == comment_node.text.decode().strip():  # type: ignore
                comment_lines.add(line)
        for comment_node in block_comments:
            start_line = comment_node.start_point[0] + 1
            end_line = comment_node.end_point[0] + 1
            if self.lines[start_line].strip().startswith("/*"):
                comment_lines.update(range(start_line, end_line + 1))
        return comment_lines

    @property
    def modified_parameters(self):
        diff_lines = self.diff_lines
        modified_parameters = {}
        if self.language == Language.C or self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                if line in diff_lines:
                    left_param = node.child_by_field_name("left")
                    if left_param is None or left_param.text.decode() == "":
                        continue
                    try:
                        modified_parameters[line].add(left_param.text.decode())
                    except:
                        modified_parameters[line] = set()
                        modified_parameters[line].add(left_param.text.decode())

        return modified_parameters

    def abstract_code_by_lines(self, lines: set[int]):
        result = "\n".join([self.abs_rel_lines[line] for line in sorted(lines)])
        return result + "\n"

    def code_by_lines(self, lines: set[int], *, placeholder: str | None = None) -> str:
        if placeholder is None:
            # print(self.rel_lines, lines)
            result = "\n".join([self.rel_lines[line] for line in sorted(lines)])
            return result + "\n"
        else:
            code_with_placeholder = ""
            last_line = 0
            placeholder_counter = 0
            for line in sorted(lines):
                if line - last_line > 1:
                    is_comment = True
                    for i in range(last_line + 1, line):
                        if self.rel_lines[i].strip() == "":
                            continue
                        if not self.rel_lines[i].strip().startswith("//"):
                            is_comment = False
                            break
                    if is_comment:
                        pass
                    elif line - last_line == 2 and (
                        self.rel_lines[line - 1].strip() == ""
                        or self.rel_lines[line - 1].strip().startswith("//")
                    ):
                        pass
                    else:
                        code_with_placeholder += f"{placeholder}\n"
                        placeholder_counter += 1
                code_with_placeholder += self.rel_lines[line] + "\n"
                last_line = line
            return code_with_placeholder

    def reduced_hunks(self, slines: set[int]) -> list[str]:
        placeholder_lines = self.rel_line_set - slines
        return self.code_hunks(placeholder_lines)

    def code_hunks(self, lines: set[int]) -> list[str]:
        hunks: list[str] = []
        lineg = group_consecutive_ints(list(lines))
        for g in lineg:
            hunk = self.code_by_lines(set(g))
            hunks.append(hunk)
        return hunks

    def code_by_exclude_lines(self, lines: set[int], *, placeholder: str | None) -> str:
        exclude_lines = self.rel_line_set - lines
        return self.code_by_lines(exclude_lines, placeholder=placeholder)

    def identifier_by_lines(self, lines: set[int], pure=False):
        identifier_list = {}
        if self.language == Language.C or self.language == Language.CPP:
            identifier_nodes = self.file.parser.get_all_identifier_node()
            for node in identifier_nodes:
                if node.parent.type == "unary_expression" and not pure:
                    line = node.parent.start_point[0] + 1
                    if line in lines:
                        assert node.parent.text is not None
                        try:
                            identifier_list[line].add(node.parent.text.decode())
                        except:
                            identifier_list[line] = {node.parent.text.decode()}
                else:
                    line = node.start_point[0] + 1
                    if line in lines:
                        assert node.text is not None
                        try:
                            identifier_list[line].add(node.text.decode())
                        except:
                            identifier_list[line] = {node.text.decode()}
        return identifier_list

    def conditions_by_lines(self, lines: set[int]):
        conditions_list = set()
        if self.language == Language.C or self.language == Language.CPP:
            conditional_nodes = self.file.parser.get_all_conditional_node()
            for node in conditional_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    conditions_list.add(line)
        return conditions_list

    def ret_by_lines(self, lines: set[int]):
        ret_list = set()
        if self.language == Language.C or self.language == Language.CPP:
            ret_nodes = self.file.parser.get_all_return_node()
            for node in ret_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        return ret_list

    def assignment_by_lines(self, lines: set[int]):
        assign_list = set()
        if self.language == Language.C or self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    assign_list.add(line)
        return assign_list

    def call_by_lines(self, lines: set[int]):
        ret_list = set()
        if self.language == Language.C or self.language == Language.CPP:
            call_nodes = self.file.parser.get_all_call_node()
            for node in call_nodes:
                line = node.start_point[0] + 1
                if line in lines:
                    ret_list.add(line)
        return ret_list

    def all_assignment_lines(self):
        assign_list = set()
        if self.language == Language.C or self.language == Language.CPP:
            assign_nodes = self.file.parser.get_all_assign_node()
            for node in assign_nodes:
                line = node.start_point[0] + 1
                assign_list.add(line)
        return assign_list

    @cached_property
    def all_flow_control_lines(self):
        control_list = {}
        if self.language == Language.C or self.language == Language.CPP:
            control_nodes = self.file.parser.get_all_flow_control_goto()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "goto"
            control_nodes = self.file.parser.get_all_flow_control_break()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "break"
            control_nodes = self.file.parser.get_all_flow_control()
            for node in control_nodes:
                line = node.start_point[0] + 1
                control_list[line] = "continue"
        return control_list

    @property
    def normalized_body_code(self) -> str:
        return format_code.normalize(self.body_code)

    @property
    def formatted_code(self) -> str:
        return format.format(
            self.code, self.language, del_comment=True, del_linebreak=True
        )

    @property
    def rel_start_line(self) -> int:
        return 1

    @property
    def rel_end_line(self) -> int:
        return self.end_line - self.start_line + 1

    @property
    def rel_body_start_line(self) -> int:
        return self.body_start_line - self.start_line + 1

    @property
    def rel_body_end_line(self) -> int:
        return self.body_end_line - self.start_line + 1

    @property
    def rel_lines(self) -> dict[int, str]:
        return {line - self.start_line + 1: code for line, code in self.lines.items()}

    @property
    def abs_rel_lines(self) -> dict[int, str]:
        self.abs_lines: dict[int, str] = {
            i + self.start_line: line
            for i, line in enumerate(self.abstract_code.split("\n"))
        }
        return {
            line - self.start_line + 1: code for line, code in self.abs_lines.items()
        }

    @property
    def length(self):
        return self.end_line - self.start_line + 1

    @property
    def file_suffix(self):
        if self.language == Language.C:
            suffix = ".c"
        elif self.language == Language.JAVA:
            suffix = ".java"
        elif self.language == Language.CPP:
            suffix = ".cpp"
        else:
            suffix = ""
        return suffix

    def write_cg(self, path = None):
        if self.file.path == "libcpp/init.c":
            return
        
        if self.pdg is None:
            return
        assert self.cpg is not None
        nx.nx_agraph.write_dot(self.cpg.g, path)
        
    def write_dot(self, dir: str | None = None):
        if self.file.path == "libcpp/init.c":
            return
        
        if self.pdg is None:
            return
        assert self.pdg is not None
        dot_name = f"{self.file.project.project_name}.dot"
        if dir is not None:
            dot_path = os.path.join(dir, dot_name)
        else:
            dot_path = os.path.join(self.dot_dir, dot_name)
        nx.nx_agraph.write_dot(self.pdg.g, dot_path)

    def write_code(self, dir: str | None = None):
        assert self.method_dir is not None
        file_name = f"{self.file.project.project_name}{self.file_suffix}"
        if dir is not None:
            code_path = os.path.join(dir, file_name)
        else:
            code_path = os.path.join(self.method_dir, file_name)
        with open(code_path, "w") as f:
            f.write(self.code)

    @staticmethod
    def backward_slice(criteria_lines: set[int], criteria_nodes: list[PDGNode], criteria_identifier: dict[int, set[str]], all_nodes: dict[int, list[PDGNode]], level: int) -> dict[int, dict[int, int]]:
        result_lines = {}
        for line in criteria_lines:
            result_lines[line] = {}
        if level == 0:
            level = 1000

        
        for slice_line in criteria_lines:
            for node in all_nodes[slice_line]:
                if node.type == "METHOD" or "METHOD_RETURN" in ast.literal_eval(node.type):
                    continue
                for pred_node in node.pred_cfg_nodes:
                    if pred_node.line_number is None or int(pred_node.line_number) == sys.maxsize:
                        continue
                    if int(pred_node.line_number) in result_lines[slice_line]:
                        result_lines[slice_line][int(pred_node.line_number)] = min(result_lines[slice_line][int(pred_node.line_number)], 1)
                    else:
                        result_lines[slice_line][int(pred_node.line_number)] = 1

        
        for sline in criteria_lines:
            for node in all_nodes[sline]:
                if node.type == "METHOD" or "METHOD_RETURN" in ast.literal_eval(node.type):
                    continue
                visited = set()
                queue: deque[tuple[PDGNode, int]] = deque([(node, 0)])
                while queue:
                    node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        if node.line_number is not None:
                            if node.line_number in result_lines[sline]:
                                result_lines[sline][node.line_number] = min(result_lines[sline][node.line_number], depth)
                            else:
                                result_lines[sline][node.line_number] = depth
                        if depth < level:
                            for pred_node, edge in node.pred_ddg:
                                if pred_node.line_number is None or int(pred_node.line_number) == sys.maxsize or node.line_number is None:
                                    continue
                                if pred_node.line_number > node.line_number:
                                    continue
                                if edge not in node.code:
                                    continue
                                if len(criteria_identifier) > 0:
                                    if node.line_number in criteria_identifier:
                                        if edge not in criteria_identifier[node.line_number]:
                                            continue
                                queue.append((pred_node, depth + 1))

        return result_lines

    @staticmethod
    def forward_slice(criteria_lines: set[int], criteria_nodes: list[PDGNode], criteria_identifier: dict[int, set[str]], all_nodes: dict[int, list[PDGNode]], level: int) -> dict[int, dict[int, int]]:
        result_lines = {}
        for line in criteria_lines:
            result_lines[line] = {}
        if level == 0:
            level = 1000

        for slice_line in criteria_lines:
            for node in all_nodes[slice_line]:
                if node.type == "METHOD" or "METHOD_RETURN" in ast.literal_eval(node.type):
                    continue
                if node.line_number is None:
                    continue
                for succ_node in node.succ_cfg_nodes:
                    if succ_node.line_number is None or int(succ_node.line_number) == sys.maxsize:
                        continue
                    if succ_node.line_number < node.line_number:
                        continue
                    if int(succ_node.line_number) in result_lines[slice_line]:
                        result_lines[slice_line][int(succ_node.line_number)] = min(result_lines[slice_line][int(succ_node.line_number)], 1)
                    else:
                        result_lines[slice_line][int(succ_node.line_number)] = 1

        for sline in criteria_lines:
            for node in all_nodes[sline]:
                if node.type == "METHOD" or "METHOD_RETURN" in ast.literal_eval(node.type):
                    continue
                visited = set()
                queue: deque[tuple[PDGNode, int]] = deque([(node, 0)])
                while queue:
                    node, depth = queue.popleft()
                    if node not in visited:
                        visited.add(node)
                        if node.line_number is not None:
                            if node.line_number in result_lines[sline]:
                                result_lines[sline][node.line_number] = min(result_lines[sline][node.line_number], depth)
                            else:
                                result_lines[sline][node.line_number] = depth
                        if depth < level:
                            for succ_node, edge in node.succ_ddg:
                                if edge not in node.code:
                                    continue
                                if succ_node.line_number is None or int(succ_node.line_number) == sys.maxsize or node.line_number is None:
                                    continue
                                if succ_node.line_number < node.line_number:
                                    continue
                                if node.line_number in criteria_identifier:
                                    if edge not in criteria_identifier[node.line_number]:
                                        continue
                                queue.append((succ_node, depth + 1))

        return result_lines

    def slice(self, criteria_lines: set[int], criteria_identifier: dict[int, set[str]], backward_slice_level: int = 4, forward_slice_level: int = 4, is_rel: bool = False):
        assert self.pdg is not None
        if is_rel:
            criteria_lines = set([line + self.start_line - 1 for line in criteria_lines])

        all_lines = set(self.lines.keys())
        all_nodes: dict[int, list[PDGNode]] = {
            line: self.pdg.get_nodes_by_line_number(line) for line in all_lines
        }
        criteria_nodes: list[PDGNode] = []
        for line in criteria_lines:
            for node in self.pdg.get_nodes_by_line_number(line):
                node.is_patch_node = True
                node.add_attr("color", "red")
                criteria_nodes.append(node)

        slice_result_lines = {}
        for line in criteria_lines:
            slice_result_lines[line] = {}

        
        result_lines = self.backward_slice(
            criteria_lines, criteria_nodes, criteria_identifier, all_nodes, backward_slice_level)
        for line in result_lines:
            slice_result_lines[line].update(result_lines[line])
        result_lines = self.forward_slice(
            criteria_lines, criteria_nodes, criteria_identifier, all_nodes, forward_slice_level)
        for line in result_lines:
            slice_result_lines[line].update(result_lines[line])

        return slice_result_lines

    def slice_by_diff_lines(self, backward_slice_level: int = 0, forward_slice_level: int = 0, need_criteria_identifier: bool = False, write_dot: bool = False):
        criteria_identifier = self.diff_identifiers if need_criteria_identifier else {}
        slice_results = self.slice(self.diff_lines, criteria_identifier,
                                   backward_slice_level, forward_slice_level, is_rel=False)
        return slice_results

if __name__ == "__main__":
    pass
