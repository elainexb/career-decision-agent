"""Render validated support assessments. Counts are distributions, never scores."""
import hashlib
import json
from collections import Counter
from pathlib import Path

GROUPS = (
    ('direct', '直接优势', '同类经历对这项要求已有充分支持'),
    ('transfer', '可迁移路径', '直接支持不足，但有明确的迁移机制'),
    ('limited', '两侧支持有限', '已有相关证据，但覆盖和迁移仍有限'),
    ('unknown', '待核实', '不能把材料不足当作能力低'),
)
CONTEXT_LABELS = {'Directly related':'直接相关','Adjacent transferable':'相邻可迁移','Materially different':'差异明显','Unknown':'待核实','Execution contribution':'执行贡献','Delivery coordination':'交付协调','Domain owner':'领域负责人','Overall product or business owner':'整体产品或业务负责人','Mixed':'混合','Explicit yes':'明确有','Explicit no':'明确无'}
LEVELS = {'High': '高', 'Limited': '有限', 'Unknown': '待核实', 'Not assessed': '无需借助迁移'}
PRIORITIES = {'High Priority': '高优先投递', 'Selective': '选择性投递', 'Low Priority': '低优先', 'Insufficient Information': '信息不足'}


def group(row):
    direct = row['direct_support']['level']
    transfer = row['transfer_support']['level']
    if direct == 'High':
        return 'direct'
    if transfer == 'High':
        return 'transfer'
    if direct == transfer == 'Limited':
        return 'limited'
    return 'unknown'


def distribution(rows):
    total = len(rows)
    counts = Counter(group(row) for row in rows)
    return {'total': total, 'groups': [
        {'id': key, 'label': label, 'description': description, 'count': counts[key],
         'denominator': total, 'percentage': 100 * counts[key] / total if total else None}
        for key, label, description in GROUPS]}


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def evidence_proof(evidence, ref):
    index = int(ref.removeprefix('/evidence/'))
    item = evidence['evidence'][index]
    source = next(u for s in evidence['sources'].values() for u in s['units']
          if u['source_unit_id'] == item['source_unit_id'])
    role=evidence['profile']
    for part in item['role_ref'].strip('/').split('/'):
        role=role[int(part)] if isinstance(role,list) else role[part]
    return {'role':role['position'],'period':[role['start_month'],role['end_month']],'ref': ref, 'title': item['title'], 'scope': item['responsibility_scope'] or '待核实',
           'review': item['review']['status'], 'original': source['normalized_text'],
           'star': item['star'], 'metrics': item['metrics']}


def build_report(state, artifacts, evidence):
    analysis, fit, decision = (artifacts[key] for key in ('analysis', 'fit', 'decision'))
    requirements = {r['requirement_id']: r for r in analysis['requirements'] if r['kind'] == 'capability'}
    matches = {r['requirement_id']: r for r in fit['matches']}
    if len(matches) != len(fit['matches']) or set(matches) != set(requirements):
        raise ValueError('Report requires exact, unique capability coverage.')
    if fit['schema_version'] != 'requirement-match-0.3.0':
        raise ValueError('Independent support assessments are missing; do not infer them from legacy labels.')
    if fit['analysis_hash'] != digest(analysis) or fit['evidence_hash'] != digest(evidence):
        raise ValueError('Report input snapshots do not match.')
    if decision['fit_hash'] != digest(fit):
        raise ValueError('Decision does not bind the current fit.')
    rows = []
    for rid, requirement in requirements.items():
        row = matches[rid]
        if row['importance'] != requirement['importance'] or row['jd_text'] != requirement['jd_text']:
            raise ValueError('Report cannot alter importance or source wording.')
        refs = row['evidence_refs']
        proofs = []
        for ref in refs:
            proofs.append(evidence_proof(evidence, ref))
        rows.append({**row, 'label': requirement['interpretation'], 'group': group(row),
                     'jd_item_ids': requirement['jd_item_ids'], 'proofs': proofs})
    included = [r for r in rows if r['importance'] in ('Critical', 'Important')]
    critical = [r for r in rows if r['importance'] == 'Critical']
    secondary = [r for r in rows if r['importance'] not in ('Critical', 'Important')]
    return {'title': artifacts['jd']['role_title'], 'company': artifacts['jd']['company'],
            'mode': fit['mode'], 'priority': PRIORITIES[decision['priority']], 'decision': decision,
            'rows': included, 'critical': critical, 'secondary': secondary,
            'role_context': analysis['role_context'], 'context_fit': fit['context_fit'],
            'context_sources': {i['jd_item_id']: i['exact_text'] for i in artifacts['jd']['items']},
            'context_proofs': {ref: evidence_proof(evidence,ref) for c in fit['context_fit'].values() for ref in c['evidence_refs']},
            'conditions': [r for r in analysis['requirements'] if r['kind'] == 'condition'],
            'overview': distribution(included), 'critical_overview': distribution(critical),
            'context_labels': CONTEXT_LABELS, 'resume_changes': fit['resume_changes'], 'groups': GROUPS, 'level_labels': LEVELS,
            'sources': state['inputs'], 'hashes': {'evidence': fit['evidence_hash'],
                                                'analysis': fit['analysis_hash'], 'fit': digest(fit)},
            'run_id': state['run_id'], 'claim_status': 'Supported Inference',
            'count_note': '按固定能力要求 ID 计数；未加权，待核实项目包含在分母。不是总匹配分数、工作量占比或录用概率。'}


def percent(value):
    return '不适用' if value is None else f'{value:.2f}'.rstrip('0').rstrip('.') + '%'


def markdown(report):
    def cell(text):
        return str(text).replace('|', '\\|').replace('\n', ' ')
    lines = [f'# {report["title"]} · 职位匹配', '',
             f'**投递优先级：{report["priority"]}**', '', report['decision']['rationale'], '',
             '个人事实仍待本人确认；以下是当前证据支持判断。' if report['mode'] == 'Preliminary' else '基于已批准事实的匹配推断。', '',
             '## 最重要的要求', '', '| 要求 | 直接支持 | 可迁移支持 | 下一步 |', '|---|---|---|---|']
    for r in report['critical']:
        lines.append('| ' + ' | '.join(cell(x) for x in [r['label'], LEVELS[r['direct_support']['level']],
                                                         LEVELS[r['transfer_support']['level']], r['next_check']]) + ' |')
    if not report['critical']:
        lines.append('| 未识别到 Critical；不代表没有关键门槛 | — | — | 核实要求重要性 |')
    lines += ['', '## 岗位画像与背景匹配', '', '| 维度 | 判断 | 依据与限制 |', '|---|---|---|']
    for name,label in [('industry','行业相似性'),('business_scenario','业务场景相似性')]:
        c=report['context_fit'][name];lines.append('| '+' | '.join(cell(x) for x in [label,CONTEXT_LABELS[c['classification']],c['rationale']])+' |')
    for name,label in [('work_nature','工作性质'),('people_management','是否带人')]:
        c=report['role_context'][name];lines.append('| '+' | '.join(cell(x) for x in [label,CONTEXT_LABELS[c['classification']],c['text']])+' |')
    lines += ['', f'## 重要要求分布 · {report["overview"]["total"]} 项', '',
              '| 类别 | 项数 | 占比 |', '|---|---:|---:|']
    for g in report['overview']['groups']:
        lines.append(f'| {g["label"]} | {g["count"]}/{g["denominator"]} | {percent(g["percentage"])} |')
    lines += ['', report['count_note'], '', '## 分类查看', '']
    for key, label, _ in GROUPS:
        lines += [f'### {label}', '', '| 要求 | 直接支持 | 可迁移支持 |', '|---|---|---|']
        rows = [r for r in report['rows'] if r['group'] == key]
        for r in rows:
            lines.append('| ' + ' | '.join(cell(x) for x in [r['label'], LEVELS[r['direct_support']['level']],
                                                             LEVELS[r['transfer_support']['level']]]) + ' |')
        if not rows:
            lines += ['| 当前没有此类要求 | — | — |']
        lines += ['']
    lines += ['## 简历调整', ''] + [f'- **{c["priority"]}**：{c["rationale"]}' for c in report['resume_changes']]
    lines += ['', '## 岗位条件与风险', '']
    lines += ['- '+r['interpretation'] for r in report['conditions']]
    lines += [f'- {r["dimension"]} · {r["level"]}：{r["assessment"]["text"]}' for r in report['decision']['risks']]
    lines += ['', '[打开可展开的完整报告](report.html)', '', '详细判断、JD 原文、真实经历、来源及限制均在 HTML 报告中。']
    return '\n'.join(lines) + '\n'


def render_report(folder, state, artifacts, evidence):
    report = build_report(state, artifacts, evidence)
    payload = json.dumps(report, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    template = Path(__file__).with_name('report.template.html').read_text()
    (Path(folder) / 'report.html').write_text(template.replace('__REPORT_DATA__', payload))
    (Path(folder) / 'report.md').write_text(markdown(report))
    return report
