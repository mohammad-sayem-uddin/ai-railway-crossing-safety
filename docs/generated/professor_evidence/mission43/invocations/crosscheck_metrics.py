"""Independent exact-count/ranking check on actual adopted-reference comparison inputs."""
from common import *
from fractions import Fraction
import csv,collections
with(D/'AUDIO_ADOPTED_EVENT_COMPARISONS.csv').open(newline='')as f:rows=list(csv.DictReader(f))
y=[int(x['adopted_event_horn_label'])for x in rows];scores=[float(x['maximum_window_score'])for x in rows];pred=[int(s>=.37)for s in scores];counts=collections.Counter(('TP'if p and t else'FP'if p else'FN'if t else'TN')for p,t in zip(pred,y));tp,fp,fn,tn=[counts[k]for k in ['TP','FP','FN','TN']];n=len(y)
def ratio(a,b):return float(Fraction(a,b))if b else None
positive=[s for s,t in zip(scores,y)if t];negative=[s for s,t in zip(scores,y)if not t]
roc=ratio(sum(2*(p>q)+(p==q)for p in positive for q in negative),2*len(positive)*len(negative))
ap=Fraction(0)
for score in sorted(set(scores),reverse=True):
 at=sum(s==score and t==1 for s,t in zip(scores,y));above=sum(s>=score and t==1 for s,t in zip(scores,y));total=sum(s>=score for s in scores)
 if at:ap+=Fraction(at,len(positive))*Fraction(above,total)
expected={'accuracy':ratio(tp+tn,n),'precision':ratio(tp,tp+fp),'recall':ratio(tp,tp+fn),'specificity':ratio(tn,tn+fp),'f1_score':ratio(2*tp,2*tp+fp+fn),'balanced_accuracy':(ratio(tp,tp+fn)+ratio(tn,tn+fp))/2 if(tp+fn)and(tn+fp)else None,'auc_roc':roc,'pr_auc':float(ap)if positive else None}
m=read(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json');assert m['confusion_matrix']=={'tp':tp,'fp':fp,'fn':fn,'tn':tn};assert m['actual_event_denominator']==n==23
for key,value in expected.items():assert m['rates'][key]==(round(value,4)if value is not None else None),(key,m['rates'][key],value)
save(D/'METRIC_CALCULATION_CROSSCHECK.json',{'schema':'mission43-actual-metric-crosscheck/1','valid':True,'actual_adopted_label_events':n,'confusion':dict(tp=tp,fp=fp,fn=fn,tn=tn),'independent_ranking_rates':expected,'reference_method':'Exact integer/Fraction counts; pairwise positive-negative ranking ROC-AUC with half-credit ties; tied-score grouped AP. No imported evaluator reused for reference computation.','reported_precision':'Original audio evaluator serializes rates to4decimals; all agree with independent exact-input calculations','metric_payload_sha256':sha(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json'),'input_table_sha256':sha(D/'AUDIO_ADOPTED_EVENT_COMPARISONS.csv'),'not_new_model_execution_or_independent_human_GT':True})
print('Actual23-event metric counts/rankings independently agree:',dict(counts),expected)
