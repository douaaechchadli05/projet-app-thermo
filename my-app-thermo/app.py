"""
Application Flask - Pression de bulle (Benzène/Toluène)
Avec historique et interface responsive
"""
from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import math
from datetime import datetime

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'calculs.db')

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES D'ANTOINE
# ══════════════════════════════════════════════════════════════════════════════
#
# La loi d'Antoine : log10(P_sat) = A - B / (C + T)
#   P_sat en mmHg,  T en °C
#
ANTOINE = {
    'benzene': {'A': 6.90565, 'B': 1211.033, 'C': 220.790},   # NIST
    'toluene': {'A': 6.95334, 'B': 1343.943, 'C': 219.377},   # NIST
}

def antoine_psat_mmhg(composant, T_celsius):
    """
    Calcule la pression de vapeur saturante (mmHg) via la loi d'Antoine.
    log10(Psat) = A - B / (C + T)
    """
    c = ANTOINE[composant]
    log_p = c['A'] - c['B'] / (c['C'] + T_celsius)
    return 10 ** log_p

def mmhg_to_kpa(p_mmhg):
    """Convertit mmHg → kPa (1 mmHg = 0.133322 kPa)"""
    return p_mmhg * 0.133322

def calculer_psat(T_celsius):
    """
    Retourne P1sat (benzène) et P2sat (toluène) en kPa pour une température T.
    """
    p1_mmhg = antoine_psat_mmhg('benzene', T_celsius)
    p2_mmhg = antoine_psat_mmhg('toluene', T_celsius)
    p1_kpa  = round(mmhg_to_kpa(p1_mmhg), 3)
    p2_kpa  = round(mmhg_to_kpa(p2_mmhg), 3)
    return p1_kpa, p2_kpa

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS calculs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT    NOT NULL DEFAULT 'Sans nom',
            date        TEXT    NOT NULL,
            temperature REAL    NOT NULL,
            x1          REAL    NOT NULL,
            x2          REAL    NOT NULL,
            p1sat       REAL    NOT NULL,
            p2sat       REAL    NOT NULL,
            p_bulle     REAL    NOT NULL,
            y1          REAL    NOT NULL,
            y2          REAL    NOT NULL,
            somme_yi    REAL    NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Base de données prête :", DB_PATH)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ══════════════════════════════════════════════════════════════════════════════
# CALCULS — Loi de Raoult
# ══════════════════════════════════════════════════════════════════════════════

def calculer_tout(x1, x2, p1_sat, p2_sat):
    p_bulle  = round(x1 * p1_sat + x2 * p2_sat, 4)
    y1       = round((x1 * p1_sat) / p_bulle, 4)
    y2       = round((x2 * p2_sat) / p_bulle, 4)
    somme_yi = round(y1 + y2, 4)
    return {
        'p_bulle':  p_bulle,
        'terme1':   round(x1 * p1_sat, 4),
        'terme2':   round(x2 * p2_sat, 4),
        'y1':       y1,
        'y2':       y2,
        'somme_yi': somme_yi,
        'verif_ok': abs(somme_yi - 1.0) < 0.001
    }

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculer', methods=['POST'])
def calculer():
    data = request.get_json()
    try:
        nom  = str(data.get('nom', 'Sans nom')).strip() or 'Sans nom'
        T    = float(data['temperature'])
        x1   = float(data['x1'])
        x2   = float(data['x2'])

        # ── Validations ──────────────────────────────────────────────
        if abs((x1 + x2) - 1.0) > 0.01:
            return jsonify({'erreur': f'x₁ + x₂ doit être égal à 1. Actuellement : {round(x1+x2,3)}'}), 400
        if x1 < 0 or x2 < 0 or x1 > 1 or x2 > 1:
            return jsonify({'erreur': 'Les fractions molaires doivent être comprises entre 0 et 1.'}), 400
        if T < 0 or T > 200:
            return jsonify({'erreur': 'Température doit être entre 0 et 200 °C.'}), 400

        # ── Calcul automatique de Psat via Antoine ───────────────────
        p1_sat, p2_sat = calculer_psat(T)
        
        # Calcul des valeurs en mmHg pour affichage
        p1_mmhg = round(antoine_psat_mmhg('benzene', T), 1)
        p2_mmhg = round(antoine_psat_mmhg('toluene', T), 1)

        # ── Calculs Raoult ───────────────────────────────────────────
        r = calculer_tout(x1, x2, p1_sat, p2_sat)

        # ── Sauvegarde BDD ───────────────────────────────────────────
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calculs
                (nom, date, temperature, x1, x2, p1sat, p2sat, p_bulle, y1, y2, somme_yi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            nom, datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            T, x1, x2, p1_sat, p2_sat,
            r['p_bulle'], r['y1'], r['y2'], r['somme_yi']
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        # ── Réponse JSON ─────────────────────────────────────────────
        return jsonify({
            'id': new_id,
            'antoine': {
                'p1sat_kpa': p1_sat,
                'p2sat_kpa': p2_sat,
                'p1sat_mmhg': p1_mmhg,
                'p2sat_mmhg': p2_mmhg,
            },
            'resultats': {
                'p_bulle': r['p_bulle'],
                'y1': r['y1'],
                'y2': r['y2'],
                'somme_yi': r['somme_yi'],
                'verif_ok': r['verif_ok']
            }
        })

    except (KeyError, ValueError) as e:
        return jsonify({'erreur': f'Données invalides : {str(e)}'}), 400


@app.route('/historique', methods=['GET'])
def historique():
    conn = get_db()
    rows = conn.execute('SELECT * FROM calculs ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/historique/<int:calc_id>', methods=['DELETE'])
def supprimer(calc_id):
    conn = get_db()
    conn.execute('DELETE FROM calculs WHERE id = ?', (calc_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Calcul #{calc_id} supprimé.'})

@app.route('/historique/tout', methods=['DELETE'])
def supprimer_tout():
    conn = get_db()
    conn.execute('DELETE FROM calculs')
    conn.commit()
    conn.close()
    return jsonify({'message': 'Historique vidé.'})


if __name__ == '__main__':
    init_db()
    print("🚀 Serveur démarré sur http://127.0.0.1:5000")
    app.run(debug=True)