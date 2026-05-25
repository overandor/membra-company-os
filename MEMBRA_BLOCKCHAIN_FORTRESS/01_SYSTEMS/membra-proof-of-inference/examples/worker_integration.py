"""PoI integration for inference workers"""
import hashlib, json, time

def compute_merkle_root(tokens):
    if not tokens: return "0"*64
    hashes = [hashlib.sha256(str(t).encode()).hexdigest() for t in tokens]
    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            if i+1 < len(hashes):
                combined = hashes[i] + hashes[i+1]
                next_level.append(hashlib.sha256(combined.encode()).hexdigest())
            else:
                next_level.append(hashes[i])
        hashes = next_level
    return hashes[0]

def generate_poi_proof(prompt, tokens, model_cid, seed=42):
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    token_hash = compute_merkle_root(tokens)
    inference_id = hashlib.sha256(f"{prompt_hash}{token_hash}{seed}".encode()).hexdigest()
    
    return {
        "model_cid": model_cid,
        "prompt_hash": prompt_hash,
        "token_sequence_hash": token_hash,
        "token_count": len(tokens),
        "seed": seed,
        "timestamp": time.time(),
        "inference_id": inference_id,
    }

# Usage in llama.cpp/vLLM worker:
# proof = generate_poi_proof(prompt, tokens, model_cid)
# submit_to_poi_network(proof)
