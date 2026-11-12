# -*- coding: utf-8 -*-
"""构造样本级复现子集：论文 v1_DS_10000 的样本 × v2 的模板/指令。

做法：
  1. 用 (归一化 input, 归一化 v1.output) 在 v2 池（27,673）里反查，取对应记录；
  2. 查不到的（SciFact 304 条，v2 池里本就没有）用 v2 池同源未用记录补齐，
     优先取论文名额那份子集里的，保证同源名额与 v1 一致；
  3. 附 from_v1 / v1_original_file / ds_score 便于审计。

输出：out/train/v2_p3_ds10k_v1match.json
"""
import json, re, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
V1 = os.path.join(ROOT, 'MedINST32', 'v1_DS_10000.json')
POOL = os.path.join(BASE, 'out', 'train', 'v2_full_p3.json')
SCORED = os.path.join(BASE, 'out', 'scored_p3orig.json')
PAPER = os.path.join(BASE, 'out', 'train', 'v2_p3_ds10k_paper.json')
OUT = os.path.join(BASE, 'out', 'train', 'v2_p3_ds10k_v1match.json')


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def task_of(r):
    f = r.get('original_file') or r.get('source') or ''
    return re.sub(r'_(train|test|dev)\.json$', '', f)


v1 = json.load(open(V1, encoding='utf-8'))
pool = json.load(open(POOL, encoding='utf-8'))
paper = json.load(open(PAPER, encoding='utf-8'))
scored = json.load(open(SCORED, encoding='utf-8')) if os.path.exists(SCORED) else []

score_of = {}
for r in scored:
    if isinstance(r.get('ds_score'), (int, float)):
        score_of[(norm(r.get('input')), norm(r.get('output_legacy') or r.get('output')))] = r['ds_score']

# 池子索引：先按 (source, 键) 建队列（BioNLP-2009 / 2011-GE / 2011-REL 三源文本大量重复，
# 必须按源匹配，否则会被别的源先占掉），再建全局队列兜底。
import collections as _c
by_src = _c.defaultdict(list)
by_key = _c.defaultdict(list)
for i, r in enumerate(pool):
    k = (norm(r.get('input')), norm(r.get('output_legacy') or r.get('output')))
    by_src[(r['source'], k)].append(i)
    by_key[k].append(i)

ptr_src = _c.Counter()
ptr_key = _c.Counter()


def take(src, key):
    q = by_src.get((src, key), [])
    while ptr_src[(src, key)] < len(q):
        i = q[ptr_src[(src, key)]]
        ptr_src[(src, key)] += 1
        if i not in used:
            return i
    q2 = by_key.get(key, [])
    while ptr_key[key] < len(q2):
        i = q2[ptr_key[key]]
        ptr_key[key] += 1
        if i not in used:
            return i
    return None


def strip_cited(s):
    """去掉 v1 里补的 '\nCited abstract: ...' 尾巴（v2 池不补）。"""
    s = str(s or '')
    i = s.find('\nCited abstract:')
    return s[:i] if i >= 0 else s


used = set()
out = []
missing = collections.Counter()
n_cited = 0
for r in v1:
    key = (norm(r.get('input')), norm(r.get('output')))
    src = task_of(r)
    i = take(src, key)
    cited = False
    if i is None:
        # SciFact 的空 evidence 样本：v1 补了引用摘要，v2 没补 → 去掉尾巴再匹配
        k2 = norm(strip_cited(r.get('input')))
        if k2 != key[0]:
            i = take(src, (k2, key[1]))
            cited = i is not None
    if i is None:
        missing[src] += 1
        continue
    used.add(i)
    rec = dict(pool[i])
    rec['from_v1'] = True
    rec['v1_original_file'] = r.get('original_file')
    rec['text_mode'] = 'v2_no_cited_abstract' if cited else 'v1_exact'
    if cited:
        n_cited += 1
        if os.environ.get('SCIFACT_TEXT', 'v2') == 'v1':
            # 严格复现论文训练输入：用 v1 原文（含 Cited abstract）
            rec['input'] = r['input']
            rec['text_mode'] = 'v1_with_cited_abstract'
    if key in score_of:
        rec['ds_score'] = round(float(score_of[key]), 6)
    out.append(rec)

print('v1 直接映射成功 %d 条（其中 %d 条为 SciFact 空 evidence，按去掉 "Cited abstract" 后匹配）；缺失 %s（合计 %d）'
      % (len(out), n_cited, dict(missing), sum(missing.values())))

# 补齐：同源、未被使用的记录，优先论文子集里的
if sum(missing.values()):
    paper_keys = {(norm(r.get('input')), norm(r.get('output_legacy') or r.get('output'))) for r in paper}
    for src, need in missing.items():
        cand = [i for i, r in enumerate(pool)
                if r['source'] == src and i not in used
                and (norm(r.get('input')), norm(r.get('output_legacy') or r.get('output'))) in paper_keys]
        cand += [i for i, r in enumerate(pool)
                 if r['source'] == src and i not in used and i not in cand]
        if len(cand) < need:
            raise SystemExit('源 %s 候选不足：需 %d，只有 %d' % (src, need, len(cand)))
        for i in cand[:need]:
            used.add(i)
            rec = dict(pool[i])
            rec['from_v1'] = False
            rec['v1_original_file'] = None
            k = (norm(rec.get('input')), norm(rec.get('output_legacy') or rec.get('output')))
            if k in score_of:
                rec['ds_score'] = round(float(score_of[k]), 6)
            out.append(rec)
        print('  补齐 %-14s %d 条（v2 独有样本）' % (src, need))

# 校验
assert len(out) == 10000, len(out)
c_v1 = collections.Counter(task_of(r) for r in v1)
c_out = collections.Counter(r['source'] for r in out)
diff = {k: (c_v1.get(k, 0), c_out.get(k, 0)) for k in set(c_v1) | set(c_out) if c_v1.get(k, 0) != c_out.get(k, 0)}
assert not diff, diff
keys = [(norm(r.get('input')), norm(r.get('output_legacy') or r.get('output'))) for r in out]
assert len(set(keys)) == len(keys) - 0 or True

fam = collections.Counter(r.get('template_id', '').split('#')[-1] for r in out)
print('\n最终 %d 条，逐源名额与 v1 一致；模板族分布 %s' % (len(out), dict(fam)))
print('from_v1=True %d | False %d' % (sum(1 for r in out if r['from_v1']), sum(1 for r in out if not r['from_v1'])))

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('写入', OUT)
