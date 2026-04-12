from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Vérifier si le template existe
        template_path = 'templates/index_modern.html'
        if not os.path.exists(template_path):
            return f"Template manquant: {template_path}"
        
        # Lire le template pour vérifier les erreurs
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier la syntaxe HTML basique
        if content.count('<html>') != content.count('</html>'):
            return "Erreur: Balises HTML non fermées correctement"
        
        if content.count('<body>') != content.count('</body>'):
            return "Erreur: Balises body non fermées correctement"
        
        # Si tout semble bon, essayer de rendre
        return render_template('index_modern.html')
        
    except Exception as e:
        import traceback
        error_details = f"Erreur: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return f"<pre>{error_details}</pre>"

@app.route('/test')
def test():
    return "<h1>Test OK</h1><p>L'application Flask fonctionne</p>"

if __name__ == '__main__':
    print("Démarrage de l'application minimale...")
    print("Accès: http://127.0.0.1:5003")
    app.run(debug=True, host='127.0.0.1', port=5003)
