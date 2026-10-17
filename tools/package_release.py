"""Package the reviewed allowlist, never a recursive directory copy."""
from pathlib import Path
import hashlib,json,sys,zipfile
from verify_publication import ROOT,verify
verify()
output=Path(sys.argv[1]).resolve()
assert not output.is_relative_to(ROOT),'Archive must be outside the source tree'
assert not output.exists(),'Refusing to overwrite an existing archive'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name in json.loads((ROOT/'PUBLICATION_POLICY.json').read_text())['files']:
        info=zipfile.ZipInfo(name,date_time=(2026,10,18,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,(ROOT/name).read_bytes())
verify(output)
digest=hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix+'.sha256').write_text(digest+'  '+output.name+'\n')
print(json.dumps({'archive':str(output),'sha256':digest},indent=2))
