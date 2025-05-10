from collections import Counter
from typing import List

import torch
import torch.nn as nn
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import DataStructs

from diffms.utils import is_valid, canonical_mol_from_inchi

class K_ACC:
    def __init__(self, k: int):
        self.correct = 0
        self.total = 0

        self.k = k

    def update(self, generated_inchis: list[str], true_inchi: str):
        if true_inchi in generated_inchis[:self.k]:
            self.correct += 1
        self.total += 1

    def compute(self):
        if self.total == 0:
            return 0
        return self.correct / self.total
    
    def reset(self):
        self.correct = 0
        self.total = 0
        
class K_ACC_Collection:
    def __init__(self, k_list: List[int]):
        self.k_list = k_list

        self.metrics = {}
        for k in self.k_list:
            self.metrics[f"acc_at_{k}"] = K_ACC(k)

    def reset(self):
        for metric in self.metrics.values():
            metric.reset()

    def update(self, generated_mols: list[str], true_mol: str):
        # filter mols and select unique
        inchis = [Chem.MolToInchi(mol) for mol in generated_mols if is_valid(mol)]

        inchi_counter = Counter(inchis)
        inchis = [item for item, count in inchi_counter.most_common()]

        for metric in self.metrics.values():
            metric.update(inchis, Chem.MolToInchi(true_mol))

    def compute(self):
        res = {}
        for k, metric in self.metrics.items():
            res[k] = metric.compute()
        return res

class K_TanimotoSimilarity:
    def __init__(self, k: int):
        self.similarity = 0
        self.total = 0

        self.k = k

    def update(self, generated_mols, true_mol):
        true_fp = AllChem.GetMorganFingerprintAsBitVect(true_mol, 2, nBits=2048)

        max_sim = 0
        for mol in generated_mols[:self.k]:
            try:
                gen_fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
                max_sim = max(max_sim, DataStructs.TanimotoSimilarity(gen_fp, true_fp))
            except Exception as e:
                pass
            
        self.similarity += max_sim
        self.total += 1
        
    def compute(self):
        return self.similarity / self.total

    def reset(self):
        self.similarity = 0
        self.total = 0

class K_CosineSimilarity:
    def __init__(self, k: int):
        self.similarity = 0
        self.total = 0

        self.k = k

    def update(self, generated_mols, true_mol):
        true_fp = AllChem.GetMorganFingerprintAsBitVect(true_mol, 2, nBits=2048)

        max_sim = 0
        for mol in generated_mols[:self.k]:
            try:
                gen_fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
                max_sim = max(max_sim, DataStructs.CosineSimilarity(gen_fp, true_fp))
            except Exception as e:
                pass
            
        self.similarity += max_sim
        self.total += 1
        
    def compute(self):
        return self.similarity / self.total
    
    def reset(self):
        self.similarity = 0
        self.total = 0
    
class K_SimilarityCollection:
    def __init__(self, k_list: List[int]):

        self.k_list = k_list
        self.metrics = {}
        for k in self.k_list:
            self.metrics[f"tanimoto_at_{k}"] = K_TanimotoSimilarity(k)
            self.metrics[f"cosine_at_{k}"] = K_CosineSimilarity(k)

    def reset(self):
        for metric in self.metrics.values():
            metric.reset()

    def update(self, generated_mols, true_mol):
        # filter mols and select unique
        inchis = [Chem.MolToInchi(mol) for mol in generated_mols if is_valid(mol)]

        inchi_counter = Counter(inchis)
        inchis = [item for item, count in inchi_counter.most_common()]

        processed_mols = [canonical_mol_from_inchi(inchi) for inchi in inchis]

        for metric in self.metrics.values():
            metric.update(processed_mols, true_mol)

    def compute(self):
        res = {}
        for k, metric in self.metrics.items():
            res[k] = metric.compute()
        return res
    
class Validity:
    def __init__(self):
        self.valid = 0
        self.total = 0

    def update(self, generated_mols):
        for mol in generated_mols:
            if is_valid(mol):
                self.valid += 1
            self.total += 1

    def compute(self):
        return self.valid / self.total
    
    def reset(self):
        self.valid = 0
        self.total = 0