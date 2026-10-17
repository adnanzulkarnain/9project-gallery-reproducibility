from pathlib import Path
import json,hashlib,csv,platform,re
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'
sql=(ROOT/'snapshot/collection.sql').read_text()
values=re.search(r'INSERT INTO `karya` VALUES (.*?);\n',sql,re.S).group(1)
rows,row,token=[],[],'';quoted=escaped=inrow=False
for char in values:
    if escaped:
        token += {'n':'\n','r':'\r','0':'\0'}.get(char,char);escaped=False;continue
    if quoted and char=='\\':escaped=True;continue
    if char=="'":quoted=not quoted;continue
    if quoted:token+=char;continue
    if char=='(':inrow,row,token=True,[],''
    elif char==',' and inrow:row.append(token);token=''
    elif char==')' and inrow:row.append(token);rows.append(row);inrow,token=False,''
    elif inrow:token+=char
keys=['id','judul','seniman','tahun','deskripsi','gambar','lebar','tinggi','created_at','updated_at']
data=[dict(zip(keys,row)) for row in rows]
for item in data:
    for key in ['id','lebar','tinggi']:item[key]=int(item[key])
    file=ROOT/'assets/uploads/karya'/item['gambar']
    with Image.open(file) as image:width,height=image.size
    item.update(file_exists=file.exists(),file_bytes=file.stat().st_size,actual_width=width,actual_height=height,dimensions_match=(width==item['lebar'] and height==item['tinggi']),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),test_candidate=item['judul'].strip().lower()=='test')
primary=[x for x in data if not x['test_candidate']]
summary={'python':platform.python_version(),'raw_records':len(data),'primary_records':len(primary),'available':sum(x['file_exists'] for x in primary),'dimension_matches':sum(x['dimensions_match'] for x in primary),'total_bytes':sum(x['file_bytes'] for x in primary),'over_1400':sum(max(x['actual_width'],x['actual_height'])>1400 for x in primary),'missing_year':sum(not x['tahun'] or x['tahun']=='NULL' for x in primary)}
assert len(data)==17 and len(primary)==16
assert next(x for x in data if x['id']==35)['sha256']==next(x for x in data if x['id']==33)['sha256']
(OUT/'collection.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
(OUT/'audit.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
