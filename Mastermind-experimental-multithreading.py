import random
import itertools
import sys
import os
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
from statistics import mean
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from tqdm import tqdm  # Fortschrittsbalken in der Konsole

# --- Globale Definitionen ---
farbzuordnung = {'y':'Gelb', 'r':'Rot', 'b':'Blau', 'g':'Grün', 'o':'Orange', 'p':'Lila'}
farben = list(farbzuordnung.values())

# --- Fehleranzeige ---
def beenden_mit_fehler(message):
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Fehler", message)
    sys.exit()

# --- Grundlogik ---
def farbcode_festlegen():
    return random.choices(farben, k=4)

def farbcode_raten(farbcode, code):
    fc = farbcode.copy()
    cd = code.copy()
    richtige_pos = 0
    richtige_farbe = 0
    for i in range(4):
        if cd[i] == fc[i]:
            richtige_pos += 1
            fc[i] = cd[i] = None
    for i in range(4):
        if cd[i] is not None and cd[i] in fc:
            richtige_farbe += 1
            fc[fc.index(cd[i])] = None
    return richtige_pos, richtige_farbe

def code_erraten(richtige_pos):
    return (richtige_pos == 4)

def zeige_feedback(richtige_pos, richtige_farbe):
    print(f"\nFeedback:\n  Richtige Farbe & Position: {richtige_pos}\n  Richtige Farbe, falsche Position: {richtige_farbe}\n")

def zeige_beschreibung(name):
    print(f"\nLass uns Mastermind spielen, {name}!\n"
          "Farben: Gelb(y), Rot(r), Blau(b), Grün(g), Orange(o), Lila(p)\n"
          "Beispiel: rrgb\n"
          "Tippe 'ende' zum Abbruch.\n")

# --- Spieler-Klassen ---
class Mensch:
    def __init__(self, name):
        self.typ = 'Mensch'
        self.name = name

    def code_eingabe_mensch(self):
        while True:
            code = input("Deine Vermutung: ").lower()
            if code == 'ende':
                return []
            eingabe = [farbzuordnung.get(c) for c in code if c in farbzuordnung]
            if len(eingabe) == 4:
                print(eingabe)
                return eingabe
            else:
                print("\033[31mKein valider Farbcode!\033[0m Bitte vier Farben eingeben.\n")

    def tippe_code(self):
        return self.code_eingabe_mensch()

    def feedback_mensch(self, pos, farbe):
        zeige_feedback(pos, farbe)

class Mastermind_KI:
    def __init__(self):
        self.typ = 'KI'
        self.ki_zuruecksetzen()

    def ki_zuruecksetzen(self):
        self.index = 0
        self.kombinationen = [list(k) for k in itertools.product(farben, repeat=4)]

    def tippe_code(self):
        tipp = self.kombinationen[self.index].copy()
        self.index += 1
        return tipp

    def feedback_ki(self, pos, farbe):
        pass  # einfache KI ignoriert Feedback

class Mastermind_KI_version_2(Mastermind_KI):
    def __init__(self):
        super().__init__()
        self.farben_test = [[f]*4 for f in farben]

    def ki_zuruecksetzen(self):
        super().ki_zuruecksetzen()
        self.index = 0
        self.teste_farben = True

    def tippe_code(self):
        if self.teste_farben:
            tipp = self.farben_test[self.index].copy()
            self.index += 1
            if self.index == len(self.farben_test):
                self.teste_farben = False
                self.index = 0
        else:
            tipp = super().tippe_code()
        return tipp

    def feedback_ki(self, pos, farbe):
        if self.teste_farben and pos == 0 and farbe == 0:
            f_ausg = farben[self.index-1]
            self.kombinationen = [k for k in self.kombinationen if f_ausg not in k]

class Mastermind_KI_version_3(Mastermind_KI):
    def __init__(self):
        super().__init__()

    def ki_zuruecksetzen(self):
        super().ki_zuruecksetzen()
        self.feedback = None
        self.tipp = None

    def tippe_code(self):
        self.tipp = random.choice(self.kombinationen)
        self.kombinationen.remove(self.tipp)
        return self.tipp

    def feedback_ki(self, pos, farbe):
        self.feedback = (pos, farbe)
        self.kombinationen = [
            k for k in self.kombinationen
            if farbcode_raten(farbcode=k, code=self.tipp) == self.feedback
        ]

class Mastermind_KI_version_4(Mastermind_KI):
    def __init__(self):
        super().__init__()
        self.feedback = None

    def ki_zuruecksetzen(self):
        super().ki_zuruecksetzen()
        self.feedback = None

    def feedback_testen(self):
        self.kombinationen = [
            k for k in self.kombinationen
            if farbcode_raten(farbcode=k, code=self.tipp) == self.feedback
        ]

    def berechne_beste_kombination(self):
        beste = None
        geringster = float('inf')
        for kandidat in self.kombinationen:
            freq = {}
            for ziel in self.kombinationen:
                f = farbcode_raten(farbcode=kandidat, code=ziel)
                freq[f] = freq.get(f, 0) + 1
            rest = max(freq.values())
            if rest < geringster:
                geringster = rest
                beste = kandidat
        return beste or random.choice(self.kombinationen)

    def tippe_code(self):
        if self.feedback is None:
            self.tipp = random.choice(self.kombinationen)
        else:
            self.tipp = self.berechne_beste_kombination()
        self.kombinationen.remove(self.tipp)
        return self.tipp

    def feedback_ki(self, pos, farbe):
        self.feedback = (pos, farbe)
        self.feedback_testen()

# --- Spiel-Logik ---
def spiele_mastermind(spieler):
    code_geheim = farbcode_festlegen()
    if spieler.typ == "Mensch":
        zeige_beschreibung(spieler.name)
    runde = 1
    while True:
        if spieler.typ == "Mensch":
            print(f"Runde {runde}:")
        tipp = spieler.tippe_code()
        if tipp == []:
            print("Spiel abgebrochen.")
            return None
        pos, farbe = farbcode_raten(code_geheim, tipp)
        if spieler.typ == "Mensch":
            spieler.feedback_mensch(pos, farbe)
        else:
            spieler.feedback_ki(pos, farbe)
        if code_erraten(pos):
            if spieler.typ == "Mensch":
                print(f"Bravo, {spieler.name}! In {runde} Zügen erraten!")
            return runde
        runde += 1

# --- Chunk-Funktion für mehrere Runs ---
def simuliere_chunk(spieler_klasse, runs):
    ergebnisse = []
    for _ in range(runs):
        spieler = spieler_klasse()
        spieler.ki_zuruecksetzen()
        ergebnisse.append(spiele_mastermind(spieler))
    return ergebnisse

# --- Parallele Auswertung mit Prozessen + Fortschrittsbalken ---
def eval_parallel(spieler_klasse, total_runs, workers, name):
    if total_runs <= 0:
        return 0

    base = total_runs // workers
    rest = total_runs % workers
    arbeitsaufteilung = [base + (1 if i < rest else 0) for i in range(workers)]
    alle = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(simuliere_chunk, spieler_klasse, r) for r in arbeitsaufteilung]
        with tqdm(total=total_runs, desc=name, unit="run") as pbar:
            for fut in as_completed(futures):
                chunk = fut.result()
                alle.extend(chunk)
                pbar.update(len(chunk))
    return mean(alle) if alle else 0

# --- Plot-Funktion ---
def evaluations_plot(namen, werte, durchläufe):
    plt.figure(figsize=(8,8), dpi=80)
    plt.bar(range(len(werte)), werte, tick_label=namen, width=0.8)
    plt.axhline(1296, linestyle=':', color='g')
    plt.ylabel('Ø Anzahl Versuche')
    plt.xlabel(f"Anzahl Durchläufe = {durchläufe}")
    plt.title("Evaluation der Mastermind-KIs")
    for i, val in enumerate(werte):
        plt.text(i, val+20, f"{val:.2f}", ha='center')
    plt.show()

# --- Programmstart ---
if __name__ == "__main__":
    try:
        n = int(input("Wie viele Durchläufe pro KI simulieren? "))
    except ValueError:
        beenden_mit_fehler("Bitte eine gültige Zahl eingeben.")

    # Mensch spielt einmal
    name = input("Wie heißt du? ")
    mensch = Mensch(name)
    spiele_mastermind(mensch)

    # Anzahl Worker (=pro KI Prozesse) = CPU-Kerne
    workers = os.cpu_count() or 4

    ki_list = [
        ("KI_1", Mastermind_KI),
        ("KI_2", Mastermind_KI_version_2),
        ("KI_3", Mastermind_KI_version_3),
        ("KI_4", Mastermind_KI_version_4),
    ]

    namen, werte = [], []
    print(f"\nStarte parallele KI-Evaluation mit {workers} Prozessen pro KI…")
    for alias, kc in ki_list:
        mw = eval_parallel(kc, n, workers, alias)
        namen.append(alias)
        werte.append(mw)
        print(f"{alias}: Ø {mw:.2f} Versuche")

    # Ergebnis-Plot
    evaluations_plot(namen, werte, n)
