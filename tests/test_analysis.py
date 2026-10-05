import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run import generate,analyze,pair_contrasts

class MarketingTests(unittest.TestCase):
    def test_pair_randomization_and_channel_compliance(self):
        d=generate()
        assignment=d[['pair_id','geo_id','is_treatment']].drop_duplicates()
        self.assertTrue((assignment.groupby('pair_id').is_treatment.sum()==1).all())
        self.assertTrue((d.loc[(d.is_treatment==1)&(d.is_post==1),'spend_usd']==0).all())
        self.assertTrue((d.loc[d.is_post==0,'channel_on']==1).all())
    def test_known_signal_recovery_at_pair_level(self):
        r=analyze(generate())
        self.assertTrue(8 < r['daily_lost_conversions_per_suppressed_geo'] < 27)
        self.assertEqual(len(pair_contrasts(generate(),range(56),range(56,84))),24)
        self.assertLess(r['paired_randomization_p_value'],.01)
    def test_no_channel_effect_has_no_systematic_lift(self):
        estimates=[analyze(generate(seed=s,channel_effect_scale=0))['daily_lost_conversions_per_suppressed_geo'] for s in range(8)]
        self.assertLess(abs(sum(estimates)/len(estimates)),1.)
if __name__=='__main__':unittest.main()
