import json
# The file is UTF-16 LE encoded due to PowerShell output redirection
with open('.graphify_detect.json', encoding='utf-16') as f:
    data = json.load(f)
print(f"Total files: {data['total_files']}")
print(f"Total words: {data['total_words']}")
print(f"Code files: {len(data['files']['code'])}")
print(f"Docs: {len(data['files']['document'])}")
print(f"Images: {len(data['files']['image'])}")
if data.get('warning'):
    print(f"\n⚠ Warning: {data['warning']}")
