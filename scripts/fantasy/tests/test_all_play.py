"""Verified Week 7 regressions plus explicitly synthetic edge cases."""
import copy
import json
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import all_play as calc


class AllPlayTests(unittest.TestCase):
    def setUp(self):
        self.data = calc.read_json(ROOT / 'examples/week7-checkpoint.json')
        self.week = calc.read_json(ROOT / 'examples/week7-scores.json')
        self.teams = self.data['teams']

    def test_verified_week7(self):
        _, through, actual, ap, reports = calc.calculate(self.data)
        weekly = reports[0]
        self.assertEqual(through, 7)
        self.assertEqual(sum(weekly['scores'].values()), Decimal('1273.6'))
        order = ['Richard', 'Rickey', 'Scott', 'Paul', 'Ashley', 'Jerry',
                 'Shawn', 'Phil', 'Danny', 'Hilton', 'Thomas', 'Jim']
        for i, team in enumerate(order):
            self.assertEqual(weekly['all_play'][team], [11-i, i, 0])
            self.assertEqual(sum(ap[team]), 77)
        expected = ['4.9','4.6','4.6','4.3','3.5','3.5','3.4','3.1','2.8','2.7','2.5','2.0']
        luck = ['+2.1','+0.4','+0.4','-0.3','-0.5','-0.5','+0.6','-0.1','+0.2','-0.7','-0.5','-1.0']
        for team, exp, rating in zip(self.teams, expected, luck):
            self.assertEqual(calc.decimal_text(calc.expected(ap[team])), exp)
            self.assertEqual(calc.decimal_text(Decimal(actual[team][0])-calc.expected(ap[team]), True), rating)
        self.assertEqual(ap['Scott'], [53,23,1])
        self.assertEqual(ap['Phil'], [47,29,1])
        self.assertEqual(sum(calc.expected(r) for r in ap.values()), Decimal(42))
        self.assertIn('League points: 1,273.6', calc.markdown(calc.calculate(self.data)))

    def test_replay_week7_from_derived_week6_checkpoint(self):
        # Arithmetic test baseline, not a claim of independently sourced Week 6 data.
        weekly = calc.week_results(self.week, self.teams)
        before = copy.deepcopy(self.data)
        cp = before['checkpoint']
        cp.pop('last_week')
        cp['through_week'] = 6
        cp['all_play'] = calc.subtract(cp['all_play'], weekly['all_play'])
        cp['actual_records'] = calc.subtract(cp['actual_records'], weekly['actual'])
        result = calc.calculate(before, [self.week])
        self.assertEqual(result[1:4], calc.calculate(self.data)[1:4])
        by_record = copy.deepcopy(self.week)
        by_record.pop('matchups')
        by_record['actual_records'] = self.data['checkpoint']['actual_records']
        self.assertEqual(calc.calculate(before, [by_record])[1:4], result[1:4])

    def test_synthetic_ties_and_checkpoint_roundtrip(self):
        # Generic Week 1 fixture, deliberately not invented Week 8 results.
        week = {'week': 1, 'scores': {t: '100.10' for t in self.teams},
                'matchups': self.week['matchups']}
        result = calc.calculate({'teams': self.teams, 'weeks': [week]})
        for team in self.teams:
            self.assertEqual(result[2][team], [0,0,1])
            self.assertEqual(result[3][team], [0,0,11])
            self.assertEqual(calc.expected(result[3][team]), Decimal('0.5'))
        self.assertIn('-0.5', calc.markdown(result))
        restored = calc.calculate(calc.checkpoint_document(result))
        self.assertEqual(restored[:4], result[:4])

    def test_multiway_tie_and_negative_score(self):
        scores = {t: Decimal(i) for i,t in enumerate(self.teams)}
        for t in self.teams[:3]:
            scores[t] = Decimal('-1.25')
        ap = calc.all_play(scores)
        self.assertEqual(ap[self.teams[0]], [0,9,2])
        self.assertEqual(sum(r[0] for r in ap.values()), sum(r[1] for r in ap.values()))

    def test_bad_scores(self):
        for bad in [None, True, 'NaN', 'Infinity', 'not a score', []]:
            with self.subTest(bad=bad):
                week = copy.deepcopy(self.week)
                week['scores']['Jim'] = bad
                with self.assertRaises(ValueError):
                    calc.week_results(week, self.teams)
        self.week['scores'].pop('Jim')
        with self.assertRaises(ValueError):
            calc.week_results(self.week, self.teams)

    def test_bad_schedule_and_duplicate_week(self):
        with self.assertRaisesRegex(ValueError, 'expected Week 8'):
            calc.calculate(self.data, [self.week])
        for number in [6,9,True]:
            week = dict(self.week, week=number)
            with self.assertRaises(ValueError):
                calc.calculate(self.data, [week])
        self.week['matchups'][0] = ['Scott','Phil']
        with self.assertRaises(ValueError):
            calc.week_results(self.week, self.teams)

    def test_bad_checkpoint_and_record_changes(self):
        for record in [[52,23,1], [54,22,1], [-1,77,1], [53.0,23,1]]:
            data = copy.deepcopy(self.data)
            data['checkpoint']['all_play']['Scott'] = record
            with self.assertRaises(ValueError):
                calc.calculate(data)
        week = copy.deepcopy(self.week)
        week.pop('matchups')
        week['actual_records'] = self.data['checkpoint']['actual_records']
        previous = copy.deepcopy(week['actual_records'])
        previous['Scott'] = [8,0,0]
        with self.assertRaises(ValueError):
            calc.week_results(week, self.teams, previous)

    def test_duplicate_json_keys(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            json.loads('{"Jim": 1, "Jim": 2}', object_pairs_hook=calc.unique_object)

    def test_cli_outputs_and_error(self):
        with tempfile.TemporaryDirectory() as directory:
            md, checkpoint = [Path(directory)/name for name in ('report.md','checkpoint.json')]
            command = [sys.executable, str(ROOT/'all_play.py'), str(ROOT/'examples/week7-checkpoint.json')]
            run = subprocess.run(command + ['--output', str(md), '--save-checkpoint', str(checkpoint)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('| Scott | 7–0–0 | 53–23–1 | 4.9 | +2.1 |', md.read_text())
            self.assertEqual(calc.calculate(calc.read_json(checkpoint))[:4], calc.calculate(self.data)[:4])
            run = subprocess.run(command + ['--week', str(ROOT/'examples/week7-scores.json')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertIn('expected Week 8', run.stderr)
            self.assertNotIn('Traceback', run.stderr)


if __name__ == '__main__':
    unittest.main()
