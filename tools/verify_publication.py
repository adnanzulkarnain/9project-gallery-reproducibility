"""Fail closed on unapproved files, changed bytes, document signatures and Git history."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, io, json, re, subprocess, zipfile
ROOT=Path(__file__).resolve().parents[1]
BANNED={'.doc','.docx','.docm','.dot','.dotx','.dotm','.xls','.xlsx','.xlsm','.ppt','.pptx','.pptm','.odt','.ods','.odp','.rtf','.pdf','.zip','.7z','.rar','.gz','.tar','.bz2','.xz'}
def inspect(name,data):
    p=PurePosixPath(name);low=name.lower()
    assert p.name!='.DS_Store' and p.suffix not in {'.pyc','.log'}, f'Local artifact: {name}'
    assert not p.is_absolute() and '..' not in p.parts, f'Unsafe path: {name}'
    assert p.suffix.lower() not in BANNED, f'Forbidden extension: {name}'
    assert not any(x.startswith(('~$','.env')) for x in p.parts), f'Local/private file: {name}'
    assert not any(x in low for x in ['manuscript','review_reviewer','tanggapan','laporan_']), f'Editorial file: {name}'
    assert not data.startswith((bytes.fromhex('d0cf11e0a1b11ae1'),b'%PDF-',b'{\\rtf',b'7z\xbc\xaf\x27\x1c',b'Rar!',b'\x1f\x8b')), f'Document/archive signature: {name}'
    assert not zipfile.is_zipfile(io.BytesIO(data)) and not data.startswith(b'PK\x03\x04'), f'Nested ZIP/Office container: {name}'
    assert not (len(data)>262 and data[257:262]==b'ustar'), f'TAR archive: {name}'
    if p.suffix.lower() in {'.py','.cjs','.js','.php','.json','.md','.html','.sql','.cff','.txt'} and len(data)<4_000_000:
        assert not re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)',data), f'Credential signature: {name}'
def verify(archive=None):
    policy=json.loads((ROOT/'PUBLICATION_POLICY.json').read_text());allowed=set(policy['files'])
    manifest=json.loads((ROOT/'MANIFEST.json').read_text())['sha256']
    assert set(manifest)==allowed-{'MANIFEST.json'}, 'Manifest coverage mismatch'
    actual=set()
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if '.git' in rel.parts:continue
        if '__pycache__' in rel.parts and p.suffix=='.pyc':continue
        assert not p.is_symlink(),f'Symlink: {rel}'
        if p.is_file():actual.add(rel.as_posix())
    assert actual==allowed, f'Allowlist mismatch; extra={sorted(actual-allowed)}, missing={sorted(allowed-actual)}'
    for name in sorted(allowed):
        data=(ROOT/name).read_bytes();inspect(name,data)
        if name in manifest:assert hashlib.sha256(data).hexdigest()==manifest[name], f'Hash mismatch: {name}'
    history=0
    if (ROOT/'.git').exists():
        def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
        refs=git('rev-list','--all').decode().splitlines()
        for commit in refs:
            for row in git('ls-tree','-r','-z',commit).split(b'\0'):
                if not row:continue
                meta,name=row.split(b'\t',1);mode,kind,oid=meta.split();name=name.decode()
                assert name in allowed,f'Historical unapproved file: {name}'
                assert mode!=b'120000' and kind==b'blob',f'Unsupported Git entry: {name}'
                inspect(name,git('cat-file','blob',oid.decode()));history+=1
    if archive:
        with zipfile.ZipFile(archive) as z:
            entries=z.infolist();names=[i.filename for i in entries]
            assert len(names)==len(set(names)),'Duplicate ZIP entries'
            assert set(names)==allowed,'Archive allowlist mismatch'
            for entry in entries:
                name=entry.filename;assert (entry.external_attr>>16)&0o170000!=0o120000,'Archive symlink'
                data=z.read(entry);inspect(name,data)
                assert data==(ROOT/name).read_bytes(),f'Archive content mismatch: {name}'
    return {'passed':True,'allowed_files':len(allowed),'history_file_checks':history,'office_files':0,'archive_verified':bool(archive)}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive');args=p.parse_args()
    print(json.dumps(verify(args.archive),indent=2))
