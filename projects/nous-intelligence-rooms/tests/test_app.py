import json, pathlib, sys, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
import server
class NousTests(unittest.TestCase):
    def test_demo_has_required_top_level_fields(self):
        data=server.load_demo()
        for key in server.SCHEMA['required']:
            self.assertIn(key,data)
    def test_scores_are_bounded(self):
        data=server.load_demo()
        self.assertTrue(0<=data['overall_score']<=100)
        self.assertTrue(all(0<=m['score']<=100 for m in data['metrics']))
    def test_evidence_is_traceable(self):
        data=server.load_demo()
        self.assertGreaterEqual(len(data['evidence']),4)
        self.assertTrue(all(e['source'] and e['observation'] and e['implication'] for e in data['evidence']))
if __name__=='__main__':unittest.main()
