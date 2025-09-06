import pandas as pd
import json

df = pd.read_excel("./patch_transfer.xlsx")
sheet_data = df.to_dict(orient='records')

results = {}
results['all'] = {}
results['all']['git'] = {}
results['all']['tsbport'] = {}
results['all']['count'] = 0
results['correct'] = {}
results['correct']['git'] = {}
results['correct']['tsbport'] = {}
results['correct']['count'] = 0
results['incorrect'] = {}
results['incorrect']['git'] = {}
results['incorrect']['tsbport'] = {}
results['incorrect']['count'] = 0


cnt = 0
incorrect_cves = ["CVE-2018-13867", "CVE-2018-17237", "CVE-2019-20171", "CVE-2020-15190", "CVE-2020-19481", "CVE-2020-21830", "CVE-2020-21841", "CVE-2020-23321", "CVE-2021-39530", "CVE-2022-31620", "CVE-2022-3598", "CVE-2022-47087", "CVE-2022-47088", "CVE-2022-47660", "CVE-2023-0796", "CVE-2023-2610", "CVE-2023-36274", "CVE-2023-37836", "gpac-1421"]
cves = ["CVE-2023-0797", "CVE-2023-36271", "CVE-2023-37837"]

for data in sheet_data:
    if str(data['CVE_ID']) =="nan":
        continue
    if str(data['cherry pick origin compile'] )== "nan":
        continue
    try:
        results['all']['git']['cr_raw'] +=  data['cherry pick origin compile']
    except:
        results['all']['git']['cr_raw'] =  data['cherry pick origin compile']

    try:
        results['all']['git']['fr_raw'] +=  data['cherry pick origin fix']
    except:
        results['all']['git']['fr_raw'] =  data['cherry pick origin fix']

    try:
        results['all']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
    except:
        results['all']['git']['cr_cc'] =  data['cherry pick ccpatch compile']

    try:
        results['all']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
    except:            
        results['all']['git']['fr_cc'] =  data['cherry pick ccpatch fix']

    try:
        results['all']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
    except:
        results['all']['tsbport']['cr_raw'] =  data['tsbport origin compile']

    try:
        results['all']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
    except:
        results['all']['tsbport']['fr_raw'] =  data['tsbport origin fix']
    results['all']['count'] += 1


    cnt += 1
    try:
        results['all']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
    except:
        results['all']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']

    try:
        results['all']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
    except:
        results['all']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']

    if data['CVE_ID'] in cves:
        print(data['CVE_ID'])
        print(data['cherry pick origin compile'], data['cherry pick origin fix'], data['cherry pick ccpatch compile'], data['cherry pick ccpatch fix'], data['tsbport origin compile'], data['tsbport origin fix'], data['tsbport ccpatch compile'], data['tsbport ccpatch fix'])
            

    if data['CVE_ID'] in incorrect_cves:
        results['incorrect']['count'] += 1
        try:
            results['incorrect']['git']['cr_raw'] +=  data['cherry pick origin compile']
        except:
            results['incorrect']['git']['cr_raw'] =  data['cherry pick origin compile']
        try:
            results['incorrect']['git']['fr_raw'] +=  data['cherry pick origin fix']
        except:
            results['incorrect']['git']['fr_raw'] =  data['cherry pick origin fix']
        try:
            results['incorrect']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
        except:
            results['incorrect']['git']['cr_cc'] =  data['cherry pick ccpatch compile']
        try:
            results['incorrect']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
        except:
            results['incorrect']['git']['fr_cc'] =  data['cherry pick ccpatch fix']
        try:
            results['incorrect']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
        except:
            results['incorrect']['tsbport']['cr_raw'] =  data['tsbport origin compile']
        try:
            results['incorrect']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
        except:
            results['incorrect']['tsbport']['fr_raw'] =  data['tsbport origin fix']
        try:
            results['incorrect']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
        except:
            results['incorrect']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']
        try:
            results['incorrect']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
        except:
            results['incorrect']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']
    else:
        results['correct']['count'] += 1
        try:
            results['correct']['git']['cr_raw'] +=  data['cherry pick origin compile']
        except:
            results['correct']['git']['cr_raw'] =  data['cherry pick origin compile']
        try:
            results['correct']['git']['fr_raw'] +=  data['cherry pick origin fix']
        except:
            results['correct']['git']['fr_raw'] =  data['cherry pick origin fix']
        try:
            results['correct']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
        except:
            results['correct']['git']['cr_cc'] =  data['cherry pick ccpatch compile']
        try:
            results['correct']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
        except:
            results['correct']['git']['fr_cc'] =  data['cherry pick ccpatch fix']
        try:
            results['correct']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
        except:
            results['correct']['tsbport']['cr_raw'] =  data['tsbport origin compile']
        try:
            results['correct']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
        except:
            results['correct']['tsbport']['fr_raw'] =  data['tsbport origin fix']
        try:
            results['correct']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
        except:
            results['correct']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']
        try:
            results['correct']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
        except:
            results['correct']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']

for typ in results:
    for tool in results[typ]:
        if tool == "count":
            continue
        print(typ, tool, results[typ][tool]["fr_raw"], results[typ][tool]["fr_cc"], results[typ][tool]["cr_raw"], results[typ][tool]["cr_cc"])
        results[typ][tool]["cr_raw"] = round(results[typ][tool]["cr_raw"] / results[typ]['count'], 2)
        results[typ][tool]["cr_cc"] = round(results[typ][tool]["cr_cc"] / results[typ]['count'], 2)
        results[typ][tool]["fr_raw"] = round(results[typ][tool]["fr_raw"] / results[typ]['count'], 2)
        results[typ][tool]["fr_cc"] = round(results[typ][tool]["fr_cc"] / results[typ]['count'], 2)
        if results[typ][tool]["fr_raw"] == 0:
            results[typ][tool]['fr_ratio'] = "nan"
        else:            
            results[typ][tool]['fr_ratio'] = round((results[typ][tool]["fr_cc"] - results[typ][tool]["fr_raw"]) / results[typ][tool]["fr_raw"], 2)
        if results[typ][tool]["cr_raw"] == 0:
            results[typ][tool]['cr_ratio'] = "nan"
        else:
            results[typ][tool]['cr_ratio'] = round((results[typ][tool]["cr_cc"] - results[typ][tool]["cr_raw"]) / results[typ][tool]["cr_raw"], 2)

fp = open("results.json", "w")
json.dump(results, fp, indent=4)
fp.close()