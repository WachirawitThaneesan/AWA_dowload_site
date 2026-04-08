import os
import re

toc_path = r'build\AI_feedback\Analysis-00.toc'
if os.path.exists(toc_path):
    with open(toc_path, 'r', encoding='utf-8', errors='ignore') as f:
        data = f.read()
    
    # Simple regex to find paths like 'C:\...\something.dll'
    # Analysis-00.toc usually contains many ('name', 'path', 'TYPE') tuples
    matches = re.findall(r"'([A-Za-z]:\\[^']+\.(?:dll|pyd|so|exe))'", data)
    unique_paths = list(set(matches))
    
    file_sizes = []
    for p in unique_paths:
        if os.path.exists(p):
            file_sizes.append((p, os.path.getsize(p)))
        else:
            # Maybe relative path?
            if os.path.exists(os.path.join('build', 'AI_feedback', p)):
                file_sizes.append((p, os.path.getsize(os.path.join('build', 'AI_feedback', p))))
    
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print("Total binaries found:", len(file_sizes))
    print("Top 50 Largest Binary Files in Bundle:")
    for p, s in file_sizes[:50]:
        print(f"{s/(1024*1024):.2f} MB - {p}")
else:
    print(f"File not found: {toc_path}")
