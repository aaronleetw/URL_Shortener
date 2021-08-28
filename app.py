from flask import *
import pyrebase
from datetime import datetime
import pytz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import random
import os
# from dotenv import load_dotenv

# load_dotenv()


app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
config = {
    "apiKey": os.environ.get('apiKey'),
    "authDomain": os.environ.get('authDomain'),
    "databaseURL": os.environ.get('databaseURL'),
    "storageBucket": os.environ.get('storageBucket'),
    "serviceAccount": os.environ.get('serviceAccount'),
    "messagingSenderId": os.environ.get('messagingSenderId'),
    "appId": os.environ.get('appId'),
    "measurementId": os.environ.get('measurementId'),
}
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()
tz = pytz.timezone('Asia/Taipei')


def send_email(to, subject, html_content):
    message = Mail(
        from_email=os.environ.get('SENDGRID_FROM'),
        to_emails=to,
        subject=subject,
        html_content=html_content)
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(message)
    except Exception as e:
        print(e)


@ app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if 'is_logged_in' not in session or session['is_logged_in'] == False:
            return render_template('login.html', error=False)
        return redirect('/manage')
    elif request.method == 'POST':
        if 'is_logged_in' not in session or session['is_logged_in'] == False:
            try:
                user = auth.sign_in_with_email_and_password(
                    request.form['email'], request.form['password'])
                session['is_logged_in'] = True
                session['email'] = user['email']
                session['uid'] = user['localId']
                session['token'] = user['idToken']
                return redirect('/manage')
            except Exception as e:
                return render_template('login.html', error=True)
        else:
            return redirect('/manage')


@ app.route('/manage', methods=['GET'])
def manage():
    if 'is_logged_in' not in session or session['is_logged_in'] == False:
        return redirect('/')
    else:
        data = db.child("URLs").get(session['token']).val()
        if data is None:
            return render_template('manage.html', data={})
        return render_template('manage.html', data=data)


@ app.route('/manage/create', methods=['GET', 'POST'])
def create():
    if 'is_logged_in' not in session or session['is_logged_in'] == False:
        return redirect('/')
    else:
        if request.method == 'GET':
            return redirect('/manage')
        else:
            if db.child("URLs").child(request.form['short']).get().val() is not None:
                return render_template('create.html', edit=False, error=True)
            db.child("URLs").child(request.form['short']).child(
                "url").set(request.form['url'], session['token'])
            db.child("URLs").child(request.form['short']).child(
                "created").set(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), session['token'])
            return redirect('/manage')


@ app.route('/manage/bulk', methods=['GET', 'POST'])
def bulk():
    if 'is_logged_in' not in session or session['is_logged_in'] == False:
        return redirect('/')
    else:
        if request.method == 'GET':
            data = db.child("URLs").get(session['token']).val()
            if data is None:
                return render_template('bulk.html', data={})
            return render_template('bulk.html', data=data)
        else:
            for key in request.form:
                if (key.startswith("short-")):
                    db.child("URLs").child(
                        request.form[key]).child("url").set(request.form['url-' + key[6:]], session['token'])
                    db.child("URLs").child(request.form[key]).child(
                        "created").set(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), session['token'])
            return redirect('/manage')


@ app.route('/manage/edit/<short>', methods=['GET', 'POST'])
def edit(short):
    if 'is_logged_in' not in session or session['is_logged_in'] == False:
        return redirect('/')
    else:
        if request.method == 'GET':
            data = db.child("URLs").child(short).get().val()
            return render_template('create.html', edit=True, short=short, url=data['url'])
        else:
            db.child("URLs").child(request.form['short']).child(
                "url").set(request.form['url'], session['token'])
            db.child("URLs").child(request.form['short']).child(
                "created").set(datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S"), session['token'])
            return redirect('/manage')


@ app.route('/manage/delete/<short>', methods=['GET'])
def delete(short):
    if 'is_logged_in' not in session or session['is_logged_in'] == False:
        return redirect('/')
    else:
        db.child("URLs").child(short).remove(session['token'])
        return redirect('/manage')


@ app.route('/manage/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')


@ app.route('/manage/request', methods=['GET', 'POST'])
def requestacc():
    if request.method == 'POST':
        requests_data = db.child("Requests").get().val()
        time = datetime.now(tz).strftime("%m-%d-%y")
        if requests_data is not None and time in requests_data:
            return "Limit one request per day."
        ref = str(random.randint(1000, 9999))
        send_email(request.form['email'], 'Shortener Request',
                   'Thank you for submitting this request. We will get to you in a few days. Reference number: ' + ref)
        send_email(os.environ.get('ADMIN_EMAIL'), 'Shortener Request',
                   '<h1>New Shortener Request</h1><br> Email: '+request.form['email'] + '<br>Name: '+request.form['name'] + '<br>Reason: ' + request.form['why'] + '<br>IP: ' + str(request.remote_addr) + '<br> Reference Number: ' + ref)
        db.child("Requests").child(time).set(0)
        return "Thank you for submitting this request. We will get to you in a few days. Reference number: " + ref
    else:
        return render_template('request.html')


@ app.route('/<short>', methods=['GET'])
def routeredir(short):
    url = db.child("URLs").child(short).child("url").get().val()
    if url is None:
        abort(404)
    return redirect(url)


# if __name__ == '__main__':
#     app.run(debug=True)
