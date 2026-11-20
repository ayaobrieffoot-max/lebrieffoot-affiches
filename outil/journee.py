"""Génère l'affiche « journée internationale du jour » à partir d'un fichier JSON.

Usage : python3 outil/journee.py journees/AAAA-MM-JJ.json journees/AAAA-MM-JJ.jpg

Format du JSON :
{
  "date": "Vendredi 20 novembre 2026",
  "type": "mondiale",                      (mondiale / internationale / nationale)
  "titre": "Journée mondiale de l'enfance", (≤ 60 caractères)
  "organisme": "Proclamée par l'ONU",
  "accroche": "Une phrase forte ≤ 110 caractères.",
  "faits": ["fait chiffré ≤ 95 caractères", "...", "..."],   (2 ou 3)
  "autres": ["Autre journée du jour", "..."],                 (0 à 2, facultatif)
  "source": "ONU · UNICEF",
  "couleur": "#1cabe2"                     (couleur de la cause, facultatif)
}
"""
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
e = html.escape


def construire_html(d: dict) -> str:
    g = (ICI / "journee.html").read_text(encoding="utf-8")
    titre = d["titre"]
    taille = 104 if len(titre) <= 30 else 88 if len(titre) <= 45 else 74
    faits = "".join(
        '<div class="fait"><b>%d</b><div>%s</div></div>' % (i, e(f))
        for i, f in enumerate(d.get("faits", [])[:3], start=1)
    )
    autres = ""
    if d.get("autres"):
        autres = '<div class="autres"><span>Aussi aujourd\'hui</span>%s</div>' % " · ".join(
            e(a) for a in d["autres"][:2]
        )
    rep = {
        "{{COULEUR}}": d.get("couleur") or "#ffb703",
        "{{TAILLE}}": str(taille),
        "{{TYPE}}": e(d.get("type", "internationale")),
        "{{DATE}}": e(d["date"]),
        "{{TITRE}}": e(titre),
        "{{ORGANISME}}": e(d.get("organisme", "")),
        "{{ACCROCHE}}": e(d["accroche"]),
        "{{FAITS}}": faits,
        "{{AUTRES}}": autres,
        "{{SOURCE}}": e(d.get("source", "")),
    }
    for k, v in rep.items():
        g = g.replace(k, v)
    return g


def main() -> None:
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sortie = Path(sys.argv[2])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    page_html = ICI / "_rendu_journee.html"
    page_html.write_text(construire_html(d), encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        page = nav.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(page_html.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(sortie), type="jpeg", quality=92)
        nav.close()
    page_html.unlink()
    print(sortie)


if __name__ == "__main__":
    main()
