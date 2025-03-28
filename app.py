from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random
import datetime
import os

app = Flask(__name__)
app.secret_key = 'simple_secret_key'

# Database configuration (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'drops.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a simple Drop model
class Drop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    opened_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

# A small default dataset (extend to 50+ rows as required)
default_items = [
    {'item_name': 'AK-47 | Redline', 'rarity': 'Mil-Spec', 'price': 5.0},
    {'item_name': 'M4A1-S | Nitro', 'rarity': 'Mil-Spec', 'price': 4.5},
    {'item_name': 'SG 553 | Tiger Moth', 'rarity': 'Mil-Spec', 'price': 3.5},
    {'item_name': 'P90 | Grim', 'rarity': 'Mil-Spec', 'price': 2.5},
    
    {'item_name': 'AWP | Worm God', 'rarity': 'Restricted', 'price': 20.0},
    {'item_name': 'Desert Eagle | Conspiracy', 'rarity': 'Restricted', 'price': 15.0},
    {'item_name': 'Glock-18 | Fade', 'rarity': 'Restricted', 'price': 12.0},
    
    {'item_name': 'M4A4 | Desolate Space', 'rarity': 'Classified', 'price': 50.0},
    {'item_name': 'AK-47 | Fire Serpent', 'rarity': 'Classified', 'price': 60.0},
    
    {'item_name': 'AK-47 | Case Hardened', 'rarity': 'Covert', 'price': 250.0},
    {'item_name': 'M4A1-S | Hyper Beast', 'rarity': 'Covert', 'price': 300.0},
    
    {'item_name': 'Karambit | Doppler', 'rarity': 'Exceedingly Rare', 'price': 2000.0},
    {'item_name': 'Butterfly Knife | Fade', 'rarity': 'Exceedingly Rare', 'price': 2200.0},
]

# Global dataset – can be replaced via CSV upload.
items_dataset = default_items.copy()

# Define weighted drop probabilities (for simplicity)
rarity_weights = {
    'Mil-Spec': 80,
    'Restricted': 16,
    'Classified': 3,
    'Covert': 1,
    'Exceedingly Rare': 0.5
}

def simulate_case_open():
    # Choose a rarity based on weights
    rarities = list(rarity_weights.keys())
    weights = list(rarity_weights.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    available_items = [i for i in items_dataset if i['rarity'] == chosen_rarity]
    # Fallback: if no items of chosen rarity, pick any random item
    if not available_items:
        available_items = items_dataset
    return random.choice(available_items)

@app.route('/')
def home():
    total = Drop.query.count()
    return render_template('home.html', total=total)

@app.route('/open', methods=['GET', 'POST'])
def open_case():
    result = None
    if request.method == 'POST':
        result = simulate_case_open()
        drop = Drop(item_name=result['item_name'], rarity=result['rarity'], price=result['price'])
        db.session.add(drop)
        db.session.commit()
        flash(f"You got: {result['item_name']} ({result['rarity']})", 'success')
    return render_template('open_case.html', result=result)

@app.route('/inventory')
def inventory():
    drops = Drop.query.all()
    return render_template('inventory.html', drops=drops)

@app.route('/stats')
def stats():
    # Count drops by rarity for chart
    data = db.session.query(Drop.rarity, db.func.count(Drop.id)).group_by(Drop.rarity).all()
    labels = [d[0] for d in data]
    counts = [d[1] for d in data]
    return render_template('stats.html', labels=labels, counts=counts)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    global items_dataset
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                # CSV must have these columns:
                if not {'item_name', 'rarity', 'price'}.issubset(df.columns):
                    flash('CSV must include item_name, rarity, price columns.', 'danger')
                    return redirect(url_for('upload'))
                items_dataset = df.to_dict(orient='records')
                flash(f"Loaded {len(items_dataset)} items from CSV.", 'success')
                return redirect(url_for('home'))
            except Exception as e:
                flash(f"Error: {e}", 'danger')
                return redirect(url_for('upload'))
        else:
            flash('Please upload a valid CSV file.', 'danger')
            return redirect(url_for('upload'))
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)

