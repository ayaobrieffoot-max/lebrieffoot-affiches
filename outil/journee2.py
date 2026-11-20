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
    """Cinq enfants en illustration « flat » détaillée, qui se tiennent la main."""
    kids = [
        # (x, échelle, peau, peau ombre, cheveux, style, haut, bas, type bas, chaussures)
        (110, 0.95, "#8d5524", "#74451c", "#1b1110", "afro_puffs", "#ff4d6d", "#3a86ff", "jupe", "#ffffff"),
        (280, 0.88, "#f3c9a1", "#e0ad83", "#6b3e1f", "court", "#2a9d8f", "#264653", "short", "#e63946"),
        (450, 1.00, "#5c3a21", "#4a2e1a", "#120c0a", "afro", "#ffbe0b", "#1d3557", "short", "#ffffff"),
        (620, 0.90, "#e8b98c", "#d39f72", "#2b1b12", "tresses", "#8338ec", "#ffffff", "jupe", "#3a86ff"),
        (790, 0.96, "#a86b3c", "#8f5a31", "#1b1110", "boucles", "#3a86ff", "#ffbe0b", "short", "#12123a"),
    ]
    sol = 385

    def pt(x, s, dx, dy):
        return x + dx * s, sol + dy * s

    def hair(style, x, s, c):
        hx, hy = pt(x, s, 0, -255)
        r = 47 * s
        if style == "afro":
            bumps = "".join(
                f'<circle cx="{hx + 52*s*__import__("math").cos(a/10)}" cy="{hy - 12*s + 50*s*__import__("math").sin(a/10)}" r="{20*s}" fill="{c}"/>'
                for a in range(-34, 3, 4)
            )
            return f'<circle cx="{hx}" cy="{hy-14*s}" r="{60*s}" fill="{c}"/>' + bumps, ""
        if style == "afro_puffs":
            back = (f'<circle cx="{hx-52*s}" cy="{hy-40*s}" r="{27*s}" fill="{c}"/>'
                    f'<circle cx="{hx+52*s}" cy="{hy-40*s}" r="{27*s}" fill="{c}"/>'
                    f'<rect x="{hx-36*s}" y="{hy-44*s}" width="{10*s}" height="{8*s}" rx="3" fill="#ffbe0b"/>'
                    f'<rect x="{hx+26*s}" y="{hy-44*s}" width="{10*s}" height="{8*s}" rx="3" fill="#ffbe0b"/>')
            front = f'<path d="M{hx-r},{hy-2*s} A{r},{r} 0 0 1 {hx+r},{hy-2*s} Q{hx+30*s},{hy-34*s} {hx},{hy-30*s} Q{hx-30*s},{hy-34*s} {hx-r},{hy-2*s}Z" fill="{c}"/>'
            return back, front
        if style == "court":
            front = (f'<path d="M{hx-r-2*s},{hy+4*s} Q{hx-r-6*s},{hy-r-8*s} {hx},{hy-r-6*s} Q{hx+r+8*s},{hy-r-6*s} {hx+r+2*s},{hy+4*s} '
                     f'Q{hx+34*s},{hy-26*s} {hx+8*s},{hy-24*s} Q{hx-10*s},{hy-14*s} {hx-22*s},{hy-26*s} Q{hx-36*s},{hy-20*s} {hx-r-2*s},{hy+4*s}Z" fill="{c}"/>')
            return "", front
        if style == "tresses":
            back = (f'<path d="M{hx-r+2*s},{hy} Q{hx-r-6*s},{hy+60*s} {hx-r+6*s},{hy+92*s}" stroke="{c}" stroke-width="{18*s}" fill="none" stroke-linecap="round"/>'
                    f'<path d="M{hx+r-2*s},{hy} Q{hx+r+6*s},{hy+60*s} {hx+r-6*s},{hy+92*s}" stroke="{c}" stroke-width="{18*s}" fill="none" stroke-linecap="round"/>'
                    f'<circle cx="{hx-r+6*s}" cy="{hy+92*s}" r="{8*s}" fill="#ff4d6d"/><circle cx="{hx+r-6*s}" cy="{hy+92*s}" r="{8*s}" fill="#ff4d6d"/>')
            front = (f'<path d="M{hx-r-3*s},{hy+8*s} Q{hx-r-4*s},{hy-r-10*s} {hx},{hy-r-6*s} Q{hx+r+4*s},{hy-r-10*s} {hx+r+3*s},{hy+8*s} '
                     f'Q{hx+r-8*s},{hy-24*s} {hx},{hy-28*s} Q{hx-r+8*s},{hy-24*s} {hx-r-3*s},{hy+8*s}Z" fill="{c}"/>'
                     f'<path d="M{hx},{hy-r-4*s} L{hx},{hy-26*s}" stroke="#00000033" stroke-width="{3*s}"/>')
            return back, front
        if style == "boucles":
            import math
            curls = "".join(
                f'<circle cx="{hx + 44*s*math.cos(math.radians(a))}" cy="{hy - 6*s + 44*s*math.sin(math.radians(a))}" r="{15*s}" fill="{c}"/>'
                for a in range(180, 361, 22)
            )
            return "", curls
        return "", ""

    def child(x, s, peau, ombre, chev, style, haut, bas, typebas, chauss, mains):
        o = []
        back, front = hair(style, x, s, chev)
        o.append(back)
        # jambes + chaussures
        for dx in (-15, 15):
            lx, ly = pt(x, s, dx, -88)
            o.append(f'<rect x="{lx-7*s}" y="{ly}" width="{14*s}" height="{80*s}" rx="{7*s}" fill="{peau}"/>')
            sx, sy = pt(x, s, dx + (4 if dx > 0 else -4), -6)
            o.append(f'<ellipse cx="{sx}" cy="{sy}" rx="{17*s}" ry="{9*s}" fill="{chauss}" stroke="#12123a22" stroke-width="2"/>')
        # bas
        if typebas == "jupe":
            a = pt(x, s, -30, -120); b = pt(x, s, 30, -120); c = pt(x, s, 46, -72); d = pt(x, s, -46, -72)
            o.append(f'<path d="M{a[0]},{a[1]} L{b[0]},{b[1]} L{c[0]},{c[1]} Q{x},{c[1]+8*s} {d[0]},{d[1]}Z" fill="{bas}"/>')
        else:
            bx, by = pt(x, s, -31, -122)
            o.append(f'<rect x="{bx}" y="{by}" width="{62*s}" height="{44*s}" rx="{10*s}" fill="{bas}"/>')
            mx, my = pt(x, s, 0, -100)
            o.append(f'<line x1="{mx}" y1="{my}" x2="{mx}" y2="{my+22*s}" stroke="#00000022" stroke-width="{3*s}"/>')
        # bras (derrière le buste)
        for side, m in mains:
            sx, sy = pt(x, s, 26 * side, -192)
            mx, my = m
            cx_, cy_ = (sx + mx) / 2 + 6 * side * s, (sy + my) / 2 + 14 * s
            o.append(f'<path d="M{sx},{sy} Q{cx_},{cy_} {mx},{my}" stroke="{peau}" stroke-width="{15*s}" fill="none" stroke-linecap="round"/>')
            o.append(f'<path d="M{sx},{sy} Q{sx+10*side*s},{sy+14*s} {sx+14*side*s},{sy+26*s}" stroke="{haut}" stroke-width="{24*s}" fill="none" stroke-linecap="round"/>')
        # buste
        tx, ty = pt(x, s, -33, -205)
        o.append(f'<rect x="{tx}" y="{ty}" width="{66*s}" height="{92*s}" rx="{22*s}" fill="{haut}"/>')
        # cou
        nx, ny = pt(x, s, -9, -218)
        o.append(f'<rect x="{nx}" y="{ny}" width="{18*s}" height="{18*s}" fill="{ombre}"/>')
        cxl, cyl = pt(x, s, 0, -206)
        o.append(f'<path d="M{cxl-14*s},{cyl} Q{cxl},{cyl+12*s} {cxl+14*s},{cyl}" fill="none" stroke="#ffffff88" stroke-width="{4*s}"/>')
        # tête
        hx, hy = pt(x, s, 0, -255)
        for side in (-1, 1):
            o.append(f'<circle cx="{hx+46*side*s}" cy="{hy+4*s}" r="{11*s}" fill="{ombre}"/>')
        o.append(f'<circle cx="{hx}" cy="{hy}" r="{47*s}" fill="{peau}"/>')
        o.append(f'<path d="M{hx-30*s},{hy+36*s} Q{hx},{hy+52*s} {hx+30*s},{hy+36*s} Q{hx},{hy+46*s} {hx-30*s},{hy+36*s}Z" fill="{ombre}"/>')
        o.append(front)
        # visage
        for side in (-1, 1):
            ex, ey = hx + 17 * side * s, hy + 2 * s
            o.append(f'<ellipse cx="{ex}" cy="{ey}" rx="{8.5*s}" ry="{10*s}" fill="#fff"/>')
            o.append(f'<circle cx="{ex+1*s}" cy="{ey+1.5*s}" r="{6*s}" fill="#2b1a10"/>')
            o.append(f'<circle cx="{ex+3*s}" cy="{ey-1.5*s}" r="{2.2*s}" fill="#fff"/>')
            o.append(f'<path d="M{ex-9*s},{ey-15*s} Q{ex},{ey-20*s} {ex+9*s},{ey-15*s}" stroke="#2b1a10" stroke-width="{3.5*s}" fill="none" stroke-linecap="round"/>')
            o.append(f'<circle cx="{hx+30*side*s}" cy="{hy+18*s}" r="{8*s}" fill="#ff6b6b" opacity=".35"/>')
        o.append(f'<path d="M{hx-3*s},{hy+12*s} Q{hx},{hy+16*s} {hx+3*s},{hy+12*s}" stroke="{ombre}" stroke-width="{3*s}" fill="none" stroke-linecap="round"/>')
        o.append(f'<path d="M{hx-15*s},{hy+22*s} Q{hx},{hy+40*s} {hx+15*s},{hy+22*s}Z" fill="#7a1f2b"/>')
        o.append(f'<path d="M{hx-12*s},{hy+23*s} L{hx+12*s},{hy+23*s} L{hx+10*s},{hy+27*s} L{hx-10*s},{hy+27*s}Z" fill="#fff"/>')
        return "".join(o)

    # points où les mains se rejoignent
    jonctions = []
    for i in range(4):
        x1, s1 = kids[i][0], kids[i][1]
        x2, s2 = kids[i + 1][0], kids[i + 1][1]
        jonctions.append(((x1 + x2) / 2, sol - 128 * (s1 + s2) / 2))
    out = []
    for i, k in enumerate(kids):
        x, s = k[0], k[1]
        mains = []
        mains.append((-1, jonctions[i - 1] if i > 0 else pt(x, s, -48, -112)))
        mains.append((1, jonctions[i] if i < 4 else pt(x, s, 48, -112)))
        out.append(child(*k, mains))
    for i, (jx, jy) in enumerate(jonctions):
        out.append(f'<circle cx="{jx}" cy="{jy}" r="{10}" fill="{kids[i][2]}"/>')
        out.append(f'<circle cx="{jx+4}" cy="{jy+2}" r="{9}" fill="{kids[i+1][2]}"/>')
    for i in (0, 4):
        x, s = kids[i][0], kids[i][1]
        hx, hy = pt(x, s, -48 if i == 0 else 48, -112)
        out.append(f'<circle cx="{hx}" cy="{hy}" r="{9*s}" fill="{kids[i][2]}"/>')
    ombre_sol = f'<ellipse cx="450" cy="{sol+4}" rx="420" ry="14" fill="#12123a" opacity=".12"/>'
    coeurs = "".join(
        f'<path transform="translate({x},{y}) scale({sc})" d="M0,8 C0,-4 18,-4 18,8 C18,-4 36,-4 36,8 C36,22 18,32 18,36 C18,32 0,22 0,8Z" fill="#e63946"/>'
        for x, y, sc in [(180, 20, 1.0), (432, -6, 1.3), (700, 20, 1.0)]
    )
    return f'<svg viewBox="0 -20 900 420" xmlns="http://www.w3.org/2000/svg">{coeurs}{ombre_sol}{"".join(out)}</svg>'


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
