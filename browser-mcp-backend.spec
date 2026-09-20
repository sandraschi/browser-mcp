import sys, os
site_pkgs = os.path.abspath('.venv/Lib/site-packages')
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)
# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['run_server.py'], pathex=['src'],
    datas=[('src/browser_mcp', 'browser_mcp')],
    hiddenimports=['uvicorn.logging','uvicorn.loops','uvicorn.loops.asyncio','uvicorn.protocols','uvicorn.protocols.http','uvicorn.protocols.http.httptools_impl','uvicorn.protocols.http.h11_impl','uvicorn.lifespan','uvicorn.lifespan.on',
    "_strptime",
],
excludes=['tkinter','setuptools','pip','wheel','test','tests','unittest','_distutils_hack'],
    noarchive=True,
)
for _list in [a.datas, a.binaries, a.zipfiles, a.scripts]:
    _list[:] = [e for e in _list if not (isinstance(e, tuple) and '.dist-info' in str(e[0]))]
import PyInstaller.utils.hooks as h
for p in ['fastapi','uvicorn','pydantic','starlette','httpx','fastmcp','email-validator','mcp','opentelemetry-api']:
    try:
        for src_dir, dest_dir in h.copy_metadata(p):
            # copy_metadata() returns the dist-info DIRECTORY as one entry; a 'DATA'
            # TOC entry must be a single file, so walk the dir and add each file.
            for root, _dirs, files in os.walk(src_dir):
                for fn in files:
                    fsrc = os.path.join(root, fn)
                    fdest = os.path.join(dest_dir, os.path.relpath(fsrc, src_dir))
                    a.datas.append((fdest, fsrc, 'DATA'))
    except: pass
SKIP = ['torch','playwright','bitsandbytes','llvmlite','pyarrow','pymupdf','grpc','numba','Cython','google','azure','boto3','botocore','matplotlib','PIL','pandas','scipy','sklearn','onnxruntime']
a.binaries = [b for b in a.binaries if not any(s in b[0].lower() for s in SKIP)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='browser-mcp-backend', debug=False, strip=False, upx=False, upx_exclude=[],
     runtime_tmpdir=None, console=False)













