import json
from pathlib import Path

# Load each chunk file and format as FILE_LIST
for i in range(1, 7):
    chunk_file = Path(f'.graphify_chunk_{i}.txt')
    files = chunk_file.read_text(encoding='utf-8').strip().split('\n')
    
    # Create a formatted list for the prompt
    file_list = '\n'.join(f'- {f}' for f in files)
    
    # Save as a separate file for reference
    Path(f'.graphify_chunk_{i}_list.txt').write_text(file_list, encoding='utf-8')
    
    print(f'Chunk {i}: {len(files)} files')

print('\nReady to dispatch 6 agents')
