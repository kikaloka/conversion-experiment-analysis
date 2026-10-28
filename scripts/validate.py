"""Independent arithmetic and deliverable consistency checks."""
from pathlib import Path
import hashlib,json,re,math,zipfile,xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import nbformat
from scipy.stats import norm, binomtest
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'results'
checks=[]
def check(name,ok):
    checks.append({'check':name,'passed':bool(ok)})
def near(name,a,b,tol=1e-10): check(name,abs(a-b)<tol)
m=json.loads((out/'metrics.json').read_text())
d=pd.read_csv(ROOT/'data/original/ab_data.csv')
check('Source checksum',hashlib.sha256((ROOT/'data/original/ab_data.csv').read_bytes()).hexdigest()==m['sha256'])
check('Schema',list(d.columns)==['country','group','converted'])
check('No missing fields',not d.isna().any().any())
check('Country values',set(d.country)=={'CA','UK','US'})
check('Group values',set(d.group)=={'control','treatment'})
check('Binary outcomes',set(d.converted)=={0,1})
check('All rows retained',len(d)==m['source_rows']==m['analysis_rows']==69889)
a=pd.read_csv(out/'conversion_summary.csv').set_index('group')
c=pd.read_csv(out/'country_summary.csv'); reg=pd.read_csv(out/'regression_summary.csv')
for g in ['control','treatment']:
    sub=d[d.group==g]; n=len(sub); x=int(sub.converted.sum())
    check(g+' n',n==m[g+'_n']==a.loc[g,'n'])
    check(g+' conversions',x==m[g+'_conversions']==a.loc[g,'conversions'])
    near(g+' rate',x/n,m[g+'_rate']); near(g+' aggregate rate',x/n,a.loc[g,'rate'])
    check(g+' country n',c[c.group==g].n.sum()==n)
    check(g+' country conversions',c[c.group==g].conversions.sum()==x)
    near(g+' country shares',c[c.group==g].within_group_share.sum(),1)
for _,row in c.iterrows():
    sub=d[(d.country==row.country)&(d.group==row.group)]
    check(row.country+' '+row.group+' n',len(sub)==row.n)
    near(row.country+' '+row.group+' rate',sub.converted.mean(),row.rate)
n0,n1=m['control_n'],m['treatment_n']; x0,x1=m['control_conversions'],m['treatment_conversions']
allocation=m['allocation_diagnostic']
near('Conditional exact allocation diagnostic',binomtest(n1,n0+n1,p=.5,alternative='two-sided').pvalue,allocation['p_value'])
check('50:50 explicitly unestablished',allocation['assumed_treatment_probability']==.5 and allocation['assumption_established'] is False)
check('Conditional diagnostic retains all rows',m['analysis_rows']==n0+n1==m['source_rows'])
p0,p1=x0/n0,x1/n1; diff=p1-p0; pooled=(x0+x1)/(n0+n1)
z=diff/math.sqrt(pooled*(1-pooled)*(1/n0+1/n1)); pv=2*norm.sf(abs(z))
near('Manual difference',diff,m['risk_difference']); near('Manual relative lift',diff/p0,m['relative_lift'])
near('Manual z',z,m['z']); near('Manual log p',math.log(pv),math.log(m['p_value']),1e-8)
def wilson(x,n):
    z=norm.ppf(.975); p=x/n; den=1+z*z/n
    center=(p+z*z/(2*n))/den; half=z/den*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return center-half,center+half
l0,u0=wilson(x0,n0); l1,u1=wilson(x1,n1)
near('Independent Newcombe lower',diff-math.sqrt((p1-l1)**2+(u0-p0)**2),m['ci_low'])
near('Independent Newcombe upper',diff+math.sqrt((u1-p1)**2+(p0-l0)**2),m['ci_high'])
odds=(x1/(n1-x1))/(x0/(n0-x0)); se=math.sqrt(1/x1+1/(n1-x1)+1/x0+1/(n0-x0))
near('2x2 odds ratio vs logistic',odds,reg.iloc[0].odds_ratio)
near('Independent OR lower',math.exp(math.log(odds)-norm.ppf(.975)*se),reg.iloc[0].or_ci_low)
near('Independent OR upper',math.exp(math.log(odds)+norm.ppf(.975)*se),reg.iloc[0].or_ci_high)
check('Adjusted OR similar',abs(reg.iloc[1].odds_ratio-odds)<.001)
check('Standardized effect similar',abs(m['country_standardized_risk_difference']-diff)<.0001)
nb=nbformat.read(ROOT/'notebooks/conversion_experiment.ipynb',as_version=4)
cells=[c for c in nb.cells if c.cell_type=='code']
check('Four executed cells',len(cells)==4 and [c.execution_count for c in cells]==[1,2,3,4])
check('No notebook error outputs',all(o.output_type!='error' for c in cells for o in c.outputs))
for path in list(ROOT.glob('*.md'))+list((ROOT/'docs').glob('*.md')):
    for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        if not link.startswith(('http:','https:','#')):
            check('Link '+path.name+' -> '+link,(path.parent/link.split('#')[0]).exists())
for name in ['conversion','country','effect']:
    check('Chart '+name,(out/'charts'/f'{name}.png').stat().st_size>1000)
check('Notebook HTML exists',(out/'notebook-report.html').stat().st_size>10000)
check('Raw excluded by gitignore','data/original/*' in (ROOT/'.gitignore').read_text())
for name,size,blob in [('pptx',1876066,'23312f1c934a3a7ecef76033befd8f929fa3bbdb'),('pdf',344930,'039b1332c5132e91110235cb7cb4bd09258f477f')]:
    payload=(ROOT/'presentation'/f'ecommerce_ab_test_portfolio.{name}').read_bytes()
    check('Verified presentation size '+name,len(payload)==size)
    check('Verified presentation Git blob '+name,hashlib.sha1(f'blob {len(payload)}\0'.encode()+payload).hexdigest()==blob)
with zipfile.ZipFile(ROOT/'presentation/ecommerce_ab_test_portfolio.pptx') as deck:
    slides=[n for n in deck.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
    charts=[n for n in deck.namelist() if re.search(r'/charts/chart\d+\.xml$',n)]
    check('Seven presentation slides',len(slides)==7)
    check('Three native editable charts',len(charts)==3)
    text=' '.join(' '.join(ET.fromstring(deck.read(n)).itertext()) for n in slides)
    check('Deck conversion effect agrees','5.01' in text and '47.57' in text)
    check('Deck conditional allocation caveat','Intended allocation unknown' in text and '0.0442' in text)
result={'checks':len(checks),'passed':sum(x['passed'] for x in checks),'failed':[x['check'] for x in checks if not x['passed']],'details':checks,'limitations':['Slide visual inspection performed in parent creation workflow; local checks preserve exact verified bytes','HTML browser layout not verified','Statistical assumptions cannot be established from three-field dataset']}
(out/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))
assert not result['failed']
