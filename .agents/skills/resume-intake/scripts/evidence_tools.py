#!/usr/bin/env python3
"""Validate and read one source-backed Evidence document; no model calls or automatic fact approval."""
import argparse,json,re,sys
from pathlib import Path
from jsonschema import Draft202012Validator
import yaml,hashlib

def load(path):return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pointer(data,path):
    if not path.startswith('/'):raise ValueError('invalid pointer')
    for token in path[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~');data=data[int(token)] if isinstance(data,list) else data[token]
    return data

def leaves(value,path=''):
    if isinstance(value,dict):
        for k,v in value.items():yield from leaves(v,path+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from leaves(v,path+'/'+str(i))
    elif value is not None:yield path,value

def compact_intake(value):return re.sub(r'\s+','',str(value))
SCHEMA=Path(__file__).resolve().parents[1]/'schemas/evidence.schema.json'

def validate_evidence(d,source,raw,additional=None):
    errors=[f'master schema {list(e.absolute_path)}: {e.message}' for e in Draft202012Validator(json.loads(SCHEMA.read_text())).iter_errors(d)]
    if errors:return errors
    if source is None or raw is None:return ['actual source and frozen extraction are required for grounding']
    profile=d['profile'];primary=profile['source_ref'];inputs={primary:(source,raw)};inputs.update(additional or {});units={};origins={}
    for sid,src in d['sources'].items():
        if sid not in inputs:errors.append('missing grounding input for source '+sid);continue
        actual,extraction=inputs[sid]
        if file_hash(actual)!=src['sha256'] or extraction.get('source_sha256')!=src['sha256']:errors.append('actual source hash mismatch')
        if str(actual)!=src['path']:errors.append('actual source path mismatch')
        pages={p['page']:p['text'].splitlines() for p in extraction['pages']};coverage={p:[] for p in pages}
        if len(pages)!=src['page_count']:errors.append('source page count mismatch')
        for u in src['units']:
            uid=u['source_unit_id']
            if uid in units:errors.append('duplicate source coordinates across materials')
            units[uid]=u;origins[uid]=sid
            rows=pages.get(u['page'],[]);a=u['line_start'];z=u['line_end']
            if a>z or z>len(rows):errors.append('invalid source lines');continue
            exact='\n'.join(rows[a-1:z]);norm=''.join(rows[a-1:z]).removeprefix(' ')
            if u['exact_text']!=exact or u['normalized_text']!=norm:errors.append('immutable source unit changed')
            coverage[u['page']]+=list(range(a,z+1))
        for page,rows in coverage.items():
            if sorted(rows)!=list(range(1,len(pages[page])+1)):errors.append('source catalogue must cover every line once')
    if primary not in d['sources']:errors.append('Profile source missing')
    if errors:return errors
    fields=dict(leaves(profile['candidate'],'/candidate'));bindings=profile['field_bindings']
    if set(fields)!=set(bindings) or set(fields)!=set(profile['field_sources']):errors.append('Profile bindings must cover every non-null field exactly')
    for path,value in fields.items():
        b=bindings.get(path)
        if not b:continue
        sid=b['source_unit_id'];q=b['quote'];mode=b['transform'];u=units.get(sid)
        if not u or compact_intake(q) not in compact_intake(u['normalized_text']):errors.append('Profile quote absent from actual source');continue
        if profile['field_sources'].get(path)!=[sid]:errors.append('Profile binding/source disagreement')
        allowed='start_month' if path.endswith('/start_month') else 'end_month' if path.endswith('/end_month') else 'category' if path.endswith('/kind') else 'employer_ref' if path.endswith('/employer_ref') else 'literal'
        if mode!=allowed:errors.append('Profile field transform mismatch');continue
        if mode=='literal':
            if compact_intake(value)!=compact_intake(q):errors.append('Profile value changed beyond original')
            if path=='/candidate/display_name' and compact_intake(q)!=compact_intake(u['normalized_text']):errors.append('name must retain full original')
        elif mode in ('start_month','end_month'):
            dates=re.findall(r'(\d{4})年(\d{1,2})月',q)
            if len(dates)!=2:errors.append('date source requires two endpoints');continue
            y,m=dates[0 if mode=='start_month' else 1]
            if value!=f'{y}-{int(m):02}':errors.append('date disagrees with source')
        elif mode=='category':
            if value!=('learning_practice' if u['category']=='learning_practice' else 'skill_declaration'):errors.append('learning/skill kind changed')
        else:
            try:
                if pointer(profile,value)['employer']!=q or not re.fullmatch(r'/candidate/employment_history/\d+',value):errors.append('role employer pointer mismatch')
            except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid role employer reference')
    if profile['review_status']=='approved' and not profile['approval_ref']:errors.append('approved Profile requires specific confirmation')
    roles=profile['candidate']['professional_history'];role_headers=[]
    for i,r in enumerate(roles):
        try:
            e=pointer(profile,r['employer_ref']);h=units[profile['field_sources'][f'/candidate/professional_history/{i}/position'][0]]
            role_headers.append((h['page'],h['line_end'],i))
            if all(x is not None for x in (e['start_month'],r['start_month'],r['end_month'],e['end_month'])) and not e['start_month']<=r['start_month']<=r['end_month']<=e['end_month']:errors.append('role dates outside employment')
        except (KeyError,IndexError,ValueError,TypeError):errors.append('role header invalid')
    seen=[]
    for i,record in enumerate(d['evidence']):
        sid=record['source_unit_id'];seen.append(sid);u=units.get(sid)
        if not u or u['category']!='experience_bullet':errors.append('record must reference actual experience paragraph');continue
        prior=[h for h in role_headers if (h[0],h[1])<(u['page'],u['line_start'])]
        if origins[sid]==primary and (not prior or record['role_ref']!=f'/candidate/professional_history/{max(prior)[2]}'):errors.append('experience attributed to wrong role')
        try:pointer(profile,record['role_ref'])
        except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid experience role reference')
        if record['title'] not in u['normalized_text']:errors.append('record title must be supported by original')
        if record['review']['status']=='approved' and not record['review']['approval_ref']:errors.append('approved evidence requires specific fact approval')
        if record['evidence_id'] and not record['id_approval_ref']:errors.append('formal Evidence ID requires explicit ID approval')
        if record['responsibility_scope'] and record['responsibility_scope'] not in u['normalized_text']:errors.append('responsibility scope must be source-supported')
        known_cases={x['case_ref'] for x in d['cases']}
        if any(x not in known_cases for x in record['case_refs']):errors.append('unresolved case reference')
        for key,node in record['star'].items():
            if not node['statements'] and not node['metric_refs'] and not node['unknowns']:errors.append('missing STAR dimension must say Unknown')
            for quote in node['statements']:
                if quote not in u['normalized_text']:errors.append('STAR statement not supported by original experience')
                if key=='result' and any(m['status']=='target_threshold' and (m['quote'] in quote or quote in m['quote']) for m in record['metrics']):errors.append('release gate statement cannot become an achieved STAR result')
            for index in node['metric_refs']:
                if index>=len(record['metrics']):errors.append('invalid metric reference')
                elif key=='result' and record['metrics'][index]['status'] in ('target_threshold','reported_frequency','reported_lifecycle'):errors.append('target/process/lifecycle cannot become an achieved STAR result')
        covered=set();text=u['normalized_text']
        for metric in record['metrics']:
            q=metric['quote'];pos=text.find(q)
            if metric['source_unit_id']!=sid or pos<0 or metric['scope_quote'] not in text:errors.append('metric scope/quote/source disagreement');continue
            if metric['status']=='reported_lifecycle' or metric['frequency'] or metric['qualitative_before_after'] :covered.update(range(pos,pos+len(q)))
            for o in metric['observations']:
                oq=o['quote'];num=re.search(r'\d+(?:\.\d+)?',oq)
                if oq not in q or not num:errors.append('number quote unsupported');continue
                a=pos+q.index(oq);covered.update(range(a,a+len(oq)))
                value=float(num.group())*(100000000 if '亿' in oq else 1)
                op='>=' if '≥' in oq else '<=' if '内' in oq else 'approx' if '约' in oq else 'plus_unspecified' if '+' in oq else '='
                uq=o['unit_quote'];unit=compact_intake(uq)
                if o['value']!=value or o['operator']!=op or uq not in q or compact_intake(o['unit'])!=unit:errors.append('typed number/operator/unit changed')
                if op=='<=' and o['phase']!='deadline':errors.append('deadline upper bound lost')
                if o['phase'] in ('before','after') and (q.find('降至')<0 or (o['phase']=='before')!=(q.index(oq)<q.find('降至'))):errors.append('before/after reversed')
                if metric['status']=='target_threshold' and o['phase']!='target':errors.append('target phase changed')
            if metric['status']=='target_threshold' and any(o['phase']!='target' for o in metric['observations']):errors.append('threshold observations must remain target')
            if any(o['phase']=='target' for o in metric['observations']) and metric['status']!='target_threshold':errors.append('target phase cannot become achieved result')
            if re.search(r'为.{0,30}Gate|作为.{0,10}门槛|验收门槛',metric['scope_quote'],re.I) and metric['status']!='target_threshold':errors.append('quoted acceptance gate must remain threshold')
            if compact_intake(metric['scope_quote']) not in compact_intake(u['normalized_text']):errors.append('metric scope expanded beyond quoted source')
            if metric['qualitative_before_after'] and any(metric['qualitative_before_after'][k] not in q for k in ('before','after')):errors.append('qualitative comparison changed')
        for match in re.finditer(r'\d+(?:\.\d+)?',text):
            if not set(range(match.start(),match.end()))<=covered:errors.append('source number missing metric index')
    expected={sid for sid,u in units.items() if u['category']=='experience_bullet'}
    if set(seen)!=expected:errors.append('every source experience must be represented')
    ids=[e['evidence_id'] for e in d['evidence'] if e['evidence_id']]
    if len(ids)!=len(set(ids)):errors.append('duplicate formal Evidence ID')
    case_ids=[c['case_ref'] for c in d['cases']]
    if len(case_ids)!=len(set(case_ids)):errors.append('duplicate case reference')
    for case in d['cases']:
        if case['review_status']=='approved' and not case['approval_ref']:errors.append('approved case requires confirmation')
        for ref in case['evidence_refs']:
            try:row=pointer(d,ref)
            except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid case evidence reference');continue
            if not re.fullmatch(r'/evidence/\d+',ref):errors.append('case must cite an Evidence record')
        if any(x not in units for x in case['source_unit_ids']):errors.append('case cites unknown source unit')
        if case['additional_context'] and not any(case['additional_context'] in units[x]['normalized_text'] for x in case['source_unit_ids'] if x in units):errors.append('case background unsupported by original')
    return errors

def resolved(d):
    units={u['source_unit_id']:u for source in d['sources'].values() for u in source['units']};rows=[]
    for i,e in enumerate(d['evidence']):
        role=pointer(d['profile'],e['role_ref']);employer=pointer(d['profile'],role['employer_ref'])
        rows.append({**e,'record_ref':f'/evidence/{i}','employer':employer['employer'],'position':role['position'],'role_period':[role['start_month'],role['end_month']],'original':units[e['source_unit_id']]['normalized_text']})
    return {'evidence_hash':digest(d),'profile':d['profile']['candidate'],'evidence':rows,'cases':d['cases'],'limitations':d['limitations']}

def render(d):
    v=resolved(d);out=['# Evidence审核视图','',f'输入快照：`{v["evidence_hash"]}`','', '由同一Evidence文档生成；事实确认与结构检查分开。']
    for r in v['evidence']:
        out += ['',f'## {r["record_ref"]} — {r["title"]}', '',f'{r["employer"]} / {r["position"]} / {" – ".join(r["role_period"])}（任职区间）', '',f'确认状态：{r["review"]["status"]}；正式Evidence ID：{r["evidence_id"] or "未添加"}', '', '> '+r['original']]
        for key,label in [('situation','S 背景'),('task','T 任务／责任'),('action','A 行动'),('result','R 产出／结果')]:
            node=r['star'][key];out+=['',f'**{label}**','']+['- '+s for s in node['statements']]
            for j in node['metric_refs']:
                m=r['metrics'][j];out += [f'- {m["quote"]}（{m["status"]}；范围：{m["scope_quote"]}）']
            if not node['statements'] and not node['metric_refs']:out+=['- Unknown：材料未说明。']
            out+=['- 待核对：'+s for s in node['unknowns']]
    return '\n'.join(out)+'\n'

def schema_errors(value,name):
    base=Path(__file__).resolve().parents[2]
    location=base/('candidate-fit/schemas/match.schema.json' if name=='match' else 'resume-review/schemas/review.schema.json')
    return [e.message for e in Draft202012Validator(json.loads(location.read_text())).iter_errors(value)]

def evidence_ref(d,ref):
    if not re.fullmatch(r'/evidence/\d+',ref):raise ValueError('not an Evidence reference')
    return pointer(d,ref)

def validate_match(report,d,jd):
    errors=[e.message for e in Draft202012Validator(json.loads(SCHEMA.read_text())).iter_errors(d)]
    errors+=schema_errors(report,'match')
    if errors:return errors
    if report['evidence_hash']!=digest(d) or report['jd_hash']!=digest(jd):errors.append('match snapshot mismatch')
    items={x['jd_item_id']:x for x in jd['items'] if x['section'] in ('Responsibilities','Requirements','Preferred')}
    rows={x['jd_item_id']:x for x in report['matches']}
    if len(rows)!=len(report['matches']) or set(rows)!=set(items):errors.append('match must cover every actual JD capability/responsibility once')
    for row in report['matches']:
        if row['jd_item_id'] not in items or row['jd_text']!=items[row['jd_item_id']]['exact_text']:errors.append('JD quote mismatch')
        if row['classification'] in ('Strong','Transferable','Partial') and not row['evidence_refs']:errors.append('positive fit requires actual Evidence')
        if row['classification']=='Strong' and row['missing_dimensions']:errors.append('Strong cannot conceal missing dimensions')
        if row['classification']=='Gap' and not row['evidence_refs']:errors.append('Gap requires explicit supporting evidence; absence alone is Unknown')
        for ref in row['evidence_refs']:
            try:e=evidence_ref(d,ref)
            except (IndexError,KeyError,ValueError,TypeError):errors.append('unknown Evidence reference');continue
            if e['review']['status']=='retired':errors.append('retired Evidence cannot support current fit')
            if report['mode']=='Personal' and e['review']['status']!='approved':errors.append('Personal fit requires approved facts')
            if row['claim_status']=='Verified Fact' and e['review']['status']!='approved':errors.append('pending fact cannot become Verified Fact')
        if row['claim_status']!='Unknown' and not row['evidence_refs'] and row['classification'] not in ('Gap','Unknown'):errors.append('claim lacks personal source')
        if items.get(row['jd_item_id'],{}).get('uncertain') and row['classification']=='Strong':errors.append('uncertain JD cannot support Strong')
    for change in report['resume_changes']:
        if any(x not in rows for x in change['jd_item_ids']):errors.append('resume change cites absent JD requirement')
        for ref in change['evidence_refs']:
            try:e=evidence_ref(d,ref)
            except (IndexError,KeyError,ValueError,TypeError):errors.append('resume change cites unknown Evidence');continue
            if report['mode']=='Personal' and e['review']['status']!='approved':errors.append('formal wording requires approved facts')
        if change['proposed_text'] and not change['evidence_refs']:errors.append('new factual wording requires Evidence')
        if change['action']=='Need evidence' and change['proposed_text']:errors.append('Need evidence cannot generate an unsupported claim')
    if report['mode']=='Preliminary' and not report['limitations']:errors.append('Preliminary must disclose unconfirmed facts')
    return errors

def validate_review(report,d,resume,jd=None):
    errors=[e.message for e in Draft202012Validator(json.loads(SCHEMA.read_text())).iter_errors(d)]
    errors+=schema_errors(report,'review')
    if errors:return errors
    if report['evidence_hash']!=digest(d) or report['resume_hash']!=hashlib.sha256(resume.encode()).hexdigest() or report['jd_hash']!=(digest(jd) if jd else None):errors.append('review snapshot mismatch')
    lines={i:t for i,t in enumerate(resume.splitlines(),1) if t.strip()};rows={r['line']:r for r in report['lines']}
    if len(rows)!=len(report['lines']) or set(rows)!=set(lines):errors.append('review must cover every nonblank line once')
    for row in report['lines']:
        if lines.get(row['line'])!=row['text']:errors.append('review does not quote actual generated text')
        for ref in row['evidence_refs']:
            try:e=evidence_ref(d,ref)
            except (IndexError,KeyError,ValueError,TypeError):errors.append('review reference missing');continue
            if row['classification']=='Supported' and e['review']['status']!='approved':errors.append('Supported wording requires approved facts')
        for ref in row['profile_refs']:
            try:pointer(d,ref)
            except (KeyError,IndexError,ValueError,TypeError):errors.append('invalid Profile reference')
            if not ref.startswith('/profile/candidate/'):errors.append('Profile reference must cite personal field')
            if row['classification']=='Supported' and d['profile']['review_status']!='approved':errors.append('Profile facts require actual confirmation')
        if row['classification']=='Supported' and not (row['evidence_refs'] or row['profile_refs']):errors.append('Supported wording requires actual personal source')
        if row['classification']=='Revise' and report['verdict']!='Revise':errors.append('revision finding requires Revise')
    if report['verdict']=='Pass' and any(r['classification'] not in ('Supported','Not a claim') for r in report['lines']):errors.append('Pass cannot contain unsupported claims')
    if report['verdict']=='Pass' and report['mode']!='Personal':errors.append('Preliminary cannot formally Pass')
    if report['verdict']=='Pass' and report['scope']=='Full resume' and d['profile']['review_status']!='approved':errors.append('full resume Pass requires confirmed Profile/timeline')
    if jd is None and report['jd_alignment']!='Not assessed':errors.append('no JD means alignment not assessed')
    if jd is not None and report['jd_alignment']=='Addressed' and report['verdict']!='Pass':errors.append('unconfirmed draft cannot claim full JD alignment')
    return errors

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['check','view','render','match-check','review-check']);p.add_argument('data',type=Path);p.add_argument('--source',type=Path);p.add_argument('--material',action='append',nargs=3,metavar=('SOURCE_ID','FILE','RAW'));p.add_argument('--raw',type=Path);p.add_argument('--out',type=Path);p.add_argument('--report',type=Path);p.add_argument('--jd',type=Path);p.add_argument('--resume',type=Path);a=p.parse_args();d=load(a.data)
    if a.mode=='check':errors=validate_evidence(d,a.source,load(a.raw) if a.raw else None,{sid:(Path(file),load(raw)) for sid,file,raw in a.material or []})
    elif a.mode=='match-check':errors=validate_match(load(a.report),d,load(a.jd))
    elif a.mode=='review-check':errors=validate_review(load(a.report),d,a.resume.read_text(),load(a.jd) if a.jd else None)
    elif a.mode=='view':print(json.dumps(resolved(d),ensure_ascii=False,indent=2));return
    else:
        content=render(d)
        if a.out:a.out.write_text(content,encoding='utf-8')
        else:print(content)
        return
    for e in errors:print('FAIL:',e)
    if errors:sys.exit(1)
    print('PASS: structure, references and deterministic invariants; semantic quality and truth need review.')
if __name__=='__main__':main()
