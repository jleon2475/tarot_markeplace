from flask_socketio import emit, join_room
from flask import session, request
from .extension import socketio, mysql
import time, random

online_psychic = {}
pending_requests ={}

#Creando el temporizador para medir la contestación del psiquico
#Crear evento cuando el cliente solicita lectura
@socketio.on('request_reading')
def request_reading(data):

    cliente_id = session.get('user_id')
    psychic_id = data.get('psychic_id')
    
    room = f"reading_{cliente_id}_{psychic_id}"

    join_room(room)

    pending_requests[cliente_id] = {
        "psychic_id" : psychic_id,
        "status" : "waiting"
    }

    emit('reading_requested', {
        'room' : room,
        'timeout' : 60
    }, room=room)

    socketio.start_background_task(
        auto_cancel_request,
        cliente_id,
        psychic_id,
        room
    )
def auto_cancel_request(cliente_id,psychic_id,room):

    time.sleep(60)

    request = pending_requests.get(cliente_id)

    if request and request["status"] == "waiting":
        request["status"] = "cancelado"

        socketio.emit('reading_timeout',{
            'message':'El psiquico no contestó a tiempo'
        }, room=room)

        #Liberar psiquico
        if psychic_id in online_psychic:
            online_psychic[psychic_id]["available"] = True

#Cuando el psiquico acepta antes de los 60 segundos
@socketio.on('accept_reading')
def accept_reading(data):

    question_id = data.get('question_id')
    psychic_id = session.get('user_id')

    cur = mysql.connection.cursor()
    cur.execute("""
                UPDATE questions 
                SET status='accepted', psychic_id=%s
                WHERE id = %s AND status='pending'
                """, (psychic_id, question_id) )
    
    mysql.connection.commit()
    cur.close()

    room_name = f"question_{question_id}"

    join_room(room_name)

    emit('question_accepted', {
        'question_id': question_id
    }, room=room_name)

    
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

        print(f"Psiquico {user_id} conectado")

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
        
        print(f"Psiquico{user_id} desconectado")

        #Notificar a todos los clientes que se actualizó la lista
        emit('update_psychic', {
            'psychic':list(online_psychic.keys()),
            'count':len(online_psychic)
            },broadcast=True)

    print("Usuario desconectado")    

#Cliente envia una pregunta
@socketio.on('send_question')
def handle_question(data):

    question = data.get('question')
    user_id = session.get('user_id')
    print("Pregunta enviada:",question)
    
    cur = mysql.connection.cursor()
    #Seleccionar todas las cartas 
    cur.execute("""
                SELECT id,name,image FROM tarot_cards
                ORDER BY RAND() LIMIT 3""")
    
    cards = cur.fetchall()

    #Elegir 3 cartas únics aleatorias 
    ramdon_cards = random.sample(cards,3)

    card1 = ramdon_cards[0][0]
    card2 = ramdon_cards[1][0]
    card3 = ramdon_cards[2][0]
    
    #Insertar preguntas con cartas asignadas por el sistema
    cur.execute("""
                INSERT INTO questions (user_id, card1, card2, card3, questions, status)
                VALUES (%s,%s,%s,%s,%s, 'pending')
                """, (user_id, card1,card2,card3,question))

    mysql.connection.commit()
    question_id = cur.lastrowid
    cur.close()

    room_name = f"question_{question_id}"

    #usuario entra a su room privado
    join_room(room_name)

    socketio.start_background_task(
        auto_cancel_question,
        question_id,
        room_name
    )

    cards_data = []

    for card in cards:
        cards_data.append({
            "id": card[0],
            "name":card[1],
            "image":card[2]
        })


    emit('new_question', {
        'question_id':question_id,
        'question':question,
        'cards': cards_data,
        'room': room_name,
        'timeout': 60
    }, broadcast=True)

def auto_cancel_question(question_id,room_name):
    
    socketio.sleep(60)

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM questions WHERE id = %s",(question_id,))
    result = cur.fetchone()

    if result and result[0] == 'pending':
        cur.execute("UPDATE questions SET status = 'cancelled' WHERE id = %s", (question_id,))
        mysql.connection.commit()

        socketio.emit('question_timeout', {
            'question_id':question_id,
            'message': 'Ningun psiquico respondió a tiempo'
        }, room = room_name)

    cur.close()
 
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

#Para tomar la pregunta y bloquearla apenas conteste 1 psiquico
@socketio.on('take_question')
def take_question(data):
    question_id = data['question_id']
    psychic_id = session.get('user_id')

    if session.get('user_role')!='psychic':
        return

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE questions
        SET status = 'taken', taken_by=%s
        WHERE id=%s AND status='open'""",(psychic_id,question_id))
    
    mysql.connection.commit()
    
    if cur.rowcount == 1:
        emit('question_taken', {
            'question_id': question_id,
            'psychic_id': psychic_id
            }, broadcast=True)
        
    else:
        #ya estaba tomada la pregunta
        emit('question_already_taken', {
            'question_id':question_id
        })

    cur.close()