import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time
import random
import uuid
import streamlit.components.v1 as components

# Konfiguracja strony Streamlit
st.set_page_config(page_title="Aplikacja Ratownictwa", page_icon="🚑", layout="wide")

# Połączenie z bazą danych SQLite
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Funkcja do tworzenia tabeli w bazie danych, jeśli nie istnieje
def create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, 
                  message TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  session_id TEXT)''')
    conn.commit()

# Funkcja do dodawania wiadomości do bazy danych
def add_message(user, message, session_id):
    c.execute('INSERT INTO messages (user, message, timestamp, session_id) VALUES (?, ?, ?, ?)', 
              (user, message, datetime.now(), session_id))
    conn.commit()

# Funkcja do pobierania wszystkich wiadomości z bazy danych
def get_messages(session_id):
    c.execute('SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC', (session_id,))
    data = c.fetchall()
    return data

# Inicjalizacja tabeli (uruchomienie tylko raz)
create_table()

# Tytuł aplikacji
st.title("Aplikacja wspierająca zespoły ratownictwa")

# Dane do wyświetlania na mapie
data = pd.DataFrame({
    'lat': [37.7749, 34.0522, 40.7128, 51.5074, 48.8566],
    'lon': [-122.4194, -118.2437, -74.0060, -0.1278, 2.3522],
    'name': ['San Francisco', 'Los Angeles', 'New York', 'London', 'Paris'],
    'description': ['Zespół 1', 'Zespół 2', 'Zespół 3', 'Zespół 4', 'Zespół 5']
})

# Funkcja do wyświetlania mapy z lokalizacją zespołów ratownictwa
def create_map(data):
    st.subheader("Lokalizacja zespołów ratownictwa")
    st.map(data)

# Funkcja do generowania odpowiedzi czatbota
def generate_bot_response(user_message, conversation_state):
    user_message = user_message.lower()
    response = "Dziękujemy za Twoją wiadomość. Pracujemy nad rozwiązaniem problemu."

    if conversation_state == 'initial':
        if 'pomoc' in user_message:
            response = "Ile osób potrzebuje pomocy? (Proszę podać liczbę)"
            conversation_state = 'num_people'
        elif 'awaria' in user_message:
            response = "Proszę opisać problem."
            conversation_state = 'awaiting_issue_description'
    elif conversation_state == 'num_people':
        if user_message.isdigit():
            response = "Proszę opisać stan poszkodowanych. Czy są przytomni? Czy oddychają? Jakie obrażenia zauważyłeś?"
            conversation_state = 'describe_condition'
        else:
            response = "Proszę podać liczbę osób potrzebujących pomocy."
    elif conversation_state == 'describe_condition':
        # Generowanie losowego czasu przybycia zespołów ratowniczych
        arrival_time = random.randint(15, 45)  # Losowy czas przybycia w minutach (od 15 do 45)
        response = f"Zespoły ratownictwa są w drodze. Przybliżony czas przybycia: {arrival_time} minut. Czy mogę w czymś jeszcze pomóc?"
        conversation_state = 'final'
    elif conversation_state == 'awaiting_issue_description':
        response = "Zgłoszenie zostało przyjęte. Zespoły ratownictwa są w drodze. Przybliżony czas przybycia zostanie określony. Czy mogę w czymś jeszcze pomóc?"
        conversation_state = 'final'

    return response, conversation_state

# Funkcja do interfejsu komunikatora
def chat_interface():
    st.subheader("Komunikator")

    if 'user' not in st.session_state:
        st.session_state['user'] = ''

    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(uuid.uuid4())

    if 'messages' not in st.session_state:
        st.session_state['messages'] = get_messages(st.session_state['session_id'])  # Initialize messages in session state

    if 'delayed_messages' not in st.session_state:
        st.session_state['delayed_messages'] = {}  # Store delayed messages

    if 'conversation_state' not in st.session_state:
        st.session_state['conversation_state'] = 'initial'  # Track conversation state

    if not st.session_state['user']:
        user_input = st.text_input("Wprowadź swoje imię", key="username_input")
        if user_input:
            st.session_state['user'] = user_input
            st.session_state['session_id'] = str(uuid.uuid4())  # Generate new session ID for new user
            st.rerun()  # Przeładowanie aplikacji po podaniu nazwy użytkownika

    if st.session_state['user']:
        st.write(f"Witaj, {st.session_state['user']}!")

        if len(st.session_state['messages']) == 0:
            initial_message = "Witaj, tu Ratownik SAR. Jak mogę Ci pomóc? Możliwości: [pomoc, awaria]"
            add_message("Ratownik SAR", initial_message, st.session_state['session_id'])
            st.session_state['messages'].insert(0, (None, "Ratownik SAR", initial_message, datetime.now(), st.session_state['session_id']))
            st.rerun()

        with st.form(key='message_form', clear_on_submit=True):
            message_input = st.text_area("Twoja wiadomość", key="message_input")
            submit_button = st.form_submit_button(label='Wyślij')

        if submit_button and message_input.strip():  # Sprawdzenie, czy wiadomość nie jest pusta
            st.write("Debug: Przed dodaniem wiadomości do bazy danych")
            add_message(st.session_state['user'], message_input, st.session_state['session_id'])
            st.session_state['messages'].insert(0, (None, st.session_state['user'], message_input, datetime.now(), st.session_state['session_id']))  # Append new message

            # Odpowiedź czatbota SAR na podstawie wiadomości użytkownika
            bot_response, new_state = generate_bot_response(message_input, st.session_state['conversation_state'])



            add_message("Ratownik SAR", bot_response, st.session_state['session_id'])
            st.session_state['messages'].insert(0, (None, "Ratownik SAR", bot_response, datetime.now(), st.session_state['session_id']))



            # Update conversation state
            st.session_state['conversation_state'] = new_state



            # Schedule the message for delayed display
            st.session_state['delayed_messages'][(st.session_state['user'], message_input)] = {
                'show_time': time.time() + random.uniform(3, 5)  # Time when "Wyświetlono" should be shown
            }


            # Odtworzenie dźwięku po wysłaniu wiadomości przez ratownika za pomocą JavaScript
            audio_html = """
            <audio autoplay>
                <source src="level-up-191997.mp3" type="audio/mpeg">
            </audio>
            """
            # Komunikat debugowania
            st.write("Debug: Odtwarzanie dźwięku")
            components.html(audio_html, height=0, width=0)
            

            st.rerun()  # Przeładowanie aplikacji po wysłaniu wiadomości



        # Wyświetlenie wszystkich wiadomości z sesji
        for message in st.session_state['messages']:
            user, text, timestamp, session_id = message[1], message[2], message[3], message[4]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            formatted_time = timestamp.strftime('%H:%M:%S')  # Formatowanie czasu
             # Wyświetlenie wiadomości
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{user}: {text}")
            with col2:
                if (user, text) in st.session_state['delayed_messages']:
                    details = st.session_state['delayed_messages'][(user, text)]
                    if time.time() >= details['show_time']:
                        st.write(f"*Wyświetlono o {formatted_time}*")

# Rozdzielenie interfejsu na dwie kolumny: mapę i komunikator
col1, col2 = st.columns(2)

with col1:
    create_map(data)  # Ensure the map is always rendered

with col2:
    chat_interface()  # Ensure the chat interface is always rendered

# Zamknięcie połączenia z bazą danych SQLite
conn.close()