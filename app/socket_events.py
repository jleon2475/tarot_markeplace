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

        #Guarda en el diccionario los psiquicos conectados
        online_psychic[user_id] = request.sid

        #Entra a sala de psiquicos
        join_room("psychics")

        print("Psiquico unido al chat")

        emit('update_psychic', {
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

    print("Data Recibida: ", data)

    question = data.get('question')
    cards = data.get('cards')

    user_id = session.get('user_id')

    card1 = cards[0]["id"]
    card2 = cards[1]["id"]
    card3 = cards[2]["id"]
    
    cur = mysql.connection.cursor()

    #Seleccionar todas las cartas     
    cur.execute("""
                INSERT INTO questions (user_id, card1, card2, card3, questions, status, taken_by)
                VALUES (%s,%s,%s,%s,%s, 'pending',NULL)
                """, (user_id, card1,card2,card3,question))

    mysql.connection.commit()

    question_id = cur.lastrowid

    cur.close()

    emit('new_question', {
        'question_id':question_id,
        'question':question,
        'cards': cards,        
    }, room='psychics')
    print("enviando pregunta a psiquicos", question)

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
        VALUES (%s,%s,%s)""",(question_id,psychic_id,answer))
    mysql.connection.commit()
    cur.close()

    room_name =f"question_{question_id}"

    emit('receive_answer',{
       'answer':answer
        },room=room_name)

#Para tomar la pregunta y bloquearla apenas conteste 1 psiquico
@socketio.on('take_question')
def take_question(data):
    
    question_id = data.get("question_id")
    psychic_id = session.get("user_id")

    if session.get("user_role") != 'psychic':
        return

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT taken_by
        FROM questions WHERE id=%s""",(question_id,))
    
    result = cur.fetchone()

    print("Esto es el resultado", result)

    if result and result[0] is None:
        cur.execute(""" 
                    UPDATE questions 
                    SET taken_by = %s, status = 'taken' 
                    WHERE id = %s AND taken_by is NULL""", (psychic_id,question_id))    
    
        mysql.connection.commit()
        print("Filas afectadas:", cur.rowcount)

    if cur.rowcount > 0:

        room_name = f"question_{question_id}"
        
        join_room(room_name)

        emit("open_chat", {
            "question_id" : question_id
        })

        socketio.emit("question_taken",{
            "question_id": question_id,
            "psychic_id":psychic_id
        }, skip_sid = request.sid)

    else:
        emit("already_take", {
            "question_id": question_id
        })   

    cur.close()
#Fin socketio.on(take_question)

@socketio.on("join_question_room")
def join_question_room(data):

    question_id = data.get("question_id")

    room_name = f"question_{question_id}"

    join_room(room_name)

    print("Usuario unido a ", room_name)

#Evento para enviar mensajes a sala de chat privado
@socketio.on('send_chat_message')
def send_chat_message(data):

    question_id = data.get('question_id')
    message = data.get('message')
    user_name = session.get('user_name')

    room_name = f'question_{question_id}'

    emit('receive_chat_message',
         {'user': user_name,
          'message':message        
    },room=room_name)
    




