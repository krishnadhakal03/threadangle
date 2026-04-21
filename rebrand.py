import os

replacements = {
    "Threadangle": "Threadangle",
    "threadangle": "threadangle",
    "THREADANGLE": "THREADANGLE",
    "threadangle": "threadangle",
    "threadangle": "threadangle"
}

modified_files = []
total_replacements = 0

for root, dirs, files in os.walk("f:/Threadforge"):
    if any(ignore in root for ignore in ["node_modules", "venv", ".git", "__pycache__", ".gemini"]):
        continue
    
    for file in files:
        if file.endswith(('.py', '.json', '.jsx', '.html', '.md', '.txt', '.js', '.css', '.example', '.sh', '.conf')):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                found_count = 0
                for old in replacements.keys():
                    found_count += content.count(old)
                    content = content.replace(old, replacements[old])
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    modified_files.append((filepath, found_count))
                    total_replacements += found_count
                    
            except UnicodeDecodeError:
                pass

print(f"Total files changed: {len(modified_files)}")
print(f"Total replacements made: {total_replacements}")
print("List of modified files:")
for f, count in modified_files:
    print(f"  {f}: {count} replacements")
