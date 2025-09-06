import pandas as pd
import json
import sys
import os
from tqdm import tqdm

def get_ccpatch_metrics():
    file_path = 'results_tgpatch.xlsx'
    df = pd.read_excel(file_path)
    
    df_dict_cc = df.to_dict(orient='records')  
    incorrect_cves = ["CVE-2018-13867", "CVE-2018-17237", "CVE-2019-20171", "CVE-2020-15190", "CVE-2020-19481", "CVE-2020-21830", "CVE-2020-21841", "CVE-2020-23321", "CVE-2021-39530", "CVE-2022-31620", "CVE-2022-3598", "CVE-2022-47087", "CVE-2022-47088", "CVE-2022-47660", "CVE-2023-0796", "CVE-2023-2610", "CVE-2023-36274", "CVE-2023-37836", "gpac-1421"]
    cves = ["CVE-2023-0797", "CVE-2023-36271", "CVE-2023-37837"]

    tp_v = 0
    fp_v = 0
    fn_v = 0

    tp_f = 0
    fp_f = 0
    fn_f = 0
    results = {}
    tp_data = []

    for data in df_dict_cc:
        if data['CVE'] in cves:
            # print(111111111111)
            if "cves" not in results:
                results["cves"] = {}
            if data['TP/FP'] == "TP":
                try:
                    results["cves"]['tg_TP'] += 1
                except:
                    results["cves"]['tg_TP'] = 1
            if "FIRE" in data['TOOL']:
                if "FIRE" not in results["cves"]:
                    results["cves"]["FIRE"] = {}
                    results["cves"]["FIRE"]["tg_TP"] = 0
                    results["cves"]["FIRE"]["tg_FP"] = 0
                if data['TP/FP'] == "TP":
                    try:
                        results["cves"]["FIRE"]["tg_TP"] += 1
                    except:
                        results["cves"]["FIRE"]["tg_TP"] = 1
                if data['TP/FP'] == "FP":
                    try:
                        results["cves"]["FIRE"]["tg_FP"] += 1
                    except:
                        results["cves"]["FIRE"]["tg_FP"] = 1
                    
            if "VUDDY" in data['TOOL']:
                if "VUDDY" not in results["cves"]:
                    results["cves"]["VUDDY"] = {}
                    results["cves"]["VUDDY"]["tg_TP"] = 0
                    results["cves"]["VUDDY"]["tg_FP"] = 0
                if data['TP/FP'] == "TP":
                    try:
                        results["cves"]["VUDDY"]["tg_TP"] += 1
                    except:
                        results["cves"]["VUDDY"]["tg_TP"] = 1
                if data['TP/FP'] == "FP":
                    try:
                        results["cves"]["VUDDY"]["tg_FP"] += 1
                    except:
                        results["cves"]["VUDDY"]["tg_FP"] = 1

        if "all" not in results:
            results["all"] = {}
        
        if data['TP/FP'] == "TP":
            try:
                results["all"]['tg_TP'] += 1
            except:
                results["all"]['tg_TP'] = 1
        
        if "FIRE" in data['TOOL']:
            if "FIRE" not in results["all"]:
                results["all"]["FIRE"] = {}
                results["all"]["FIRE"]["tg_TP"] = 0
                results["all"]["FIRE"]["tg_FP"] = 0
                
            if data['TP/FP'] == "TP":
                try:
                    results["all"]["FIRE"]["tg_TP"] += 1
                except:
                    results["all"]["FIRE"]["tg_TP"] = 1
                    
            if data['TP/FP'] == "FP":
                try:
                    results["all"]["FIRE"]["tg_FP"] += 1
                except:
                    results["all"]["FIRE"]["tg_FP"] = 1
                    
        if "VUDDY" in data['TOOL']:
            if "VUDDY" not in results["all"]:
                results["all"]["VUDDY"] = {}
                results["all"]["VUDDY"]["tg_TP"] = 0
                results["all"]["VUDDY"]["tg_FP"] = 0
                
            if data['TP/FP'] == "TP":
                try:
                    results["all"]["VUDDY"]["tg_TP"] += 1
                except:
                    results["all"]["VUDDY"]["tg_TP"] = 1
                    
            if data['TP/FP'] == "FP":
                try:
                    results["all"]["VUDDY"]["tg_FP"] += 1
                except:
                    results["all"]["VUDDY"]["tg_FP"] = 1

        if data['CVE'] in incorrect_cves:
            print(data['CVE'])
            if "incorrect" not in results:
                results["incorrect"] = {}            
            if data['TP/FP'] == "TP":
                try:
                    results["incorrect"]['tg_TP'] += 1
                except:
                    results["incorrect"]['tg_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results["incorrect"]:
                    results["incorrect"]['FIRE'] = {}
                    results["incorrect"]['FIRE']['tg_TP'] = 0
                    results["incorrect"]['FIRE']['tg_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["incorrect"]['FIRE']['tg_TP'] += 1
                    except:
                        results["incorrect"]['FIRE']['tg_TP'] = 1
                else:
                    try:
                        results["incorrect"]['FIRE']['tg_FP'] += 1
                    except:
                        results["incorrect"]['FIRE']['tg_FP'] = 1
            
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results["incorrect"]:
                    results["incorrect"]['VUDDY'] = {}
                    results["incorrect"]['VUDDY']['tg_TP'] = 0
                    results["incorrect"]['VUDDY']['tg_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["incorrect"]['VUDDY']['tg_TP'] += 1
                    except:
                        results["incorrect"]['VUDDY']['tg_TP'] = 1
                else:
                    try:
                        results["incorrect"]['VUDDY']['tg_FP'] += 1
                    except:
                        results["incorrect"]['VUDDY']['tg_FP'] = 1
        else:
            if "correct" not in results:
                results["correct"] = {}
            if data['TP/FP'] == "TP":
                try:
                    results["correct"]['tg_TP'] += 1
                except:
                    results["correct"]['tg_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results["correct"]:
                    results["correct"]['FIRE'] = {}
                    results["correct"]['FIRE']['tg_TP'] = 0
                    results["correct"]['FIRE']['tg_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["correct"]['FIRE']['tg_TP'] += 1
                    except:
                        results["correct"]['FIRE']['tg_TP'] = 1
                else:
                    try:
                        results["correct"]['FIRE']['tg_FP'] += 1
                    except:
                        results["correct"]['FIRE']['tg_FP'] = 1
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results["correct"]:
                    results["correct"]['VUDDY'] = {}
                    results["correct"]['VUDDY']['tg_TP'] = 0
                    results["correct"]['VUDDY']['tg_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["correct"]['VUDDY']['tg_TP'] += 1
                    except:
                        results["correct"]['VUDDY']['tg_TP'] = 1
                else:
                    try:
                        results["correct"]['VUDDY']['tg_FP'] += 1
                    except:
                        results["correct"]['VUDDY']['tg_FP'] = 1

    file_path = 'results_ccpatch.xlsx'
    df = pd.read_excel(file_path)
    
    df_dict_cc = df.to_dict(orient='records') 

    for data in df_dict_cc:
        if data['CVE'] in cves:
            print(1111111111)
            if "cves" not in results:
                results["cves"] = {}
            if data['TP/FP'] == "TP":
                try:
                    results["cves"]['cc_TP'] += 1
                except:
                    results["cves"]['cc_TP'] = 1
            if "FIRE" in data['TOOL']:
                if "FIRE" not in results["cves"]:
                    results["cves"]["FIRE"] = {}
                    results["cves"]["FIRE"]["cc_TP"] = 0
                    results["cves"]["FIRE"]["cc_FP"] = 0
                    
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["cves"]["FIRE"]["cc_TP"] += 1
                    except:
                        results["cves"]["FIRE"]["cc_TP"] = 1
                        
                if data['TP/FP'] == "FP":
                    try:
                        results["cves"]["FIRE"]["cc_FP"] += 1
                    except:
                        results["cves"]["FIRE"]["cc_FP"] = 1
                        
            if "VUDDY" in data['TOOL']:
                if "VUDDY" not in results["cves"]:
                    results["cves"]["VUDDY"] = {}
                    results["cves"]["VUDDY"]["cc_TP"] = 0
                    results["cves"]["VUDDY"]["cc_FP"] = 0
                    
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["cves"]["VUDDY"]["cc_TP"] += 1
                    except:
                        results["cves"]["VUDDY"]["cc_TP"] = 1
                        
                        
                if data['TP/FP'] == "FP":
                    try:
                        results["cves"]["VUDDY"]["cc_FP"] += 1
                    except:
                        results["cves"]["VUDDY"]["cc_FP"] = 1
                        
                        
        if "all" not in results:
            results["all"] = {}
        if data['TP/FP'] == "TP":
            try:
                results["all"]['cc_TP'] += 1
            except:
                results["all"]['cc_TP'] = 1
        if "FIRE" in data['TOOL']:
            if "FIRE" not in results["all"]:
                results["all"]["FIRE"] = {}
                results["all"]["FIRE"]["cc_TP"] = 0
                results["all"]["FIRE"]["cc_FP"] = 0
                
            if data['TP/FP'] == "TP":
                results
                try:
                    results["all"]["FIRE"]["cc_TP"] += 1
                except:
                    results["all"]["FIRE"]["cc_TP"] = 1
                    
            if data['TP/FP'] == "FP":
                try:
                    results["all"]["FIRE"]["cc_FP"] += 1
                except:
                    results["all"]["FIRE"]["cc_FP"] = 1
        if "VUDDY" in data['TOOL']:
            if "VUDDY" not in results["all"]:
                results["all"]["VUDDY"] = {}
                results["all"]["VUDDY"]["cc_TP"] = 0
                results["all"]["VUDDY"]["cc_FP"] = 0
                
                
            if data['TP/FP'] == "TP":
                try:
                    results["all"]["VUDDY"]["cc_TP"] += 1
                except:
                    results["all"]["VUDDY"]["cc_TP"] = 1
                    
            if data['TP/FP'] == "FP":
                try:
                    results["all"]["VUDDY"]["cc_FP"] += 1
                except:
                    results["all"]["VUDDY"]["cc_FP"] = 1
                    
        if data['CVE'] in incorrect_cves:
            if "incorrect" not in results:
                results["incorrect"] = {}            
            if data['TP/FP'] == "TP":
                try:
                    results["incorrect"]['cc_TP'] += 1
                except:
                    results["incorrect"]['cc_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results["incorrect"]:
                    results["incorrect"]['FIRE'] = {}
                    results["incorrect"]['FIRE']['cc_TP'] = 0
                    results["incorrect"]['FIRE']['cc_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["incorrect"]['FIRE']['cc_TP'] += 1
                    except:
                        results["incorrect"]['FIRE']['cc_TP'] = 1
                else:    
                    try:
                        results["incorrect"]['FIRE']['cc_FP'] += 1
                    except:
                        results["incorrect"]['FIRE']['cc_FP'] = 1
            
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results["incorrect"]:
                    results["incorrect"]['VUDDY'] = {}
                    results["incorrect"]['VUDDY']['cc_TP'] = 0
                    results["incorrect"]['VUDDY']['cc_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["incorrect"]['VUDDY']['cc_TP'] += 1
                    except:
                        results["incorrect"]['VUDDY']['cc_TP'] = 1
                else:
                    try:
                        results["incorrect"]['VUDDY']['cc_FP'] += 1
                    except:
                        results["incorrect"]['VUDDY']['cc_FP'] = 1
        else:
            if "correct" not in results:
                results["correct"] = {}
            if data['TP/FP'] == "TP":
                try:
                    results["correct"]['cc_TP'] += 1
                except:
                    results["correct"]['cc_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results["correct"]:
                    results["correct"]['FIRE'] = {}
                    results["correct"]['FIRE']['cc_TP'] = 0
                    results["correct"]['FIRE']['cc_FP'] = 0

                if data['TP/FP'] == "TP":
                    try:
                        results["correct"]['FIRE']['cc_TP'] += 1
                    except:
                        results["correct"]['FIRE']['cc_TP'] = 1
                else:
                    try:
                        results["correct"]['FIRE']['cc_FP'] += 1
                    except:
                        results["correct"]['FIRE']['cc_FP'] = 1
            
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results["correct"]:
                    results["correct"]['VUDDY'] = {}
                    results["correct"]['VUDDY']['cc_TP'] = 0
                    results["correct"]['VUDDY']['cc_FP'] = 0
                    
                if data['TP/FP'] == "TP":
                    try:
                        results["correct"]['VUDDY']['cc_TP'] += 1
                    except:
                        results["correct"]['VUDDY']['cc_TP'] = 1
                else:
                    try:
                        results["correct"]['VUDDY']['cc_FP'] += 1
                    except:
                        results["correct"]['VUDDY']['cc_FP'] = 1

    for type in results:
        for tool in results[type]:
            if tool == "cc_TP" or tool == "tg_TP":
                continue
            print(type, tool)
            print(results[type][tool])
            if "tg_TP" not in results[type][tool]:
                results[type][tool]['tg_TP'] = 0
            if "tg_FP" not in results[type][tool]:
                results[type][tool]['tg_FP'] = 0
            if "cc_TP" not in results[type][tool]:
                results[type][tool]['cc_TP'] = 0
            if "cc_FP" not in results[type][tool]:
                results[type][tool]['cc_FP'] = 0
                
            results[type][tool]['tg_pre'] = results[type][tool]['tg_TP'] / (results[type][tool]['tg_TP']+results[type][tool]['tg_FP'])
            results[type][tool]['tg_rec'] = results[type][tool]['tg_TP'] / results[type]['tg_TP']
            results[type][tool]['tg_f1'] = 2*results[type][tool]['tg_pre']*results[type][tool]['tg_rec'] / (results[type][tool]['tg_rec']+results[type][tool]['tg_pre'])
            results[type][tool]['cc_pre'] = results[type][tool]['cc_TP'] / (results[type][tool]['cc_TP']+results[type][tool]['cc_FP'])
            results[type][tool]['cc_rec'] = results[type][tool]['cc_TP'] / results[type]['tg_TP']
            results[type][tool]['cc_f1'] = 2*results[type][tool]['cc_pre']*results[type][tool]['cc_rec'] / (results[type][tool]['cc_rec']+results[type][tool]['cc_pre'])

    
    fp = open("results.json","w")
    json.dump(results, fp, indent=4)
    fp.close()

if __name__ == "__main__":
    get_ccpatch_metrics()
        