"""Génère l'affiche du jour à partir d'un fichier JSON.

Usage : python3 outil/generer.py edition.json affiches/AAAA-MM-JJ.png

Format du JSON :
{
  "date": "Mercredi 18 novembre 2026",
  "items": [
    {"tag": "CAN 2027", "title": "Titre court", "detail": "Une phrase.", "react": "Petite phrase pour faire réagir 🤔"},
    ... (5 éléments)
  ]
}
"""
import html
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent


def construire_html(data: dict) -> str:
    gabarit = (ICI / "affiche.html").read_text(encoding="utf-8")
    items = []
    for i, it in enumerate(data["items"][:5], start=1):
        items.append(
            '<div class="item"><div class="num">%d</div><div class="txt">'
            '<div class="tag">%s</div><div class="title">%s</div><div class="detail">%s</div>%s'
            "</div></div>"
            % (
                i,
                html.escape(it["tag"]),
                html.escape(it["title"]),
                html.escape(it["detail"]),
                '<div class="react">%s</div>' % html.escape(it["react"]) if it.get("react") else "",
            )
        )
    return gabarit.replace("{{DATE}}", html.escape(data["date"])).replace("{{ITEMS}}", "".join(items))


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sortie = Path(sys.argv[2])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    page_html = ICI / "_rendu.html"
    page_html.write_text(construire_html(data), encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        page = nav.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(page_html.as_uri())
        page.wait_for_timeout(400)
        page.screenshot(path=str(sortie), type="png")
        nav.close()
    page_html.unlink()
    print(sortie)


if __name__ == "__main__":
    main()
