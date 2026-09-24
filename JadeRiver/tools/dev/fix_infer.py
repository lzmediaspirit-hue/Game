"""Dev helper: run Godot's parser and replace ':=' with '=' on lines where GDScript
cannot infer a static type from a Variant expression. Loops until clean."""
import re, subprocess, sys, os
GODOT = os.environ.get("GODOT", "godot")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
pat = re.compile(r'SCRIPT ERROR: Parse Error: (Cannot infer the type of "(\w+)"|The variable type is being inferred from a Variant value)[^\n]*\n\s+at: GDScript::reload \(res://([^:]+):(\d+)\)')
for it in range(40):
    out = subprocess.run([GODOT, "--headless", "--path", ROOT, "--quit"], capture_output=True, text=True, timeout=300).stdout + ""
    out += subprocess.run([GODOT, "--headless", "--path", ROOT, "--quit"], capture_output=True, text=True, timeout=300).stderr
    fixes = pat.findall(out)
    if not fixes:
        errs = [l for l in out.splitlines() if "ERROR" in l or "at: " in l]
        print("\n".join(errs[:60]))
        break
    done = set()
    for _, name, path, line in fixes:
        key = (path, int(line))
        if key in done: continue
        done.add(key)
        fp = os.path.join(ROOT, path)
        lines = open(fp).read().split("\n")
        i = int(line) - 1
        if ":=" in lines[i]:
            lines[i] = lines[i].replace(":=", "=", 1)
            open(fp, "w").write("\n".join(lines))
    print("iteration", it, "fixed", len(done))
