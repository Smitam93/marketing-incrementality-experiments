"""Synthetic paired-geo randomized channel suppression experiment."""
from pathlib import Path
import json,sqlite3
import numpy as np
import pandas as pd
from scipy.stats import t
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
SEED=20261002

def generate(seed=SEED,pairs=24,channel_effect_scale=1.):
    rng=np.random.default_rng(seed); rows=[]
    for pair in range(pairs):
        scale=rng.uniform(130,260); treatment_geo=rng.integers(2)
        channel_effect=channel_effect_scale*rng.uniform(12,23)
        # Same planned channel budget in each matched pair, fixed before randomization.
        budget=rng.uniform(600,1000)
        shared_shock=rng.normal(0,4,84)
        for member in range(2):
            level=scale+rng.normal(0,5)
            for day in range(84):
                suppressed=int(member==treatment_geo and day>=56)
                baseline=level+.12*day+12*np.sin(2*np.pi*day/7)+shared_shock[day]
                conversions=max(0,int(round(baseline+channel_effect*(1-suppressed)+rng.normal(0,8))))
                # Attributed conversions include organic customers; deliberately not causal.
                attributed=0 if suppressed else int(round(.19*conversions+channel_effect*.3))
                rows.append({'pair_id':pair,'geo_id':f'G{pair:02d}-{member}',
                             'day':day,'date':str(pd.Timestamp('2025-01-01')+pd.Timedelta(days=day))[:10],
                             'is_treatment':int(member==treatment_geo),'is_post':int(day>=56),
                             'channel_on':1-suppressed,'conversions':conversions,
                             'revenue_usd':conversions*80.,'planned_spend_usd':budget,
                             'spend_usd':budget*(1-suppressed),'attributed_conversions':attributed})
    return pd.DataFrame(rows)

def pair_contrasts(d, pre_days, post_days):
    v=d.copy(); v['period']=np.where(v.day.isin(pre_days),'pre',np.where(v.day.isin(post_days),'post','exclude'))
    v=v[v.period!='exclude']
    means=v.groupby(['pair_id','is_treatment','period']).conversions.mean().unstack('period')
    changes=(means['post']-means['pre']).unstack('is_treatment')
    return changes[1]-changes[0] # Negative = conversions lost by switching channel off.

def analyze(d):
    contrasts=pair_contrasts(d,range(56),range(56,84)); n=len(contrasts)
    mean=float(contrasts.mean()); se=float(contrasts.std(ddof=1)/np.sqrt(n)); bound=t.ppf(.975,n-1)*se
    rng=np.random.default_rng(SEED+1)
    perm=(rng.choice([-1,1],(10000,n))*contrasts.to_numpy()).mean(axis=1)
    p=(1+np.sum(np.abs(perm)>=abs(mean)))/(len(perm)+1)
    # Effect of maintaining channel is the negative of suppression effect.
    incremental=-mean*n*28; ci=[-(mean+bound)*n*28, -(mean-bound)*n*28]
    planned=d[(d.is_treatment==1)&(d.is_post==1)].planned_spend_usd.sum()
    return {'pairs':n,'holdout_days':28,'daily_lost_conversions_per_suppressed_geo':-mean,
            'incremental_conversions_in_test_geos':incremental,'conversion_ci_95':ci,
            'incremental_revenue_usd':incremental*80,
            'incremental_roas':incremental*80/planned,
            'iroas_ci_95':[x*80/planned for x in ci],
            'restored_channel_spend_usd':float(planned),
            'paired_randomization_p_value':float(p),
            'preperiod_placebo_daily_difference':float(pair_contrasts(d,range(28),range(28,56)).mean()),
            'scope':'Synthetic 28-day experiment; no annualization or LTV extrapolation'}

def main():
    d=generate(); d.to_csv(ROOT/'data/geo_daily.csv',index=False); result=analyze(d)
    (ROOT/'outputs/summary.json').write_text(json.dumps(result,indent=2))
    contrasts=pair_contrasts(d,range(56),range(56,84))
    contrasts.rename('suppression_did_daily_conversions').to_csv(ROOT/'outputs/pair_effects.csv')
    conn=sqlite3.connect(ROOT/'outputs/analytics.sqlite'); d.to_sql('geo_daily',conn,if_exists='replace',index=False)
    pd.read_sql_query((ROOT/'sql/01_geo_metrics.sql').read_text(),conn).to_csv(ROOT/'outputs/geo_metrics.csv',index=False); conn.close()
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for treatment,g in d.groupby('is_treatment'):
        daily=g.groupby('day').conversions.mean()
        ax.plot(daily.index,daily,label='Suppression geos' if treatment else 'Channel-on geos')
    ax.axvline(56,color='black',linestyle='--'); ax.set(xlabel='Day',ylabel='Conversions / geo / day',title='Synthetic geo holdout: all-channel conversions'); ax.legend()
    fig.savefig(ROOT/'outputs/geo_holdout.png',dpi=160); plt.close(fig)
    ci=result['conversion_ci_95']; iroas=result['iroas_ci_95']
    memo=f'''# Synthetic marketing decision memo

The channel suppression experiment estimates {result['incremental_conversions_in_test_geos']:,.0f} incremental conversions over 28 days across 24 suppressed geos (95% paired-t CI: {ci[0]:,.0f} to {ci[1]:,.0f}). Estimated incremental revenue ROAS is {result['incremental_roas']:.2f} (95% CI: {iroas[0]:.2f} to {iroas[1]:.2f}). This uses all-channel conversions, not attributed channel conversions.

The paired randomization p-value is {result['paired_randomization_p_value']:.4f}; inference uses 24 randomized pairs, not 4,032 independent geo-day rows. The preperiod placebo difference is {result['preperiod_placebo_daily_difference']:.2f} conversions per geo-day and is a diagnostic, not proof of parallel trends.

Interpretation: the interval estimates the channel contribution in these test markets and dates. Revenue ROAS does not equal profit ROAS. At a hypothetical 60% gross margin the revenue break-even iROAS would be 1/0.60 = 1.67; compare the full interval with that threshold before recommending spend. These results cannot establish lifetime value, annual channel impact, or marginal returns from doubling budgets.

Assumptions: no cross-geo spillover; channel actually disabled; matching and budgets fixed before randomization; stable revenue per conversion. Paired-t confidence intervals are approximate; sign-flip testing is valid under the sharp null and the within-pair random assignment. A non-random historical rollout would need stronger identification and robustness checks.

Next: examine pair heterogeneity, run a longer confirmatory test, and measure contribution and customer quality before scaling.
'''
    (ROOT/'outputs/decision_memo.md').write_text(memo)
    print('Marketing analysis complete:',len(d),'synthetic geo-day rows')
if __name__=='__main__':main()
