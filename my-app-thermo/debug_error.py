import sys
import traceback
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    try:
        print("Tentative de rendu du template index_modern.html")
        return render_template('index_modern.html')
    except Exception as e:
        print(f"Erreur dans le template: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return f"Erreur template: {str(e)}"

@app.route('/debug')
def debug():
    try:
        import os
        template_path = 'templates/index_modern.html'
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"Template existe, taille: {len(content)} chars"
        else:
            return f"Template manquant: {template_path}"
    except Exception as e:
        return f"Erreur debug: {str(e)}"

@app.route('/simple')
def simple():
    return "<h1>Page simple fonctionne</h1><p>Ceci est un test pour vérifier que Flask fonctionne</p>"

if __name__ == '__main__':
    print("Test de diagnostic...")
    with app.test_client() as client:
        print("Test route simple:")
        response = client.get('/simple')
        print(f"  Status: {response.status_code}")
        
        print("\nTest route debug:")
        response = client.get('/debug')
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.data.decode()}")
        
        print("\nTest route index:")
        response = client.get('/')
        print(f"  Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Error: {response.data.decode()}")
    
    print("\nDémarrage du serveur de test sur http://127.0.0.1:5002")
    app.run(debug=True, host='127.0.0.1', port=5002)
