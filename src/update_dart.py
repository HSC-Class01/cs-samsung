#!/usr/bin/env python3
"""OpenDART periodic-report collector. Requires DART_API_KEY environment variable."""
from __future__ import annotations
import json, os, time, zipfile
from datetime import date
from io import BytesIO
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'config.json').read_text(encoding='utf-8'))
OUT = ROOT/'docs'/'data'; REPORT_DIR = ROOT/'data'/'reports'
BASE = 'https://opendart.fss.or.kr/api'
KEY = os.environ.get('DART_API_KEY', '').strip()
HEADERS = {'User-Agent': 'dart-samsung-finance-dashboard/1.0'}
PERIODS = {'annual':'11011', 'half-year':'11012', 'quarterly':'11013'}

def api(path, **params):
    if not KEY: raise RuntimeError('DART_API_KEY is not set. Add it as a GitHub Actions secret.')
    r = requests.get(f'{BASE}/{path}', params={'crtfc_key':KEY, **params}, headers=HEADERS, timeout=60)
    r.raise_for_status(); payload=r.json()
    if payload.get('status') not in ('000','013'):
        raise RuntimeError(f"DART {path}: {payload.get('status')} {payload.get('message')}")
    return payload

def to_num(v):
    try: return int(str(v).replace(',','').strip())
    except (TypeError, ValueError): return None

def match(rows, candidates):
    # Prefer consolidated financial statements when both forms exist.
    for fs in ('CFS','OFS'):
        for c in candidates:
            for r in rows:
                if r.get('fs_div') == fs and r.get('account_nm') == c:
                    return to_num(r.get('thstrm_amount'))
    return None

def report_list(year):
    records=[]; page=1
    while True:
        p=api('list.json', corp_code=CFG['company']['corp_code'], bgn_de=f'{year}0101', end_de=f'{year}1231',
              pblntf_ty='A', page_no=page, page_count=100)
        records += p.get('list', [])
        if page >= int(p.get('total_page', 1)): break
        page += 1; time.sleep(.15)
    seen=set(); out=[]
    for r in records:
        name=r.get('report_nm','')
        category = 'annual' if '사업보고서' in name else ('half-year' if '반기보고서' in name else ('quarterly' if '분기보고서' in name else None))
        if category and r['rcept_no'] not in seen:
            seen.add(r['rcept_no']); out.append({'category':category,'year':year,'report_name':name,'receipt_no':r['rcept_no'],
             'filed_at':r.get('rcept_dt'), 'viewer_url':f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={r['rcept_no']}"})
    return out

def download_raw(r):
    # Disabled by default: report ZIPs can quickly make a Git repository too large.
    res=requests.get(f'{BASE}/document.xml',params={'crtfc_key':KEY,'rcept_no':r['receipt_no']},timeout=120)
    res.raise_for_status(); target=REPORT_DIR/f"{r['receipt_no']}.zip"; target.write_bytes(res.content)
    return str(target.relative_to(ROOT))

def main():
    OUT.mkdir(parents=True, exist_ok=True); REPORT_DIR.mkdir(parents=True, exist_ok=True)
    reports=[]; rows=[]
    for year in range(CFG['start_year'], date.today().year+1):
        found=report_list(year); reports += found
        for report in found:
            if CFG['download_raw_reports']: report['raw_archive']=download_raw(report)
            if year < CFG['financial_api_start_year']: continue
            all_rows=api('fnlttSinglAcntAll.json', corp_code=CFG['company']['corp_code'], bsns_year=year, reprt_code=PERIODS[report['category']], fs_div='CFS').get('list',[])
            values={k:match(all_rows, v) for k,v in CFG['metrics'].items()}
            if not any(v is not None for v in values.values()): continue
            assets, equity, liab=values['assets'],values['equity'],values['liabilities']; rev=values['revenue']; op=values['operating_income']; net=values['net_income']
            ratios={
              'operating_margin': (op/rev*100 if op is not None and rev else None), 'net_margin': (net/rev*100 if net is not None and rev else None),
              'roe': (net/equity*100 if net is not None and equity else None), 'debt_to_equity': (liab/equity*100 if liab is not None and equity else None),
              'current_ratio': (values['current_assets']/values['current_liabilities']*100 if values['current_assets'] is not None and values['current_liabilities'] else None),
              'roa': (net/assets*100 if net is not None and assets else None)}
            rows.append({'period':f"{year} {report['category']}", 'year':year,'category':report['category'], 'receipt_no':report['receipt_no'], **values, **ratios})
            time.sleep(.15)
    reports.sort(key=lambda x:(x['filed_at'] or '',x['receipt_no']), reverse=True)
    rows.sort(key=lambda x:(x['year'], x['category']))
    (OUT/'reports.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'financials.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'peer_firms.json').write_text(json.dumps(CFG['peer_firms'],ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Updated {len(reports)} reports and {len(rows)} financial rows.')
if __name__=='__main__': main()
