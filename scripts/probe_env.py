
import subprocess, sys, os
PY = sys.executable
BASE = {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"], "PREFIX": os.environ["PREFIX"]}
def ok(env):
    try:
        r = subprocess.run([PY, "-c", "print(1)"], env=env, capture_output=True)
        return r.returncode == 0
    except Exception:
        return False
print("base only ->", ok(BASE))
keys = sorted(os.environ)
# cari kunci yang membuatkan exec berjaya bila ditambah pada BASE
critical = []
for k in keys:
    if ok({**BASE, k: os.environ[k]}):
        critical.append(k)
print("kunci kritikal (satu-satunya tambahan yang cukup):", critical)
# juga: adakah env penuh berjaya?
print("env penuh ->", ok(dict(os.environ)))
