from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)

app.config['SECRET_KEY'] = 'dsfzapwff0ofsqdf2ksd'


socketio = SocketIO(app, manage_session=False)
socketio.init_app(app, cors_allowed_origins="*")
data = {}
users = []

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/admin211', methods=['GET', 'POST'])
def admin():    
    return render_template('admin.html')

@app.route('/update_vidurl', methods=['GET', 'POST'])
def update_vidurl():
    data['video_url'] = str(request.form['videoUrl']).strip(' \t\n\r') or None
    return render_template('chatroom.html', session = session, data=data)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    prev_url_endpoint = str(request.referrer).split('/')[-1]
    admin_url_endpoint = str(url_for('admin')).strip('/')
    
    if(request.method == 'POST'):        
        username = str(request.form['username']).strip(' \t\n\r').capitalize() or None
        room = str(request.form['room']).strip(' \t\n\r').upper() or None
        if("password" in request.form):
            pwd = str(request.form['password']).strip(' \t\n\r') or None
        if(username in users):
            error = "Username already logged in. Try another name."
            return render_template('index.html', error=error)
        if(username == None or room == None):
            error = "Check your credentials"
            return render_template('index.html', error=error)
        elif(prev_url_endpoint == admin_url_endpoint):
            if(username =='Admin' and pwd == 'password'):
                session['is_admin_logged_in'] = True                        
                data['video_url'] = request.form['videoUrl']
                session['username'] = username
                session['room'] = room
                return render_template('chatroom.html', session = session, data = data)
            else:
                return redirect(url_for('admin'))        
        elif(request.method=='POST' and request.referrer != url_for('admin')):            
            if(username == "Admin"):
                error = "Choose another name"
                return render_template('index.html', error=error)
            session['username'] = username
            session['room'] = room
            return render_template('chatroom.html', session = session, data = data)
        else:        
            return redirect(url_for('index'))

    if(request.method == 'GET'):
        return redirect(url_for('index'))

@socketio.on('join', namespace='/chat')
def join(message):    
    room = session.get('room')
    username = session.get('username')
    join_room(room)
    users.append(username)
    print(users)
    emit('status', {'msg':  session.get('username') + ' entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    print(message['msg'])
    room = session.get('room')
    emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)    


@socketio.on('left', namespace='/chat')
def left(message):
    print(users)
    room = session.get('room')
    username = session.get('username')
    if(username == "Admin"):
        data={}
        session['is_admin_logged_in'] = False
    leave_room(room)
    users.remove(username)
    session.clear()
    emit('status', {'msg': username + ' left the room.'}, room=room)

@socketio.on('disconnect', namespace='/chat')
def disconnect_user():
    room = session.get('room')
    username = session.get('username')
    if(username == "Admin"):
        data={}
        session['is_admin_logged_in'] = False
    leave_room(room)
    users.remove(username)
    session.clear()
    emit('status', {'msg': 'Network issues...user: ' + username + ' disconnected.'}, room=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)