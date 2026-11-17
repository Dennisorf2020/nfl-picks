"""Build plain HTML and CSV prediction feeds, no JavaScript required."""
import csv
import html
import io
import json
import math
from pathlib import Path

def esc(value):
    return html.escape(str(value), quote=True)

def fmt(n):
    return f"{n:g}"

def status(game):
    value = game.get("pregame_eligible")
    return "Pregame" if value is True else "Late / excluded" if value is False else "Unverified"

FIELDS = ["season","week","away","home","pick","away_score","home_score","home_margin","predicted_total","confidence","timing_status","kickoff_at","snapshot_captured_at"]

def records(week):
    for g in week["games"]:
        a,h = g["away_score"],g["home_score"]
        if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x < 0 for x in (a,h)):
            raise ValueError(f"Invalid scores: {g}")
        if a == h or g["pick"] != (g["away"] if a > h else g["home"]):
            raise ValueError(f"Official pick contradicts projected scores: {g}")
        if g["away"] == g["home"] or g["pick"] not in (g["away"],g["home"]):
            raise ValueError(f"Invalid matchup: {g}")
        yield dict(season=week["season"],week=week["week"],away=g["away"],home=g["home"],pick=g["pick"],away_score=fmt(a),home_score=fmt(h),home_margin=fmt(h-a),predicted_total=fmt(h+a),confidence="" if g.get("confidence") is None else fmt(g["confidence"]),timing_status=status(g),kickoff_at=g.get("kickoff_at") or "",snapshot_captured_at=week.get("captured_at") or "")

def export_csv(rows):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=FIELDS,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()

def page(week, all_weeks, latest=False):
    season,number=week["season"],week["week"]
    title=f"{season} NFL Week {number} Predictions"
    data=list(records(week))
    body="\n".join("<tr data-away=\""+esc(r["away"])+"\" data-home=\""+esc(r["home"])+"\" data-pick=\""+esc(r["pick"])+"\">"+"".join(f"<td>{esc(r[field] or '—')}</td>" for field in ["away","home","pick","away_score","home_score","home_margin","predicted_total","confidence","timing_status"])+"</tr>" for r in data)
    links=" | ".join(f'<a href="{("./" if latest else "../")}{w["season"]}/week-{w["week"]:02d}.html">{w["season"]} Week {w["week"]}</a>' for w in reversed(all_weeks))
    csv_url="./latest.csv" if latest else f'./week-{number:02d}.csv'
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} | NFL Prediction Lab</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1150px;margin:2rem auto;padding:0 1rem;color:#192334}}a{{color:#135f99}}table{{border-collapse:collapse;width:100%}}th,td{{padding:.55rem;text-align:left;border:1px solid #c5ced6;white-space:nowrap}}th{{background:#edf2f7}}tr:nth-child(even){{background:#f6f8fb}}.scroll{{overflow-x:auto}}small{{color:#536172}}</style>
</head><body><nav><a href="{"../" if latest else "../../"}">Dashboard</a> | <a href="{"./" if latest else "../"}">Latest picks</a> | <a href="{csv_url}">CSV feed</a></nav>
<h1>{esc(title)}</h1>
<p>Official model winner selections and projected scores. All prediction values are directly included in this page's HTML.</p>
<p><small>Season {season} · Week {number} · Snapshot timestamp: {esc(week.get("captured_at") or "unavailable")} · Source: {esc(week.get("provenance") or "unavailable")}</small></p>
<p><small>Predicted margin is home score minus away score. Pregame means explicitly eligible in the archive. Unverified timestamps are not proof of timely public publication. Final game results are intentionally omitted.</small></p>
<div class="scroll"><table><thead><tr><th>Away</th><th>Home</th><th>Official winner pick</th><th>Predicted away score</th><th>Predicted home score</th><th>Home margin</th><th>Predicted total</th><th>Confidence %</th><th>Timing</th></tr></thead>
<tbody>{body}</tbody></table></div>
<h2>Weekly archive</h2><nav>{links}</nav><footer><p><small>Predictions sourced from stored weekly records; updating final scores does not modify predictions.</small></p></footer>
</body></html>"""

def build(source="results.json", output="_site/tracker"):
    data=json.loads(Path(source).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not data.get("weeks"):
        raise ValueError("Unsupported prediction archive")
    weeks=sorted(data["weeks"],key=lambda w:(w["season"],w["week"]))
    if len({(w["season"],w["week"]) for w in weeks}) != len(weeks):
        raise ValueError("Duplicate season/week")
    dest=Path(output)
    dest.mkdir(parents=True,exist_ok=True)
    for week in weeks:
        entries=list(records(week))
        if len({(r["away"],r["home"]) for r in entries}) != len(entries):
            raise ValueError("Duplicate matchup")
        folder=dest/str(week["season"])
        folder.mkdir(parents=True,exist_ok=True)
        stem=f'week-{week["week"]:02d}'
        (folder/(stem+".html")).write_text(page(week,weeks),encoding="utf-8")
        (folder/(stem+".csv")).write_text(export_csv(entries),encoding="utf-8")
    latest=weeks[-1]
    (dest/"index.html").write_text(page(latest,weeks,latest=True),encoding="utf-8")
    (dest/"latest.csv").write_text(export_csv(list(records(latest))),encoding="utf-8")
    print(f"Published {len(weeks)} weeks; latest {latest['season']} W{latest['week']}")

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",default="results.json")
    parser.add_argument("--output",default="_site/tracker")
    args=parser.parse_args()
    build(args.source,args.output)
