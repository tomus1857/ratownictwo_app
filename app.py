import streamlit as st
import pandas as pd
import sqlite3
#Apka12
#Ap
st.set_page_config(page_title="Aplikacja Ratownictwa", page_icon="🚑", layout="wide")

conn = sqlite3.connect('database.db')
c = conn.cursor()

def create_table():
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user TEXT, 
                  message TEXT)''')
    conn.commit()


def add_message(user, message):
    c.execute('INSERT INTO messages (user, message) VALUES (?, ?)', (user, message))
    conn.commit()


def get_messages():
    c.execute('SELECT * FROM messages')
    data = c.fetchall()
    return data


create_table()


st.title("Aplikacja wspierająca zespoły ratownictwa")


data = pd.DataFrame({
    'lat': [37.7749, 34.0522, 40.7128, 51.5074, 48.8566],
    'lon': [-122.4194, -118.2437, -74.0060, -0.1278, 2.3522],
    'name': ['San Francisco', 'Los Angeles', 'New York', 'London', 'Paris'],
    'description': ['Zespół 1', 'Zespół 2', 'Zespół 3', 'Zespół 4', 'Zespół 5']
})


def create_map(data):
    st.subheader("Lokalizacja zespołów ratownictwa")
    st.map(data)


def chat_interface():
    st.subheader("Komunikator")

    if 'user' not in st.session_state:
        st.session_state['user'] = ''

    if st.session_state['user'] == '':
        st.session_state['user'] = st.text_input("Wprowadź swoje imię", key="username_input")
    else:
        st.text(f"Witaj, {st.session_state['user']}!")

        with st.form(key='chat_form', clear_on_submit=True):
            user_message = st.text_input("Twoja wiadomość", key="message_input")
            submit_button = st.form_submit_button(label='Wyślij')

            if submit_button and user_message:
                add_message(st.session_state['user'], user_message)

        messages = get_messages()
        for message in messages:
            st.write(f"{message[1]}: {message[2]}")


col1, col2 = st.columns(2)


with col1:
    create_map(data)

with col2:
    chat_interface()


conn.close()
