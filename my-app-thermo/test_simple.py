from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    try:
        return render_template('index_modern.html')
    except Exception as e:
        return f"Erreur template: {str(e)}"

@app.route('/test')
def test():
    return "Test OK - Application fonctionne"

if __name__ == '__main__':
    print("Test simple de l'application...")
    with app.test_client() as client:
        response = client.get('/test')
        print(f"Test route: {response.status_code} - {response.data.decode()}")
        
        response = client.get('/')
        print(f"Index route: {response.status_code}")
        if response.status_code != 200:
            print(f"Erreur: {response.data.decode()}")
    
    print("\nDémarrage de l'application sur http://127.0.0.1:5001")
    app.run(debug=True, host='127.0.0.1', port=5001)
