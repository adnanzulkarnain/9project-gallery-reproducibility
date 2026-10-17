"""Repeat generator checks on Linux in a disposable copy, without network access."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
image=os.environ.get('AUDIT_NODE_IMAGE','node:24-alpine')
def run(args):return subprocess.run(['docker']+args,check=True,text=True,capture_output=True).stdout.strip()
with tempfile.TemporaryDirectory(prefix='9project-linux-') as tmp:
    dest=Path(tmp)/'audit';dest.mkdir()
    for name in ['scripts','snapshot','results']:shutil.copytree(ROOT/name,dest/name)
    names=['results/generator.json','results/per_artwork.csv','results/extended.json','snapshot/index_thumbnail_variant.html']
    before={n:hashlib.sha256((dest/n).read_bytes()).hexdigest() for n in names}
    command=['run','--rm','--network','none','--mount','type=bind,src='+str(dest)+',dst=/audit','--workdir','/audit',image]
    env=json.loads(run(command+['node','-e','console.log(JSON.stringify({node:process.version,platform:process.platform,architecture:process.arch}))']))
    steps=[]
    for script in ['scripts/test_generator.cjs','scripts/test_extended.cjs']:
        run(command+['node',script]);steps.append({'script':script,'exit_code':0})
    matches={n:hashlib.sha256((dest/n).read_bytes()).hexdigest()==h for n,h in before.items()}
    semantic={}
    for n in ['results/generator.json','results/extended.json']:
        a=json.loads((ROOT/n).read_text());b=json.loads((dest/n).read_text())
        different=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
        semantic[n]={'differing_top_level_fields':different}
        print(n,different)
        assert different==(['environment'] if n.endswith('generator.json') else [])
    assert all(matches[n] for n in ['results/per_artwork.csv','snapshot/index_thumbnail_variant.html'])
report={'scope':'Cross-environment execution by the same session; not independent external reproduction',
        'environment':env,'image_id':run(['image','inspect',image,'--format','{{.Id}}']),
        'network':'none','steps':steps,'byte_matches':matches,'json_comparison':semantic,'external_reproduction':False}
(ROOT/'results/linux_reproduction.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
