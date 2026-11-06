"""Refresh only final-score fields in the published prediction archive."""
import csv
import io
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

SOURCE = 'https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'
ALIASES = {'LA': 'LAR', 'WSH': 'WAS', 'JAC': 'JAX', 'OAK': 'LV', 'SD': 'LAC', 'STL': 'LAR'}

def team(value):
    return ALIASES.get(value, value)

def refresh(data, rows):
    lookup = {}
    for row in rows:
        if row.get('game_type') != 'REG':
            continue
        key = (int(row['season']), int(row['week']), team(row['away_team']), team(row['home_team']))
        if key in lookup:
            raise ValueError('Duplicate schedule matchup')
        lookup[key] = row
    # Validate complete coverage before changing anything.
    for week in data['weeks']:
        for game in week['games']:
            if (week['season'], week['week'], game['away'], game['home']) not in lookup:
                raise ValueError('Schedule does not cover the published archive')
    changed = 0
    for week in data['weeks']:
        for game in week['games']:
            row = lookup[(week['season'], week['week'], game['away'], game['home'])]
            if not row['away_score'].strip() or not row['home_score'].strip():
                continue
            a, h = float(row['away_score']), float(row['home_score'])
            if not all(math.isfinite(n) and n >= 0 and n.is_integer() for n in (a, h)):
                raise ValueError('Invalid final score')
            final = dict(actual_away=a, actual_home=h, actual_winner=game['away'] if a > h else game['home'] if h > a else 'TIE')
            changed += any(game.get(k) != v for k, v in final.items())
            game.update(final)
    data['scores_checked_at'] = datetime.now(timezone.utc).isoformat()
    return changed

def main():
    path = Path('results.json')
    data = json.loads(path.read_text())
    with urlopen(SOURCE, timeout=60) as response:
        raw = response.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError('Schedule exceeds size limit')
    rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    changed = refresh(data, rows)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)
    print(f'Checked final scores; updated {changed} games.')

if __name__ == '__main__':
    main()
