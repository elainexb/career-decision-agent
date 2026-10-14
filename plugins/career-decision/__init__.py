"""Hermes adapter: source Skills, bounded context, deterministic worker."""
import base64,json,mimetypes,subprocess
from pathlib import Path

TOOLS={
 'career_prepare_task':('Prepare actual inputs and a read-only Evidence snapshot.',{'intent':{'enum':['jd','intake','maintain','review','tailor']},'input_paths':{'type':'array','items':{'type':'string'},'minItems':1},'options':{'type':'object','description':'Optional preferences [{text,hard,condition_ids}], scope Excerpt/Full resume, company_research deferred, jd_source_ids for JD inputs when a resume is also supplied.'}},['intent','input_paths','options'],'prepare'),
 'career_get_context':('Read selected Skills, their references, contracts, actual inputs and current artifacts. Images go to the main model.',{'run_id':{'type':'string'},'skills':{'type':'array','items':{'type':'string'},'minItems':1}},['run_id','skills'],'context'),
 'career_submit_result':('Save original JSON and validate generated artifacts. Keys: jd, analysis, fit, decision, proposal, candidate_evidence, draft, review. Rejected attempts are retained; accepted artifacts are immutable.',{'run_id':{'type':'string'},'result_json':{'type':'string','description':'JSON text with artifact keys. No Markdown fences.'}},['run_id','result_json'],'submit'),
 'career_inspect_run':('Inspect actual status, failures and saved paths before reporting completion. Validation is not semantic or human acceptance.',{'run_id':{'type':'string'}},['run_id'],'inspect')}

def register(ctx):
    config_path=Path(ctx.get_config('runtime_config','')).expanduser().resolve()
    config=json.loads(config_path.read_text());project=Path(config['project_dir']);python=config['python']
    for entry in sorted((project/'.agents/skills').glob('*/SKILL.md')):
        text=entry.read_text();description=next((line.split(':',1)[1].strip() for line in text.splitlines() if line.startswith('description:')),entry.parent.name)
        ctx.register_skill(entry.parent.name,entry,description=description)
    ctx.register_system_prompt_section('career-decision-route',
        'Use Career tools for career tasks. Prepare actual inputs, then get context for Skills you select. '
        'Submit jd -> analysis -> fit -> decision for a JD task; reuse accepted artifacts. Maintenance is proposal-only. '
        'Read the delivered schemas and pipeline contract. Never write canonical Evidence or invent approval. '
        'Inspect the run before answering. A validated result still needs semantic review. '
        'Do not claim company research in this offline profile. No extra LLM client is needed.',max_chars=1200)
    for name,(description,properties,required,method) in TOOLS.items():
        def handler(args,_method=method,_required=required,**kwargs):
            try:
                if not isinstance(args,dict) or set(args)!=set(_required):raise ValueError('Supply exactly the required arguments.')
                packet={**args,'identity':{'session_id':kwargs.get('session_id'),'task_id':kwargs.get('task_id')}}
                call=subprocess.run([python,'-B',str(project/'harness/worker.py'),'--config',str(config_path),'--method',_method],input=json.dumps(packet),capture_output=True,text=True,timeout=100)
                if call.returncode:raise ValueError('Worker failed: '+call.stderr[-1500:])
                result=json.loads(call.stdout)
                if _method=='context' and result.get('ok'):
                    images=result['data'].pop('images',[])
                    if images:
                        content=[{'type':'text','text':json.dumps(result,ensure_ascii=False)}]
                        for path in images:
                            p=Path(path).resolve()
                            if not p.is_relative_to(Path(config['runs_dir']).resolve()):raise ValueError('Image outside run storage.')
                            content.append({'type':'image_url','image_url':{'url':'data:'+ (mimetypes.guess_type(p.name)[0] or 'image/png')+';base64,'+base64.b64encode(p.read_bytes()).decode()}})
                        return {'_multimodal':True,'content':content,'text_summary':'Full Career context and actual source pixels attached. Use main-model vision.'}
                return json.dumps(result,ensure_ascii=False)
            except Exception as exc:return json.dumps({'ok':False,'error':str(exc)})
        if ctx.register_tool(name=name,toolset='career',schema={'name':name,'description':description,'parameters':{'type':'object','properties':properties,'required':required,'additionalProperties':False}},handler=handler) is None:raise ValueError('Tool registration rejected: '+name)
