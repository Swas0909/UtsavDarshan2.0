from flask import Flask, render_template, redirect, url_for, request
from data import pandals, talukas

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', pandals=pandals)

@app.route('/locations')
def locations():
    return render_template('locations.html', talukas=talukas)

@app.route('/taluka/<taluka_name>')
def taluka_pandals(taluka_name):
    selected_taluka = next((t for t in talukas if t['name'].lower() == taluka_name.lower()), None)
    if not selected_taluka:
        return redirect(url_for('locations'))
    return render_template('taluka.html', taluka=selected_taluka)

@app.route('/pandal/<int:pandal_id>')
def pandal_detail(pandal_id):
    pandal = next((p for p in pandals if p['id'] == pandal_id), None)
    if not pandal:
        return redirect(url_for('index'))
    return render_template('pandal.html', pandal=pandal)

@app.route('/feedback', methods=['POST'])
def feedback():
    # For now, just print feedback to console (can be extended to save in DB or send email)
    user_feedback = request.form.get('feedback')
    print(f"Feedback received: {user_feedback}")
    return redirect(url_for('index'))

@app.route('/register_pandal', methods=['GET', 'POST'])
def register_pandal():
    if request.method == 'POST':
        # For now, just print registration data to console
        name = request.form.get('name')
        location = request.form.get('location')
        details = request.form.get('details')
        print(f"New pandal registration: {name}, {location}, {details}")
        return redirect(url_for('index'))
    return render_template('register_pandal.html')

if __name__ == '__main__':
    app.run(debug=True)
