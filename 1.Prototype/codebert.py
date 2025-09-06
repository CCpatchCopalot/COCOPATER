from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from scipy.spatial.distance import cosine

def codebert_sim(core_func_list, pre_function_dict, post_function_dict):
    # Load CodeBERT model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
    model = AutoModel.from_pretrained("microsoft/codebert-base")

    def get_embedding(text):
        # Tokenize and get model output
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
        # Use [CLS] token embedding as sentence embedding
        return outputs.last_hidden_state[:, 0, :].numpy()

    # Get embeddings for core functions
    core_embeddings = [get_embedding(func) for func in core_func_list]
    
    # fetch the function in pre and post, if any function in pre and post is similar to the core function, then add it to the core function list
    for func in pre_function_dict:
        for core_embedding in core_embeddings:
            similarity = 1 - cosine(get_embedding(func).flatten(), core_embedding.flatten())
            if similarity > 0.7:
                core_func_list.append(func)
    for func in post_function_dict:
        for core_embedding in core_embeddings:
            similarity = 1 - cosine(get_embedding(func).flatten(), core_embedding.flatten())
            if similarity > 0.7:
                core_func_list.append(func)
    return core_func_list

