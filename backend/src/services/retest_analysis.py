"""同一试件前后配对的统计口径。

对每份试件取 delta = 复测值 - 冻结前值，给出平均变化与双侧95%配对t
不确定范围。t分位取自固定表；自由度落在表档之间时取较小档，宁可把
区间放宽也不收窄。配对数不足 MIN_PAIRS 时只报告描述量，不下改善或
衰减结论。
"""
import math,statistics
from src.constants.enums import RetestConclusion

MIN_PAIRS=3

_T_TABLE=[(1,12.706),(2,4.303),(3,3.182),(4,2.776),(5,2.571),(6,2.447),(7,2.365),(8,2.306),(9,2.262),(10,2.228),(11,2.201),(12,2.179),(13,2.160),(14,2.145),(15,2.131),(16,2.120),(17,2.110),(18,2.101),(19,2.093),(20,2.086),(21,2.080),(22,2.074),(23,2.069),(24,2.064),(25,2.060),(26,2.056),(27,2.052),(28,2.048),(29,2.045),(30,2.042),(40,2.021),(60,2.000),(120,1.980)]

def t_critical(df):
    if df<1:raise ValueError('自由度至少为1')
    value=1.960
    for d,t in _T_TABLE:
        if d<=df:value=t
    return value

def paired_stats(deltas,direction):
    n=len(deltas)
    out={'pairs':n,'mean_delta':None,'std':None,'se':None,'t_crit':None,'ci_low':None,'ci_high':None,'conclusion':RetestConclusion.INSUFFICIENT.value}
    if n>=1:out['mean_delta']=statistics.fmean(deltas)
    if n>=2:
        std=statistics.stdev(deltas);se=std/math.sqrt(n);t=t_critical(n-1)
        out.update(std=std,se=se,t_crit=t,ci_low=out['mean_delta']-t*se,ci_high=out['mean_delta']+t*se)
    if n>=MIN_PAIRS:
        lo,hi=out['ci_low'],out['ci_high']
        if lo>0:out['conclusion']=RetestConclusion.IMPROVED.value if direction=='benefit' else RetestConclusion.DECLINED.value
        elif hi<0:out['conclusion']=RetestConclusion.DECLINED.value if direction=='benefit' else RetestConclusion.IMPROVED.value
        else:out['conclusion']=RetestConclusion.INCONCLUSIVE.value
    return out
