"""Configure an existing, dedicated Hermes profile. Does not read or copy credentials."""
import argparse,json
from pathlib import Path
import yaml

def main():
    p=argparse.ArgumentParser();p.add_argument('--profile-dir',required=True);p.add_argument('--project-dir',required=True);p.add_argument('--pdf-python');p.add_argument('--pdf-renderer');p.add_argument('--input-root',action='append',default=[]);args=p.parse_args()
    profile=Path(args.profile_dir).expanduser().resolve();project=Path(args.project_dir).resolve()
    if profile.name!='career-decision' or not profile.is_dir():raise ValueError('Create the dedicated career-decision profile first.')
    config=profile/'config.yaml';existing=yaml.safe_load(config.read_text()) or {}
    if existing.get('plugins',{}).get('enabled'):raise ValueError('Refusing to replace an already configured plugin profile.')
    runtime={'project_dir':str(project),'python':str(project/'.venv/bin/python'),'evidence_path':str(project/'data/private/career-master.local.yaml'),'runs_dir':str(project/'data/private/hermes-runs'),'input_roots':[str(project),str(profile/'attachments'),*args.input_root],'confirmed_preferences':[],'max_context_chars':85000,'pdf_python':args.pdf_python,'pdf_renderer':args.pdf_renderer}
    target=project/'data/private/hermes-config.local.json';target.write_text(json.dumps(runtime,indent=2)+'\n')
    link=profile/'plugins/career-decision';link.parent.mkdir(exist_ok=True)
    if link.exists() or link.is_symlink():raise ValueError('Plugin destination already exists.')
    link.symlink_to(project/'plugins/career-decision',target_is_directory=True)
    settings={'model':{'default':'gpt-6.1-sol','provider':'openai-codex'},'agent':{'max_turns':24,'image_input_mode':'native','disabled_toolsets':['terminal','file','memory','skill_manage','delegate']},'toolsets':['career'],'platform_toolsets':{key:['career'] for key in ['cli','gui','api_server']},'plugins':{'enabled':['career-decision'],'entries':{'career-decision':{'settings':{'runtime_config':str(target)}}}},'memory':{'memory_enabled':False,'user_profile_enabled':False},'compression':{'enabled':False},'skills':{'auto_load':[]}}
    config.write_text(yaml.safe_dump(settings,sort_keys=False))
    (profile/'SOUL.md').write_text('Use concise, evidence-backed answers. Keep original source wording and distinguish facts, inferences, hypotheses and unknowns. Follow selected Career Skills.\n')
    print(json.dumps({'profile':str(profile),'runtime_config':str(target),'model':settings['model'],'skills_copied':0,'credentials_copied':0}))
if __name__=='__main__':main()
