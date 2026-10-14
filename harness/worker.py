"""Deterministic Career run storage and validation. No model calls or Evidence writes."""
import argparse,copy,fcntl,hashlib,importlib.util,json,re,subprocess,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
import yaml
from jsonschema import Draft202012Validator

SKILLS=('resume-intake','jd-extract','jd-analyze','evidence-maintain','case-maintain','candidate-fit','career-decision','resume-tailor','resume-review')
CONTRACTS={'jd':'career-decision/schemas/jd.schema.json','analysis':'jd-analyze/schemas/analysis.schema.json','fit':'candidate-fit/schemas/requirement-match.schema.json','decision':'career-decision/schemas/decision.schema.json','proposal':'evidence-maintain/schemas/proposal.schema.json','candidate_evidence':'resume-intake/schemas/evidence.schema.json','review':'resume-review/schemas/review.schema.json'}
MODULE={'jd':'jd-extract','analysis':'jd-analyze','fit':'candidate-fit','decision':'career-decision','proposal':'evidence-maintain','candidate_evidence':'resume-intake','draft':'resume-tailor','review':'resume-review'}
DEPENDENCIES={'analysis':['jd'],'fit':['jd','analysis'],'decision':['jd','analysis','fit']}
INTENTS={'jd':['jd','analysis','fit','decision'],'maintain':['proposal'],'intake':['candidate_evidence'],'review':['review'],'tailor':['jd','analysis','fit','decision','draft','review']}
def digest(x):return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')

class Runs:
    def __init__(self,config):
        self.cfg=config;self.project=Path(config['project_dir']).resolve();self.skills=self.project/'.agents/skills';self.home=Path(config['runs_dir']).resolve();self.home.mkdir(parents=True,exist_ok=True)
        spec=importlib.util.spec_from_file_location('career_evidence_tools',self.skills/'resume-intake/scripts/evidence_tools.py');self.e=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.e)
    def allowed(self,p):
        p=Path(p).expanduser().resolve()
        if any(x in p.parts for x in ('.codex','.ssh','.aws')) or ('.hermes' in p.parts and 'attachments' not in p.parts):raise ValueError('Private runtime or credential paths are not task inputs.')
        if not any(p.is_relative_to(Path(r).resolve()) for r in self.cfg['input_roots']):raise ValueError('Input outside configured roots.')
        if not p.is_file() or p.stat().st_size>20_000_000:raise ValueError('Input missing or over 20 MB.')
        return p
    def rules(self):
        paths=sorted(self.skills.rglob('*.md'))+sorted(self.skills.rglob('*.json'))+sorted(self.skills.rglob('*.py'))+[self.project/'harness/worker.py',self.project/'harness/report.py',self.project/'harness/report.template.html',self.project/'harness/CONTRACT.md',self.project/'plugins/career-decision/__init__.py']
        return {str(p.relative_to(self.project)):filehash(p) for p in paths if '__pycache__' not in p.parts}
    def prepare(self,intent,input_paths,options,identity):
        if intent not in INTENTS:raise ValueError('Unknown intent.')
        if not identity.get('session_id'):raise ValueError('A host session identity is required.')
        if not isinstance(options,dict) or set(options)-{'preferences','company_research','scope','jd_source_ids'}:raise ValueError('Unknown options.')
        if options.get('company_research','deferred')!='deferred':raise ValueError('Online research is not enabled in this profile. Use a research-capable host and supply dated sources.')
        prefs=options.get('preferences',self.cfg.get('confirmed_preferences',[]))
        if prefs!=self.cfg.get('confirmed_preferences',[]):raise ValueError('Preferences must match read-only caller-confirmed configuration; the Agent cannot create constraints.')
        if not isinstance(prefs,list) or any(not isinstance(p,dict) or set(p)!={'text','hard','condition_ids'} or type(p['hard']) is not bool or not isinstance(p['condition_ids'],list) or any(not isinstance(i,str) for i in p['condition_ids']) or not isinstance(p['text'],str) for p in prefs):raise ValueError('Preferences require text, hard boolean and condition_ids (explicit rejected conditions).')
        ep=Path(self.cfg['evidence_path']).resolve();data=yaml.safe_load(ep.read_text()) if ep.is_file() else None;errors=list(Draft202012Validator(read(self.skills/CONTRACTS['candidate_evidence'])).iter_errors(data)) if data is not None else ([] if intent=='intake' else ['Current Evidence is missing.'])
        if errors:raise ValueError('Current Evidence is invalid: '+str(getattr(errors[0],'message',errors[0])))
        if not input_paths:raise ValueError('Provide actual input files.')
        paths=[self.allowed(p) for p in input_paths]
        selected=options.get('jd_source_ids',[f'input_{i}' for i in range(len(paths))])
        if not isinstance(selected,list) or not selected or set(selected)-{f'input_{i}' for i in range(len(paths))}:raise ValueError('Invalid JD input source selection.')
        rid=uuid.uuid4().hex;folder=self.home/rid;folder.mkdir()
        write(folder/'evidence.snapshot.json',data)
        inputs=[]
        for i,p in enumerate(paths):
            saved=folder/f'input-{i}{p.suffix.lower()}';saved.write_bytes(p.read_bytes());entry={'source_id':f'input_{i}','path':str(p),'snapshot':str(saved),'sha256':filehash(p),'kind':p.suffix.lower()};inputs.append(entry)
            if p.suffix.lower()=='.pdf':
                py=self.cfg.get('pdf_python');renderer=self.cfg.get('pdf_renderer')
                if not py or not renderer:raise ValueError('PDF reader and renderer are not configured; provide text/images.')
                code="from pypdf import PdfReader;import json,sys; r=PdfReader(sys.argv[1]); print(json.dumps([p.extract_text() or '' for p in r.pages],ensure_ascii=False))"
                result=subprocess.run([py,'-c',code,str(saved)],capture_output=True,text=True,timeout=40,check=True);pages=json.loads(result.stdout)
                if len(pages)>10:raise ValueError('PDF exceeds this POC limit of 10 pages.')
                write(folder/f'pdf-{i}.text.json',pages);entry['pages_text']=str(folder/f'pdf-{i}.text.json')
                subprocess.run([renderer,'-scale-to','1800','-png',str(saved),str(folder/f'pdf-{i}')],capture_output=True,timeout=40,check=True)
                entry['page_images']=[str(x) for x in sorted(folder.glob(f'pdf-{i}-*.png'),key=lambda x:int(x.stem.rsplit('-',1)[1]))]
        state={'run_id':rid,'intent':intent,'identity':identity,'prepared_at':datetime.now(timezone.utc).isoformat(),'evidence_path':str(ep),'evidence_file_hash':filehash(ep) if ep.is_file() else None,'evidence_hash':digest(data),'snapshot_hash':filehash(folder/'evidence.snapshot.json'),'inputs':inputs,'rules':self.rules(),'config_hash':digest(self.cfg),'options':{'preferences':prefs,'company_research':'deferred','scope':options.get('scope','Excerpt'),'jd_source_ids':options.get('jd_source_ids',[x['source_id'] for x in inputs])},'delivered_skills':[],'artifacts':{},'submissions':[],'status':'prepared'}
        write(folder/'run.json',state);return {'run_id':rid,'status':'prepared','evidence_hash':state['evidence_hash'],'next_action':'Read relevant Skills and context using career_get_context.'}
    def open(self,run_id,identity):
        if not re.fullmatch('[0-9a-f]{32}',run_id):raise ValueError('Invalid run_id.')
        folder=self.home/run_id;state=read(folder/'run.json')
        if not identity.get('session_id') or state['identity'].get('session_id')!=identity.get('session_id'):raise ValueError('Run belongs to another session.')
        if (filehash(state['evidence_path']) if Path(state['evidence_path']).is_file() else None)!=state['evidence_file_hash'] or filehash(folder/'evidence.snapshot.json')!=state['snapshot_hash']:raise ValueError('Evidence changed; prepare a new run.')
        if digest(self.cfg)!=state['config_hash']:raise ValueError('Runtime configuration changed; prepare a new run.')
        if self.rules()!=state['rules']:raise ValueError('Skill or harness rules changed; prepare a new run.')
        for src in state['inputs']:
            if filehash(src['path'])!=src['sha256'] or filehash(src['snapshot'])!=src['sha256']:raise ValueError('Source changed; prepare a new run.')
        for a in state['artifacts'].values():
            if filehash(a['path'])!=a['sha256']:raise ValueError('Saved artifact changed.')
        return folder,state
    def context(self,run_id,skills,identity):
        folder,state=self.open(run_id,identity)
        if not isinstance(skills,list) or not skills or set(skills)-set(SKILLS):raise ValueError('Select valid Skills.')
        resources={}
        def include(p):
            p=p.resolve()
            if not p.is_relative_to(self.skills) or p.suffix!='.md':return
            key=str(p.relative_to(self.skills))
            if key in resources:return
            resources[key]=p.read_text()
            if p.suffix=='.md':
                for link in re.findall(r'\]\(([^)]+)\)',resources[key]):
                    target=p.parent/link
                    if target.is_file():include(target)
        for n in skills:include(self.skills/n/'SKILL.md')
        contracts={k:read(self.skills/v) for k,v in CONTRACTS.items() if MODULE[k] in skills or k=='proposal' and 'case-maintain' in skills}
        inputs=[];images=[]
        for src in state['inputs']:
            x={k:v for k,v in src.items() if k not in ('snapshot','page_images','pages_text')}
            if src['kind'] in ('.jpg','.jpeg','.png','.webp'):
                if set(skills)&{'jd-extract','resume-intake','evidence-maintain','case-maintain'}:images.append(src['snapshot'])
                x['content']='Source pixels attached when an input-reading Skill is selected.'
            elif src['kind']=='.pdf':
                if set(skills)&{'resume-intake','evidence-maintain','case-maintain','jd-extract'}:x['pages']=read(src['pages_text']);images+=src['page_images']
            else:x['content']=Path(src['snapshot']).read_text()
            inputs.append(x)
        data=read(folder/'evidence.snapshot.json')
        evidence_context=data
        if data is not None and set(skills)&{'candidate-fit','resume-tailor','resume-review'} and not set(skills)&{'resume-intake','evidence-maintain','case-maintain'}:
            view=self.e.resolved(data)
            evidence_context={'view':'Resolved contributions from the canonical snapshot; not a second fact library.','schema_version':data['schema_version'],'revision':data['revision'],'profile':data['profile'],'sources':{k:{f:v for f,v in x.items() if f!='units'} for k,x in data['sources'].items()},'evidence':view['evidence'],'cases':data['cases'],'limitations':data['limitations']}
        needed=set()
        for name in skills:
            needed.update({'jd-analyze':['jd'],'candidate-fit':['jd','analysis'],'career-decision':['jd','analysis','fit'],'resume-tailor':['jd','analysis','fit','decision','draft'],'resume-review':['jd','analysis','fit','draft']}.get(name,[]))
        context={'run_id':run_id,'intent':state['intent'],'options':state['options'],'inputs':inputs,'evidence_hash':state['evidence_hash'],'evidence':evidence_context if set(skills)&{'candidate-fit','resume-intake','evidence-maintain','case-maintain','resume-tailor','resume-review'} else None,'instructions':resources,'contracts':contracts,'artifacts':{k:read(v['path']) for k,v in state['artifacts'].items() if k in needed},'hashes':{**{k:v['digest'] for k,v in state['artifacts'].items()},'preferences':digest(state['options']['preferences'])},'pipeline_contract':(self.project/'harness/CONTRACT.md').read_text()}
        text=json.dumps(context,ensure_ascii=False)
        if len(text)>min(self.cfg.get('max_context_chars',85000),85000):raise ValueError('Context exceeds configured limit; no truncated analysis is permitted.')
        state['delivered_skills']=sorted(set(state['delivered_skills'])|set(skills));state['status']='context_returned';write(folder/'run.json',state)
        return {'context':context,'images':images,'context_complete':True}
    def schema(self,key,value):return [e.message for e in Draft202012Validator(read(self.skills/CONTRACTS[key])).iter_errors(value)]
    def validate(self,key,value,all,data,state):
        errors=self.schema(key,value) if key in CONTRACTS else []
        if errors:return errors
        jd=all.get('jd');analysis=all.get('analysis');fit=all.get('fit')
        if key in ('analysis','fit','decision') and value['jd_hash']!=digest(jd):errors.append('JD snapshot mismatch.')
        if key in ('fit','decision') and value['analysis_hash']!=digest(analysis):errors.append('Analysis snapshot mismatch.')
        if key in ('fit','decision','proposal') and value['evidence_hash']!=digest(data):errors.append('Evidence snapshot mismatch.')
        if key=='jd':
            ids=[r['jd_item_id'] for r in value['items']];sources={x['source_id']:x for x in state['inputs'] if x['source_id'] in state['options']['jd_source_ids']}
            if len(ids)!=len(set(ids)):errors.append('Duplicate JD item IDs.')
            declared={x['source_id']:x for x in value['images']}
            if set(declared)!=set(sources):errors.append('JD must reference all actual inputs.')
            for sid,x in declared.items():
                if sid in sources and x['path']!=sources[sid]['path']:errors.append('JD source path mismatch.')
            for row in value['items']:
                if set(row['source_ids'])-set(sources):errors.append('JD cites unknown source.')
                if any(declared.get(s,{}).get('readability')=='Unreadable' for s in row['source_ids']) and not row['uncertain']:errors.append('Unreadable source cannot support certain wording.')
        if key=='analysis':
            items={r['jd_item_id']:r for r in jd['items']};ids=[r['requirement_id'] for r in value['requirements']];covered=set()
            if len(ids)!=len(set(ids)):errors.append('Duplicate requirement IDs.')
            for r in value['requirements']:
                covered.update(r['jd_item_ids'])
                if set(r['jd_item_ids'])-set(items):errors.append('Requirement cites absent JD item.');continue
                if r['jd_text']!='\n'.join(items[x]['exact_text'] for x in r['jd_item_ids']):errors.append('Requirement must retain complete original quotes.')
            required={r['jd_item_id'] for r in jd['items'] if r['section'] in ('Responsibilities','Requirements','Preferred','Employment','Compensation')}
            if not required<=covered:errors.append('Analysis omitted JD requirements or conditions.')
            for c in [value['mission'],*value['hiring_hypotheses']]:
                if set(c['refs'])-set(items):errors.append('Mission/hypothesis cites absent item.')
                if c['status']=='Verified Fact' and c in value['hiring_hypotheses']:errors.append('Hiring motives need explicit evidence, not a hypothesis marked fact.')
            context=value['role_context']
            for claim in context.values():
                if set(claim['refs'])-set(items):errors.append('Role context cites absent JD item.')
                if claim['status'] not in ('Unknown','Hypothesis') and not claim['refs']:errors.append('Known role context needs JD evidence.')
            nature=context['work_nature'];management=context['people_management']
            for claim in (nature,management):
                if (claim['classification']=='Unknown')!=(claim['status']=='Unknown'):errors.append('Role classification and certainty must agree.')
            if nature['classification']!='Unknown':
                if nature['status']=='Hypothesis':errors.append('Known work nature needs supported duties.')
                if not any(items[x]['section'] not in ('Role','Company') for x in nature['refs'] if x in items):errors.append('Title alone cannot establish work nature.')
            if nature['classification'] in ('Domain owner','Overall product or business owner'):
                if any(context[x]['status'] in ('Unknown','Hypothesis') or not context[x]['refs'] for x in ('decision_rights','accountability')):errors.append('Owner type requires decision rights and accountability.')
            if nature['classification'] in ('Domain owner','Overall product or business owner'):
                for name in ('decision_rights','accountability'):
                    if not any(items[x]['section'] not in ('Role','Company') for x in context[name]['refs'] if x in items):errors.append('Title alone cannot establish owner authority or accountability.')
            if management['classification']!='Unknown':
                if management['status']!='Verified Fact':errors.append('Explicit people management needs explicit posting evidence.')
                if not any(items[x]['section'] not in ('Role','Company') for x in management['refs'] if x in items):errors.append('Title alone cannot establish people management.')
        if key=='fit':
            valid_evidence={f'/evidence/{i}' for i in range(len(data['evidence']))}
            valid_items={r['jd_item_id'] for r in jd['items']}
            for name,c in value['context_fit'].items():
                if set(c['target_refs'])-valid_items or set(c['evidence_refs'])-valid_evidence:errors.append('Context comparison cites absent source.')
                unknown=c['classification']=='Unknown'
                if unknown!=(c['status']=='Unknown'):errors.append('Context class and certainty must agree.')
                if not unknown:
                    if c['status']=='Hypothesis':errors.append('A known context comparison cannot be hypothetical.')
                    if not c['target_refs'] or not c['evidence_refs']:errors.append('Known context comparison needs target and candidate evidence.')
                    if analysis['role_context'][name]['status'] in ('Unknown','Hypothesis'):errors.append('Unknown target context cannot establish known similarity.')
                if value['mode']=='Personal' and any(data['evidence'][int(ref.split('/')[-1])]['review']['status']!='approved' for ref in c['evidence_refs'] if ref in valid_evidence):errors.append('Personal context comparison needs approved Evidence.')
                if c['classification'] in ('Adjacent transferable','Materially different') and not c['differences']:errors.append('Context adaptation or difference must be explicit.')
            req={r['requirement_id']:r for r in analysis['requirements'] if r['kind']=='capability'}
            transformed=copy.deepcopy(value);transformed.pop('analysis_hash');transformed.pop('context_fit');transformed['schema_version']='evidence-match-0.1.0'
            virtual={'items':[]}
            items={r['jd_item_id']:r for r in jd['items']}
            for rid,r in req.items():virtual['items'].append({'jd_item_id':rid,'section':'Requirements','exact_text':r['jd_text'],'uncertain':any(items[x]['uncertain'] for x in r['jd_item_ids'])})
            for r in transformed['matches']:
                r.pop('direct_support',None);r.pop('transfer_support',None)
                r['jd_item_id']=r.pop('requirement_id');original=req.get(r['jd_item_id'])
                if original and (r['importance']!=original['importance'] or r['importance_reason']!=original['importance_reason']):errors.append('Fit changed authoritative requirement importance.')
                if r['claim_status']=='Verified Fact':errors.append('Fit classification must not be Verified Fact.')
            for c in transformed['resume_changes']:c['jd_item_ids']=c.pop('requirement_ids')
            transformed['jd_hash']=digest(virtual);errors+=self.e.validate_match(transformed,data,virtual)
            for r in value['matches']:
                direct=r['direct_support'];transfer=r['transfer_support']
                if (r['classification']=='Strong')!=(direct['level']=='High'):errors.append('Strong and High direct support must agree.')
                if r['classification']=='Transferable' and transfer['level']!='High':errors.append('Transferable requires High transfer support.')
                if transfer['level']=='High' and r['classification'] in ('Gap','Unknown'):errors.append('Unknown or Gap cannot claim a known High transfer route.')
                if transfer['level']=='Not assessed' and direct['level']!='High':errors.append('Transfer may be unassessed only when direct support is High.')
                if transfer['level']=='Not assessed' and (transfer['evidence_refs'] or transfer['mechanism']):errors.append('Unassessed transfer cannot claim sources or a mechanism.')
                for axis in (direct,transfer):
                    if axis['level'] in ('High','Limited') and not axis['evidence_refs']:errors.append('Known support needs concrete Evidence.')
                    if set(axis['evidence_refs'])-set(r['evidence_refs']):errors.append('Support cites Evidence absent from the match.')
                if transfer['level'] in ('High','Limited') and not transfer['mechanism'].strip():errors.append('Known transfer needs a concrete mechanism.')
                if transfer['level'] in ('High','Limited') and not transfer['limits']:errors.append('Known transfer must state scope or adaptation limits.')

        if key=='decision':
            if value['fit_hash']!=digest(fit) or value['preferences_hash']!=digest(state['options']['preferences']):errors.append('Decision input hash mismatch.')
            req={r['requirement_id']:r for r in analysis['requirements']};matches={r['requirement_id']:r for r in fit['matches']}
            gaps={rid for rid,r in matches.items() if r['importance']=='Critical' and r['classification']=='Gap'}
            if set(value['critical_gaps'])!=gaps:errors.append('Decision must retain every Critical Gap.')
            expected={(rid,i) for i,p in enumerate(state['options']['preferences']) if p['hard'] for rid in p['condition_ids'] if rid in req and req[rid]['kind']=='condition' and req[rid]['status']=='Verified Fact'}
            declared={(b['condition_id'],b['preference_index']) for b in value['hard_blockers']}
            unresolved={rid for p in state['options']['preferences'] if p['hard'] for rid in p['condition_ids'] if rid not in req or req[rid]['kind']!='condition' or req[rid]['status']!='Verified Fact'}
            if any(rid not in ' '.join(value['material_unknowns']) for rid in unresolved):errors.append('Unresolved preference condition bindings must be explicit material unknowns.')
            if len(declared)!=len(value['hard_blockers']):errors.append('Duplicate hard blockers.')
            if expected!=declared:errors.append('Decision omitted or invented a confirmed hard blocker.')
            for b in value['hard_blockers']:
                prefs=state['options']['preferences'];i=b['preference_index'];r=req.get(b['condition_id'])
                if not r or r['kind']!='condition' or r['status']!='Verified Fact' or i>=len(prefs) or not prefs[i]['hard'] or b['condition_id'] not in prefs[i]['condition_ids']:errors.append('Hard blocker needs explicit JD condition and caller-approved hard preference binding.')
            dims=[r['dimension'] for r in value['risks']]
            if set(dims)!={'Company','Employment','Ownership','Longevity'} or len(dims)!=4:errors.append('Exactly four distinct risk dimensions required.')
            valid=set(req)|{r['jd_item_id'] for r in jd['items']}|{f'/evidence/{i}' for i in range(len(data['evidence']))}
            for r in value['risks']:
                if set(r['assessment']['refs'])-valid:errors.append('Risk cites absent source.')
                if r['level']!='Unknown' and not r['assessment']['refs']:errors.append('Known risk needs evidence.')
                if r['dimension']=='Company' and r['level']!='Unknown':errors.append('Company research deferred: Company risk must remain Unknown.')
                if r['level']!='Unknown' and r['assessment']['status'] in ('Hypothesis','Unknown'):errors.append('Unverified risk cannot be a known classification.')
            if set(value['career_value']['assessment']['refs'])-valid:errors.append('Career value cites absent source.')
            priority=value['priority']
            if value['hard_blockers'] and priority!='Low Priority':errors.append('Confirmed hard blocker requires Low Priority.')
            elif not value['hard_blockers'] and value['material_unknowns'] and priority!='Insufficient Information':errors.append('Material unknown requires Insufficient Information.')
            elif not value['material_unknowns'] and gaps and priority!='Low Priority':errors.append('Critical Gap requires Low Priority.')
            if priority=='High Priority':
                critical=[x for x in fit['matches'] if x['importance']=='Critical']
                if not critical or any(x['classification'] not in ('Strong','Transferable') for x in critical) or not any(x['classification']=='Strong' for x in fit['matches']) or value['career_value']['classification']!='Expanded' or any(x['level']=='High' for x in value['risks']):errors.append('High Priority gates not met.')
            if fit['mode']=='Preliminary' and not any('pending' in x.lower() or 'unconfirmed' in x.lower() for x in value['limitations']):errors.append('Decision must disclose pending personal facts.')
        if key=='proposal':
            sources={x['source_id'] for x in state['inputs']}
            for change in value['changes']:
                if set(change['source_ids'])-sources:errors.append('Proposal cites absent new material.')
                for ref in change['target_refs']:
                    try:self.e.pointer(data,ref)
                    except Exception:errors.append('Proposal target does not exist.')
                    if not ref.startswith(('/evidence/','/cases/','/profile/')):errors.append('Invalid proposal target.')
                if change['operation'] in ('Merge','Split') and not change['target_refs']:errors.append('Structural proposal needs existing targets.')
        if key=='candidate_evidence':
            if any(e['review']['status']!='pending' or e['evidence_id'] is not None or e['id_approval_ref'] is not None or e['review']['approval_ref'] is not None for e in value['evidence']) or value['profile']['review_status']!='pending' or value['profile']['approval_ref'] is not None or any(c['review_status']!='pending' or c['approval_ref'] is not None for c in value['cases']):errors.append('Intake cannot approve facts or allocate formal IDs.')
            actual={x['sha256'] for x in state['inputs']}
            if any(s['sha256'] not in actual for s in value['sources'].values()):errors.append('Intake source hash not among actual inputs.')
        if key=='draft':
            if not isinstance(value,str) or not value.strip():errors.append('Draft must be actual nonempty resume text.')
        if key=='review':
            resume=all.get('draft')
            if resume is None:
                text_inputs=[x for x in state['inputs'] if x['kind']=='.txt']
                if len(text_inputs)!=1:errors.append('Review requires one actual text draft.');return errors
                resume=Path(text_inputs[0]['snapshot']).read_text()
            errors+=self.e.validate_review(value,data,resume,jd)
            if value['scope']!=state['options']['scope']:errors.append('Review scope differs from caller-selected scope.')
        return errors
    def submit(self,run_id,result_json,identity):
        folder,state=self.open(run_id,identity);index=len(state['submissions'])+1;raw=folder/f'submission-{index}.txt';raw.write_text(result_json)
        errors=[];accepted=[]
        try:
            incoming=json.loads(result_json)
            if not isinstance(incoming,dict) or not incoming or set(incoming)-set(MODULE):raise ValueError('Submit a nonempty object of supported artifact keys.')
            all={k:read(v['path']) for k,v in state['artifacts'].items()}
            for key,value in incoming.items():
                if MODULE[key] not in state['delivered_skills'] and not (key=='proposal' and 'case-maintain' in state['delivered_skills']):raise ValueError(f'Obtain {MODULE[key]} context before submission.')
                if key in all:raise ValueError('Accepted artifacts are immutable. Prepare a new run for revisions.')
                if any(d not in all and d not in incoming for d in DEPENDENCIES.get(key,[])):raise ValueError(f'{key} needs accepted dependencies.')
            data=read(folder/'evidence.snapshot.json')
            for key in MODULE:
                if key not in incoming:continue
                all[key]=incoming[key];found=self.validate(key,incoming[key],all,data,state)
                errors += [f'{key}: {e}' for e in found]
            if not errors:
                for key,value in incoming.items():
                    p=folder/f'{key}.json';write(p,value);state['artifacts'][key]={'path':str(p),'sha256':filehash(p),'digest':digest(value)};accepted.append(key)
        except Exception as exc:errors.append(str(exc))
        event={'attempt':index,'submission':str(raw),'errors':errors,'accepted':accepted};state['submissions'].append(event)
        state['status']='output_invalid' if errors else ('validated_pending_review' if set(INTENTS[state['intent']])<=set(state['artifacts']) else 'in_progress')
        write(folder/f'validation-{index}.json',event);write(folder/'run.json',state)
        if state['status']=='validated_pending_review':self.report(folder,state)
        return {'run_id':run_id,'status':state['status'],'accepted':accepted,'errors':errors,'artifact_paths':{k:v['path'] for k,v in state['artifacts'].items()},'next_action':'Inspect run before claiming completion.' if state['status']=='validated_pending_review' else 'Correct rejected output or submit remaining modules.'}
    def report(self,folder,state):
        artifacts={k:read(v['path']) for k,v in state['artifacts'].items()};lines=['# Career Decision','',f'Run: {state["run_id"]}', '', 'Status: validated_pending_review (structure checked; semantics and facts require review).','']
        if 'decision' in artifacts:
            d=artifacts['decision'];lines += [f'Application priority: **{d["priority"]}**','',d['rationale'],'','## Requirement fit','']
            for r in artifacts['fit']['matches']:lines += [f'- **{r["requirement_id"]} / {r["importance"]} / {r["classification"]}**: {r["jd_text"]}', f'  - {r["rationale"]}', f'  - Evidence: {", ".join(r["evidence_refs"]) or "Unknown"}; status: {r["claim_status"]}']
            lines += ['','## Resume adjustments','']
            for c in artifacts['fit']['resume_changes']:lines += [f'- {c["priority"]} / {c["action"]}: {c["rationale"]}',f'  - Evidence: {", ".join(c["evidence_refs"])}; requirements: {", ".join(c["requirement_ids"])}',f'  - Suggested text: {c["proposed_text"] or "None; evidence needed"}']
            lines += ['','## Risks','']+[f'- {r["dimension"]}: {r["level"]}. {r["assessment"]["text"]}' for r in d['risks']]
            lines += ['','## Career value','',d['career_value']['assessment']['text'],'','## Next checks','']+['- '+x for x in d['next_checks']]+['','## Limitations','']+['- '+x for x in d['limitations']]
        if 'proposal' in artifacts:lines+=['## Maintenance proposal','',artifacts['proposal']['summary'],'',json.dumps(artifacts['proposal']['changes'],ensure_ascii=False,indent=2)]
        if 'review' in artifacts:lines+=['## Resume review','',artifacts['review']['verdict'],'',json.dumps(artifacts['review'],ensure_ascii=False,indent=2)]
        if 'candidate_evidence' in artifacts:lines+=['Intake produced a pending candidate document. Canonical Evidence was not updated.']
        lines+=['','## Provenance','',f'Evidence hash: `{state["evidence_hash"]}`']+['- '+x['source_id']+': '+x['path']+' (SHA256 '+x['sha256']+')' for x in state['inputs']]
        (folder/'report.md').write_text('\n'.join(lines)+'\n')
        if 'decision' in artifacts:
            spec=importlib.util.spec_from_file_location('career_report',self.project/'harness/report.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.render_report(folder,state,artifacts,read(folder/'evidence.snapshot.json'))
    def inspect(self,run_id,identity):
        folder,state=self.open(run_id,identity)
        return {**state,'report_path':str(folder/'report.md') if (folder/'report.md').is_file() else None,'report_html_path':str(folder/'report.html') if (folder/'report.html').is_file() else None,'formal_evidence_updated':False,'semantic_acceptance':'pending'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--method',choices=['prepare','context','submit','inspect'],required=True);args=parser.parse_args()
    try:
        packet=json.loads(sys.stdin.read());engine=Runs(read(args.config))
        with (engine.home/'.worker.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX);result=getattr(engine,args.method)(**packet)
        print(json.dumps({'ok':True,'data':result},ensure_ascii=False))
    except Exception as exc:print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False))
if __name__=='__main__':main()
