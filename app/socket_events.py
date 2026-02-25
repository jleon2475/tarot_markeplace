from flask_socketio import emit, join_room
from flask import session, request
from .extension import socketio, mysql

online_psychic = {}

@socketio.on('connect')
def handle_connect():
    print("cliente conectado")

    emit('update_psychic', {
            'psychics' : list(online_psychic.keys()),
            'count': len(online_psychic)
            })


@socketio.on('psychic_online')
def psychic_online():
    print("EVENTO psychic_online recibido")
    print("SESSION: ", dict(session))
    
    if session.get('user_role') == 'psychic':

        user_id = session.get('user_id')
        online_psychic[user_id] = request.sid

        print("=== PSIQUICO CONECTADO ===")
        print("Online: ", online_psychic)

        #print(f"Psiquico {user_id} conectado")

        emit('update_psychic', {
            'psychics' : list(online_psychic.keys()),
            'count': len(online_psychic)
            }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    role = session.get('user_role')
    
    if role == 'psychic' and user_id in online_psychic:
        del online_psychic[user_id]
        
        print("=== PSIQUICO DESCONECTADO ===")
        print("Online: ", online_psychic)
        
        #print(f"Psiquico{user_id} desconectado")

        #Notificar a todos los clientes que se actualizó la lista
        emit('update_psychic', {
            'psychic':list(online_psychic.keys()),
            'count':len(online_psychic)
            },broadcast=True)

    print("Usuario desconectado")    

#Usuario envia una pregunta
@socketio.on('send_question')
def handle_question(data):
    question = data['question']
    cards = data['cards']
    user_id = session.get('user_id')

    cur = mysql.connection.cursor()
    cur.execute("""INSERT INTO questions (user_id,card1,card2,card3,question) VALUES (%s,%s,%s,%s,%s)
                """, (user_id,cards[0],cards[1],cards[2],question))
    mysql.connection.commit()
    question_id = cur.lastrowid
    cur.close()

    room_name = f"question_{question_id}"

    #usuario entra a su room privado
    join_room(room_name)

    emit('new_question', {
        'question_id':question_id,
        'question':question,
        'cards': cards,
        'room': room_name
    }, broadcast=True)

#Psiquico responde
@socketio.on('send_answer')
def handle_answer(data):
    question_id = data['question_id']
    answer = data['answer']
    psychic_id = session.get('user_id')

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO answers (question_id, psychic_id,answer) 
        VALUE (%s,%s,%s)""",(question_id,psychic_id,answer))
    mysql.connection.commit()
    cur.close()

    room_name =f"question_{question_id}"

    emit('receive_answer',{
       'answer':answer
        },room=room_name)









