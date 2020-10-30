from flask import Flask, session, render_template
import os
from utils import db

app = Flask(__name__, template_folder='templates')

app.config['SECRET_KEY'] = os.getenv('USER_SERVICE_SECRET_KEY')


@app.route('/')
def catalog():
    # TODO: integrate with Login and get session['user_id'] automatically
    session['user_id'] = 0
    return f"** session ** user id is: {session['user_id']}"


@app.route('/test', methods=['GET'])
def get_current_signal():
    session_user_id = session['user_id']
    df = db.get_signals(session_user_id)
    table_html = df[['strategy_name', 'modified_date']].to_html()
    return table_html


def main():
    app.run(debug=True, threaded=True, host='0.0.0.0', port='5000')


if __name__ == "__main__":
    main()
