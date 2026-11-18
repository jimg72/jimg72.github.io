"""Weekly results from the November 17 Frozen Tundra newsletter."""
from decimal import Decimal
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import all_play as calc

# Winner, winning score, opponent, losing score.
GAMES = [
    ('Shawn', '92.6', 'Scott', '92.3'),
    ('Jerry', '164.8', 'Richard', '102.0'),
    ('Jim', '162.3', 'Paul', '87.0'),
    ('Hilton', '152.8', 'Danny', '120.7'),
    ('Phil', '141.0', 'Rickey', '111.2'),
    ('Ashley', '91.1', 'Thomas', '82.0'),
]


class Week10Tests(unittest.TestCase):
    def setUp(self):
        self.week = calc.read_json(ROOT / 'examples/week10-scores.json')
        self.base = calc.read_json(ROOT / 'examples/week8-checkpoint.json')

    def test_published_week(self):
        report = calc.week_results(self.week, self.base['teams'])
        self.assertEqual(report['week'], 10)
        self.assertEqual(sum(report['scores'].values()), Decimal('1399.8'))
        self.assertCountEqual(
            [frozenset(pair) for pair in self.week['matchups']],
            [frozenset((a, b)) for a, _, b, _ in GAMES],
        )
        for winner, high, loser, low in GAMES:
            with self.subTest(winner=winner, loser=loser):
                self.assertEqual(report['scores'][winner], Decimal(high))
                self.assertEqual(report['scores'][loser], Decimal(low))
                self.assertEqual(report['actual'][winner], [1, 0, 0])
                self.assertEqual(report['actual'][loser], [0, 1, 0])

        ranking = 'Jerry Jim Hilton Phil Danny Rickey Richard Shawn Scott Ashley Paul Thomas'.split()
        for losses, team in enumerate(ranking):
            with self.subTest(team=team):
                self.assertEqual(report['all_play'][team], [11 - losses, losses, 0])

    def test_week_eight_checkpoint_requires_week_nine(self):
        with self.assertRaisesRegex(ValueError, 'expected Week 9'):
            calc.calculate(self.base, [self.week])
