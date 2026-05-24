import os, json, random, re

random.seed(42)
dataset = []

# --- 1. ChatGPT conversations ---
chat_dir = '/Users/alep/Downloads/training_data/chatgpt_exports/chatgpt'
for fname in os.listdir(chat_dir):
    if not fname.endswith('.md'):
        continue
    path = os.path.join(chat_dir, fname)
    try:
        with open(path, 'r', errors='ignore') as f:
            text = f.read()
    except Exception:
        continue
    if len(text) < 200:
        continue
    text = re.sub(r'!\[.*?\]\(https://images\.openai\.com/.*?\)', '', text)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[([^\]]+)\]\(.*?\)', r'\1', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    dataset.append({'text': text})

print(f'ChatGPT files: {len(dataset)}')

# --- 2. cartman.csv ---
with open('/Users/alep/Downloads/cartman.csv', 'r') as f:
    lines = f.readlines()
chunk = []
for line in lines:
    chunk.append(line.strip())
    if len('\n'.join(chunk)) > 1000:
        dataset.append({'text': '\n'.join(chunk)})
        chunk = []
if chunk:
    dataset.append({'text': '\n'.join(chunk)})

print(f'After cartman: {len(dataset)}')

# --- 3. Python code corpus ---
code_files = []
for root, dirs, files in os.walk('/Users/alep/Downloads'):
    dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'env', 'training_data', 'go', 'Library'}]
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            try:
                s = os.path.getsize(p)
                if 500 < s < 40000:
                    code_files.append(p)
            except Exception:
                pass

random.shuffle(code_files)
selected = code_files[:50]
for p in selected:
    try:
        with open(p, 'r', errors='ignore') as f:
            content = f.read()
        if len(content) > 500:
            dataset.append({'text': f'# File: {os.path.basename(p)}\n{content}'})
    except Exception:
        pass

print(f'Total after code: {len(dataset)}')

random.shuffle(dataset)
split = int(len(dataset) * 0.9)
train = dataset[:split]
valid = dataset[split:]

with open('/Users/alep/Downloads/training_data/train.jsonl', 'w') as f:
    for item in train:
        f.write(json.dumps(item) + '\n')
with open('/Users/alep/Downloads/training_data/valid.jsonl', 'w') as f:
    for item in valid:
        f.write(json.dumps(item) + '\n')

total_chars = sum(len(d['text']) for d in dataset)
print(f'Train: {len(train)}, Valid: {len(valid)}, Total chars: {total_chars:,}')
