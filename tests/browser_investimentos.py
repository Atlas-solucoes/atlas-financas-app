"""Interface em Chromium com duas sessões e backend REST em memória.
Não autentica nem grava no Supabase real. LIVE_CDI=1 permite apenas GET público ao BCB.
"""
import copy
import datetime
import json
import os
import re
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright, expect
from browser_pagamentos import exercise_wallet

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'test-results'
ARTIFACTS.mkdir(exist_ok=True)

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, *args):
        pass

def run():
    server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    remote = {'row': None}
    evidence = []
    def backend(route):
        req = route.request
        parsed = urlparse(req.url)
        if req.method == 'OPTIONS':
            route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'})
            return
        if parsed.path != '/rest/v1/app_state':
            route.fulfill(status=404, json={'message': 'Only app_state is mocked'})
            return
        headers = {'Access-Control-Allow-Origin': '*'}
        query = parse_qs(parsed.query)
        body = req.post_data_json if req.post_data else {}
        assert req.headers.get('authorization') == 'Bearer token-test-only'
        if req.method == 'GET':
            assert query['user_id'] == ['eq.' + UID]
            data = [remote['row']] if remote['row'] else []
        elif req.method == 'POST':
            assert body['user_id'] == UID
            assert remote['row'] is None
            remote['row'] = copy.deepcopy(body)
            data = [remote['row']]
        elif req.method == 'PATCH':
            assert query['user_id'] == ['eq.' + UID]
            if query.get('revision') == ['eq.' + str(remote['row']['revision'])]:
                remote['row'].update(copy.deepcopy(body))
                data = [remote['row']]
            else:
                data = []
        else:
            raise AssertionError('Unexpected write operation: ' + req.method)
        route.fulfill(status=200, json=data, headers=headers)

    UID = '00000000-0000-4000-8000-000000000001'
    session = {'uid': UID, 'tok': 'token-test-only', 'exp': 4102444800000}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        contexts = []
        try:
            for _ in range(2):
                ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
                # Toda chamada ao Supabase é interceptada. Nenhuma credencial real é carregada.
                ctx.route('https://*.supabase.co/**', backend)
                ctx.add_init_script("""if(!sessionStorage.getItem('test-seeded')){localStorage.setItem('atlas-financas-nuvem-v1',%s);sessionStorage.setItem('test-seeded','1')}""" % json.dumps(json.dumps(session)))
                contexts.append(ctx)
            a = contexts[0].new_page()
            b = contexts[1].new_page()
            errors = []
            a.on('pageerror', lambda e: errors.append(str(e)))
            b.on('pageerror', lambda e: errors.append(str(e)))
            # Primeiro aparelho cria documento fictício, antes de B baixar.
            a.goto(base + '/nuvem/', wait_until='domcontentloaded')
            a.wait_for_function('N.rev === 1 && !nvBusy')
            a.evaluate("""() => {db.onb=true;db.recs.push({id:'despesa-teste',t:'d',v:5000,data:todayStr(),desc:'Mercado teste',cat:'outros',st:'real',fixa:false});save();closeSheet();render()}""")
            a.wait_for_function('N.rev === 2 && !N.dirty && !nvBusy')
            b.goto(base + '/nuvem/', wait_until='domcontentloaded')
            b.wait_for_function("db.recs.some(x=>x.id==='despesa-teste') && !nvBusy")
            # Cadastro no iframe usa a bridge, não armazenamento isolado.
            a.locator('nav [data-v="investimentos"]').click()
            frame = a.frame_locator('iframe[title="Investimentos Atlas"]')
            frame.locator('#institution').fill('Banco de homologação')
            frame.locator('#amount').fill('1000')
            frame.locator('#save').click()
            a.wait_for_function('db.investimentos.length === 1 && !N.dirty && !nvBusy')
            a_id = a.evaluate('db.investimentos[0].id')
            assert a_id
            b.evaluate('nvSync()')
            b.wait_for_function('db.investimentos.length === 1 && !nvBusy')
            b.reload(wait_until='domcontentloaded')
            b.wait_for_function('db.investimentos.length === 1 && !nvBusy')
            assert b.evaluate('db.investimentos[0].id') == a_id
            assert b.evaluate('db.recs[0].v') == 5000
            evidence.append('PASS: UI → bridge → REST simulado → segundo navegador → recarga; lançamento preservado')
            evidence.append(exercise_wallet(a, b, ARTIFACTS))
            for width in (320, 360, 390):
                a.set_viewport_size({'width': width, 'height': 844})
                assert a.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert frame.locator('html').evaluate('(el)=>el.scrollWidth <= innerWidth')
            a.screenshot(path=str(ARTIFACTS / 'investimentos-mobile.png'), full_page=True)
            evidence.append('PASS: sem rolagem horizontal em 320/360/390 px (Chromium emulado)')
            if os.environ.get('LIVE_CDI') == '1':
                previous_live = frame.locator('#cdi').input_value()
                official = False
                for attempt in range(2):
                    frame.locator('#fetchCdi').click()
                    expect(frame.locator('#cdiStatus')).to_contain_text(re.compile('BCB/SGS 4389|Consulta indisponível'), timeout=20000)
                    if 'BCB/SGS 4389' in frame.locator('#cdiStatus').inner_text():
                        official = True
                        break
                if official:
                    evidence.append('PASS: consulta BCB real pelo navegador, incluindo CORS; ' + frame.locator('#cdiStatus').inner_text())
                else:
                    assert frame.locator('#cdi').input_value() == previous_live
                    evidence.append('EXTERNAL UNAVAILABLE: BCB real após duas tentativas; fallback manual preservou a taxa, sem inventar cotação')
            else:
                evidence.append('NOT RUN: CDI real (defina LIVE_CDI=1)')
            contexts[0].route('https://api.bcb.gov.br/**', lambda route: route.fulfill(status=200, json=[{'data': '23/10/2026', 'valor': '13.65'}], headers={'Access-Control-Allow-Origin': '*'}))
            frame.locator('#fetchCdi').click()
            expect(frame.locator('#cdiStatus')).to_contain_text('BCB/SGS 4389')
            assert frame.locator('#cdi').input_value() == '13.65'
            evidence.append('PASS: contrato BCB positivo com payload de teste identificado (rede simulada)')
            # Falha de API não pode zerar a taxa já escolhida.
            contexts[0].route('https://api.bcb.gov.br/**', lambda route: route.fulfill(status=503, body='indisponível', headers={'Access-Control-Allow-Origin': '*'}))
            previous_rate = frame.locator('#cdi').input_value()
            frame.locator('#fetchCdi').click()
            expect(frame.locator('#cdiStatus')).to_contain_text('Consulta indisponível')
            assert frame.locator('#cdi').input_value() == previous_rate
            evidence.append('PASS: falha na API preserva taxa da simulação')
            # Offline: SW serve HTML/iframe/manifest previamente armazenados.
            a.evaluate('navigator.serviceWorker.ready.then(()=>true)')
            a.reload(wait_until='domcontentloaded')
            a.wait_for_function('navigator.serviceWorker.controller !== null')
            contexts[0].set_offline(True)
            a.reload(wait_until='domcontentloaded')
            a.locator('nav [data-v="investimentos"]').click()
            expect(a.frame_locator('iframe').locator('#institution')).to_be_visible()
            evidence.append('PASS: PWA abre app e investimentos offline após instalação do SW')
            contexts[0].set_offline(False)
            assert not errors, errors
            evidence.append('PASS: zero exceções JavaScript não tratadas')
            if os.environ.get('PUBLIC_SITE'):
                published = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
                contexts.append(published)
                # Perfil novo, sem login; bloquear Supabase impede qualquer acesso a contas reais.
                published.route('https://*.supabase.co/**', lambda route: route.abort())
                live = published.new_page()
                live.goto(os.environ['PUBLIC_SITE'], wait_until='domcontentloaded')
                assert 'Atlas' in live.title()
                assert live.evaluate('document.documentElement.scrollWidth <= innerWidth')
                live.screenshot(path=str(ARTIFACTS / 'pagina-publicada-mobile.png'), full_page=True)
                evidence.append('PASS: endereço publicado responde e cabe em 390 px; perfil novo sem acesso ao Supabase real')

        finally:
            for ctx in contexts:
                ctx.close()
            browser.close()
            server.shutdown()
            report = {'date': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'Chromium emulado; Supabase simulado, nenhum dado real', 'results': evidence}
            (ARTIFACTS / 'browser-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
            print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    run()
