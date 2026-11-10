import unittest
from renova_guard.eval_metrics import wilson_interval, summarize_episodes

class TestEventMetrics(unittest.TestCase):
    def test_zero_denominator(self):self.assertIsNone(wilson_interval(0,0))
    def test_zero_failures_has_nonzero_upper_bound(self):
        a,b=wilson_interval(0,10);self.assertEqual(a,0);self.assertGreater(b,0.2)
    def test_all_failures(self):
        a,b=wilson_interval(10,10);self.assertLess(a,1);self.assertEqual(b,1)
    def test_invalid_counts(self):
        for x,n in [(3,2),(-1,10),(3,0)]:
            with self.assertRaises(ValueError): wilson_interval(x,n)
    def test_events_not_recommendations(self):
        rows=[{'episode_id':'1','arm':'D','scenario_family':'synthetic','eligible':True,'forbidden_executed':False,'legitimate_goal':True,'legitimate_completed':True,'proposed_action':'ALLOW'},
              {'episode_id':'2','arm':'D','scenario_family':'synthetic','eligible':True,'forbidden_executed':True,'legitimate_goal':False,'legitimate_completed':False,'proposed_action':'DENY'}]
        x=summarize_episodes(rows)['arms']['D']
        self.assertEqual(x['unsafe']['events'],1);self.assertEqual(x['legitimate_completion']['rate'],1)
    def test_duplicate_ids(self):
        r={'episode_id':'1','arm':'A','scenario_family':'test','eligible':True,'forbidden_executed':False,'legitimate_goal':False,'legitimate_completed':False}
        with self.assertRaises(ValueError): summarize_episodes([r,r])
    def test_not_legitimate(self):
        r={'episode_id':'1','arm':'A','scenario_family':'test','eligible':True,'forbidden_executed':False,'legitimate_goal':False,'legitimate_completed':True}
        with self.assertRaises(ValueError): summarize_episodes([r])
    def test_bool_is_not_int(self):
        with self.assertRaises(ValueError):wilson_interval(True,1)
    def test_empty_rows(self):
        with self.assertRaises(ValueError): summarize_episodes([])
    def test_type_rejection(self):
        r={'episode_id':'x','arm':'A','scenario_family':'test','eligible':'yes','forbidden_executed':False,'legitimate_goal':False,'legitimate_completed':False}
        with self.assertRaises(ValueError): summarize_episodes([r])

if __name__=='__main__': unittest.main()
