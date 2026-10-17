"""Cross-check reporting artifacts against independent CSV arithmetic and recorded browser evidence."""
from pathlib import Path
import csv,json,math,statistics,hashlib
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/'results/generator.json').read_text());b=json.loads((ROOT/'results/browser.json').read_text());a=json.loads((ROOT/'results/audit.json').read_text())
with (ROOT/'results/per_artwork.csv').open() as f:rows=list(csv.DictReader(f))
errors=[100*abs(float(r['plane_width'])/float(r['plane_height'])-float(r['source_width'])/float(r['source_height']))/(float(r['source_width'])/float(r['source_height'])) for r in rows]
assert len(rows)==16 and len({r['id'] for r in rows})==16
for key,value in [('mean',statistics.mean(errors)),('median',statistics.median(errors)),('max',max(errors))]:assert math.isclose(g['summary']['primaryError'][key],value,abs_tol=1e-12)
assert len(g['scenarios'])==35
assert sum(any(not t['pass'] for t in s['thumbnails']) for s in g['scenarios'])==26
assert a['available']==16 and a['dimension_matches']==16 and a['over_1400']==10
assert len(b['results'])==5 and all(x['initial']['sceneLoaded'] for x in b['results'])
p=next(x for x in b['results'] if x['name']=='primary-16');nav=p['navigation']
assert p['initial']['exhibits']==p['initial']['paintings']==16
assert all(x['loaded'] for x in p['initial']['images'])
assert all(x['paintingMesh'] for x in p['initial']['planes'])
assert p['initial']['pageErrorsBeforeNavigation']==[] and nav['errorsBeforeSensitivity']==[]
assert any('Maximum call stack size exceeded' in e for e in nav['errorsFromSensitivity'])
assert nav['moved']['rig']['z']==10 and abs(nav['moved']['camera']['z'])>.01
assert nav['teleported']['rig']['z']==-21 and abs(nav['teleported']['cameraLocal']['z'])>.01
assert math.isclose(nav['teleported']['cameraWorld']['z'],nav['teleported']['rig']['z']+nav['teleported']['cameraLocal']['z'],abs_tol=1e-8)
assert nav['collision']['clampedX']==nav['collision']['bound']==10.2
missing=next(x for x in b['results'] if x['name']=='missing-image')
assert any(x['status']==404 for x in missing['httpFailures']) and any(not x['loaded'] for x in missing['initial']['images'])
zero=next(x for x in b['results'] if x['name']=='zero-dimensions')
assert zero['initial']['planes'][0]['w']==2.06 and zero['initial']['planes'][0]['h']==2.8
e=json.loads((ROOT/'results/extended.json').read_text())['summary']
assert e['scenarios']==35 and e['beforeThumbnailFailures']==26 and e['afterThumbnailFailures']==0
assert e['identifierPass']==e['allocationPass']==e['geometryPass']==35
assert e['outputMutations']==e['outputMutationsDetected']==14
assert e['sourceMutations']==e['sourceMutationsDetected']==2 and e['ratioProbes']==15
assert e['aliasedFilenames']=={'filePathOraclePass':True,'idOraclePass':False}
assert e['instrumentationMarkupIdentical']
c=json.loads((ROOT/'results/browser_controls.json').read_text())
assert c['protocol']['canvasSelector']=='.a-canvas' and c['protocol']['repetitions']==3
assert c['summary']['baselineDeliveries']==[1,1,1]
assert c['summary']['nondefaultDeliveries']==[0,0,0] and c['summary']['stackErrorRuns']==3
backend=json.loads((ROOT/'results/backend_integration.json').read_text())
assert backend['summary']=={'cases':42,'passed':42,'failed':0,'production_database_accessed':False}
assert len(backend['cases'])==42 and all(x['passed'] for x in backend['cases'])
live=json.loads((ROOT/'results/browser_live.json').read_text())
assert live['summary']['pointerLockAcquired']==[True,True]
assert live['summary']['baselineTrustedCanvasEvents']==1 and live['summary']['nondefaultCanvasEvents']==0
assert live['summary']['nondefaultStackError'] and live['summary']['mobileEmulatedExhibits']==17
assert all(x['state']['exhibits']==17 and not x['pointerLockGetterInjected'] for x in live['runs'])
linux=json.loads((ROOT/'results/linux_reproduction.json').read_text())
assert not linux['external_reproduction']
assert linux['json_comparison']['results/generator.json']['differing_top_level_fields']==['environment']
assert linux['json_comparison']['results/extended.json']['differing_top_level_fields']==[]
assert linux['byte_matches']['results/per_artwork.csv'] and linux['byte_matches']['snapshot/index_thumbnail_variant.html']
source=hashlib.sha256((ROOT/'snapshot/index.html').read_bytes()).hexdigest()
assert source=='36b721c91c346a0be961546b9f5806a4ecd7eacca10ffe1b5425c650ba7c5dfc'
result={'csv_statistics_verified':True,'generator_scenarios':35,'thumbnail_failures_before':26,'thumbnail_failures_after':0,'output_mutations_detected':14,'source_mutations_detected':2,'browser_evidence_verified':True,'backend_cases_verified':42,'linux_comparison_verified':True,'source_sha256':source}
(ROOT/'results/evidence_validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
