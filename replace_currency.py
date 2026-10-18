"""Replace AED with ETB across all HTML templates."""
import os

base = r'c:\Users\mezig\Videos\ecommer\qenagebeya\templates'
count = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            new = content.replace('AED ', 'ETB ')
            if new != content:
                with open(path, 'w', encoding='utf-8') as fh:
                    fh.write(new)
                print('  Updated:', os.path.relpath(path, base))
                count += 1
print(f'Done. {count} file(s) updated.')
