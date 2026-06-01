import json
from pathlib import Path

# Load uncached files
uncached = Path('.graphify_uncached.txt').read_text(encoding='utf-8').strip().split('\n')

# Filter to non-code files only (docs + images)
# Code extensions
code_exts = {'.py', '.ts', '.js', '.go', '.rs', '.java', '.cpp', '.c', '.rb', '.swift', '.kt', '.cs', '.scala', '.php', '.cc', '.cxx', '.hpp', '.h', '.kts', '.lua', '.gradle', '.gradle.kts', '.sh', '.bat', '.ps1', '.txt'}

non_code = [f for f in uncached if not any(Path(f).name.endswith(ext) for ext in code_exts) and Path(f).suffix.lower() not in code_exts]

print(f'Files needing semantic extraction: {len(non_code)}')

# Split into chunks of 20-25
chunk_size = 22
chunks = [non_code[i:i+chunk_size] for i in range(0, len(non_code), chunk_size)]
print(f'Chunks: {len(chunks)}')

for i, chunk in enumerate(chunks, 1):
    print(f'Chunk {i}: {len(chunk)} files')

# Save chunk manifest
with open('.graphify_chunks_manifest.json', 'w', encoding='utf-8') as f:
    json.dump({'total_chunks': len(chunks), 'total_files': len(non_code), 'chunks': [{'num': i, 'count': len(c)} for i, c in enumerate(chunks, 1)]}, f, indent=2, ensure_ascii=False)

# Save each chunk to a file for agent dispatch
for i, chunk in enumerate(chunks, 1):
    with open(f'.graphify_chunk_{i}.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(chunk))
    print(f'Saved .graphify_chunk_{i}.txt')
