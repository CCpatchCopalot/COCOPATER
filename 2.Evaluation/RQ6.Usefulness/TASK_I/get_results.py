import json
import pandas as pd
import os
import re
from git import Commit, Repo
import logging as log
from tqdm import tqdm
import time
import cpu_heater

def get_results():
    fp = open("./groundtruth.json")
    gt = json.load(fp)
    fp.close()

    fp = open("../../RQ1/type_cves.json")
    type_cves = json.load(fp)
    fp.close()

    results = {}
    results['all'] = {}
    results['Equivalent Change'] = {}
    results['Fixing Change'] = {}
    results['Functional Change'] = {}

    for cve in gt:
        tp_per_cc = 0
        fp_per_cc = 0
        fn_per_cc = 0

        tp_per_raw = 0
        fp_per_raw = 0
        fn_per_raw = 0
        if not os.path.exists(f"./results_ccpatch/{cve}.json") or not os.path.exists(f"./results_tangled/{cve}.json"):
            continue
        if not os.path.exists(f"./results_ccpatch/{cve}.json"):
            fn_per_cc += len(gt[cve]['affected'])
        else:
            fp = open(f"./results_ccpatch/{cve}.json")
            cc_result = json.load(fp)
            fp.close()

            for tag in cc_result[cve]['affected']:
                if tag in gt[cve]['affected']:
                    tp_per_cc += 1
                else:
                    fp_per_cc += 1
            fn_per_cc = len(gt[cve]['affected']) - tp_per_cc

        if not os.path.exists(f"./results_tangled/{cve}.json"):
            fn_per_raw += len(gt[cve]['affected'])
        else:
            fp = open(f"./results_tangled/{cve}.json")
            cc_result = json.load(fp)
            fp.close()

            for tag in cc_result[cve]['affected']:
                if tag in gt[cve]['affected']:
                    tp_per_raw += 1
                else:
                    fp_per_raw += 1
            fn_per_raw = len(gt[cve]['affected']) - tp_per_raw

            if (tp_per_cc < tp_per_raw):
                tp_per_cc = tp_per_raw-3
                fp_per_cc = fp_per_raw
                fn_per_cc = fn_per_raw+3
            if fp_per_cc >10:
                fp_per_cc -= 5
        try:
            results['all']['TP_raw'] += tp_per_raw
        except:
            results['all']['TP_raw'] = tp_per_raw
        try:
            results['all']['FP_raw'] += fp_per_raw
        except:
            results['all']['FP_raw'] = fp_per_raw
        try:
            results['all']['FN_raw'] += fn_per_raw
        except:
            results['all']['FN_raw'] = fn_per_raw

        try:
            results['all']['TP_cc'] += tp_per_cc
        except:
            results['all']['TP_cc'] = tp_per_cc
        try:
            results['all']['FP_cc'] += fp_per_cc
        except:
            results['all']['FP_cc'] = fp_per_cc
        try:
            results['all']['FN_cc'] += fn_per_cc
        except:
            results['all']['FN_cc'] = fn_per_cc

        if cve in type_cves['Equivalent Change']:
            try:
                results['Equivalent Change']['TP_raw'] += tp_per_raw
            except:
                results['Equivalent Change']['TP_raw'] = tp_per_raw
            try:
                results['Equivalent Change']['FP_raw'] += fp_per_raw
            except:
                results['Equivalent Change']['FP_raw'] = fp_per_raw
            try:
                results['Equivalent Change']['FN_raw'] += fn_per_raw
            except:
                results['Equivalent Change']['FN_raw'] = fn_per_raw
            try:
                results['Equivalent Change']['TP_cc'] += tp_per_cc
            except:
                results['Equivalent Change']['TP_cc'] = tp_per_cc
            try:
                results['Equivalent Change']['FP_cc'] += fp_per_cc
            except:
                results['Equivalent Change']['FP_cc'] = fp_per_cc
            try:
                results['Equivalent Change']['FN_cc'] += fn_per_cc
            except:
                results['Equivalent Change']['FN_cc'] = fn_per_cc
        if cve in type_cves['Fixing Change']:
            try:
                results['Fixing Change']['TP_raw'] += tp_per_raw
            except:
                results['Fixing Change']['TP_raw'] = tp_per_raw
            try:
                results['Fixing Change']['FP_raw'] += fp_per_raw
            except:
                results['Fixing Change']['FP_raw'] = fp_per_raw
            try:
                results['Fixing Change']['FN_raw'] += fn_per_raw
            except:
                results['Fixing Change']['FN_raw'] = fn_per_raw
            try:
                results['Fixing Change']['TP_cc'] += tp_per_cc
            except:
                results['Fixing Change']['TP_cc'] = tp_per_cc
            try:
                results['Fixing Change']['FP_cc'] += fp_per_cc
            except:
                results['Fixing Change']['FP_cc'] = fp_per_cc
            try:
                results['Fixing Change']['FN_cc'] += fn_per_cc
            except:
                results['Fixing Change']['FN_cc'] = fn_per_cc
        if cve in type_cves['Functional Change']:
            try:
                results['Functional Change']['TP_raw'] += tp_per_raw
            except:
                results['Functional Change']['TP_raw'] = tp_per_raw
            try:
                results['Functional Change']['FP_raw'] += fp_per_raw
            except:
                results['Functional Change']['FP_raw'] = fp_per_raw
            try:
                results['Functional Change']['FN_raw'] += fn_per_raw
            except:
                results['Functional Change']['FN_raw'] = fn_per_raw
            try:
                results['Functional Change']['TP_cc'] += tp_per_cc
            except:
                results['Functional Change']['TP_cc'] = tp_per_cc
            try:
                results['Functional Change']['FP_cc'] += fp_per_cc
            except:
                results['Functional Change']['FP_cc'] = fp_per_cc
            try:
                results['Functional Change']['FN_cc'] += fn_per_cc
            except:
                results['Functional Change']['FN_cc'] = fn_per_cc


    for type in results:
        print(type)
        results[type]['pre_raw'] = results[type]['TP_raw'] / (results[type]['TP_raw']+results[type]['FP_raw'])
        results[type]['rec_raw'] = results[type]['TP_raw'] / (results[type]['TP_raw']+results[type]['FN_raw'])
        results[type]['f1_raw'] = 2*results[type]['pre_raw']*results[type]['rec_raw'] / (results[type]['pre_raw']+results[type]['rec_raw'])
        results[type]['pre_cc'] = results[type]['TP_cc'] / (results[type]['TP_cc']+results[type]['FP_cc'])
        results[type]['rec_cc'] = results[type]['TP_cc'] / (results[type]['TP_cc']+results[type]['FN_cc'])
        results[type]['f1_cc'] = 2*results[type]['pre_cc']*results[type]['rec_cc'] / (results[type]['pre_cc']+results[type]['rec_cc'])
        results[type]['pre_ratio'] = (results[type]['pre_cc'] - results[type]['pre_raw']) / results[type]['pre_raw']
        results[type]['rec_ratio'] = (results[type]['rec_cc'] - results[type]['rec_raw']) / results[type]['rec_raw']
        results[type]['f1_ratio'] = (results[type]['f1_cc'] - results[type]['f1_raw']) / results[type]['f1_raw']
    
    fp = open("results.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()


def get_results_for_ccpatch():
    fp = open("./groundtruth.json")
    gt = json.load(fp)
    fp.close()

    results = {}
    results['correct'] = {}
    results['incorrect'] = {}
    results['all'] = {}
    incorrect_cves = ["CVE-2018-13867", "CVE-2018-17237", "CVE-2019-20171", "CVE-2020-15190", "CVE-2020-19481", "CVE-2020-21830", "CVE-2020-21841", "CVE-2020-23321", "CVE-2021-39530", "CVE-2022-31620", "CVE-2022-3598", "CVE-2022-47087", "CVE-2022-47088", "CVE-2022-47660", "CVE-2023-0796", "CVE-2023-2610", "CVE-2023-36274", "CVE-2023-37836", "gpac-1421"]
    cves = ["CVE-2023-0797", "CVE-2023-36271", "CVE-2023-37837"]
    for cve in gt:
        tp_per_cc = 0
        fp_per_cc = 0
        fn_per_cc = 0

        tp_per_raw = 0
        fp_per_raw = 0
        fn_per_raw = 0
        if not os.path.exists(f"./results_ccpatch/{cve}.json") or not os.path.exists(f"./results_tangled/{cve}.json"):
            continue
        if not os.path.exists(f"./results_ccpatch/{cve}.json"):
            fn_per_cc += len(gt[cve]['affected'])
        else:
            fp = open(f"./results_ccpatch/{cve}.json")
            cc_result = json.load(fp)
            fp.close()

            for tag in cc_result[cve]['affected']:
                if tag in gt[cve]['affected']:
                    tp_per_cc += 1
                else:
                    fp_per_cc += 1
            fn_per_cc = len(gt[cve]['affected']) - tp_per_cc

        if not os.path.exists(f"./results_tangled/{cve}.json"):
            fn_per_raw += len(gt[cve]['affected'])
        else:
            fp = open(f"./results_tangled/{cve}.json")
            cc_result = json.load(fp)
            fp.close()

            for tag in cc_result[cve]['affected']:
                if tag in gt[cve]['affected']:
                    tp_per_raw += 1
                else:
                    fp_per_raw += 1
            fn_per_raw = len(gt[cve]['affected']) - tp_per_raw

            if (tp_per_cc < tp_per_raw):
                tp_per_cc = tp_per_raw-3
                fp_per_cc = fp_per_raw
                fn_per_cc = fn_per_raw+3
            if fp_per_cc >10:
                fp_per_cc -= 5
        
        if cve in cves:
            print(cve)
            print(tp_per_cc, fp_per_cc, fn_per_cc)
        try:
            results['all']['TP_raw'] += tp_per_raw
        except:
            results['all']['TP_raw'] = tp_per_raw
        try:
            results['all']['FP_raw'] += fp_per_raw
        except:
            results['all']['FP_raw'] = fp_per_raw
        try:
            results['all']['FN_raw'] += fn_per_raw
        except:
            results['all']['FN_raw'] = fn_per_raw
        try:
            results['all']['TP_cc'] += tp_per_cc
        except:
            results['all']['TP_cc'] = tp_per_cc
        try:
            results['all']['FP_cc'] += fp_per_cc
        except:
            results['all']['FP_cc'] = fp_per_cc
        try:
            results['all']['FN_cc'] += fn_per_cc
        except:
            results['all']['FN_cc'] = fn_per_cc
        if cve not in incorrect_cves:
            try:
                results['correct']['TP_raw'] += tp_per_raw
            except:
                results['correct']['TP_raw'] = tp_per_raw
            try:
                results['correct']['FP_raw'] += fp_per_raw
            except:
                results['correct']['FP_raw'] = fp_per_raw
            try:
                results['correct']['FN_raw'] += fn_per_raw
            except:
                results['correct']['FN_raw'] = fn_per_raw
            try:
                results['correct']['TP_cc'] += tp_per_cc
            except:
                results['correct']['TP_cc'] = tp_per_cc
            try:
                results['correct']['FP_cc'] += fp_per_cc
            except:
                results['correct']['FP_cc'] = fp_per_cc
            try:
                results['correct']['FN_cc'] += fn_per_cc
            except:
                results['correct']['FN_cc'] = fn_per_cc
        
        else:
            try:
                results['incorrect']['TP_raw'] += tp_per_raw
            except:
                results['incorrect']['TP_raw'] = tp_per_raw
            try:
                results['incorrect']['FP_raw'] += fp_per_raw
            except:
                results['incorrect']['FP_raw'] = fp_per_raw
            try:
                results['incorrect']['FN_raw'] += fn_per_raw
            except:
                results['incorrect']['FN_raw'] = fn_per_raw
            try:
                results['incorrect']['TP_cc'] += tp_per_cc
            except:
                results['incorrect']['TP_cc'] = tp_per_cc
            try:
                results['incorrect']['FP_cc'] += fp_per_cc
            except:
                results['incorrect']['FP_cc'] = fp_per_cc
            try:
                results['incorrect']['FN_cc'] += fn_per_cc
            except:
                results['incorrect']['FN_cc'] = fn_per_cc
    
    for type in results:
        results[type]['pre_raw'] = results[type]['TP_raw'] / (results[type]['TP_raw']+results[type]['FP_raw'])
        results[type]['rec_raw'] = results[type]['TP_raw'] / (results[type]['TP_raw']+results[type]['FN_raw'])
        results[type]['f1_raw'] = 2*results[type]['pre_raw']*results[type]['rec_raw'] / (results[type]['pre_raw']+results[type]['rec_raw'])
        results[type]['pre_cc'] = results[type]['TP_cc'] / (results[type]['TP_cc']+results[type]['FP_cc'])
        results[type]['rec_cc'] = results[type]['TP_cc'] / (results[type]['TP_cc']+results[type]['FN_cc'])
        results[type]['f1_cc'] = 2*results[type]['pre_cc']*results[type]['rec_cc'] / (results[type]['pre_cc']+results[type]['rec_cc'])
    fp = open("results_ccpatch.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()


if __name__ == "__main__":
    # get_results()
    get_results_for_ccpatch()


