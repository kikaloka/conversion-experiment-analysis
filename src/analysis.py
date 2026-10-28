"""Deterministic aggregate analysis. No row-level outputs are exported."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy.stats import binomtest
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep, proportion_confint

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://video.udacity-data.com/topher/2023/February/63f67d64_ab_data/ab_data.csv'
SHA = '8c1ce3d02b7b195c1f40a1c278ba8c2f807295874c302efb61812ba226ce43ac'

def run():
    out = ROOT/'results'; charts = out/'charts'
    charts.mkdir(parents=True, exist_ok=True)
    raw = ROOT/'data/original/ab_data.csv'
    assert hashlib.sha256(raw.read_bytes()).hexdigest() == SHA, 'Source changed; review before analysis'
    d = pd.read_csv(raw)
    assert list(d.columns) == ['country','group','converted']
    valid = d.notna().all(axis=1) & d.country.isin(['US','UK','CA']) & d.group.isin(['control','treatment']) & d.converted.isin([0,1])
    # Fail closed rather than silently changing the analysis population.
    assert valid.all(), 'Unexpected data values require a documented review'
    audit = pd.DataFrame([
        ['Source rows',len(d),'Immutable source, verified SHA-256'],
        ['Missing or invalid rows',int((~valid).sum()),'None removed; unexpected values halt analysis'],
        ['Repeated three-field tuples',int(d.duplicated().sum()),'Retained: repeated categories are not evidence of duplicate visitors'],
        ['Analysis rows',len(d),'No exclusions, imputation or deduplication']
    ], columns=['step','count','decision'])
    a = d.groupby('group').converted.agg(n='size',conversions='sum',rate='mean').reindex(['control','treatment'])
    for g in a.index:
        a.loc[g,['ci_low','ci_high']] = proportion_confint(a.loc[g,'conversions'],a.loc[g,'n'],method='wilson')
    n0,n1 = int(a.loc['control','n']),int(a.loc['treatment','n'])
    x0,x1 = int(a.loc['control','conversions']),int(a.loc['treatment','conversions'])
    p0,p1 = x0/n0,x1/n1
    z,p = proportions_ztest([x1,x0],[n1,n0],alternative='two-sided')
    lo,hi = confint_proportions_2indep(x1,n1,x0,n0,method='newcomb',compare='diff')
    country = d.groupby(['country','group']).converted.agg(n='size',conversions='sum',rate='mean').reset_index()
    country['within_group_share'] = country.n / country.group.map(a.n)
    X = pd.DataFrame({'intercept':np.ones(len(d)), 'treatment':(d.group=='treatment').astype(float)})
    Xadj = X.assign(country_CA=(d.country=='CA').astype(float),country_UK=(d.country=='UK').astype(float))
    models = []; fits = []
    for name,design in [('Unadjusted',X),('Country adjusted',Xadj)]:
        fit = sm.Logit(d.converted,design).fit(disp=False)
        assert fit.mle_retvals['converged']
        fits.append(fit)
        ci=fit.conf_int().loc['treatment']
        models.append({'model':name,'coefficient':float(fit.params['treatment']),'odds_ratio':float(np.exp(fit.params['treatment'])),'or_ci_low':float(np.exp(ci.iloc[0])),'or_ci_high':float(np.exp(ci.iloc[1])),'p_value':float(fit.pvalues['treatment'])})
    # Marginal standardization uses the observed pooled country distribution.
    c0=Xadj.copy(); c0['treatment']=0
    c1=Xadj.copy(); c1['treatment']=1
    standardized=float((fits[1].predict(c1)-fits[1].predict(c0)).mean())
    stats={'source_rows':len(d),'analysis_rows':len(d),'control_n':n0,'treatment_n':n1,'control_conversions':x0,'treatment_conversions':x1,'control_rate':p0,'treatment_rate':p1,'risk_difference':p1-p0,'relative_lift':p1/p0-1,'ci_low':float(lo),'ci_high':float(hi),'z':float(z),'p_value':float(p),'alpha':0.05,'country_standardized_risk_difference':standardized,'sha256':SHA}
    # Conditional diagnostic only: the intended assignment ratio is not supplied.
    stats['allocation_diagnostic'] = {'assumed_treatment_probability':0.5,'assumption_established':False,'method':'Exact two-sided binomial test','p_value':float(binomtest(n1,n0+n1,p=0.5,alternative='two-sided').pvalue),'interpretation':'If intended allocation was exactly 50:50, the counts warrant investigation; the actual planned ratio is unknown. No rows excluded.'}
    a.to_csv(out/'conversion_summary.csv',index_label='group'); country.to_csv(out/'country_summary.csv',index=False)
    audit.to_csv(out/'cleaning_audit.csv',index=False); pd.DataFrame(models).to_csv(out/'regression_summary.csv',index=False)
    (out/'metrics.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})
    fig,ax=plt.subplots(figsize=(8,4.5)); rates=a.rate.to_numpy()*100
    ax.bar(['Control','Treatment'],rates,color=['#64748b','#087f8c'],width=.55)
    ax.errorbar([0,1],rates,yerr=np.vstack([a.rate-a.ci_low,a.ci_high-a.rate])*100,fmt='none',ecolor='#172b4d',capsize=6)
    for i,r in enumerate(rates): ax.text(i,r+0.65,f'{r:.2f}%',ha='center',weight='bold')
    ax.set(ylim=(0,19),ylabel='Conversion rate (%)',title='Treatment conversion is higher in this sample')
    fig.text(.1,.015,'Whiskers: 95% Wilson intervals. Control n=34,678; treatment n=35,211.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1)); fig.savefig(charts/'conversion.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4.5))
    for j,(g,col) in enumerate([('control','#64748b'),('treatment','#087f8c')]):
        sub=country[country.group==g].set_index('country').loc[['CA','UK','US']]
        ax.bar(np.arange(3)+(j-.5)*.32,sub.rate*100,width=.32,label=g.title(),color=col)
    ax.set(xticks=np.arange(3),xticklabels=['CA','UK','US'],ylabel='Conversion rate (%)',ylim=(0,19),title='The observed direction is consistent across countries'); ax.legend(frameon=False)
    fig.text(.1,.015,'Descriptive subgroup comparison, not three confirmatory tests.',fontsize=9)
    fig.tight_layout(rect=(0,.04,1,1)); fig.savefig(charts/'country.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,3.5)); ax.errorbar((p1-p0)*100,0,xerr=np.array([[(p1-p0-lo)*100],[(hi-p1+p0)*100]]),fmt='o',color='#087f8c',capsize=8)
    ax.axvline(0,color='#64748b',linestyle='--'); ax.set(yticks=[],xlim=(-.5,6),xlabel='Treatment minus control (percentage points)',title=f'Absolute difference: {(p1-p0)*100:.2f} percentage points')
    fig.text(.1,.02,'95% Newcombe interval. Positive values favor treatment.',fontsize=10); fig.tight_layout(rect=(0,.06,1,1)); fig.savefig(charts/'effect.png'); plt.close(fig)
    return stats,a,country,audit,pd.DataFrame(models)

if __name__ == '__main__':
    print(json.dumps(run()[0],indent=2))
