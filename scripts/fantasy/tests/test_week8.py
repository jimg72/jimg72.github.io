"""Week 8 expectations transcribed from the November 3 published newsletter."""
import copy
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import all_play as calc

# Owner: weekly AP, cumulative AP, actual record, displayed expected wins, luck.
PUBLISHED = {
    'Scott': ([9,2,0], [62,25,1], [8,0,0], '5.7', '+2.3'),
    'Richard': ([11,0,0], [62,26,0], [6,2,0], '5.6', '+0.4'),
    'Rickey': ([7,4,0], [58,30,0], [6,2,0], '5.3', '+0.7'),
    'Phil': ([6,5,0], [53,34,1], [5,3,0], '4.9', '+0.1'),
    'Jerry': ([10,1,0], [47,41,0], [5,3,0], '4.3', '+0.7'),
    'Paul': ([3,8,0], [41,47,0], [3,5,0], '3.7', '-0.7'),
    'Ashley': ([1,10,0], [40,48,0], [3,5,0], '3.6', '-0.6'),
    'Hilton': ([8,3,0], [36,52,0], [2,6,0], '3.3', '-1.3'),
    'Jim': ([2,9,0], [36,52,0], [3,5,0], '3.3', '-0.3'),
    'Shawn': ([5,6,0], [36,52,0], [4,4,0], '3.3', '+0.7'),
    'Thomas': ([0,11,0], [30,58,0], [2,6,0], '2.7', '-0.7'),
    'Danny': ([4,7,0], [26,62,0], [1,7,0], '2.4', '-1.4'),
}


class Week8Tests(unittest.TestCase):
    def setUp(self):
        self.base = calc.read_json(ROOT / 'examples/week7-checkpoint.json')
        self.week = calc.read_json(ROOT / 'examples/week8-scores.json')
        self.result = calc.calculate(self.base, [self.week])

    def test_published_results(self):
        teams, through, actual, cumulative, reports = self.result
        self.assertEqual(through, 8)
        weekly = reports[-1]
        self.assertEqual(weekly['week'], 8)
        self.assertEqual(sum(weekly['scores'].values()), Decimal('1255.5'))
        self.assertEqual(set(teams), set(PUBLISHED))
        winners = {'Richard', 'Scott', 'Jerry', 'Phil', 'Rickey', 'Shawn'}
        for team, (ap, season, record, exp, luck) in PUBLISHED.items():
            with self.subTest(team=team):
                self.assertEqual(weekly['all_play'][team], ap)
                self.assertEqual(weekly['actual'][team], [1,0,0] if team in winners else [0,1,0])
                self.assertEqual(cumulative[team], season)
                self.assertEqual(actual[team], record)
                self.assertEqual(sum(cumulative[team]), 88)
                self.assertEqual(calc.decimal_text(calc.expected(season)), exp)
                self.assertEqual(calc.decimal_text(Decimal(record[0])-calc.expected(season), True), luck)
                row = f'| {team} | {calc.record_text(record)} | {calc.record_text(season)} | {exp} | {luck} |'
                self.assertIn(row, calc.markdown(self.result))

    def test_checkpoint_and_no_double_counting(self):
        saved = calc.read_json(ROOT / 'examples/week8-checkpoint.json')
        self.assertEqual(saved, calc.checkpoint_document(self.result))
        self.assertEqual(calc.calculate(saved)[:4], self.result[:4])
        self.assertEqual(saved['weeks'], [])
        with self.assertRaisesRegex(ValueError, 'expected Week 9'):
            calc.calculate(saved, [self.week])
        # Week 7 last_week is display-only: removing it cannot change totals.
        base = copy.deepcopy(self.base)
        base['checkpoint'].pop('last_week')
        self.assertEqual(calc.calculate(base, [self.week])[:4], self.result[:4])

    def test_cli_export(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'checkpoint.json'
            run = subprocess.run([
                sys.executable, str(ROOT / 'all_play.py'),
                str(ROOT / 'examples/week7-checkpoint.json'),
                '--week', str(ROOT / 'examples/week8-scores.json'),
                '--save-checkpoint', str(output),
            ], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn('League points: 1,255.5', run.stdout)
            self.assertIn('88 all-play comparisons per owner.', run.stdout)
            self.assertEqual(calc.read_json(output), calc.read_json(ROOT / 'examples/week8-checkpoint.json'))


if __name__ == '__main__':
    unittest.main()
