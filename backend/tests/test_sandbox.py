import os, glob, sys
sys.path.insert(0, r"C:\Users\MSI\Desktop\MiniML_Lab")
from backend.sandbox import run_script

work = os.path.join(os.environ["TEMP"], "sbx_test")
data = r"C:\Users\MSI\Desktop\MiniML_Lab\storage\sessions\586392b45ca2.csv"

for f in glob.glob(work + r"\*"):
    if not f.endswith("exp.py"):
        os.remove(f)

p = run_script(work + r"\exp.py", work, data, timeout=120)
print("normal run rc:", p.returncode)
print("out:", p.stdout.strip())
print("model exists:", os.path.exists(os.path.join(work, "trained_model.pkl")))

with open(os.path.join(work, "net.py"), "w") as f:
    f.write(
        "import urllib.request\n"
        "try:\n"
        "    urllib.request.urlopen('https://example.com', timeout=5)\n"
        "    print('NET_OK')\n"
        "except Exception as e:\n"
        "    print('NET_BLOCKED:', type(e).__name__)\n"
    )
p2 = run_script(os.path.join(work, "net.py"), work, data, timeout=60)
print("net rc:", p2.returncode, "| out:", p2.stdout.strip()[:200])

with open(os.path.join(work, "env.py"), "w") as f:
    f.write("import os; print('env keys:', sorted(os.environ.keys()))")
p3 = run_script(os.path.join(work, "env.py"), work, data, timeout=60)
print(p3.stdout.strip()[:500])
