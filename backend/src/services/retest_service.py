import csv,hashlib,io,json,logging
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from src.models import TrialNote,RetestRecord,RetestAnalysis
from src.services.run_service import get_run
from src.services.retest_analysis import paired_stats,MIN_PAIRS

ALGORITHM='paired-t-v1'
BOUNDS={'absorption':(0.,1.),'impact':(0.,1000.),'carbon':(0.,1000.),'price':(0.,10000.),'thickness':(0.,1000.)}

def get_note(db,id):
    item=db.get(TrialNote,id)
    if not item:raise HTTPException(404,'试样计划不存在')
    return item

def approved_note(db,id):
    item=get_note(db,id)
    if item.status!='approved':raise HTTPException(409,'仅已同意的试样计划可回传复测')
    return item

def list_records(db,note_id):
    get_note(db,note_id)
    return db.scalars(select(RetestRecord).where(RetestRecord.note_id==note_id).order_by(RetestRecord.id)).all()

def submit_retests(db,note_id,data,user):
    approved_note(db,note_id)
    accepted=supplemented=duplicates=0;conflicts=[]
    for row in data.rows:
        metric=row.metric.value
        existing=db.scalar(select(RetestRecord).where(RetestRecord.note_id==note_id,RetestRecord.metric==metric,RetestRecord.sample_code==row.sample_code))
        if existing:
            if existing.value==row.value and existing.unit==row.unit:duplicates+=1
            elif existing.value is None and row.value is not None:
                existing.value=row.value;existing.unit=row.unit;existing.batch=data.batch;existing.submitted_by=user.email;supplemented+=1
            else:conflicts.append({'sample_code':row.sample_code,'metric':metric,'reason':'同一试件已有不同的回传记录，不覆盖'})
            continue
        db.add(RetestRecord(note_id=note_id,metric=metric,sample_code=row.sample_code,value=row.value,unit=row.unit,batch=data.batch,submitted_by=user.email));accepted+=1
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'回传与并行提交冲突，请重新提交本批')
    return {'accepted':accepted,'supplemented':supplemented,'duplicates':duplicates,'conflicts':conflicts}

def records_fingerprint(note_id,records,run):
    payload={'algorithm':ALGORITHM,'note_id':note_id,'snapshot':(run.result or {}).get('fingerprint',''),'records':sorted((r.id,r.metric,r.sample_code,r.value,r.unit) for r in records)}
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def exclusion(r,reason):return {'record_id':r.id,'code':r.sample_code,'metric':r.metric,'reason':reason}

def create_analysis(db,note_id,user):
    note=approved_note(db,note_id)
    run=get_run(db,note.run_id)
    snap=run.snapshot or {}
    samples={s['code']:s for s in snap.get('samples',[])}
    criteria={c['code']:c for c in snap.get('criteria',[])}
    records=list_records(db,note_id)
    if not records:raise HTTPException(409,'还没有回传记录，无法生成配对分析')
    fp=records_fingerprint(note_id,records,run)
    latest=db.scalar(select(RetestAnalysis).where(RetestAnalysis.note_id==note_id).order_by(RetestAnalysis.version.desc()).limit(1))
    if latest and latest.detail.get('records_fingerprint')==fp:raise HTTPException(409,f'第{latest.version}版已覆盖当前全部回传，补测后再生成新版本')
    pairs=[];exclusions=[]
    for r in records:
        sample=samples.get(r.sample_code)
        if not sample:exclusions.append(exclusion(r,'试件不在冻结候选快照'));continue
        expected=criteria.get(r.metric,{}).get('unit')
        if expected is not None and r.unit!=expected:exclusions.append(exclusion(r,f'单位不符：口径要求 {expected}，回传 {r.unit}'));continue
        if r.value is None:exclusions.append(exclusion(r,'缺测：回传行未给出测量值'));continue
        lo,hi=BOUNDS[r.metric]
        if not lo<=r.value<=hi:exclusions.append(exclusion(r,f'数值超出口径范围 [{lo:g}, {hi:g}]'));continue
        pairs.append({'record_id':r.id,'code':r.sample_code,'metric':r.metric,'pre':sample[r.metric],'post':r.value,'delta':r.value-sample[r.metric]})
    metrics={}
    for code in sorted({p['metric'] for p in pairs}):
        crit=criteria.get(code,{})
        metrics[code]={'unit':crit.get('unit',''),'direction':crit.get('direction','benefit'),**paired_stats([p['delta'] for p in pairs if p['metric']==code],crit.get('direction','benefit'))}
    headline='absorption' if 'absorption' in metrics else (sorted(metrics)[0] if metrics else None)
    detail={'algorithm':ALGORITHM,'min_pairs':MIN_PAIRS,'snapshot_fingerprint':(run.result or {}).get('fingerprint',''),'record_count':len(records),'records_fingerprint':fp,'headline_metric':headline,'conclusion':metrics[headline]['conclusion'] if headline else 'insufficient','metrics':metrics,'pairs':pairs,'exclusions':exclusions}
    item=RetestAnalysis(note_id=note_id,version=(latest.version+1) if latest else 1,created_by=user.email,detail=detail)
    db.add(item);db.commit()
    try:
        Path('/artifacts').mkdir(exist_ok=True)
        Path(f'/artifacts/retest-analysis-{item.id}.json').write_text(json.dumps(detail,ensure_ascii=False,allow_nan=False))
    except Exception:logging.exception('retest analysis artifact write failed')
    return item

def list_analyses(db,note_id):
    get_note(db,note_id)
    return db.scalars(select(RetestAnalysis).where(RetestAnalysis.note_id==note_id).order_by(RetestAnalysis.version.desc())).all()

def get_analysis(db,note_id,version):
    item=db.scalar(select(RetestAnalysis).where(RetestAnalysis.note_id==note_id,RetestAnalysis.version==version))
    if not item:raise HTTPException(404,'分析版本不存在')
    return item

def export_analysis(db,note_id,version):
    item=get_analysis(db,note_id,version);note=get_note(db,note_id);d=item.detail;out=io.StringIO();w=csv.writer(out)
    w.writerow(['retest_analysis','note','version','created_by','created_at','algorithm','min_pairs','records_fingerprint'])
    w.writerow([item.id,note.name,item.version,item.created_by,item.created_at.isoformat(),d['algorithm'],d['min_pairs'],d['records_fingerprint']])
    w.writerow(['scope','同一试件处理前后配对；平均变化与95%配对t不确定范围；配对不足或区间跨0不作改善/衰减结论；不是采购建议，原权衡与审批不变'])
    w.writerow(['metric','direction','unit','pairs','mean_delta','std','se','t_crit','ci_low','ci_high','conclusion'])
    for code,m in d['metrics'].items():w.writerow([code,m['direction'],m['unit'],m['pairs'],m['mean_delta'],m['std'],m['se'],m['t_crit'],m['ci_low'],m['ci_high'],m['conclusion']])
    w.writerow(['pair','record_id','code','metric','pre','post','delta'])
    for p in d['pairs']:w.writerow(['pair',p['record_id'],p['code'],p['metric'],p['pre'],p['post'],p['delta']])
    w.writerow(['exclusion','record_id','code','metric','reason'])
    for e in d['exclusions']:w.writerow(['exclusion',e['record_id'],e['code'],e['metric'],e['reason']])
    return '\ufeff'+out.getvalue()
