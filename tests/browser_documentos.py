"""Anexos com Storage/REST em memória: nenhum documento ou conta real é usado."""
import base64
import copy
import hashlib
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import expect

UID='00000000-0000-4000-8000-000000000001'

class DocsBackend:
    def __init__(self):
        self.cases={};self.docs={};self.objects={};self.uploads=0
    def install(self, context):
        context.route('**/rest/v1/atlas_expense_cases*', self.cases_route)
        context.route('**/rest/v1/atlas_documents*', self.docs_route)
        context.route('**/storage/v1/**', self.storage_route)
    def response(self, route, data, status=200):
        route.fulfill(status=status,json=data,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'})
    def allowed(self, route):
        if route.request.method=='OPTIONS':
            self.response(route,{});return False
        if route.request.headers.get('authorization')!='Bearer token-test-only':
            self.response(route,{'message':'Não autorizado'},401);return False
        return True
    def body(self, route):
        return route.request.post_data_json or {}
    def filtered(self, rows, query):
        result=[]
        for row in rows:
            include=True
            for key, ops in query.items():
                if key in ('order','offset','limit','select'):continue
                for op in ops:
                    value=str(row.get(key) or '')
                    if op.startswith('eq.'):include &= value==op[3:]
                    elif op.startswith('in.('):include &= value in op[4:-1].split(',')
                    elif op.startswith('gte.'):include &= value>=op[4:]
                    elif op.startswith('lte.'):include &= value<=op[4:]
                    elif op.startswith('ilike.'):include &= op[6:].strip('*').lower() in value.lower()
            if include:result.append(copy.deepcopy(row))
        return result
    def cases_route(self, route):
        if not self.allowed(route):return
        req=route.request;q=parse_qs(urlparse(req.url).query)
        if req.method=='GET':
            data=self.filtered(self.cases.values(),q)
            data.sort(key=lambda r:r['created_at'],reverse=True)
            offset=int(q.get('offset',['0'])[0]);self.response(route,data[offset:offset+int(q.get('limit',['1000'])[0])]);return
        body=self.body(route)
        if req.method=='POST':
            assert body['user_id']==UID
            if any(x['parent_id']==body['parent_id'] and x['parent_type']==body['parent_type'] for x in self.cases.values()):
                self.response(route,{'code':'23505','message':'duplicate'},409);return
            row={**body,'revision':1,'created_at':datetime.now(timezone.utc).isoformat()};self.cases[row['id']]=row;self.response(route,[row]);return
        if req.method=='PATCH':
            rows=self.filtered(self.cases.values(),q);result=[]
            for row in rows:
                row.update(body);row['revision']+=1;self.cases[row['id']]=row;result.append(row)
            self.response(route,result);return
        raise AssertionError(req.method)
    def docs_route(self, route):
        if not self.allowed(route):return
        req=route.request;q=parse_qs(urlparse(req.url).query)
        if req.method=='GET':self.response(route,self.filtered(self.docs.values(),q));return
        if req.method=='POST':
            body=self.body(route);assert body['user_id']==UID;assert self.cases[body['case_id']]['user_id']==UID
            if any(d['case_id']==body['case_id'] and d['sha256']==body['sha256'] for d in self.docs.values()):
                self.response(route,{'code':'23505'},409);return
            assert body['path'].startswith(UID+'/'+body['case_id']+'/')
            assert body['path'] in self.objects
            assert hashlib.sha256(self.objects[body['path']][0]).hexdigest()==body['sha256']
            self.docs[body['id']]={**body,'created_at':datetime.now(timezone.utc).isoformat()};self.response(route,[body]);return
        if req.method=='DELETE':
            for d in self.filtered(self.docs.values(),q):self.docs.pop(d['id'])
            self.response(route,[]);return
        raise AssertionError(req.method)
    def storage_route(self, route):
        if not self.allowed(route):return
        req=route.request;path=urlparse(req.url).path
        prefix='/storage/v1/object/atlas-financas-documentos/'
        if req.method=='POST' and path.startswith(prefix):
            name=path[len(prefix):];assert name.startswith(UID+'/');assert req.headers['x-upsert']=='false'
            assert name.split('/')[1] in self.cases
            payload=req.post_data_buffer;self.objects[name]=(payload,req.headers['content-type']);self.uploads+=1;self.response(route,{'Key':name});return
        if req.method=='GET':
            prefix='/storage/v1/object/authenticated/atlas-financas-documentos/';assert path.startswith(prefix)
            name=path[len(prefix):]
            if not name.startswith(UID+'/'):self.response(route,{'message':'Forbidden'},403);return
            payload,mime=self.objects[name];route.fulfill(status=200,body=payload,content_type=mime,headers={'Access-Control-Allow-Origin':'*'});return
        if req.method=='DELETE':
            for name in self.body(route)['prefixes']:
                assert name.startswith(UID+'/');self.objects.pop(name,None)
            self.response(route,[]);return
        raise AssertionError(req.url)

def receipt(page, personal=False):
    result=page.evaluate('''(personal)=>{const c=document.createElement('canvas');c.width=1200;c.height=600;const x=c.getContext('2d');x.fillStyle='white';x.fillRect(0,0,c.width,c.height);x.fillStyle='black';x.font='48px Arial';const data=todayStr().split('-').reverse().join('/');[personal?'FARMACIA PESSOAL':'RESTAURANTE EXEMPLO','CNPJ 00.000.000/0001-00','DATA '+data,personal?'TOTAL A PAGAR R$ 29,00':'TOTAL A PAGAR R$ 85,00'].forEach((t,i)=>x.fillText(t,50,100+i*110));return c.toDataURL('image/png').split(',')[1]}''',personal)
    return {'name':'nota-pessoal.png' if personal else 'nota-almoco.png','mimeType':'image/png','buffer':base64.b64decode(result)}

def sample_pdf():
    stream=b'BT /F1 20 Tf 50 760 Td (BOLETO DE TESTE) Tj 0 -30 Td (VENCIMENTO 05/11/2026) Tj 0 -30 Td (VALOR DO DOCUMENTO R$ 150,00) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream']
    data=bytearray(b'%PDF-1.4\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(data));data.extend(str(i).encode()+b' 0 obj\n'+obj+b'\nendobj\n')
    xref=len(data);data.extend(b'xref\n0 6\n0000000000 65535 f \n')
    for offset in offsets[1:]:data.extend(f'{offset:010} 00000 n \n'.encode())
    data.extend(b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF')
    return {'name':'boleto-teste.pdf','mimeType':'application/pdf','buffer':bytes(data)}

def exercise_documents(a, b, backend, artifacts):
    def close():a.evaluate('closeSheet()')
    def listing():
        close();a.locator('.top [data-act="documentos"]').click();expect(a.locator('#ad-fscope')).to_be_visible()
    def new():
        listing();a.locator('[data-doc="new"]').click();expect(a.locator('#ad-file')).to_be_visible()
    a.on('dialog',lambda dialog:dialog.accept())
    a.context.add_init_script("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async(data)=>{window.testShared={names:data.files.map(f=>f.name),text:data.text};}})")
    a.evaluate("Object.defineProperty(navigator,'canShare',{configurable:true,value:()=>true});Object.defineProperty(navigator,'share',{configurable:true,value:async(data)=>{window.testShared={names:data.files.map(f=>f.name),text:data.text};}})")
    sample=receipt(a);new()
    a.locator('#ad-title').fill('Almoço corporativo')
    a.locator('#ad-amount').fill('8500')
    a.locator('#ad-scope').select_option('corporativo')
    a.locator('#ad-company').fill('Empresa Teste')
    a.locator('#ad-reimbursement').select_option('a_solicitar')
    a.locator('#ad-file').set_input_files(sample)
    expect(a.locator('#ad-canvas')).to_be_visible()
    if os.environ.get('LIVE_OCR')=='1':
        a.locator('[data-doc="read"]').click()
        expect(a.locator('#ad-pamount')).to_be_visible(timeout=180000)
        assert a.locator('#ad-pamount').input_value()=='R$ 85,00'
        a.locator('[data-doc="apply"]').click()
    a.locator('[data-doc="upload"]').click()
    expect(a.locator('#ad-status')).to_contain_text('Arquivo anexado',timeout=30000)
    assert len(backend.docs)==1 and backend.uploads==1
    cid=next(iter(backend.cases));bank=a.evaluate("db.meios.find(m=>m.tipo==='banco').id")
    before=a.evaluate('db.recs.length')
    # Anexar, classificar e reconhecer não alteram saldos ou lançamentos.
    assert a.evaluate('db.recs.length')==before
    a.locator('#ad-file').set_input_files(sample)
    expect(a.locator('#ad-canvas')).to_be_visible()
    a.locator('[data-doc="upload"]').click()
    expect(a.locator('#ad-status')).to_contain_text('já está anexado')
    assert len(backend.docs)==1 and backend.uploads==1
    a.locator('#ad-file').set_input_files({'name':'falsa.jpg','mimeType':'image/jpeg','buffer':b'<html>nao e imagem</html>'})
    expect(a.locator('#ad-status')).to_contain_text('Formato não suportado')
    assert backend.uploads==1
    # Outro documento pessoal nunca deve entrar no filtro e pacote corporativo.
    personal=receipt(a,True);new()
    a.locator('#ad-title').fill('Despesa pessoal de teste')
    a.locator('#ad-amount').fill('2900')
    a.locator('#ad-file').set_input_files(personal)
    expect(a.locator('#ad-canvas')).to_be_visible()
    a.locator('[data-doc="upload"]').click()
    expect(a.locator('#ad-status')).to_contain_text('Arquivo anexado')
    assert len(backend.docs)==2
    new();a.locator('#ad-title').fill('PDF pessoal de teste')
    a.locator('#ad-file').set_input_files(sample_pdf())
    expect(a.locator('[data-doc="read"]')).to_be_visible()
    if os.environ.get('LIVE_OCR')=='1':
        a.locator('[data-doc="read"]').click()
        expect(a.locator('#ad-pamount')).to_have_value('R$ 150,00',timeout=120000)
        expect(a.locator('#ad-pdue')).to_have_value('2026-11-05')
    a.locator('[data-doc="upload"]').click()
    expect(a.locator('#ad-status')).to_contain_text('Arquivo anexado')
    assert len(backend.docs)==3
    listing();a.locator('#ad-fscope').select_option('corporativo');a.locator('#ad-fcompany').fill('Empresa Teste');a.locator('#ad-fstatus').select_option('a_solicitar');a.locator('[data-doc="filter"]').click()
    expect(a.locator('#ad-root')).not_to_contain_text('Despesa pessoal de teste')
    a.locator(f'[data-doc-check="{cid}"]').check()
    a.locator('[data-doc="prepare-share"]').click()
    expect(a.locator('[data-doc="share"]')).to_be_visible()
    a.locator('[data-doc="share"]').click()
    a.wait_for_function('window.testShared !== undefined')
    assert len(a.evaluate('testShared.names'))==1
    assert not any('pessoal' in name for name in a.evaluate('testShared.names'))
    # Abrir o compartilhamento não confirma envio.
    assert backend.cases[cid]['reimbursement_status']=='a_solicitar'
    with a.expect_download() as download:
        a.locator('[data-doc="zip"]').click()
    target=artifacts/'comprovantes-teste.zip';download.value.save_as(target)
    with zipfile.ZipFile(target) as archive:
        assert len(archive.namelist())==2
        assert archive.testzip() is None
        assert not any('pessoal' in name for name in archive.namelist())
    a.locator('[data-doc="mark-requested"]').click()
    a.wait_for_function("document.querySelector('#ad-status').textContent.includes('solicitações')")
    assert backend.cases[cid]['reimbursement_status']=='solicitado'
    # Segunda sessão enxerga os mesmos metadados e pode baixar o anexo privado.
    b.evaluate('closeSheet()');b.locator('.top [data-act="documentos"]').click()
    expect(b.locator('#ad-root')).to_contain_text('Empresa Teste')
    b.locator(f'[data-doc="case"][data-id="{cid}"]').click()
    expect(b.locator('#ad-files')).to_contain_text('nota-almoco.jpg')
    b.locator('[data-doc="view"]').click()
    expect(b.locator('#ad-proposal img')).to_be_visible()
    # Importação proposta: revisão abre o formulário, só Salvar cria o gasto.
    listing();a.locator(f'[data-doc="case"][data-id="{cid}"]').click()
    if os.environ.get('LIVE_OCR')=='1':
        a.locator('[data-doc="read-existing"]').click()
        expect(a.locator('#ad-pamount')).to_be_visible(timeout=180000)
        prev=a.evaluate('db.recs.length')
        a.locator('[data-doc="review"]').click()
        expect(a.locator('#qv')).to_be_visible()
        assert a.evaluate('db.recs.length')==prev
        a.locator('#qmeio').select_option(bank)
        a.locator('[data-act="saveadd"]').click()
        a.wait_for_function('(id)=>db.recs.some(r=>r.anCase===id)',arg=cid)
        assert a.evaluate('(id)=>db.recs.filter(r=>r.anCase===id).length',cid)==1
        a.wait_for_function('!N.dirty && !nvBusy')
        assert backend.cases[cid]['parent_type']=='gasto'
        # Reembolso cria uma única entrada revisada, sem nova despesa.
        listing();a.locator(f'[data-doc="case"][data-id="{cid}"]').click()
        a.locator('[data-doc="reimbursement"]').click()
        expect(a.locator('#qv')).to_be_visible()
        a.locator('#qmeio').select_option(bank)
        a.locator('[data-act="saveadd"]').click()
        a.wait_for_function('(id)=>db.recs.some(r=>r.anReembolso===id)',arg=cid)
        a.wait_for_function('!N.dirty && !nvBusy')
        assert backend.cases[cid]['reimbursement_status']=='recebido'
        assert a.evaluate('(id)=>db.recs.filter(r=>r.anReembolso===id).length',cid)==1
    # Reconciliação do saldo anterior de fatura: considera o que já existe,
    # inclui somente a diferença e repetir a confirmação não duplica a dívida.
    close();a.evaluate('pgCarteira()')
    card=a.evaluate("db.meios.find(m=>m.tipo==='cartao').id")
    invoice_key=card+'|2026-12-05'
    a.locator(f'[data-act="anexos"][data-id="{invoice_key}"]').click()
    a.locator('#ad-file').set_input_files(sample_pdf())
    expect(a.locator('[data-doc="upload"]')).to_be_visible()
    a.locator('[data-doc="upload"]').click()
    expect(a.locator('#ad-status')).to_contain_text('Arquivo anexado')
    if os.environ.get('LIVE_OCR')=='1':
        for repeat in range(2):
            if repeat:
                a.evaluate('pgCarteira()')
                a.locator(f'[data-act="anexos"][data-id="{invoice_key}"]').click()
            a.locator('[data-doc="read-existing"]').click()
            expect(a.locator('#ad-pamount')).to_have_value('R$ 150,00',timeout=120000)
            a.locator('#ad-pdue').fill('2026-12-05')
            a.locator('[data-doc="review"]').click()
            expect(a.locator('#ad-idiff')).to_contain_text('116,66')
            a.locator('[data-doc="invoice-save"]').click()
            expect(a.locator('#ad-icase')).to_have_count(0)
            a.wait_for_function("db.recs.some(r=>r.pgAbertura)")
            assert a.evaluate("db.recs.filter(r=>r.pgAbertura).length")==1
            assert a.evaluate("(card)=>pgFaturas(db).find(f=>f.id===card&&f.data==='2026-12-05').total",card)==15000
            a.wait_for_function('!N.dirty && !nvBusy')
        # O mesmo campo também funciona manualmente, sem executar leitura de arquivo.
        a.evaluate('pgCarteira()')
        a.locator(f'[data-act="anexos"][data-id="{invoice_key}"]').click()
        a.locator('#ad-amount').fill('15000')
        a.locator('[data-doc="invoice-manual"]').click()
        expect(a.locator('#ad-idiff')).to_contain_text('116,66')
        a.locator('[data-doc="invoice-save"]').click()
        expect(a.locator('#ad-icase')).to_have_count(0)
        assert a.evaluate("db.recs.filter(r=>r.pgAbertura).length")==1
        assert a.evaluate("(card)=>pgFaturas(db).find(f=>f.id===card&&f.data==='2026-12-05').total",card)==15000
        a.wait_for_function('!N.dirty && !nvBusy')
    listing()
    for width in (320,360,390):
        a.set_viewport_size({'width':width,'height':844})
        assert a.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert a.locator('.pn').evaluate('(el)=>el.scrollWidth <= el.clientWidth+1')
    a.screenshot(path=str(artifacts/'documentos-reembolsos-mobile.png'),full_page=True)
    # Fechar uma leitura cujo worker não iniciou não pode bloquear os documentos.
    if os.environ.get('LIVE_OCR')=='1':
        new();a.locator('#ad-file').set_input_files(sample)
        expect(a.locator('#ad-canvas')).to_be_visible()
        a.evaluate("window.testOriginalCreateWorker=Tesseract.createWorker;Tesseract.createWorker=()=>{window.testOcrInitHeld=true;return new Promise(()=>{})}")
        a.locator('[data-doc="read"]').click()
        a.wait_for_function('window.testOcrInitHeld === true')
        a.locator('#sheet [data-act="close"]').click()
        a.evaluate('Tesseract.createWorker=window.testOriginalCreateWorker')
        listing()
        expect(a.locator('#ad-fscope')).to_be_visible()
    # Cabeçalhos já recebidos não autorizam aplicar corpo antigo após logout.
    close()
    a.evaluate('''() => {window.testPreviousSession={...N};window.testOriginalFetch=window.fetch;window.fetch=async(...args)=>{const r=await window.testOriginalFetch(...args);if(String(args[0]).includes('/rest/v1/atlas_expense_cases')&&!window.testBodyHeld){window.testBodyHeld=true;const data=await r.json();r.json=()=>new Promise(resolve=>{window.testReleaseBody=()=>resolve(data)});}return r;}}''')
    a.locator('.top [data-act="documentos"]').click()
    a.wait_for_function("typeof window.testReleaseBody === 'function'")
    a.evaluate('nvSair();closeSheet();render();window.testReleaseBody()')
    expect(a.locator('#toast')).to_contain_text('Conta alterada',timeout=10000)
    assert a.locator('#ad-root').count()==0
    a.evaluate('window.fetch=window.testOriginalFetch;N=window.testPreviousSession;nvStore();render()')
    b.evaluate('closeSheet()')
    a.locator('nav [data-v="investimentos"]').click()
    return 'PASS: foto privada, OCR revisado, duplicação bloqueada, pessoal/corporativo, filtros, compartilhamento simulado e ZIP, reembolso, saldo anterior de fatura sem duplicação segunda sessão, cancelamento de OCR e corpo atrasado após logout (Storage/REST simulados)'
