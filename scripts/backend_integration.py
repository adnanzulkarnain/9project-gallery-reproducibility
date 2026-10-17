"""Execute the frozen PHP backend against a disposable MySQL database.
Never connects to the existing application or reads its .env file.
Requires Docker, Pillow and images galeri-web:latest and mysql:8.0.
"""
from pathlib import Path
import hashlib,http.cookiejar,io,json,os,re,secrets,shutil,subprocess,tempfile,time,urllib.error,urllib.parse,urllib.request
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
docker=os.environ.get('DOCKER_BINARY','docker');suffix=secrets.token_hex(4)
network='9project-audit-'+suffix;db=network+'-db';web=network+'-web';password=secrets.token_hex(24)
webimage=os.environ.get('AUDIT_WEB_IMAGE','galeri-web:latest');dbimage=os.environ.get('AUDIT_DB_IMAGE','mysql:8.0')
results=[];started=[];base=None
def run(args,input=None,check=True):
    p=subprocess.run([docker]+args,input=input,text=True,capture_output=True)
    if check and p.returncode:raise RuntimeError(p.stderr)
    return p
def sql(query):
    return run(['exec','-i','-e','MYSQL_PWD='+password,db,'mysql','-uroot','--batch','--skip-column-names','audit'],query).stdout.strip()
def record(name,expected,observed):
    passed=expected==observed
    results.append({'name':name,'expected':expected,'observed':observed,'passed':passed})
    print(name, 'PASS' if passed else 'FAIL',flush=True)
def client():return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),NoRedirect())
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def request(c,path,fields=None,file=None,raw=None):
    headers={};data=None
    if fields is not None:
        data=urllib.parse.urlencode(fields).encode()
        headers['Content-Type']='application/x-www-form-urlencoded'
    if file:
        boundary='audit'+secrets.token_hex(12);parts=[]
        for k,v in (fields or {}).items():parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        filename,mime,content=file
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="gambar"; filename="{filename}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+content+b'\r\n')
        parts.append(f'--{boundary}--\r\n'.encode());data=b''.join(parts);headers['Content-Type']='multipart/form-data; boundary='+boundary
    if raw is not None:data=raw;headers['Content-Type']='application/octet-stream'
    req=urllib.request.Request(base+path,data=data,headers=headers)
    try:r=c.open(req,timeout=45)
    except urllib.error.HTTPError as e:r=e
    return r.code,dict(r.headers),r.read()
def token(c,path):
    status,_,body=request(c,path);assert status==200
    return re.search(rb'name="csrf_token" value="([a-f0-9]+)"',body)[1].decode()
def image(fmt,size=(2800,1400),alpha=False):
    b=io.BytesIO();im=Image.new('RGBA' if alpha else 'RGB',size,(0,0,0,0) if alpha else (40,90,150));im.save(b,format=fmt);return b.getvalue()
report={'scope':'Isolated PHP/Apache and MySQL integration; no user study or external reproduction','cases':results}
try:
  with tempfile.TemporaryDirectory(prefix='9project-backend-') as tmp:
    public=Path(tmp)/'public';shutil.copytree(ROOT/'assets',public)
    shutil.copyfile(ROOT/'snapshot/index.html',public/'index.html')
    shutil.copytree(ROOT/'snapshot/backend',public,dirs_exist_ok=True)
    run(['network','create',network]);started.append('network')
    run(['run','-d','--name',db,'--network',network,'-e','MYSQL_ROOT_PASSWORD='+password,'-e','MYSQL_DATABASE=audit',dbimage]);started.append(db)
    for _ in range(60):
        if run(['exec','-e','MYSQL_PWD='+password,db,'mysql','-h127.0.0.1','-uroot','--execute','SELECT 1'],check=False).returncode==0:break
        time.sleep(1)
    else:raise RuntimeError('Disposable MySQL did not become ready')
    sql((ROOT/'snapshot/collection.sql').read_text())
    schema='CREATE TABLE admin_users (id INT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(50) UNIQUE,password_hash VARCHAR(255)); CREATE TABLE kunjungan (id INT AUTO_INCREMENT PRIMARY KEY,dikunjungi_pada TIMESTAMP DEFAULT CURRENT_TIMESTAMP,ip_hash VARCHAR(64),user_agent VARCHAR(255));'
    sql(schema)
    # Synthetic account exists only in the disposable database.
    adminpass=secrets.token_hex(16)
    phphash=run(['run','--rm','--network','none','--entrypoint','php',webimage,'-r','echo password_hash($argv[1], PASSWORD_DEFAULT);',adminpass]).stdout
    sql("INSERT INTO admin_users(username,password_hash) VALUES ('audit_admin','"+phphash+"');")
    run(['run','-d','--name',web,'--network',network,'-p','127.0.0.1::80','-e','DB_HOST='+db,'-e','DB_NAME=audit','-e','DB_USER=root','-e','DB_PASSWORD='+password,'--mount','type=bind,src='+str(public)+',dst=/var/www/html',webimage]);started.append(web)
    port=run(['port',web,'80/tcp']).stdout.strip().rsplit(':',1)[1];base='http://127.0.0.1:'+port
    for _ in range(30):
        try:
            if request(client(),'/api/karya.php')[0]==200:break
        except (OSError,urllib.error.URLError):pass
        time.sleep(1)
    original=json.loads(request(client(),'/api/karya.php')[2]);expected=json.loads((ROOT/'results/collection.json').read_text())
    record('API collection IDs and order',[r['id'] for r in expected],[r['id'] for r in original])
    record('API dimensions match SQL',True,all(int(a['lebar'])==b['lebar'] and int(a['tinggi'])==b['tinggi'] for a,b in zip(original,expected)))
    record('Unauthenticated admin redirect',302,request(client(),'/admin/index.php')[0])
    record('Track GET rejected',405,request(client(),'/api/track.php')[0])
    before=int(sql('SELECT COUNT(*) FROM kunjungan'))
    status,_,body=request(client(),'/api/track.php',fields={})
    record('Track POST persists row',[200,True,before+1],[status,json.loads(body)['ok'],int(sql('SELECT COUNT(*) FROM kunjungan'))])
    record('Track stores SHA256-shaped hash',64,int(sql('SELECT LENGTH(ip_hash) FROM kunjungan ORDER BY id DESC LIMIT 1')))
    c=client();s,_,b=request(c,'/admin/login.php',{'username':'audit_admin','password':'invalid'})
    record('Wrong password rejected',True,s==200 and b'Username atau password salah' in b)
    record('Wrong-password session remains unauthenticated',302,request(c,'/admin/index.php')[0])
    s,h,_=request(c,'/admin/login.php',{'username':'audit_admin','password':adminpass})
    record('Synthetic account login',302,s)
    t=token(c,'/admin/create.php')
    record('Invalid CSRF rejected',400,request(c,'/admin/create.php',{'csrf_token':'bad','judul':'audit','seniman':'audit'})[0])
    s,_,b=request(c,'/admin/create.php',{'csrf_token':t,'judul':'','seniman':'audit'})
    record('Required title validation',True,s==200 and b'Judul dan seniman wajib' in b)
    fields={'csrf_token':t,'judul':'AUDIT synthetic','seniman':'Synthetic test','tahun':'2026','deskripsi':'Disposable integration test'}
    for fmt,mime,alpha in [('JPEG','image/jpeg',False),('PNG','image/png',True),('WEBP','image/webp',False)]:
        s,_,b=request(c,'/admin/create.php',fields,file=('test.'+fmt.lower(),mime,image(fmt,alpha=alpha)))
        record('Upload '+fmt+' redirects',302,s)
        row=sql("SELECT id,gambar,lebar,tinggi FROM karya WHERE judul='AUDIT synthetic' ORDER BY id DESC LIMIT 1").split('\t');ident=int(row[0]);filename=row[1]
        file=public/'uploads/karya'/filename
        with Image.open(file) as im:
            record('Upload '+fmt+' WebP and dimensions',['WEBP',1400,700,1400,700],[im.format,*im.size,int(row[2]),int(row[3])])
            if alpha:record('PNG transparency flattened onto white',True,min(im.convert('RGB').getpixel((0,0)))>=250)
        edit=token(c,'/admin/edit.php?id='+str(ident));updated={**fields,'csrf_token':edit,'id':str(ident),'judul':'AUDIT edited'}
        record('Edit '+fmt+' metadata',302,request(c,'/admin/edit.php?id='+str(ident),updated)[0])
        record('Edit '+fmt+' persisted title','AUDIT edited',sql('SELECT judul FROM karya WHERE id='+str(ident)))
        updated['judul']='AUDIT replaced'
        record('Replace '+fmt+' image',302,request(c,'/admin/edit.php?id='+str(ident),updated,file=('small.png','image/png',image('PNG',(100,50))))[0])
        newfile=sql('SELECT gambar FROM karya WHERE id='+str(ident))
        record('Replace '+fmt+' removes old file',True,not file.exists() and (public/'uploads/karya'/newfile).exists())
        record('Delete '+fmt,302,request(c,'/admin/delete.php',{'csrf_token':edit,'id':str(ident)})[0])
        record('Delete '+fmt+' removes row and file',True,sql('SELECT COUNT(*) FROM karya WHERE id='+str(ident))=='0' and not (public/'uploads/karya'/newfile).exists())
    s,_,b=request(c,'/admin/create.php',fields,file=('fake.png','image/png',b'not an image'))
    record('Invalid image rejected',True,s==200 and b'Format gambar harus' in b)
    record('Edit unknown record',404,request(c,'/admin/edit.php?id=999999')[0])
    record('Authenticated delete GET rejected',405,request(c,'/admin/delete.php')[0])
    record('Logout redirects',302,request(c,'/admin/logout.php')[0])
    record('Logout invalidates protected access',302,request(c,'/admin/index.php')[0])
    record('Original collection restored',True,[r['id'] for r in json.loads(request(client(),'/api/karya.php')[2])]==[r['id'] for r in original])
    if os.environ.get('RUN_BROWSER')=='1':
        env={**os.environ,'AUDIT_BASE_URL':base}
        subprocess.run([os.environ.get('NODE_BINARY','node'),str(ROOT/'scripts/browser_live.cjs')],env=env,check=True)
        report['integrated_browser_executed']=True
    runtime=run(['exec',web,'php','-r','echo json_encode(["php"=>PHP_VERSION,"gd"=>gd_info(),"exif"=>function_exists("exif_read_data")]);']).stdout
    report['runtime']={'php':json.loads(runtime),'mysql':sql('SELECT VERSION()'),'web_image_id':run(['image','inspect',webimage,'--format','{{.Id}}']).stdout.strip(),'db_image_id':run(['image','inspect',dbimage,'--format','{{.Id}}']).stdout.strip()}
    report['summary']={'cases':len(results),'passed':sum(r['passed'] for r in results),'failed':sum(not r['passed'] for r in results),'production_database_accessed':False}
except Exception as exc:
    report['execution_error']=str(exc);raise
finally:
    for name in reversed(started):
        if name=='network':run(['network','rm',network],check=False)
        else:run(['rm','-f','-v',name],check=False)
    report['disposable_resources_removed']=True
    (ROOT/'results/backend_integration.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['summary'],indent=2))
