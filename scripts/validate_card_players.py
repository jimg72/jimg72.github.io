#!/usr/bin/env python3
"""Validate card-page data: python scripts/validate_card_players.py (requires PyYAML).

Keep every required key. For an unverified service, use explicit null values and
explain why in comc_unavailable or tcdb_unavailable. This is schema validation,
not a live check that external sites still recognize an identifier.
"""
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {'player', 'priority', 'pid', 'tcdb_str', 'comc_str', 'ebay_str'}
OPTIONAL = {'links', 'comc_unavailable', 'tcdb_unavailable'}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f'duplicate key {key!r} at line {key_node.start_mark.line + 1}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate(players):
    errors = []
    if not isinstance(players, list) or not players:
        return ['expected a nonempty list of players']
    for index, player in enumerate(players, 1):
        label = f'record {index}'
        if not isinstance(player, dict):
            errors.append(f'{label}: expected a mapping')
            continue
        label += f' ({player.get("player", "unnamed")})'
        problems = []
        for key in sorted(REQUIRED - player.keys()):
            problems.append(f'missing key {key}')
        for key in player.keys() - REQUIRED - OPTIONAL:
            problems.append(f'unexpected key {key!r}')
        for key in ('player', 'ebay_str'):
            if not text(player.get(key)):
                problems.append(f'{key} must be a nonempty string')
        if type(player.get('priority')) is not bool:
            problems.append('priority must be true or false')
        for service, fields in [('tcdb', ('pid', 'tcdb_str')), ('comc', ('comc_str',))]:
            reason_key = f'{service}_unavailable'
            if reason_key in player:
                if not text(player[reason_key]):
                    problems.append(f'{reason_key} needs an explanation')
                if any(player.get(key) is not None for key in fields):
                    problems.append(f'{service}: unavailable fields must be null')
            else:
                for key in fields:
                    value = player.get(key)
                    valid = type(value) is int and value > 0 if key == 'pid' else text(value)
                    if not valid:
                        problems.append(f'{key} needs a valid value or an explicit {reason_key} explanation')
        if 'links' in player:
            links = player['links']
            if not isinstance(links, list):
                problems.append('links must be a list')
            else:
                for link in links:
                    if (not isinstance(link, dict) or set(link) != {'link_name', 'link_url'}
                            or not all(text(v) for v in link.values())):
                        problems.append('each link needs only nonempty link_name and link_url')
        errors.extend(f'{label}: {problem}' for problem in problems)
    return errors


def main():
    failed = False
    for name in ('football', 'baseball'):
        path = ROOT / '_data' / f'{name}.yaml'
        try:
            players = yaml.load(path.read_text(), Loader=UniqueKeyLoader)
            errors = validate(players)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors = [str(exc)]
        if errors:
            failed = True
            for error in errors:
                print(f'{path.relative_to(ROOT)}: {error}', file=sys.stderr)
        else:
            print(f'{name}: {len(players)} player records passed')
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
