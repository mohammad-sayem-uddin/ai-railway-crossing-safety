"""Figures from actual saved full-cohort tables; no images/raw media or fabricated GT."""
from common import *
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from railway_detection.audio.evaluation import compute_roc_curve,compute_pr_curve
F=D/'figures';F.mkdir(exist_ok=True);plots=[]
def load(name):
 with(D/name).open(newline='')as f:return list(csv.DictReader(f))
def label(event):
 cohort,n=event.split('/');return('T'if cohort=='train_events'else'N'if cohort=='no_train_events'else'E')+n[-3:]
def savefig(fig,name,inputs):
 fig.savefig(F/name,dpi=160,bbox_inches='tight');plt.close(fig);plots.append({'figure':str((F/name).relative_to(R)),'sha256':sha(F/name),'input_tables':{p:sha(D/p)for p in inputs},'scope':'Actual model outputs or explicitly scoped adopted-label comparison; not safety/independent human GT'})
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
r=read(D/'ACTUAL_FULL_COHORT_RESULTS.json');coverage=load('FULL_27_EVENT_COVERAGE_MATRIX.csv');visual=load('VISUAL_PER_EVENT_RESULTS.csv');audio=load('AUDIO_PER_EVENT_RESULTS.csv');inputs=load('B2_INPUT_COVERAGE.csv')
fig,ax=plt.subplots(figsize=(7,4));bars=ax.bar(['Train events','No-train controls','Engine-only'],[23,3,1],color=['#306d96','#ab6c35','#68477d']);ax.bar_label(bars);ax.set_ylabel('Physical events');ax.set_title('Full cohort:27 physical events /54 camera members');ax.set_ylim(0,26);fig.tight_layout();savefig(fig,'DATASET_DISTRIBUTION.png',['FULL_27_EVENT_COVERAGE_MATRIX.csv'])
events=list(INV);yy=np.arange(len(events));fig,ax=plt.subplots(figsize=(11,10))
for role,delta,color in [('front',-.18,'#267c86'),('back',.18,'#c17c38')]:
 by={x['event']:x for x in visual if x['camera']==role};vals=[int(by[e]['predicted_objects'])if e in by else np.nan for e in events];ax.barh(yy+delta,vals,height=.35,label=role,color=color)
ax.set_yticks(yy,[label(e)for e in events]);ax.invert_yaxis();ax.set_xlabel('Predicted objects summed across sampled frames');ax.set_title('Independent camera model outputs by event; not correctness');ax.legend();fig.text(.02,.01,'T=train, N=designated control, E=engine. Repeated objects are not unique trains; cameras are not extra physical events.',fontsize=9);fig.tight_layout(rect=(0,.035,1,1));savefig(fig,'VISUAL_OBJECTS_PER_EVENT.png',['VISUAL_PER_EVENT_RESULTS.csv'])
fig,ax=plt.subplots(figsize=(13,5));by={x['event']:x for x in audio};colors=[];vals=[]
for e in events:
 x=by.get(e,{});vals.append(float(x['maximum_window_score'])if x else np.nan);colors.append('#307c79'if x.get('adopted_event_horn_label')=='1'else'#b47837'if x.get('adopted_event_horn_label')=='0'else'#888888')
ax.bar([label(e)for e in events],vals,color=colors);ax.axhline(.37,color='#793749',linestyle='--',label='Frozen 0.37 threshold');ax.set_ylim(0,1.06);ax.set_ylabel('Maximum score across existing windows');ax.set_title('Front audio outputs and adopted event-label categories');ax.tick_params(axis='x',rotation=65);ax.legend();fig.text(.02,.01,'Green=adopted horn present; amber=absent_observed; gray=null. Engine separate. Colors are adopted event labels, not window truth.',fontsize=9);fig.tight_layout(rect=(0,.07,1,1));savefig(fig,'AUDIO_MAX_SCORES_BY_EVENT.png',['AUDIO_PER_EVENT_RESULTS.csv'])
fig,ax=plt.subplots(figsize=(13,5));by={x['event']:x for x in inputs};present=[int(by[e]['both_stream_record_frames'])if e in by else 0 for e in events];missing=[int(by[e]['no_audio_record_frames'])if e in by else 0 for e in events];ax.bar([label(e)for e in events],present,label='Both stream records',color='#307c79');ax.bar([label(e)for e in events],missing,bottom=present,label='No audio record in input window',color='#b47837');ax.tick_params(axis='x',rotation=65);ax.set_ylabel('Existing input frames');ax.set_title('B2 input-stage coverage; decision replay not executed');ax.legend();fig.text(.02,.01,'Input collector window 0.25s differs from replay 0.5s. Missing records are not negative predictions or decision failures.',fontsize=9);fig.tight_layout(rect=(0,.07,1,1));savefig(fig,'B2_INPUT_RECORD_COVERAGE.png',['B2_INPUT_COVERAGE.csv'])
comparison=load('AUDIO_ADOPTED_EVENT_COMPARISONS.csv');y=np.array([int(x['adopted_event_horn_label'])for x in comparison]);score=np.array([float(x['maximum_window_score'])for x in comparison]);m=read(D/'AUDIO_ADOPTED_EVENT_LABEL_METRICS.json');cm=m['confusion_matrix'];matrix=np.array([[cm['tn'],cm['fp']],[cm['fn'],cm['tp']]])
fig,ax=plt.subplots(figsize=(6,5));image=ax.imshow(matrix,cmap='Blues');ax.set_xticks([0,1],['No horn','Horn']);ax.set_yticks([0,1],['Absent observed','Present']);ax.set_xlabel('Max-window model prediction at 0.37');ax.set_ylabel('Researcher-adopted AI-assisted event label');ax.set_title(f'Exploratory event-label agreement\nN={len(y)} train events',fontsize=11,pad=12);fig.colorbar(image,ax=ax,label='Physical event count')
for i in range(2):
 for j in range(2):ax.text(j,i,str(matrix[i,j]),ha='center',va='center',fontsize=18,color='white'if matrix[i,j]>matrix.max()/2 else'black')
fig.text(.02,.005,'Engine/control excluded; not independent human GT or localized window correctness.',fontsize=8);fig.tight_layout(rect=(0,.04,1,1));savefig(fig,'AUDIO_ADOPTED_EVENT_CONFUSION.png',['AUDIO_ADOPTED_EVENT_COMPARISONS.csv'])
if len(set(y))==2:
 fpr,tpr,thresholds,auc=compute_roc_curve(y,score);precision,recall,prthresholds,ap=compute_pr_curve(y,score)
 for name,xv,yv,xlabel,ylabel,title in [('AUDIO_ADOPTED_EVENT_ROC.png',fpr,tpr,'False-positive fraction vs adopted event labels','True-positive fraction vs adopted event labels',f'Exploratory event-label ROC: AUC={auc:.4f}'),('AUDIO_ADOPTED_EVENT_PR.png',recall,precision,'Recall vs adopted event labels','Precision vs adopted event labels',f'Exploratory event-label PR: AP={ap:.4f}')]:
  fig,ax=plt.subplots(figsize=(6,5));ax.plot(xv,yv,color='#307c79',marker='o',markersize=3);ax.set(xlim=(0,1.02),ylim=(0,1.02),xlabel=xlabel,ylabel=ylabel,title=title);fig.text(.02,.005,f'N={len(y)} physical train events. Max-window score; engine separate; no independent human GT claim.',fontsize=8);fig.tight_layout(rect=(0,.04,1,1));savefig(fig,name,['AUDIO_ADOPTED_EVENT_COMPARISONS.csv'])
 figdata={'ROC':{'fpr':fpr.tolist(),'tpr':tpr.tolist(),'thresholds':thresholds.tolist(),'auc':float(auc)},'PR':{'precision':precision.tolist(),'recall':recall.tolist(),'thresholds':prthresholds.tolist(),'AP':float(ap)},'sample_unit':'Physical train event','N':len(y)};save(D/'AUDIO_EVENT_CURVE_DATA.json',figdata)
conf=load('VISUAL_CONFIDENCE_VALUES.csv');fig,ax=plt.subplots(figsize=(9,4))
for role,color in [('front','#267c86'),('back','#c17c38')]:
 values=[float(x['confidence'])for x in conf if x['camera']==role];ax.hist(values,bins=np.linspace(.35,1,14),histtype='step',linewidth=2,label=f'{role}: {len(values)} object outputs',color=color)
ax.set(xlabel='Model confidence (not correctness probability)',ylabel='Correlated object outputs',title='Confidence distribution across saved visual predictions');ax.legend();fig.tight_layout();savefig(fig,'VISUAL_CONFIDENCE_DISTRIBUTION.png',['VISUAL_CONFIDENCE_VALUES.csv'])
fig,axs=plt.subplots(3,1,figsize=(13,9),sharex=True)
for ax,role,color in zip(axs,['front','back','audio'],['#267c86','#c17c38','#68477d']):
 by={x['event']:x for x in(audio if role=='audio'else visual)if role=='audio'or x['camera']==role};ax.bar([label(e)for e in events],[float(by[e]['original_pipeline_wall_s'])if e in by else np.nan for e in events],color=color);ax.set_ylabel(role+' wall seconds')
axs[0].set_title('Recorded per-member pipeline time; stages have different work boundaries');axs[-1].tick_params(axis='x',rotation=65);fig.text(.02,.005,'Mixture of reused M39 and new M43 timings; initialization/system load differ. No real-time, cross-modal speed or hardware acceptance claim.',fontsize=9);fig.tight_layout(rect=(0,.04,1,1));savefig(fig,'ORIGINAL_PROCESSING_TIME.png',['VISUAL_PER_EVENT_RESULTS.csv','AUDIO_PER_EVENT_RESULTS.csv'])
save(D/'FIGURE_PROVENANCE.json',{'schema':'mission43-actual-result-figure-provenance/1','plotting_script_sha256':sha(__file__),'figures':plots,'raw_media_or_images_opened':False,'significance_or_CI_invented':False});print('Created',len(plots),'figures from actual saved outputs/tables.')
