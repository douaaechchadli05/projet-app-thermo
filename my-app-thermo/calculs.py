from models import db, PressionSaturante, HistoriqueCalculs
from flask_login import current_user

# Constantes d'Antoine (log10(P) = A - B/(C+T), P en mmHg, T en °C)
ANTOINE = {
    'benzene': {'A': 6.90565, 'B': 1211.033, 'C': 220.790},
    'toluene': {'A': 6.95334, 'B': 1343.943, 'C': 219.377}
}

def calculer_pression_saturante(composant, T):
    c = ANTOINE[composant]
    log_p = c['A'] - c['B'] / (c['C'] + T)
    p_mmhg = 10 ** log_p
    p_kpa = p_mmhg * 0.133322  # Conversion mmHg to kPa
    return round(p_kpa, 3)

def loi_raoult(x1, x2, p1_sat, p2_sat):
    p_bulle = x1 * p1_sat + x2 * p2_sat
    y1 = (x1 * p1_sat) / p_bulle if p_bulle > 0 else 0
    y2 = (x2 * p2_sat) / p_bulle if p_bulle > 0 else 0
    return {
        'p_bulle': round(p_bulle, 3),
        'y1': round(y1, 4),
        'y2': round(y2, 4),
        'somme_y': round(y1 + y2, 4)
    }

def effectuer_calcul(T, x_toluene, x_benzene):
    p_toluene = calculer_pression_saturante('toluene', T)
    p_benzene = calculer_pression_saturante('benzene', T)
    result = loi_raoult(x_toluene, x_benzene, p_toluene, p_benzene)
    # Sauvegarder dans historique si user connecté
    if current_user.is_authenticated:
        hist = HistoriqueCalculs(
            user_id=current_user.id,
            fraction_toluene=x_toluene,
            fraction_benzene=x_benzene,
            pression_toluene=p_toluene,
            pression_benzene=p_benzene
        )
        db.session.add(hist)
        db.session.commit()
    return {
        'temperature': T,
        'x_toluene': x_toluene,
        'x_benzene': x_benzene,
        'p_toluene': p_toluene,
        'p_benzene': p_benzene,
        **result
    }