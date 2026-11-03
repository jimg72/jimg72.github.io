#!/usr/bin/env python3
"""Standalone Frozen Tundra all-play calculator; Python 3.9+, standard library only."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'),
                      object_pairs_hook=unique_object, parse_float=Decimal)


def integer(value, label):
    require(type(value) is int and value >= 0, f'{label}: expected nonnegative integer')
    return value


def roster(mapping, teams, label):
    require(isinstance(mapping, dict) and set(mapping) == set(teams),
            f'{label}: must contain exactly the 12 team names')


def records(mapping, teams, games, label):
    roster(mapping, teams, label)
    result = {}
    for team, record in mapping.items():
        require(isinstance(record, list) and len(record) == 3,
                f'{label}/{team}: expected [wins, losses, ties]')
        result[team] = [integer(v, f'{label}/{team}') for v in record]
        require(sum(record) == games, f'{label}/{team}: expected {games} decisions')
    require(sum(r[0] for r in result.values()) == sum(r[1] for r in result.values()),
            f'{label}: total wins must equal total losses')
    require(sum(r[2] for r in result.values()) % 2 == 0, f'{label}: ties must be paired')
    return result


def scores_for(raw, teams):
    roster(raw, teams, 'scores')
    scores = {}
    for team, value in raw.items():
        require(not isinstance(value, bool) and isinstance(value, (str, int, float, Decimal)),
                f'scores/{team}: expected a finite number')
        try:
            score = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f'scores/{team}: invalid decimal') from exc
        require(score.is_finite(), f'scores/{team}: expected a finite number')
        scores[team] = score
    return scores


def all_play(scores):
    return {team: [sum(score > other for name, other in scores.items() if name != team),
                   sum(score < other for name, other in scores.items() if name != team),
                   sum(score == other for name, other in scores.items() if name != team)]
            for team, score in scores.items()}


def expected(record):
    return (Decimal(record[0]) + Decimal(record[2]) / 2) / 11


def add(left, right):
    return {team: [a + b for a, b in zip(left[team], right[team])] for team in left}


def subtract(left, right):
    return {team: [a - b for a, b in zip(left[team], right[team])] for team in left}


def week_results(week, teams, previous=None):
    require(isinstance(week, dict), 'week must be an object')
    number = integer(week.get('week'), 'week')
    require(number > 0, 'week must be positive')
    scores = scores_for(week.get('scores'), teams)
    require(('matchups' in week) != ('actual_records' in week),
            'provide exactly one of matchups or actual_records')
    if 'matchups' in week:
        pairs = week['matchups']
        require(isinstance(pairs, list) and len(pairs) == 6, 'expected six matchups')
        seen = set()
        actual = {team: [0, 0, 0] for team in teams}
        for pair in pairs:
            require(isinstance(pair, list) and len(pair) == 2, 'matchup must be [team, team]')
            a, b = pair
            require(isinstance(a, str) and isinstance(b, str) and a != b
                    and a in teams and b in teams and a not in seen and b not in seen,
                    'matchups must use each known team exactly once')
            seen.update(pair)
            if scores[a] == scores[b]:
                actual[a][2] = actual[b][2] = 1
            else:
                winner, loser = (a, b) if scores[a] > scores[b] else (b, a)
                actual[winner][0] = actual[loser][1] = 1
    else:
        require(previous is not None, 'actual_records requires previous cumulative records')
        cumulative = records(week['actual_records'], teams, number, 'actual_records')
        actual = records(subtract(cumulative, previous), teams, 1, 'weekly actual change')
    return {'week': number, 'scores': scores, 'all_play': all_play(scores), 'actual': actual}


def calculate(data, extra_weeks=()):
    require(isinstance(data, dict), 'season input must be an object')
    teams = data.get('teams')
    require(isinstance(teams, list) and len(teams) == 12
            and all(isinstance(t, str) and t.strip() and '\n' not in t for t in teams)
            and len(set(teams)) == 12, 'teams must list 12 unique, nonempty names')
    through = 0
    actual = {t: [0, 0, 0] for t in teams}
    cumulative = {t: [0, 0, 0] for t in teams}
    reports = []
    checkpoint = data.get('checkpoint')
    if checkpoint is not None:
        require(isinstance(checkpoint, dict), 'checkpoint must be an object')
        through = integer(checkpoint.get('through_week'), 'through_week')
        actual = records(checkpoint.get('actual_records'), teams, through, 'checkpoint actual')
        cumulative = records(checkpoint.get('all_play'), teams, through * 11, 'checkpoint all-play')
        if 'last_week' in checkpoint:
            last = week_results(checkpoint['last_week'], teams)
            require(last['week'] == through, 'last_week must equal checkpoint through_week')
            records(subtract(cumulative, last['all_play']), teams, (through - 1) * 11,
                    'checkpoint before last_week all-play')
            records(subtract(actual, last['actual']), teams, through - 1,
                    'checkpoint before last_week actual')
            reports.append(last)  # Display only: already counted in checkpoint.
    weeks = data.get('weeks', [])
    require(isinstance(weeks, list), 'weeks must be a list')
    for week in weeks + list(extra_weeks):
        report = week_results(week, teams, actual)
        require(report['week'] == through + 1,
                f'expected Week {through + 1}; duplicate, skipped, or out-of-order week')
        actual = add(actual, report['actual'])
        cumulative = add(cumulative, report['all_play'])
        through += 1
        reports.append(report)
    return teams, through, actual, cumulative, reports


def decimal_text(value, signed=False):
    rounded = value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    if rounded == 0:
        rounded = abs(rounded)
    return format(rounded, '+.1f' if signed else '.1f')


def record_text(record):
    return '–'.join(map(str, record))


def table(ap, actual, teams, scores=None):
    lines = ['| Owner | ' + ('Score | ' if scores is not None else '')
             + 'Actual W–L–T | All-play W–L–T | Expected wins | Luck |',
             '|:--|' + ('--:|' if scores is not None else '') + ':--:|:--:|--:|--:|']
    # Stable roster order breaks equal all-play credit; no implied playoff seeding.
    for team in sorted(teams, key=lambda t: -expected(ap[t])):
        exp = expected(ap[team])
        name = team.replace('\\', '\\\\').replace('|', '\\|')
        cells = [name]
        if scores is not None:
            cells.append(str(scores[team]))
        cells += [record_text(actual[team]), record_text(ap[team]), decimal_text(exp),
                  decimal_text(Decimal(actual[team][0]) - exp, signed=True)]
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


def markdown(result):
    teams, through, actual, cumulative, reports = result
    sections = ['Expected wins = (all-play wins + 0.5 × ties) ÷ 11. '
                'Luck = actual wins − unrounded expected wins. '
                'Actual matchup ties are recorded but do not count as wins. '
                'Displayed metrics round half up to one decimal.']
    for report in reports:
        sections.append(f"## Week {report['week']} all-play\n\nLeague points: "
                        f"{sum(report['scores'].values()):,}\n\n"
                        + table(report['all_play'], report['actual'], teams, report['scores']))
    sections.append(f'## Cumulative through Week {through}\n\n'
                    f'{through * 11} all-play comparisons per owner.\n\n'
                    + table(cumulative, actual, teams))
    return '\n\n'.join(sections) + '\n'


def checkpoint_document(result):
    teams, through, actual, cumulative, _ = result
    return {'teams': teams, 'checkpoint': {'through_week': through,
            'actual_records': actual, 'all_play': cumulative}, 'weeks': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('season', help='JSON season or checkpoint file')
    parser.add_argument('--week', action='append', default=[], help='append weekly JSON (repeat in order)')
    parser.add_argument('--output', help='write Markdown instead of stdout')
    parser.add_argument('--save-checkpoint', help='write reusable cumulative JSON checkpoint')
    args = parser.parse_args(argv)
    try:
        inputs = {Path(p).resolve() for p in [args.season] + args.week}
        outputs = [Path(p).resolve() for p in [args.output, args.save_checkpoint] if p]
        require(not inputs.intersection(outputs) and len(set(outputs)) == len(outputs),
                'output paths must differ from inputs and each other')
        result = calculate(read_json(args.season), [read_json(p) for p in args.week])
        rendered = markdown(result)
        if args.output:
            Path(args.output).write_text(rendered, encoding='utf-8')
        else:
            print(rendered, end='')
        if args.save_checkpoint:
            Path(args.save_checkpoint).write_text(
                json.dumps(checkpoint_document(result), indent=2) + '\n', encoding='utf-8')
    except (OSError, ValueError) as exc:
        parser.exit(2, f'error: {exc}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
