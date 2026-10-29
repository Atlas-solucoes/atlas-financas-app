"""Conferência HTTP somente leitura; não acessa contas nem escreve dados no Atlas."""
import hashlib
import json
import os
from pathlib import Path
import time
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
SITE='https://atlas-solucoes.github.io/atlas-financas-app/'
commit=os.environ.get('EXPECTED_COMMIT','')
checks=[]
for path in ['nuvem/index.html','nuvem/documentos-core.js','nuvem/documentos.js','nuvem/sw.js']:
    expected=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    last=''
    for attempt in range(24):
        try:
            request=Request(SITE+path+'?atlas_version='+commit,headers={'Cache-Control':'no-cache','User-Agent':'Atlas-release-check'})
            with urlopen(request,timeout=20) as response:
                actual=hashlib.sha256(response.read()).hexdigest()
            if actual==expected:
                checks.append({'file':path,'sha256_matches':True});break
            last='Publicado ainda difere do commit esperado.'
        except Exception as exc:
            last=str(exc)
        if attempt<23:time.sleep(8)
    else:
        raise AssertionError(path+': '+last)
report={'commit':commit,'scope':'HTTP público, sem autenticação e sem acesso ao Supabase','checks':checks}
(ROOT/'test-results').mkdir(exist_ok=True)
(ROOT/'test-results'/'publicacao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
print(json.dumps(report,indent=2,ensure_ascii=False))
