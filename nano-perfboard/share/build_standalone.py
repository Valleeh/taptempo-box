"""Build a single offline HTML file from the artifact viewer (libs + models inlined)."""
import json, re, pathlib
root = pathlib.Path(__file__).parent
src = (root.parent / "mech/viewer/index.html").read_text()
lib = {n: (root / "lib" / n).read_text() for n in ("three.min.js", "OrbitControls.js", "GLTFLoader.js")}
for n, code in lib.items():
    assert "</script" not in code.lower(), n
    src = re.sub(r'<script src="[^"]*/%s"></script>' % re.escape(n), lambda m: "<script>\n" + code + "\n</script>", src)
assert "cdn.jsdelivr" not in src
old = src[src.index("  function loadGLB("):src.index("  loadGLB(\"assembly")]
new = '''  function loadGLB(id, onLoad, onError) {
    try {
      const bin = atob(JSON.parse(document.getElementById(id).textContent).glb), buf = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
      loader.parse(buf.buffer, "", onLoad, onError);
    } catch (e) { onError(e); }
  }

'''
src = src.replace(old, new)
data = ""
for n in ("assembly.glb.json",):
    data += f'<script type="application/json" id="{n}">' + (root.parent / "mech/viewer" / n).read_text() + "</script>\n"
head = '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
src = src.replace("<style>", "<style>\nbody { margin: 0; }\n[hidden] { display: none !important; }", 1)
title_end = src.index("</style>") + len("</style>")
out = head + src[:title_end] + "\n</head>\n<body>\n" + data + src[title_end:] + "\n</body>\n</html>\n"
(root / "taptempo-3d.html").write_text(out)
print("ok", len(out) // 1024, "KB")
