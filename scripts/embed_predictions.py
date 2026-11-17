"""Embed a scrapeable latest-week table in the existing interactive homepage.

Only the marked section of index.html is changed. The JavaScript dashboard
replaces that fallback table with interactive matchup cards after it loads.
"""
import argparse
import html
import json
from pathlib import Path

from build_tracker import records

START = "<!-- BEGIN STATIC WEEKLY PREDICTIONS -->"
END = "<!-- END STATIC WEEKLY PREDICTIONS -->"

TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers", "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos",
    "DET": "Detroit Lions", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams",
    "LV": "Las Vegas Raiders", "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings", "NE": "New England Patriots",
    "NO": "New Orleans Saints", "NYG": "New York Giants",
    "NYJ": "New York Jets", "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers", "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}


def escape(value):
    return html.escape(str(value), quote=True)


def render(week):
    season, number = week["season"], week["week"]
    captured = week.get("captured_at") or "not recorded"
    source = week.get("provenance") or "not recorded"
    body = []
    for row in records(week):
        away, home, winner = row["away"], row["home"], row["pick"]
        if any(team not in TEAM_NAMES for team in (away, home, winner)):
            raise ValueError(f"Unrecognized team in {season} W{number}: {row}")
        values = [
            f"{away} - {TEAM_NAMES[away]}",
            f"{home} - {TEAM_NAMES[home]}",
            f"{winner} - {TEAM_NAMES[winner]}",
            row["away_score"], row["home_score"],
            row["home_margin"], row["predicted_total"],
            row["confidence"] or "—", row["timing_status"],
        ]
        body.append(
            f'<tr data-away="{escape(away)}" data-home="{escape(home)}" '
            f'data-pick="{escape(winner)}">'
            + "".join(f"<td>{escape(value)}</td>" for value in values)
            + "</tr>"
        )
    return (
        f'<div id="staticWeeklyPicks" class="table-wrap static-picks" '
        f'data-season="{season}" data-week="{number}">\n'
        f'<table id="officialWeeklyPredictions">\n'
        f'<caption>{season} NFL Week {number} official model predictions '
        f'— snapshot {escape(captured)}</caption>\n'
        '<thead><tr><th scope="col">Away team</th><th scope="col">Home team</th>'
        '<th scope="col">Official winner pick</th>'
        '<th scope="col">Predicted away score</th>'
        '<th scope="col">Predicted home score</th>'
        '<th scope="col">Predicted home margin</th>'
        '<th scope="col">Predicted total</th>'
        '<th scope="col">Confidence (%)</th>'
        '<th scope="col">Timing status</th></tr></thead>\n'
        '<tbody>\n' + "\n".join(body) + '\n</tbody>\n</table>\n'
        f'<p class="static-picks-note">Source: {escape(source)}. '
        'This is the latest saved forecast. Pregame status is only '
        'confirmed where explicitly recorded; snapshot timestamps alone '
        'do not prove when a page was publicly available.</p>\n'
        '</div>'
    )


def generate(source, page, check=False):
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not data.get("weeks"):
        raise ValueError("Invalid prediction archive")
    latest = max(data["weeks"], key=lambda w: (w["season"], w["week"]))
    page_path = Path(page)
    original = page_path.read_text(encoding="utf-8")
    if original.count(START) != 1 or original.count(END) != 1:
        raise ValueError("Homepage must contain exactly one pair of static-picks markers")
    start = original.index(START) + len(START)
    end = original.index(END)
    if start >= end:
        raise ValueError("Invalid static-picks marker order")
    replacement = "\n" + render(latest) + "\n"
    updated = original[:start] + replacement + original[end:]
    if check:
        if original != updated:
            raise ValueError("Homepage static predictions are out of date")
    elif updated != original:
        page_path.write_text(updated, encoding="utf-8")
    print(f"Homepage static picks: {latest['season']} Week {latest['week']} ({len(latest['games'])} matchups)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="results.json")
    parser.add_argument("--page", default="index.html")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate(args.source, args.page, args.check)
