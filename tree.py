import os
def print_tree(startpath, max_depth=3):
    start_level = startpath.count(os.sep)
    for root, dirs, files in os.walk(startpath):
        level = root.count(os.sep) - start_level
        if level > max_depth:
            dirs.clear()
            continue
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        if level < max_depth:
            for f in files:
                print(f"{subindent}{f}")

print_tree(r'c:\Users\Administrator\Desktop\GENESIS_CLOUD')
