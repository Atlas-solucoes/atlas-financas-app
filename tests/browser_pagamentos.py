"""Exercita carteira pelos formulários reais, sem contas/produção."""
from playwright.sync_api import expect

def exercise_wallet(a, b, artifacts):
    def close():
        a.evaluate('closeSheet()')
    def wallet():
        close()
        a.locator('.top [data-act="pg-carteira"]').click()
    def create(kind, name, cents):
        wallet()
        a.locator('[data-act="pg-novo"]').click()
        a.locator('#pg-tipo').select_option(kind)
        a.locator('#pg-nome').fill(name)
        if kind == 'cartao':
            a.locator('#pg-limite').fill(cents)
            a.locator('#pg-fecha').fill('20')
            a.locator('#pg-vence').fill('5')
            a.locator('#pg-banco').select_option(ids['b1'])
        else:
            a.locator('#pg-saldo').fill(cents)
        a.locator('[data-act="pg-salvar"]').click()
        expect(a.locator('#sheet')).to_contain_text(name)
        return a.evaluate('(name)=>db.meios.find(m=>m.nome===name).id', name)
    ids = {}
    ids['b1'] = create('banco', 'Banco primeiro', '100000')
    ids['b2'] = create('banco', 'Banco segundo', '50000')
    ids['va'] = create('va', 'Meu VA', '60000')
    ids['vr'] = create('vr', 'Meu VR', '40000')
    ids['cc'] = create('cartao', 'Meu crédito', '200000')
    a.locator('#pg-somar').check()
    a.locator('button[data-act="pg-somar"]').click()
    assert a.evaluate('budget(db,todayStr()).saldo') == 150000
    # Uma quinzena em cada banco; previstas ainda não alteram o saldo.
    a.locator('button[data-act="rendas"]').click()
    a.locator('[data-act="ritem"][data-k="div"]').click()
    a.locator('#rnm').fill('Meu salário quinzenal')
    a.locator('#rpts .rpt').nth(0).locator('.rpd').fill('5')
    a.locator('#rpts .rpt').nth(0).locator('.rpv').fill('100000')
    a.locator('#rpts .rpt').nth(0).locator('.rpb').select_option(ids['b1'])
    a.locator('#rpts .rpt').nth(1).locator('.rpd').fill('20')
    a.locator('#rpts .rpt').nth(1).locator('.rpv').fill('120000')
    a.locator('#rpts .rpt').nth(1).locator('.rpb').select_option(ids['b2'])
    a.locator('[data-act="rsave"]').click()
    salary = a.evaluate("db.recs.filter(r=>r.desc.startsWith('Meu salário quinzenal')).map(r=>({id:r.id,st:r.st}))")
    assert len(salary) == 2 and all(r['st'] == 'prev' for r in salary)
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['b1']) == 100000
    a.locator(f'[data-act="edit"][data-id="{salary[0]["id"]}"]').click()
    a.locator('[data-act="est"][data-s="real"]').click()
    a.locator('[data-act="saveedit"]').click()
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['b1']) == 200000
    # Recarga mensal VA só soma após confirmação.
    wallet()
    a.locator('button[data-act="rendas"]').click()
    a.locator('[data-act="ritem"][data-k="benef"]').click()
    a.locator('#rmeio').select_option(ids['va'])
    a.locator('#rvm').fill('30000')
    a.locator('#rdm').fill('1')
    a.locator('[data-act="rsave"]').click()
    recarga = a.evaluate("db.recs.find(r=>r.desc==='Recarga de VA / VR').id")
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['va']) == 60000
    a.locator(f'[data-act="edit"][data-id="{recarga}"]').click()
    a.locator('[data-act="est"][data-s="real"]').click()
    a.locator('[data-act="saveedit"]').click()
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['va']) == 90000
    def expense(meio, category, cents, name, installments=None):
        close()
        a.locator('nav [data-v="hoje"]').click()
        a.locator('[data-act="add"]').click()
        a.locator('#qv').fill(cents)
        a.locator('#qd').fill(name)
        a.locator(f'#qcats [data-k="{category}"]').click()
        a.locator('#qmeio').select_option(meio)
        if installments:
            a.locator('#qnp').fill(str(installments))
            a.locator('#qdt').fill('2026-10-19')
        a.locator('[data-act="saveadd"]').click()
    expense(ids['va'], 'mercado', '10000', 'Mercado com VA')
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['va']) == 80000
    assert a.evaluate('budget(db,todayStr()).saldo') == 250000
    expense(ids['cc'], 'compras', '10001', 'Compra parcelada', 3)
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['cc']) == 189999
    wallet()
    a.locator('[data-act="pg-fatura"]').first.click()
    a.locator('#pg-fbanco').select_option(ids['b1'])
    a.locator('[data-act="pg-pagar"]').click()
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['b1']) == 196666
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['cc']) == 193333
    # Meta usa o saldo de VA; programado usa VR e só vira gasto ao confirmar.
    close()
    a.locator('nav [data-v="metas"]').click()
    a.locator('[data-act="novameta"]').first.click()
    a.locator('#mn').fill('Mercado do mês')
    a.locator('#ma').fill('30000')
    a.locator('#mm').fill('15000')
    a.locator('#mmeio').select_option(ids['va'])
    a.locator('#mpagcat').select_option('mercado')
    a.locator('[data-act="savemeta"]').click()
    assert a.evaluate("db.metas.find(m=>m.nome==='Mercado do mês').meioId") == ids['va']
    wallet()
    a.locator('[data-act="pg-planejar"]').click()
    a.locator('#pg-pnome').fill('Almoço planejado')
    a.locator('#pg-pvalor').fill('2000')
    a.locator('#pg-pcat').select_option('comida')
    a.locator('#pg-pmeio').select_option(ids['vr'])
    a.locator('[data-act="pg-programar"]').click()
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['vr']) == 40000
    a.locator('[data-act="progpago"]').click()
    assert a.evaluate('(id)=>pgSaldo(db,id)', ids['vr']) == 38000
    wallet()
    for width in (320, 360, 390):
        a.set_viewport_size({'width': width, 'height': 844})
        assert a.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert a.locator('.pn').evaluate('(el)=>el.scrollWidth <= el.clientWidth + 1')
    a.screenshot(path=str(artifacts / 'carteira-mobile.png'), full_page=True)
    close()
    a.wait_for_function('!N.dirty && !nvBusy')
    b.evaluate('nvSync()')
    b.wait_for_function('db.meios.length === 5 && !nvBusy')
    b.reload(wait_until='domcontentloaded')
    b.wait_for_function('db.meios.length === 5 && !nvBusy')
    assert b.evaluate('(id)=>pgSaldo(db,id)', ids['vr']) == 38000
    assert b.evaluate("db.recs.find(r=>r.id==='despesa-teste').v") == 5000
    a.locator('nav [data-v="investimentos"]').click()
    return 'PASS: carteira com bancos/VA/VR/crédito, salário em quinzenas, recarga mensal, fatura sem duplicação, planos e reload no segundo contexto'
