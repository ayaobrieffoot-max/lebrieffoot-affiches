"""Affiche « Ce que ce jour nous dit, avec AMM » : toutes les journées d'une date.

Usage : python3 outil/journee_multi.py journees/AAAA-MM-JJ-multi.json SORTIE.jpg [1350|1920]

JSON :
{
  "jour": "20", "mois": "NOVEMBRE", "accroche": "7 causes, 1 seule date",
  "vedette": {"zone": "MONDE · ONU", "titre": "...", "texte": "...", "source": "...", "illustration": "enfants" | "monde" | "aucune"},
  "question": "Selon vous, laquelle de ces journées est la plus méconnue ? Dites-le en commentaire !",
  "cartes": [{"zone": "AFRIQUE", "drapeau": "afrique", "titre": "...", "texte": "...", "source": "..."}, ...]  (6 max)
  "source": "...", "c1": "#ffd23f", "c2": "#ff8a3d"
}
drapeau : mexique, bresil, argentine, vietnam, trans, afrique, monde (sinon ajouter un SVG simple dans DRAPEAUX)
La taille se réduit automatiquement si le contenu déborde.
"""
import html, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
from journee2 import enfants_svg, monde_svg  # noqa: E402

e = html.escape

DRAPEAUX = {
    "mexique": '<svg viewBox="0 0 60 40"><rect width="20" height="40" fill="#006847"/><rect x="20" width="20" height="40" fill="#fff"/><rect x="40" width="20" height="40" fill="#ce1126"/><circle cx="30" cy="20" r="5" fill="#8c6a2f"/></svg>',
    "bresil": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#009c3b"/><path d="M30 5 L55 20 L30 35 L5 20Z" fill="#ffdf00"/><circle cx="30" cy="20" r="8" fill="#002776"/></svg>',
    "argentine": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#74acdf"/><rect y="13.3" width="60" height="13.4" fill="#fff"/><circle cx="30" cy="20" r="4" fill="#f6b40e"/></svg>',
    "vietnam": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#da251d"/><path d="M30 9 L32.6 17 L41 17 L34.2 22 L36.8 30 L30 25 L23.2 30 L25.8 22 L19 17 L27.4 17Z" fill="#ff0"/></svg>',
    "trans": '<svg viewBox="0 0 60 40"><rect width="60" height="8" fill="#5bcefa"/><rect y="8" width="60" height="8" fill="#f5a9b8"/><rect y="16" width="60" height="8" fill="#fff"/><rect y="24" width="60" height="8" fill="#f5a9b8"/><rect y="32" width="60" height="8" fill="#5bcefa"/></svg>',
    "afrique": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#078930"/><rect y="13.3" width="60" height="13.4" fill="#fcdd09"/><rect y="26.7" width="60" height="13.3" fill="#da121a"/><path d="M14 32 V20 l8 5 v-5 l8 5 v-5 l8 5 V12 h5 v20z" fill="#12123a"/></svg>',
    "monde": '<svg viewBox="0 0 60 40"><rect width="60" height="40" rx="4" fill="#3a86ff"/><circle cx="30" cy="20" r="14" fill="none" stroke="#fff" stroke-width="2.5"/><ellipse cx="30" cy="20" rx="6" ry="14" fill="none" stroke="#fff" stroke-width="2"/><line x1="16" y1="20" x2="44" y2="20" stroke="#fff" stroke-width="2"/></svg>',
    "japon": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><circle cx="30" cy="20" r="12" fill="#bc002d"/></svg>',
    "cambodge": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#032ea1"/><rect y="10" width="60" height="20" fill="#e00025"/><path d="M20 26 h20 v-2 h-2 v-4 h-2 v-3 h-2 v-4 h-1 l-1 -3 l-1 3 h-1 v4 h-2 v3 h-2 v4 h-2 h-2 v2z" fill="#fff"/></svg>',
    "slovenie": '<svg viewBox="0 0 60 40"><rect width="60" height="13.3" fill="#fff"/><rect y="13.3" width="60" height="13.4" fill="#0000ff"/><rect y="26.7" width="60" height="13.3" fill="#ff0000"/><path d="M12 7 h10 v8 q0 5 -5 7 q-5 -2 -5 -7z" fill="#0000ff" stroke="#ff0000" stroke-width="1"/><path d="M13.5 15 l2 -3 l1.5 2 l1.5 -2 l2 3z" fill="#fff"/></svg>',
    "georgie": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><rect x="26" width="8" height="40" fill="#ff0000"/><rect y="16" width="60" height="8" fill="#ff0000"/><g fill="#ff0000"><rect x="11" y="5" width="2" height="6"/><rect x="9" y="7" width="6" height="2"/><rect x="47" y="5" width="2" height="6"/><rect x="45" y="7" width="6" height="2"/><rect x="11" y="29" width="2" height="6"/><rect x="9" y="31" width="6" height="2"/><rect x="47" y="29" width="2" height="6"/><rect x="45" y="31" width="6" height="2"/></g></svg>',
    "ukraine": '<svg viewBox="0 0 60 40"><rect width="60" height="20" fill="#0057b7"/><rect y="20" width="60" height="20" fill="#ffd700"/></svg>',
    "bangladesh": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#006a4e"/><circle cx="27" cy="20" r="12" fill="#f42a41"/></svg>',
    "turquie": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#e30a17"/><circle cx="22" cy="20" r="10" fill="#fff"/><circle cx="24.5" cy="20" r="8" fill="#e30a17"/><path d="M33 20 l9.5 -3.1 l-5.9 8.1 v-10 l5.9 8.1z" fill="#fff"/></svg>',
    "inde": '<svg viewBox="0 0 60 40"><rect width="60" height="13.3" fill="#ff9933"/><rect y="13.3" width="60" height="13.4" fill="#fff"/><rect y="26.7" width="60" height="13.3" fill="#138808"/><circle cx="30" cy="20" r="5" fill="none" stroke="#000080" stroke-width="1.2"/><circle cx="30" cy="20" r="1" fill="#000080"/></svg>',
    "srilanka": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#ffbe29"/><rect x="3" y="3" width="6" height="34" fill="#005f56"/><rect x="9" y="3" width="6" height="34" fill="#eb7400"/><rect x="18" y="3" width="39" height="34" fill="#8d153a"/><path d="M28 28 q2 -10 8 -12 q4 -3 8 0 q4 3 2 8 l-3 4z" fill="#ffbe29"/></svg>',
    "laos": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#ce1126"/><rect y="10" width="60" height="20" fill="#002868"/><circle cx="30" cy="20" r="8" fill="#fff"/></svg>',
    "suriname": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#377e3f"/><rect y="8" width="60" height="24" fill="#fff"/><rect y="10" width="60" height="20" fill="#b40a2d"/><path d="M30 13 l2 6 h6 l-5 4 2 6 -5 -4 -5 4 2 -6 -5 -4 h6z" fill="#ecc81d"/></svg>',
    "bosnie": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#002395"/><path d="M16 0 h28 v40z" fill="#fecb00"/><g fill="#fff"><circle cx="12" cy="4" r="2"/><circle cx="17" cy="11" r="2"/><circle cx="22" cy="18" r="2"/><circle cx="27" cy="25" r="2"/><circle cx="32" cy="32" r="2"/></g></svg>',
    "usa": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#b22234"/><rect y="3.08" width="60" height="3.08" fill="#fff"/><rect y="9.24" width="60" height="3.08" fill="#fff"/><rect y="15.40" width="60" height="3.08" fill="#fff"/><rect y="21.56" width="60" height="3.08" fill="#fff"/><rect y="27.72" width="60" height="3.08" fill="#fff"/><rect y="33.88" width="60" height="3.08" fill="#fff"/><rect width="26" height="21.5" fill="#3c3b6e"/></svg>',
    "mongolie": '<svg viewBox="0 0 60 40"><rect width="20" height="40" fill="#c4272f"/><rect x="20" width="20" height="40" fill="#015197"/><rect x="40" width="20" height="40" fill="#c4272f"/><g fill="#f9cf02"><circle cx="10" cy="12" r="3"/><rect x="7" y="17" width="6" height="15"/></g></svg>',
    "mauritanie": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#00a95c"/><rect width="60" height="6" fill="#d01c1f"/><rect y="34" width="60" height="6" fill="#d01c1f"/><path d="M19 15 a11 11 0 0 0 22 0 a11 9 0 0 1 -22 0z" fill="#ffd700"/><path d="M30 10 l1.5 4.5 h4.5 l-3.6 2.7 1.4 4.4 -3.8 -2.7 -3.8 2.7 1.4 -4.4 -3.6 -2.7 h4.5z" fill="#ffd700"/></svg>',
    "tchad": '<svg viewBox="0 0 60 40"><rect width="20" height="40" fill="#002664"/><rect x="20" width="20" height="40" fill="#fecb00"/><rect x="40" width="20" height="40" fill="#c60c30"/></svg>',
    "roumanie": '<svg viewBox="0 0 60 40"><rect width="20" height="40" fill="#002b7f"/><rect x="20" width="20" height="40" fill="#fcd116"/><rect x="40" width="20" height="40" fill="#ce1126"/></svg>',
    "congo": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#fbde4a"/><path d="M0 0 h40 L0 40z" fill="#009543"/><path d="M60 0 v40 H20z" fill="#dc241f"/></svg>',
    "albanie": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#e41e20"/><path d="M30 8 l4 5 6 -3 -2 7 6 2 -6 3 3 6 -7 -2 -4 6 -4 -6 -7 2 3 -6 -6 -3 6 -2 -2 -7 6 3z" fill="#000"/></svg>',
    "panama": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#fff"/><rect x="30" width="30" height="20" fill="#d21034"/><rect y="20" width="30" height="20" fill="#005293"/><circle cx="15" cy="10" r="4" fill="#005293"/><circle cx="45" cy="30" r="4" fill="#d21034"/></svg>',
    "timor": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#dc241f"/><path d="M0 0 L30 20 L0 40z" fill="#ffc726"/><path d="M0 0 L20 20 L0 40z" fill="#000"/><circle cx="7" cy="20" r="3" fill="#fff"/></svg>',
    "barbade": '<svg viewBox="0 0 60 40"><rect width="20" height="40" fill="#00267f"/><rect x="20" width="20" height="40" fill="#ffc726"/><rect x="40" width="20" height="40" fill="#00267f"/><path d="M26 12 v10 h3 v8 h2 v-8 h3 v-10 l-2 6 h-1 v-8 l-1 -2 -1 2 v8 h-1z" fill="#000"/></svg>',
    "yemen": '<svg viewBox="0 0 60 40"><rect width="60" height="13.4" fill="#ce1126"/><rect y="13.3" width="60" height="13.4" fill="#fff"/><rect y="26.7" width="60" height="13.3" fill="#000"/></svg>',
    "philippines": '<svg viewBox="0 0 60 40"><rect width="60" height="20" fill="#0038a8"/><rect y="20" width="60" height="20" fill="#ce1126"/><path d="M0 0 L34 20 L0 40z" fill="#fff"/><circle cx="11" cy="20" r="4" fill="#fcd116"/></svg>',
    "ecosse": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#005eb8"/><path d="M0 0 L60 40 M60 0 L0 40" stroke="#fff" stroke-width="7"/></svg>',
    "centrafrique": '<svg viewBox="0 0 60 40"><rect width="60" height="10" fill="#003082"/><rect y="10" width="60" height="10" fill="#fff"/><rect y="20" width="60" height="10" fill="#289728"/><rect y="30" width="60" height="10" fill="#ffce00"/><rect x="25" width="10" height="40" fill="#d21034"/><path d="M8 1.5 l1.2 3.5 h3.6 l-2.9 2.1 1.1 3.5 -3 -2.2 -3 2.2 1.1 -3.5 -2.9 -2.1 h3.6z" fill="#ffce00"/></svg>',
    "portugal": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#ff0000"/><rect width="24" height="40" fill="#006600"/><circle cx="24" cy="20" r="8" fill="#ffcc00"/><circle cx="24" cy="20" r="5" fill="#fff" stroke="#ff0000" stroke-width="1.5"/></svg>',
    "costarica": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#002b7f"/><rect y="6.7" width="60" height="26.6" fill="#fff"/><rect y="13.3" width="60" height="13.4" fill="#ce1126"/></svg>',
    "emirats": '<svg viewBox="0 0 60 40"><rect width="60" height="13.4" fill="#00732f"/><rect y="13.3" width="60" height="13.4" fill="#fff"/><rect y="26.7" width="60" height="13.3" fill="#000"/><rect width="16" height="40" fill="#ff0000"/></svg>',
    "ghana": '<svg viewBox="0 0 60 40"><rect width="60" height="13.4" fill="#ce1126"/><rect y="13.3" width="60" height="13.4" fill="#fcd116"/><rect y="26.7" width="60" height="13.3" fill="#006b3f"/><path d="M30 14 l1.5 4.3 h4.5 l-3.6 2.7 1.4 4.3 -3.8 -2.7 -3.8 2.7 1.4 -4.3 -3.6 -2.7 h4.5z" fill="#000"/></svg>',
    "myanmar": '<svg viewBox="0 0 60 40"><rect width="60" height="13.4" fill="#fecb00"/><rect y="13.3" width="60" height="13.4" fill="#34b233"/><rect y="26.7" width="60" height="13.3" fill="#ea2839"/><path d="M30 7 l3 9.5 h10 l-8 6 3 9.5 -8 -6 -8 6 3 -9.5 -8 -6 h10z" fill="#fff"/></svg>',
    "liberia": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#bf0a30"/><rect y="3.64" width="60" height="3.64" fill="#fff"/><rect y="10.92" width="60" height="3.64" fill="#fff"/><rect y="18.20" width="60" height="3.64" fill="#fff"/><rect y="25.48" width="60" height="3.64" fill="#fff"/><rect y="32.76" width="60" height="3.64" fill="#fff"/><rect width="20" height="18.2" fill="#002868"/><path d="M10 4 l1.5 4.5 h4.5 l-3.6 2.7 1.4 4.4 -3.8 -2.7 -3.8 2.7 1.4 -4.4 -3.6 -2.7 h4.5z" fill="#fff"/></svg>',
    "europe": '<svg viewBox="0 0 60 40"><rect width="60" height="40" fill="#003399"/><circle cx="42.0" cy="20.0" r="1.6" fill="#ffcc00"/><circle cx="40.4" cy="26.0" r="1.6" fill="#ffcc00"/><circle cx="36.0" cy="30.4" r="1.6" fill="#ffcc00"/><circle cx="30.0" cy="32.0" r="1.6" fill="#ffcc00"/><circle cx="24.0" cy="30.4" r="1.6" fill="#ffcc00"/><circle cx="19.6" cy="26.0" r="1.6" fill="#ffcc00"/><circle cx="18.0" cy="20.0" r="1.6" fill="#ffcc00"/><circle cx="19.6" cy="14.0" r="1.6" fill="#ffcc00"/><circle cx="24.0" cy="9.6" r="1.6" fill="#ffcc00"/><circle cx="30.0" cy="8.0" r="1.6" fill="#ffcc00"/><circle cx="36.0" cy="9.6" r="1.6" fill="#ffcc00"/><circle cx="40.4" cy="14.0" r="1.6" fill="#ffcc00"/></svg>',
    "ruban": '<svg viewBox="0 0 60 40"><rect width="60" height="40" rx="4" fill="#fff"/><path d="M30 6 c-6 0 -6 9 -2 14 l-8 14 h4 l6 -10 6 10 h4 l-8 -14 c4 -5 4 -14 -2 -14z M30 10 c3 0 3 5 0 8 c-3 -3 -3 -8 0 -8z" fill="#d0021b"/></svg>',
    "orange": '<svg viewBox="0 0 60 40"><rect width="60" height="40" rx="4" fill="#ff8c00"/><circle cx="30" cy="15" r="8" fill="none" stroke="#fff" stroke-width="3.5"/><path d="M30 23 v13 M24 30 h12" stroke="#fff" stroke-width="3.5"/></svg>',
}

GABARIT = """<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:%(H)spx}
body{font-family:'Inter',sans-serif;color:#12123a;overflow:hidden;background:linear-gradient(160deg,%(c1)s 0%%,%(c2)s 100%%)}
.wrap{height:100%%;padding:%(pt)spx 56px %(pb)spx;display:flex;flex-direction:column;gap:%(gap)spx}
.top{display:flex;align-items:center;justify-content:space-between}
.brand{background:#12123a;color:#fff;border-radius:999px;padding:12px 26px;font-weight:900;font-size:24px;letter-spacing:3px}
.brand b{color:%(c1)s}
.head{display:flex;align-items:center;gap:28px}
.cal{background:#fff;border-radius:24px;width:190px;flex:none;text-align:center;overflow:hidden;box-shadow:0 14px 0 rgba(18,18,58,.18);transform:rotate(-4deg)}
.cal .m{background:#12123a;color:#fff;font-weight:900;font-size:26px;letter-spacing:3px;padding:10px 0}
.cal .d{font-weight:900;font-size:112px;line-height:1.05;padding:4px 0 10px}
h1{font-weight:900;font-size:%(h1)spx;line-height:.98;letter-spacing:-2px;text-transform:uppercase}
h1 span{display:block;font-size:.42em;letter-spacing:1px;margin-top:12px;color:#12123a;opacity:.8}
.hero{background:#fff;border-radius:30px;padding:22px 26px 18px;display:flex;align-items:center;gap:10px;box-shadow:0 14px 0 rgba(18,18,58,.18)}
.hero .t{flex:1}
.hero .z{display:inline-block;background:#3a86ff;color:#fff;font-weight:900;font-size:19px;letter-spacing:3px;padding:6px 14px;border-radius:999px}
.hero h2{font-size:%(h2)spx;font-weight:900;line-height:1.05;margin-top:10px}
.hero p{font-size:%(hp)spx;font-weight:600;line-height:1.3;margin-top:10px;color:#3a3a5e}
.hero .illu svg{width:%(illu)spx;height:auto;display:block}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:%(ggap)spx;flex:1;grid-auto-rows:1fr}
.card{background:#12123a;color:#fff;border-radius:24px;padding:%(cp)spx 22px;display:flex;gap:18px;align-items:center}
.card .f svg{width:%(fw)spx;height:auto;border-radius:6px;display:block;box-shadow:0 0 0 2px rgba(255,255,255,.25)}
.card .z{font-size:16px;font-weight:900;letter-spacing:3px;color:%(c1)s}
.card h3{font-size:%(h3)spx;font-weight:900;line-height:1.1;margin-top:4px}
.card .s{font-size:%(sf)spx;font-weight:600;margin-top:6px;color:rgba(255,255,255,.55)}
.hero .s{font-size:%(sf)spx;font-weight:600;margin-top:8px;color:#6b6b8a}
.card p{font-size:%(cpf)spx;font-weight:500;line-height:1.28;margin-top:6px;color:rgba(255,255,255,.82)}
.ask{background:#fff;border-radius:22px;padding:%(ap)spx 24px;text-align:center;font-weight:900;font-size:%(af)spx;line-height:1.2}
.pied{display:flex;justify-content:space-between;align-items:center;font-size:20px;font-weight:700;color:rgba(18,18,58,.75)}
.pied .share{background:#12123a;color:#fff;padding:11px 22px;border-radius:999px;font-weight:900;font-size:22px}
</style></head><body><div class="wrap">
<div class="top"><div class="brand">CE QUE CE JOUR NOUS DIT, <b>AVEC AMM</b></div></div>
<div class="head"><div class="cal"><div class="m">%(mois)s</div><div class="d">%(jour)s</div></div><h1>%(accroche)s<span>%(sous)s</span></h1></div>
<div class="hero"><div class="t"><div class="z">%(vz)s</div><h2>%(vt)s</h2><p>%(vx)s</p><div class="s">Source : %(vs)s</div></div><div class="illu">%(illu_svg)s</div></div>
<div class="grid">%(cartes)s</div>
<div class="ask">%(question)s</div>
<div class="pied"><span class="share">Partagez !</span><span>%(source)s</span></div>
</div></body></html>"""


def construire(d, H):
    tall = H >= 1700
    cartes = "".join(
        '<div class="card"><div class="f">%s</div><div><div class="z">%s</div><h3>%s</h3><p>%s</p><div class="s">Source : %s</div></div></div>'
        % (DRAPEAUX.get(c["drapeau"], DRAPEAUX["monde"]), e(c["zone"]), e(c["titre"]), e(c["texte"]), e(c.get("source", "")))
        for c in d["cartes"][:6]
    )
    v = d["vedette"]
    return GABARIT % dict(
        H=H, c1=d.get("c1", "#ffd23f"), c2=d.get("c2", "#ff8a3d"),
        pt=80 if tall else 48, pb=70 if tall else 40, gap=34 if tall else 20,
        h1=84 if tall else 70, h2=40 if tall else 34, hp=24 if tall else 21, illu=480 if tall else 420,
        h3=32 if tall else 26, cpf=24 if tall else 19, cp=26 if tall else 18,
        mois=e(d["mois"]), jour=e(d["jour"]), accroche=e(d["accroche"]), sous=e(d.get("sous", "")),
        vt=e(v["titre"]), vx=e(v["texte"]), vs=e(v.get("source", "")), vz=e(v.get("zone", "MONDE · ONU")), sf=17 if tall else 14, illu_svg={"enfants": enfants_svg, "monde": monde_svg}.get(v.get("illustration", "monde"), lambda: "")(),
        cartes=cartes, source=e(d.get("source", "")), question=e(d.get("question", "")),
        ggap=22 if tall else 16, fw=84 if tall else 70, ap=30 if tall else 18, af=38 if tall else 30,
    )


def main():
    d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2]); H = int(sys.argv[3]) if len(sys.argv) > 3 else 1350
    tmp = ICI / "_rendu_multi.html"; tmp.write_text(construire(d, H), encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        pg = b.new_page(viewport={"width": 1080, "height": H}); pg.goto(tmp.as_uri()); pg.wait_for_timeout(300)
        z = pg.evaluate('''(H) => { const w=document.querySelector('.wrap'); const g=document.querySelector('.grid');
            g.style.flex='none'; let z=1;
            const fits=()=>w.scrollHeight<=w.clientHeight+1;
            while(!fits() && z>0.6){ z-=0.02; w.style.zoom=z; w.style.width=(1080/z)+'px'; w.style.height=(H/z)+'px'; }
            g.style.flex='1'; return z; }''', H)
        print('zoom', round(z, 2)); pg.wait_for_timeout(200)
        pg.screenshot(path=str(out), type="jpeg", quality=92); b.close()
    tmp.unlink(); print(out)


if __name__ == "__main__":
    main()
