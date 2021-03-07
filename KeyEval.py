import pandas as pd
from Datasets.utils import read_parquet, get_bib_info, clean
import json
import sys
sys.path.append("Models/")
from Models import *

import time

def mask(text1, text2):
    """
    a simple vectorization function
    """
    base = 0
    vectors = {}
    vector1, vector2 = [], []
    for phrase in text1:
        if phrase not in vectors:
            vectors[phrase] = base
            base += 1
        vector1.append(vectors[phrase])

    for phrase in text2:
        if phrase not in vectors:
            vectors[phrase] = base
            base += 1
        vector2.append(vectors[phrase])
    return  vector1, vector2


def get_recall(l1,l2):
    c = 0.0
    C = float(len(l1))
    for each in l2:
        if each in l1:
            c += 1.0
    return c/C


def get_precision(l1,l2):
    c = 0.0
    C = float(len(l2))
    for each in l2:
        if each in l1:
            c += 1.0
    return c/C


def get_f1(r,p):
    if r + p == 0:
        return 0.0
    return (2.0*p*r)/(p+r)


def get_Rprecision (phrase1, phrase2):
    """
    relaxed since it uses "in" instead of checkign the position of words
    """
    c = 0.0

    for w1 in phrase2.split():
        if w1 in phrase1:
            c += 1

    return c/max(len(phrase2.split()), len(phrase1.split()))


def get_all_Rprecision (gold_keywords, predicted_keywords):
    scores=[]
    for gphrase in gold_keywords:
        rscores=[]
        for pphrase in predicted_keywords:
            rscores.append(get_Rprecision(gphrase,pphrase))
        scores.append(max(rscores))

    return sum(scores) / len(scores)


def get_scores (gold_keywords, predicted_keywords):
    recall = get_recall(gold_keywords, predicted_keywords)
    precision = get_precision(gold_keywords, predicted_keywords)
    f1 = get_f1(recall, precision)
    Rprecision = get_all_Rprecision(gold_keywords, predicted_keywords)



    return f1, recall, precision, Rprecision


def get_all_scores (gold_keywords, predicted_keywords, text=None, adjust=False):
    """
    SemEval-2010 Task 5, micro averaged f1, recall, precision
    """
    metrics = get_scores(gold_keywords, predicted_keywords)

    adjusted_gold = []
    adjusted_metrics = []
    if adjust:
        if text:
            for each in gold_keywords:
                if each in text:
                    adjusted_gold.append(each)
            if len(adjusted_gold) < 1:
                adjusted_metrics = [0.0]*4
            else:
                adjusted_metrics = get_scores(adjusted_gold, predicted_keywords)

    return metrics, adjusted_metrics


def get_key_abs (filepath,year1=1900,year2=2020, bib_files=[], types=[], journals=[], count=None):
    """{'science-history-journals': 'Journals on the history, philosophy, and popularization of mathematics and
       science', 'compsci': 'Computer science journals and topics', 'acm': 'ACM Transactions', 'cryptography':
       'Cryptography', 'fonts': 'Fonts and typography', 'ieee': 'IEEE journals', 'computational': 'Computational/quantum
       chemistry/physics journals', 'numerical': 'Numerical analysis journals', 'probstat': 'Probability and statistics
       journals', 'siam': 'SIAM journals', 'math': 'Mathematics journals', 'mathbio': 'Mathematical and computational
       biology'} """
    jfile = open("Datasets/bib_info.json").read()
    tables, names = json.loads(jfile)
    new_tables = {}
    for table in tables:
        new_tables[table] = []
        for f in tables[table]:
            new_tables[table].append(list(f.keys())[0])

    df = read_parquet(filepath)


    if bib_files:
        df = df[df["bib_file"].isin(bib_files)]

    if types:
        types_list = []
        for type in types:
            types_list.extend(new_tables[type])
        df = df[df['bib_file'].isin(types_list)]

    if journals:
        df = df[df["journal"].isin(journals)]
    # year
    df["year"] = df["year"].astype("int")
    df = df[df["year"] >= year1]
    df = df[df["year"] <= year2]

    df = df[:count]

    keywords = df["keywords"].tolist()
    abstracts = df["abstract"].tolist()

    processed_keywords = []
    for i in range(len(keywords)):
        if ";" in keywords[i]:
            keyword = keywords[i].split(";")
        elif "," in keywords[i]:
            keyword = keywords[i].split(",")
        else:
            keyword = keywords[i].split(" to")

        new = []
        for key in keyword:
            if "---" in key:
                key = key.split("---")
                new.extend([clean(k) for k in key])
            else:
                new.append(clean(key))
        processed_keywords.append(new)
    return processed_keywords, abstracts


def eval_file (filepath, year1=1900, year2=2020, bib_files=[], types=[], journals=[], count=None):
    #add json input/ output
    #a way to test multiple models and features
    #output format

    keywords_gold, abstracts = get_key_abs(filepath, year1, year2, bib_files, types, journals, 10)

    model = keyBert()

    all_scores = []
    T0 = 0.0
    T1 = 0.0
    for i in range(len(keywords_gold)):
        t3 = time.time()
        predicted_keywords = model.get_keywords(abstracts[i])
        t4 = time.time()
        scores = get_all_scores(keywords_gold[i], predicted_keywords[0], abstracts[i])
        t5 = time.time()
        all_scores.append(scores[0])
        T0 += (t4 - t3)
        T1 += (t5 - t4)
    all_scores = pd.DataFrame(all_scores)
    #print(all_scores.shape)
    #print(all_scores.mean(axis=0))
    print(T0)
    print(T1)

def run_evaluation ()
t1 = time.time()
eval_file("C:/dallal/MScTartu/Courses/spring21/Thesis/dataset/TUG bibliography archive/bib_tug_dataset_full.parquet")
t2 = time.time()


print(t2-t1)
