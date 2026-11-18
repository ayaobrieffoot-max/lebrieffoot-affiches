"""Génère la vidéo TikTok du jour (1080x1920, 20 s) à partir du JSON d'édition et de l'affiche.

Usage : python3 outil/video.py editions/AAAA-MM-JJ.json affiches/AAAA-MM-JJ.jpg videos/AAAA-MM-JJ.mp4

Structure : intro 2 s, 5 infos de 3 s, récap (affiche) 3 s. Musique chill générée par le script
(aucun son protégé), avec un « whoosh » à chaque changement de scène.
"""
import html
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

ICI = Path(__file__).resolve().parent
FPS = 25
TIMING = {"intro": 2.0, "info": 3.0, "outro": 3.0}  # 20 s au total
COULEURS = ["#ffce00", "#ffffff", "#d21034", "#ffffff", "#ffce00"]
SR = 44100


def construire_html(data: dict, poster: Path) -> str:
    gabarit = (ICI / "video.html").read_text(encoding="utf-8")
    blocs = []
    for i, it in enumerate(data["items"][:5], start=1):
        mots = "".join('<span class="w" style="display:inline-block">%s&nbsp;</span>' % html.escape(m)
                       for m in it["title"].split())
        num_couleur = COULEURS[i - 1]
        blocs.append(
            '<div class="scene info">'
            '<div class="brand">LE BRIEF <b>FOOT</b> D\'AMM</div>'
            '<div class="counter">INFO %d / 5</div>'
            '<div class="num anton" style="background:%s;%s">%d</div>'
            '<div class="tag">%s</div>'
            '<div class="title anton">%s</div>'
            '<div class="detail">%s</div>'
            '<div class="react">%s</div>'
            '<div class="src">Sources : %s</div>'
            '<div class="bar"><i></i></div>'
            "</div>"
            % (i, num_couleur, "color:#fff" if num_couleur == "#d21034" else "", i,
               html.escape(it["tag"]), mots, html.escape(it["detail"]),
               html.escape(it.get("react", "")), html.escape(it.get("source", "")))
        )
    return (gabarit.replace("{{DATE}}", html.escape(data["date"]))
            .replace("{{INFOS}}", "".join(blocs))
            .replace("{{POSTER}}", poster.resolve().as_uri())
            .replace("{{TIMING}}", json.dumps(TIMING)))


def duree_totale(n: int) -> float:
    return TIMING["intro"] + n * TIMING["info"] + TIMING["outro"]


def musique(duree: float, coupures: list, chemin: Path) -> None:
    """Petit beat chill/pop (sons doux, sans saturation), stéréo, -3 dB max."""
    from scipy.signal import lfilter
    n = int(duree * SR)
    L = np.zeros(n)
    R = np.zeros(n)
    bpm = 120  # 1 temps = 0,5 s : chaque coupure (toutes les 3 s) tombe sur un temps
    beat = 60 / bpm
    rng = np.random.default_rng(7)

    def poser(son, debut, pan=0.0, gain=1.0):
        i = int(debut * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(son))
        L[i:j] += son[: j - i] * gain * (1 - max(0, pan))
        R[i:j] += son[: j - i] * gain * (1 + min(0, pan))

    def xs(d):
        return np.arange(int(d * SR)) / SR

    def lp(x, fc):
        a = np.exp(-2 * np.pi * fc / SR)
        for _ in range(2):
            x = lfilter([1 - a], [1, -a], x)
        return x

    # kick rond
    x = xs(0.45)
    kick = np.sin(2 * np.pi * (48 * x + 70 * (1 - np.exp(-x * 25)) / 25)) * np.exp(-x * 7) * 0.55
    kick *= np.minimum(1, x / 0.002)
    # clap doux : bruit filtré
    x = xs(0.25)
    clap = lp(rng.normal(0, 1, len(x)), 2500) * np.exp(-x * 18) * 0.35
    # shaker très léger
    x = xs(0.06)
    shaker = lp(rng.normal(0, 1, len(x)), 6000) * np.exp(-x * 60) * 0.06

    accords = [[220.00, 261.63, 329.63, 392.00],   # Am7
               [174.61, 220.00, 261.63, 329.63],   # Fmaj7
               [261.63, 329.63, 392.00, 493.88],   # Cmaj7
               [196.00, 246.94, 293.66, 349.23]]   # G7
    basses = [55.0, 43.65, 65.41, 49.0]
    melodie = [[659.25, 523.25, 587.33, 523.25], [587.33, 523.25, 440.0, 523.25],
               [659.25, 783.99, 659.25, 587.33], [587.33, 493.88, 523.25, 587.33]]
    mesure = 4 * beat
    phase = coupures[0] % mesure  # les mesures démarrent pour tomber pile sur les coupures
    nb_mesures = int(duree / mesure) + 2
    for m in range(-1, nb_mesures):
        d = phase + m * mesure
        intro = d < coupures[0] - 0.01
        a = accords[m % 4]
        # nappe chaude (sinus légèrement désaccordés, attaque lente)
        x = xs(mesure + 0.3)
        pad = sum(np.sin(2 * np.pi * f * x) + np.sin(2 * np.pi * f * 1.004 * x) for f in a)
        pad *= np.minimum(1, x / 0.6) * np.minimum(1, (mesure + 0.3 - x) / 0.5) * 0.022
        poser(pad, d, pan=-0.3)
        poser(pad, d, pan=0.3)
        if intro:
            continue
        # basse sinus ronde, une note par temps
        for q in range(4):
            x = xs(beat * 0.95)
            f = basses[m % 4]
            b = (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(2 * np.pi * 2 * f * x))
            b *= np.minimum(1, x / 0.01) * np.exp(-x * 2.5) * 0.30
            poser(b, d + q * beat)
        # batterie
        for q in range(4):
            poser(kick, d + q * beat)
            if q in (1, 3):
                poser(clap, d + q * beat, pan=0.1)
            for s in range(2):
                poser(shaker, d + q * beat + s * beat / 2, pan=0.4, gain=0.6 if s == 0 else 1.0)
        # petite mélodie « pluck » une mesure sur deux
        if m % 2 == 1:
            for q, f in enumerate(melodie[m % 4]):
                x = xs(beat * 0.9)
                pl = (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 2 * f * x)) * np.exp(-x * 6) * 0.07
                pl *= np.minimum(1, x / 0.005)
                poser(pl, d + q * beat, pan=-0.2)
                poser(pl * 0.35, d + q * beat + beat * 0.75, pan=0.4)  # écho
    # transitions musicales : montée de clochettes sur le dernier temps, puis note claire sur la coupure
    def cloche(f, d=1.6, g=1.0):
        x = xs(d)
        son = (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2.0 * f * x) * np.exp(-x * 6)
               + 0.12 * np.sin(2 * np.pi * 3.0 * f * x) * np.exp(-x * 10))
        return son * np.exp(-x * 3.2) * np.minimum(1, x / 0.003) * 0.09 * g

    montee = [880.00, 1046.50, 1318.51, 1567.98]  # La – Do – Mi – Sol
    for c in coupures:
        for i, f in enumerate(montee):
            poser(cloche(f, 0.8, 0.55 + 0.12 * i), c - beat + i * beat / 4, pan=-0.3 + 0.2 * i)
        for f in (1760.00, 1318.51, 880.00):  # accord clair sur le temps
            poser(cloche(f, 2.2, 0.8), c)
            poser(cloche(f, 2.2, 0.25), c + beat * 0.75, pan=0.5)  # écho
    st = np.stack([L, R])
    st = lp_st = np.stack([lp(L, 9000), lp(R, 9000)])
    fin = int(1.0 * SR)
    st[:, -fin:] *= np.linspace(1, 0, fin)
    st[:, : int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    st *= 0.70 / np.max(np.abs(st))  # environ -3 dB, aucune saturation
    data = (st.T * 32767).astype(np.int16)
    with wave.open(str(chemin), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())


def main() -> None:
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    poster = Path(sys.argv[2])
    sortie = Path(sys.argv[3])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    n = len(data["items"][:5])
    duree = duree_totale(n)
    page_html = ICI / "_video.html"
    page_html.write_text(construire_html(data, poster), encoding="utf-8")
    audio = ICI / "_musique.wav"
    coupures = [TIMING["intro"] + k * TIMING["info"] for k in range(n + 1)]
    musique(duree, coupures, audio)

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg",
         "-i", "-", "-i", str(audio), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
         str(sortie)],
        stdin=subprocess.PIPE,
    )
    with sync_playwright() as p:
        nav = p.chromium.launch(executable_path="/usr/bin/google-chrome")
        page = nav.new_page(viewport={"width": 1080, "height": 1920})
        page.goto(page_html.as_uri())
        page.wait_for_timeout(600)
        page.evaluate("layout()")
        for f in range(int(duree * FPS)):
            page.evaluate("t => render(t)", f / FPS)
            ff.stdin.write(page.screenshot(type="jpeg", quality=88))
        nav.close()
    ff.stdin.close()
    ff.wait()
    page_html.unlink()
    audio.unlink()
    if ff.returncode != 0:
        sys.exit("ffmpeg a échoué")
    print(sortie)


if __name__ == "__main__":
    main()
