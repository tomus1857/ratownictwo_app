import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import time
import random
import uuid
import streamlit.components.v1 as components
from math import radians, cos, sin, sqrt, atan2
import folium as F
from streamlit.components.v1 import html
import openrouteservice as ors

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

# Przykładowe dane do mapy
START_LAT = 54.6160  # Szerokość geograficzna Wejherowa
START_LON = 18.2453  # Długość geograficzna Wejherowa
DEST_LAT = 54.6220  # Szerokość geograficzna punktu docelowego
DEST_LON = 18.2390  # Długość geograficzna punktu docelowego

if 'lat' not in st.session_state:
    st.session_state['lat'] = START_LAT
if 'lon' not in st.session_state:
    st.session_state['lon'] = START_LON
if 'moving' not in st.session_state:
    st.session_state['moving'] = False  # Flaga oznaczająca, czy punkt się porusza
if 'blue_dot_visible' not in st.session_state:
    st.session_state['blue_dot_visible'] = True  # Flaga widoczności niebieskiej kropki
if 'returning' not in st.session_state:
    st.session_state['returning'] = False  # Flaga oznaczająca, czy punkt wraca na swoje miejsce
if 'route_coords' not in st.session_state:
    st.session_state['route_coords'] = []  # Lista współrzędnych trasy
if 'mode' not in st.session_state:
    st.session_state['mode'] = None  # Tryb transportu

# Funkcja do tworzenia mapy z kolorowymi markerami
def create_map(lat, lon, blue_visible, blue_lat=None, blue_lon=None, route_coords=None):
    st.subheader("Lokalizacja zespołów ratownictwa")
    # Utworzenie mapy
    m = F.Map(location=[lat, lon], zoom_start=15)
    # Dodanie czerwonego markera
    F.Marker(
        location=[lat, lon],
        popup="Zespół Ratownictwa",
        icon=F.Icon(color='red')
    ).add_to(m)
    # Dodanie niebieskiego markera, jeśli jest widoczny
    if blue_visible and blue_lat and blue_lon:
        F.Marker(
            location=[blue_lat, blue_lon],
            popup="Niebieska kropka",
            icon=F.Icon(color='blue')
        ).add_to(m)
    # Dodanie punktu docelowego
    F.Marker(
        location=[DEST_LAT, DEST_LON],
        popup="Punkt docelowy",
        icon=F.Icon(color='green')
    ).add_to(m)
    # Dodanie trasy, jeśli jest dostępna
    if route_coords:
        F.PolyLine(locations=route_coords,
                   color='purple',
                   weight=4,
                   tooltip="Route",
                   smooth_factor=0.1).add_to(m)
    return m

# Funkcja do rysowania drogi na mapie
def add_route(source, destination):
    API_KEY = '5b3ce3597851110001cf624879941ca8d54241dc9254a46513902f14'
    client = ors.Client(key=API_KEY)
    # Get directions between the two points
    directions_coordinates = [tuple(reversed(source)), tuple(reversed(destination))]
    route = client.directions(coordinates=directions_coordinates, profile='driving-car', format='geojson')
    # Extracting only coordinates
    routes_coords = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']]
    return routes_coords



# Rozdzielenie interfejsu na dwie kolumny: mapę i komunikator
col1, col2 = st.columns(2)

with col1:
    mode = st.radio("Wybierz tryb transportu", ("Helikopter", "Karetka"))

if mode == "Helikopter":
    with col1:
        if st.button("Simulate"):
            st.session_state['moving'] = True
            st.session_state['mode'] = "Helikopter"
        map_placeholder = st.empty()
    with col2:
        chat_interface()
    # Funkcja do aktualizacji lokalizacji bez migania
    def update_location_helikopter():
        lat_step = 0.0001
        lon_step = 0.0001
        while st.session_state['moving'] or st.session_state['returning']:
            if st.session_state['moving']:
                if abs(DEST_LAT - st.session_state['lat']) > lat_step:
                    st.session_state['lat'] += lat_step if DEST_LAT > st.session_state['lat'] else -lat_step
                if abs(DEST_LON - st.session_state['lon']) > lon_step:
                    st.session_state['lon'] += lon_step if DEST_LON > st.session_state['lon'] else -lon_step
                if abs(DEST_LAT - st.session_state['lat']) <= lat_step and abs(DEST_LON - st.session_state['lon']) <= lon_step:
                    st.session_state['blue_dot_visible'] = False
                    st.session_state['moving'] = False
                    st.session_state['returning'] = True
            elif st.session_state['returning']:
                if abs(START_LAT - st.session_state['lat']) > lat_step:
                    st.session_state['lat'] += lat_step if START_LAT > st.session_state['lat'] else -lat_step
                if abs(START_LON - st.session_state['lon']) > lon_step:
                    st.session_state['lon'] += lon_step if START_LON > st.session_state['lon'] else -lon_step
                if abs(START_LAT - st.session_state['lat']) <= lat_step and abs(START_LON - st.session_state['lon']) <= lon_step:
                    st.session_state['returning'] = False
            with map_placeholder.container():
                m = create_map(st.session_state['lat'], st.session_state['lon'], st.session_state['blue_dot_visible'],
                               blue_lat=DEST_LAT, blue_lon=DEST_LON)
                map_html = m._repr_html_()
                html(map_html, height=800)
            time.sleep(1)
            st.experimental_rerun()
    if st.session_state['mode'] == "Helikopter" and (st.session_state['moving'] or st.session_state['returning']):
        update_location_helikopter()
    else:
        with map_placeholder.container():
            m = create_map(st.session_state['lat'], st.session_state['lon'], st.session_state['blue_dot_visible'],
                           blue_lat=DEST_LAT, blue_lon=DEST_LON)
            map_html = m._repr_html_()
            html(map_html, height=800)
else:
    with col1:
        if st.button("Pomoc"):
            st.session_state['moving'] = True
            st.session_state['mode'] = "Karetka"
            source = (st.session_state['lat'], st.session_state['lon'])
            destination = (DEST_LAT, DEST_LON)
            route_coords = add_route(source, destination)
            st.session_state['route_coords'] = route_coords
        map_placeholder = st.empty()
    with col2:
        chat_interface()
    # Funkcja do aktualizacji lokalizacji bez migania dla karetki
    def update_location_karetka():
        route_coords = st.session_state['route_coords']
        while st.session_state['moving'] or st.session_state['returning']:
            if st.session_state['moving']:
                if len(route_coords) > 1:
                    next_point = route_coords.pop(0)
                    st.session_state['lat'], st.session_state['lon'] = next_point
                else:
                    st.session_state['blue_dot_visible'] = False
                    st.session_state['moving'] = False
                    st.session_state['returning'] = True
                    st.session_state['route_coords'] = add_route((DEST_LAT, DEST_LON), (START_LAT, START_LON))
                    route_coords = st.session_state['route_coords']
            elif st.session_state['returning']:
                if len(route_coords) > 1:
                    next_point = route_coords.pop(0)
                    st.session_state['lat'], st.session_state['lon'] = next_point
                else:
                    st.session_state['returning'] = False
            with map_placeholder.container():
                m = create_map(st.session_state['lat'], st.session_state['lon'], st.session_state['blue_dot_visible'], 
                               blue_lat=DEST_LAT, blue_lon=DEST_LON, route_coords=route_coords)
                map_html = m._repr_html_()
                html(map_html, height=800)
            time.sleep(1)
            st.experimental_rerun()
    if st.session_state['mode'] == "Karetka" and (st.session_state['moving'] or st.session_state['returning']):
        update_location_karetka()
    else:
        with map_placeholder.container():
            m = create_map(st.session_state['lat'], st.session_state['lon'], st.session_state['blue_dot_visible'],
                           blue_lat=DEST_LAT, blue_lon=DEST_LON, route_coords=st.session_state['route_coords'])
            map_html = m._repr_html_()
            html(map_html, height=800)



# Zamknięcie połączenia z bazą danych SQLite
conn.close()