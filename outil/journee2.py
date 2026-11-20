"""Affiche « Ce que ce jour nous dit, avec AMM » (version colorée).

Usage : python3 outil/journee2.py journees/AAAA-MM-JJ-v2.json SORTIE.jpg [hauteur]
  hauteur 1350 (Facebook, défaut) ou 1920 (TikTok vertical).

Format du JSON :
{
  "jour": "20", "mois": "NOVEMBRE",
  "titre": "Journée mondiale de l'enfance",
  "question": "1 seul pays n'a jamais ratifié la <em>Convention des droits de l'enfant</em>.",
  "reponse": "Devinez lequel ? Réponse en légende",
  "stats": [{"v": "1989", "l": "Adoption par l'ONU"}, {"v": "196", "l": "États l'ont ratifiée"}],
  "message": "Chaque enfant compte.",
  "source": "UNICEF · ONU",
  "c1": "#ffd23f", "c2": "#ff7a3d",
  "illustration": "enfants" | "monde" | "aucune"
}
Seule la balise <em> est permise dans "question" (mise en valeur).
"""
import html
import json
import random
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
e = html.escape


def enfants_svg() -> str:
    peaux = ["#8d5524", "#f1c27d", "#5c3a1e", "#e0ac69", "#c68642"]
    habits = ["#12123a", "#ffffff", "#2a9d8f", "#e63946", "#3a86ff"]
    tailles = [1.0, 0.86, 1.08, 0.9, 0.98]
    out = []
    x0, step = 90, 180
    for i, (p, h, t) in enumerate(zip(peaux, habits, tailles)):
        cx = x0 + i * step
        base = 300
        body_h = 120 * t
        head_r = 40 * t
        top = base - body_h
        out.append(
            f'<rect x="{cx-14*t}" y="{base-10}" width="{10*t}" height="{60*t}" rx="5" fill="{p}"/>'
            f'<rect x="{cx+4*t}" y="{base-10}" width="{10*t}" height="{60*t}" rx="5" fill="{p}"/>'
            f'<path d="M{cx-48*t},{base} Q{cx},{top-10} {cx+48*t},{base} Z" fill="{h}" stroke="#12123a" stroke-width="5"/>'
            f'<circle cx="{cx}" cy="{top-head_r+6}" r="{head_r}" fill="{p}" stroke="#12123a" stroke-width="5"/>'
            f'<circle cx="{cx-13*t}" cy="{top-head_r+2}" r="4.5" fill="#12123a"/>'
            f'<circle cx="{cx+13*t}" cy="{top-head_r+2}" r="4.5" fill="#12123a"/>'
            f'<path d="M{cx-14*t},{top-head_r+18} Q{cx},{top-head_r+32} {cx+14*t},{top-head_r+18}" fill="none" stroke="#12123a" stroke-width="4.5" stroke-linecap="round"/>'
        )
        if i < 4:
            nx = x0 + (i + 1) * step
            out.append(
                f'<path d="M{cx+38*t},{base-50} Q{(cx+nx)/2},{base-20} {nx-38*tailles[i+1]},{base-50}" '
                f'fill="none" stroke="{p}" stroke-width="13" stroke-linecap="round"/>'
            )
    coeurs = "".join(
        f'<path transform="translate({x},{y}) scale({s})" d="M0,8 C0,-4 18,-4 18,8 C18,-4 36,-4 36,8 C36,22 18,32 18,36 C18,32 0,22 0,8Z" fill="#e63946" stroke="#12123a" stroke-width="3"/>'
        for x, y, s in [(140, 40, 1.1), (450, 10, 1.4), (760, 40, 1.1)]
    )
    return f'<svg viewBox="0 0 900 370" xmlns="http://www.w3.org/2000/svg">{coeurs}{"".join(out)}</svg>'


def monde_svg() -> str:
    return (
        '<svg viewBox="0 0 900 330" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="450" cy="165" r="150" fill="#3a86ff" stroke="#12123a" stroke-width="6"/>'
        '<path d="M360,70 q40,-10 60,20 q10,30 -20,40 q-30,20 -10,50 q10,30 -30,40 q-40,-20 -40,-70 q0,-60 40,-80z" fill="#2a9d8f" stroke="#12123a" stroke-width="5"/>'
        '<path d="M470,60 q60,0 90,40 q20,40 -20,60 q-30,10 -20,50 q0,40 -50,60 q-20,-40 -10,-80 q-20,-30 -10,-80 q0,-40 20,-50z" fill="#2a9d8f" stroke="#12123a" stroke-width="5"/>'
        '<path d="M410,170 C410,150 440,150 440,170 C440,150 470,150 470,170 C470,195 440,212 440,220 C440,212 410,195 410,170Z" fill="#e63946" stroke="#12123a" stroke-width="4"/>'
        "</svg>"
    )


def construire_html(d: dict, hauteur: int) -> str:
    g = (ICI / "journee2.html").read_text(encoding="utf-8")
    titre = d["titre"]
    taille = 86 if len(titre) <= 32 else 72 if len(titre) <= 48 else 60
    question = e(d["question"]).replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    stats = "".join(
        '<div class="stat"><div class="v">%s</div><div class="l">%s</div></div>' % (e(s["v"]), e(s["l"]))
        for s in d.get("stats", [])[:3]
    )
    illu = {"enfants": enfants_svg, "monde": monde_svg}.get(d.get("illustration", "monde"), lambda: "")()
    rnd = random.Random(7)
    dots = "".join(
        '<i style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"></i>'
        % (rnd.randint(-40, 1060), rnd.randint(-40, hauteur), s, s)
        for s in [rnd.randint(14, 60) for _ in range(26)]
    )
    rep = {
        "{{H}}": str(hauteur), "{{CLASSE}}": "tall" if hauteur >= 1700 else "", "{{C1}}": d.get("c1", "#ffd23f"), "{{C2}}": d.get("c2", "#ff7a3d"),
        "{{DOTS}}": dots, "{{MOIS}}": e(d["mois"]), "{{JOUR}}": e(d["jour"]), "{{TAILLE}}": str(taille),
        "{{TITRE}}": e(titre), "{{ILLU}}": illu, "{{QUESTION}}": question,
        "{{REPONSE}}": e(d.get("reponse", "")), "{{STATS}}": stats,
        "{{MESSAGE}}": e(d.get("message", "")), "{{SOURCE}}": e(d.get("source", "")),
    }
    for k, v in rep.items():
        g = g.replace(k, v)
    return g


def main() -> None:
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sortie = Path(sys.argv[2])
    hauteur = int(sys.argv[3]) if len(sys.argv) > 3 else 1350
    sortie.parent.mkdir(parents=True, exist_ok=True)
    page_html = ICI / "_rendu_journee2.html"
    page_html.write_text(construire_html(d, hauteur), encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        page = nav.new_page(viewport={"width": 1080, "height": hauteur})
        page.goto(page_html.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(sortie), type="jpeg", quality=92)
        nav.close()
    page_html.unlink()
    print(sortie)


if __name__ == "__main__":
    main()
