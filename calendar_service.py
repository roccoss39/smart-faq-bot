"""
Google Calendar integration for Salon Kleopatra Bot
Obsługuje umawianie, sprawdzanie terminów i zarządzanie wizytami
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import logging
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

# KONFIGURACJA ZAAWANSOWANA:
class CalendarService:
    def __init__(self, credentials_file='credentials.json', calendar_id=None):
        self.credentials_file = credentials_file
        # Użyj zmiennej środowiskowej - BEZ domyślnego ID!
        self.calendar_id = calendar_id or os.getenv('GOOGLE_CALENDAR_ID')
        
        if not self.calendar_id:
            logger.warning("⚠️ Brak GOOGLE_CALENDAR_ID w zmiennych środowiskowych")
            logger.warning("💡 Dodaj GOOGLE_CALENDAR_ID do .env aby włączyć funkcje kalendarza")
        
        self.timezone = 'Europe/Warsaw'
        self.service = None
        
        # Godziny pracy salonu
        self.working_hours = {
            'monday': (9, 19),      # Prościej: (start, end)
            'tuesday': (9, 19),
            'wednesday': (9, 19),
            'thursday': (9, 19),
            'friday': (9, 19),
            'saturday': (9, 16),
            'sunday': None
        }
        
        # 🔧 KONFIGURACJA WEDŁUG USŁUGI
        self.SERVICE_CONFIG = {
            'Strzyżenie': {'max_clients': 3, 'duration': 30},
            'Farbowanie': {'max_clients': 1, 'duration': 90},  # Długa usługa - jeden klient
            'Pasemka': {'max_clients': 1, 'duration': 120},
            'default': {'max_clients': 2, 'duration': 45}
        }
        
        self._init_service()
    
    def _init_service(self):
        """Inicjalizacja Google Calendar API"""
        try:
            if not os.path.exists(self.credentials_file):
                logger.error(f"❌ Brak pliku credentials: {self.credentials_file}")
                return False
                
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("✅ Google Calendar API zainicjalizowane")
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd inicjalizacji Google Calendar: {e}")
            return False
    
    def is_available(self):
        """Sprawdź czy serwis jest dostępny"""
        return self.service is not None
    
    def get_available_slots(self, days_ahead=7, slot_duration=60):
        """
        Pobierz dostępne terminy na najbliższe dni
        
        Args:
            days_ahead (int): Ile dni do przodu sprawdzać
            slot_duration (int): Długość slotu w minutach
            
        Returns:
            list: Lista dostępnych terminów
        """
        if not self.service:
            logger.error("❌ Calendar service nie jest zainicjalizowany")
            return []
        
        try:
            available_slots = []
            tz = pytz.timezone(self.timezone)
            days_checked = 0
            current_day = 0
            
            # Sprawdzaj dni aż znajdziesz wystarczająco dni roboczych
            while days_checked < days_ahead and current_day < 21:  # 3 tygodnie
                date = datetime.now(tz) + timedelta(days=current_day)
                day_name = date.strftime('%A').lower()
                
                # Sprawdź czy dzień roboczy
                if day_name != 'sunday' and self.working_hours.get(day_name):
                    day_slots = self._get_day_available_slots(date, slot_duration)
                    available_slots.extend(day_slots)
                    days_checked += 1
                    
                current_day += 1
            
            # Sortuj po dacie i zwróć max 10
            available_slots.sort(key=lambda x: x['datetime'])
            
            # LEPSZE ROZWIĄZANIE - po kilka slotów z każdego dnia:
            from collections import defaultdict
            slots_by_day = defaultdict(list)
            for slot in available_slots:
                slots_by_day[slot['day_name']].append(slot)

            # Weź po 3-4 sloty z każdego dnia
            final_slots = []
            for day_name, day_slots in slots_by_day.items():
                final_slots.extend(day_slots[:4])  # Max 4 sloty z każdego dnia
                
            final_slots.sort(key=lambda x: x['datetime'])
            return final_slots[:20]  # Max 20 slotów total
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania terminów: {e}")
            return []
    
    def _get_day_available_slots(self, date, slot_duration):
        """Pobierz dostępne sloty dla konkretnego dnia"""
        day_name = date.strftime('%A').lower()
        work_hours = self.working_hours.get(day_name)
        
        if not work_hours:
            return []
        
        # Pobierz zajęte terminy
        start_of_day = date.replace(hour=0, minute=0, second=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            busy_times = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                if start and end:
                    busy_times.append((start, end))
            
            # Znajdź wolne sloty
            available_slots = []
            work_start, work_end = work_hours
            
            now = datetime.now(pytz.timezone(self.timezone))
            
            for hour in range(work_start, work_end):
                for minute in [0, 30]:  # Co 30 minut
                    slot_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    slot_end = slot_time + timedelta(minutes=slot_duration)
                    
                    # Sprawdź czy slot nie jest w przeszłości
                    if slot_time <= now:
                        continue
                    
                    # Sprawdź czy nie wykracza poza godziny pracy
                    if slot_end.hour > work_end:
                        continue
                    
                    # Sprawdź czy nie koliduje z zajętymi terminami
                    if not self._is_time_busy(slot_time, slot_end, busy_times):
                        available_slots.append({
                            'datetime': slot_time,
                            'display': slot_time.strftime('%A %d.%m %H:%M'),
                            'iso': slot_time.isoformat(),
                            'day_name': self._get_polish_day_name(slot_time.strftime('%A'))
                        })
        
            return available_slots
            
        except Exception as e:
            logger.error(f"❌ Błąd pobierania slotów dla {date}: {e}")
            return []
    
    def _is_time_busy(self, start_time, end_time, busy_times):
        """Sprawdź czy termin koliduje z zajętymi"""
        for busy_start, busy_end in busy_times:
            # Konwertuj na datetime
            if isinstance(busy_start, str):
                try:
                    busy_start = datetime.fromisoformat(busy_start.replace('Z', '+00:00'))
                    if busy_start.tzinfo is None:
                        busy_start = pytz.timezone(self.timezone).localize(busy_start)
                except:
                    continue
                    
            if isinstance(busy_end, str):
                try:
                    busy_end = datetime.fromisoformat(busy_end.replace('Z', '+00:00'))
                    if busy_end.tzinfo is None:
                        busy_end = pytz.timezone(self.timezone).localize(busy_end)
                except:
                    continue
            
            # Sprawdź kolizję
            if start_time < busy_end and end_time > busy_start:
                return True
        return False
    
    def create_appointment(self, client_name, client_phone, service_type, appointment_time, duration_minutes=60):
        """
        Utwórz wizytę w kalendarzu
        
        Args:
            client_name (str): Imię klienta
            client_phone (str): Telefon klienta
            service_type (str): Rodzaj usługi
            appointment_time (datetime): Czas wizyty
            duration_minutes (int): Długość wizyty w minutach
            
        Returns:
            str|False: ID wydarzenia lub False w przypadku błędu
        """
        if not self.service:
            logger.error("❌ Calendar service nie jest zainicjalizowany")
            return False
        
        try:
            # Sprawdź maksymalną liczbę klientów dla danej usługi
            service_config = self.SERVICE_CONFIG.get(service_type, self.SERVICE_CONFIG['default'])
            max_clients = service_config['max_clients']
            duration_minutes = service_config['duration']
            
            end_time = appointment_time + timedelta(minutes=duration_minutes)
            
            event = {
                'summary': f'{service_type} - {client_name}',
                'description': (f'👤 Klient: {client_name}\n'
                              f'📞 Telefon: {client_phone}\n'
                              f'💄 Usługa: {service_type}\n'
                              f'🤖 Umówione przez Facebook Bot\n'
                              f'📅 Data: {appointment_time.strftime("%d.%m.%Y %H:%M")}'),
                'start': {
                    'dateTime': appointment_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},  # Dzień wcześniej
                        {'method': 'popup', 'minutes': 60},       # Godzinę wcześniej
                    ],
                },
            }
            
            created_event = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            event_id = created_event.get('id')
            logger.info(f"✅ Utworzono wizytę: {event_id} dla {client_name}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ Błąd tworzenia wizyty: {e}")
            return False
    
    def cancel_appointment(self, event_id):
        """Anuluj wizytę"""
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Anulowano wizytę: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd anulowania wizyty: {e}")
            return False
    
    def _get_polish_day_name(self, english_day):
        """Konwertuj angielską nazwę dnia na polską"""
        days = {
            'Monday': 'Poniedziałek',
            'Tuesday': 'Wtorek', 
            'Wednesday': 'Środa',
            'Thursday': 'Czwartek',
            'Friday': 'Piątek',
            'Saturday': 'Sobota',
            'Sunday': 'Niedziela'
        }
        return days.get(english_day, english_day)

# Globalna instancja - singleton
calendar_service = None

def get_calendar_service():
    """Pobierz globalną instancję kalendarza"""
    global calendar_service
    if calendar_service is None:
        calendar_service = CalendarService()
    return calendar_service

# Funkcje pomocnicze dla backward compatibility
def get_available_slots(days_ahead=7):
    """Wrapper function dla kompatybilności"""
    return get_calendar_service().get_available_slots(days_ahead)

def create_appointment(client_name, client_phone, service_type, appointment_time, duration_minutes=60):
    """Wrapper function dla kompatybilności"""
    return get_calendar_service().create_appointment(
        client_name, client_phone, service_type, appointment_time, duration_minutes
    )

def cancel_appointment(client_name, client_phone, appointment_day, appointment_time):
    """Anuluj wizytę w kalendarzu Google"""
    try:
        calendar_service = get_calendar_service()
        tz = pytz.timezone('Europe/Warsaw')
        
        # 🔧 POPRAWKA - użyj TEGO SAMEGO ALGORYTMU co w tworzeniu wizyt
        day_map = {
            'poniedziałek': 0, 'wtorek': 1, 'środa': 2, 
            'czwartek': 3, 'piątek': 4, 'sobota': 5,
            'niedziela': 6
        }
        
        # Konwertuj na małe litery
        appointment_day_lower = appointment_day.lower()
        target_day = day_map.get(appointment_day_lower)
        
        if target_day is None:
            logger.error(f"❌ Nieprawidłowy dzień: {appointment_day}")
            return False
        
        # 🔧 KLUCZOWA POPRAWKA - użyj DOKŁADNIE tej samej logiki co create_appointment!
        now = datetime.now(tz)
        current_weekday = now.weekday()
        
        # Znajdź następny dzień tygodnia (może być dziś, jeśli jest późno)
        days_ahead = (target_day - current_weekday) % 7
        
        # 🔧 WAŻNE: Jeśli to dziś, ale późno - sprawdź czy wizyta mogła być na dziś
        if days_ahead == 0 and now.hour >= 18:  # Po 18:00 - wizyta na przyszły tydzień
            days_ahead = 7
        elif days_ahead == 0:  # Dziś, ale wcześnie - może być na dziś
            pass  # Zostaw days_ahead = 0
            
        appointment_date = now + timedelta(days=days_ahead)
        
        # Ustaw godzinę
        time_parts = appointment_time.split(':')
        start_datetime = appointment_date.replace(
            hour=int(time_parts[0]), 
            minute=int(time_parts[1]), 
            second=0, 
            microsecond=0
        )
        
        # 🔧 DEBUG - pokaż szukaną datę
        logger.info(f"🔍 Szukam wizyty na: {start_datetime.strftime('%Y-%m-%d %H:%M')} (dzień: {appointment_day})")
        
        # 🔧 ALTERNATYWNE PODEJŚCIE - szukaj w zakresie ±7 dni
        search_start = start_datetime - timedelta(days=7)
        search_end = start_datetime + timedelta(days=7)
        
        logger.info(f"🔍 Zakres wyszukiwania: {search_start.strftime('%Y-%m-%d')} do {search_end.strftime('%Y-%m-%d')}")
        
        events = calendar_service.service.events().list(
            calendarId=calendar_service.calendar_id,
            timeMin=search_start.isoformat(),
            timeMax=search_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events_list = events.get('items', [])
        logger.info(f"🔍 Znaleziono {len(events_list)} wydarzeń w zakresie")
        
        # Znajdź wizytę do anulowania
        for event in events_list:
            event_start = event['start'].get('dateTime')
            if not event_start:
                continue
                
            # Parsuj czas wydarzenia
            event_datetime = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
            event_datetime = event_datetime.astimezone(tz)
            
            summary = event.get('summary', '')
            description = event.get('description', '')
            
            # 🔧 ULEPSZONE WARUNKI DOPASOWANIA:
            # 1. Ten sam czas (godzina:minuta)
            time_match = (event_datetime.hour == int(time_parts[0]) and 
                         event_datetime.minute == int(time_parts[1]))
            
            # 2. Imię w tytule lub opisie (case insensitive)
            name_match = client_name.lower() in summary.lower() or client_name.lower() in description.lower()
            
            # 3. Telefon w opisie
            phone_match = client_phone in description
            
            # 4. Dzień tygodnia się zgadza
            event_weekday = event_datetime.weekday()
            day_match = event_weekday == target_day
            
            logger.info(f"🔍 Sprawdzam: {summary} - {event_start}")
            logger.info(f"   ⏰ Time match: {time_match} ({event_datetime.hour}:{event_datetime.minute:02d} vs {time_parts[0]}:{time_parts[1]})")
            logger.info(f"   👤 Name match: {name_match} ({client_name.lower()} in {summary.lower()})")
            logger.info(f"   📞 Phone match: {phone_match} ({client_phone} in description)")
            logger.info(f"   📅 Day match: {day_match} (weekday {event_weekday} vs {target_day})")
            
            if time_match and day_match and (name_match or phone_match):
                # USUŃ WIZYTĘ
                try:
                    calendar_service.service.events().delete(
                        calendarId=calendar_service.calendar_id,
                        eventId=event['id']
                    ).execute()
                    
                    logger.info(f"✅ Anulowano wizytę: {summary} - {event_start}")
                    return {
                        'success': True,
                        'event_title': summary,
                        'event_time': event_start,
                        'event_id': event['id']
                    }
                    
                except Exception as delete_error:
                    logger.error(f"❌ Błąd usuwania wydarzenia: {delete_error}")
                    return False
        
        # Nie znaleziono wizyty
        logger.warning(f"❌ Nie znaleziono wizyty: {client_name}, {appointment_day} {appointment_time}")
        logger.warning(f"❌ Szukano na: {start_datetime.strftime('%Y-%m-%d %H:%M')}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Błąd anulowania wizyty: {e}")
        return False

def get_upcoming_appointments(days_ahead=14):
    """Pobierz nadchodzące wizyty z kalendarza"""
    try:
        calendar_service = get_calendar_service()  # ← POPRAWKA: użyj get_calendar_service()
        
        if not calendar_service.service:
            logger.error("❌ Calendar service nie jest zainicjalizowany")
            return []
        
        # Zakres czasu
        tz = pytz.timezone('Europe/Warsaw')
        now = datetime.now(tz)
        time_max = now + timedelta(days=days_ahead)
        
        # Pobierz wydarzenia
        events_result = calendar_service.service.events().list(
            calendarId=calendar_service.calendar_id,  # ← POPRAWKA: użyj calendar_id z instancji
            timeMin=now.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        appointments = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            appointments.append({
                'id': event['id'],
                'summary': event.get('summary', 'Bez tytułu'),
                'start': start,
                'description': event.get('description', ''),
                'location': event.get('location', '')
            })
        
        logger.info(f"📅 Pobrano {len(appointments)} wizyt z kalendarza")
        return appointments
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania wizyt: {e}")
        return []

# DODAJ na końcu calendar_service.py:

def get_available_slots_for_day(target_day_name, slot_duration=30):
    """
    Pobierz WSZYSTKIE dostępne terminy dla konkretnego dnia
    
    Args:
        target_day_name (str): Nazwa dnia po polsku (np. "środa", "piątek")
        slot_duration (int): Długość slotu w minutach
        
    Returns:
        list: Wszystkie dostępne terminy dla tego dnia
    """
    calendar_service = get_calendar_service()
    
    if not calendar_service.service:
        logger.error("❌ Calendar service nie jest zainicjalizowany")
        return []
    
    try:
        # Mapowanie polskich nazw dni
        day_map = {
            'poniedziałek': 0, 'wtorek': 1, 'środa': 2, 
            'czwartek': 3, 'piątek': 4, 'sobota': 5, 'niedziela': 6
        }
        
        target_day_lower = target_day_name.lower()
        target_weekday = day_map.get(target_day_lower)
        
        if target_weekday is None:
            logger.error(f"❌ Nieprawidłowy dzień: {target_day_name}")
            return []
        
        # Znajdź najbliższy dzień o tej nazwie
        tz = pytz.timezone('Europe/Warsaw')
        now = datetime.now(tz)
        current_weekday = now.weekday()
        
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0 and now.hour >= 18:  # Po 18:00 - następny tydzień
            days_ahead = 7
        elif days_ahead == 0:  # Dziś, ale wcześnie
            pass
            
        target_date = now + timedelta(days=days_ahead)
        
        logger.info(f"🔍 Szukam terminów na: {target_date.strftime('%Y-%m-%d')} ({target_day_name})")
        
        # Pobierz wszystkie sloty dla tego dnia
        day_slots = calendar_service._get_day_available_slots(target_date, slot_duration)
        
        # Sortuj po godzinie
        day_slots.sort(key=lambda x: x['datetime'])
        
        logger.info(f"✅ Znaleziono {len(day_slots)} wolnych terminów na {target_day_name}")
        return day_slots
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania terminów dla {target_day_name}: {e}")
        return []
    
def verify_appointment_exists(client_name, client_phone, appointment_datetime, service_type):
    """
    Weryfikuje czy spotkanie rzeczywiście istnieje w kalendarzu Google
    
    Args:
        client_name (str): Imię klienta
        client_phone (str): Telefon klienta  
        appointment_datetime (datetime): Czas wizyty
        service_type (str): Rodzaj usługi
        
    Returns:
        dict|False: Informacje o wydarzeniu lub False jeśli nie istnieje
    """
    try:
        calendar_service = get_calendar_service()
        
        if not calendar_service.service:
            logger.error("❌ Calendar service nie jest zainicjalizowany")
            return False
        
        # Sprawdź w zakresie ±2 godzin od planowanego czasu
        search_start = appointment_datetime - timedelta(hours=2)
        search_end = appointment_datetime + timedelta(hours=2)
        
        logger.info(f"🔍 Weryfikacja spotkania: {client_name} na {appointment_datetime.strftime('%Y-%m-%d %H:%M')}")
        
        events = calendar_service.service.events().list(
            calendarId=calendar_service.calendar_id,
            timeMin=search_start.isoformat(),
            timeMax=search_end.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events_list = events.get('items', [])
        
        for event in events_list:
            event_start = event['start'].get('dateTime')
            if not event_start:
                continue
                
            # Parsuj czas wydarzenia
            event_datetime = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
            event_datetime = event_datetime.astimezone(pytz.timezone('Europe/Warsaw'))
            
            summary = event.get('summary', '')
            description = event.get('description', '')
            
            # Sprawdź dopasowanie
            time_match = abs((event_datetime - appointment_datetime).total_seconds()) < 300  # ±5 minut
            name_match = client_name.lower() in summary.lower() or client_name.lower() in description.lower()
            phone_match = client_phone in description
            service_match = service_type.lower() in summary.lower() or service_type.lower() in description.lower()
            
            if time_match and (name_match or phone_match) and service_match:
                logger.info(f"✅ Spotkanie zweryfikowane: {summary} - {event_start}")
                return {
                    'exists': True,
                    'event_id': event['id'],
                    'summary': summary,
                    'start_time': event_start,
                    'description': description
                }
        
        logger.warning(f"❌ Spotkanie nie znalezione w kalendarzu: {client_name}, {appointment_datetime}")
        return False
        
    except Exception as e:
        logger.error(f"❌ Błąd weryfikacji spotkania: {e}")
        return False

def format_available_slots(requested_day):
    """Formatuje sloty w ładny sposób z polskimi nazwami dni"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # 🔧 DYNAMICZNE MAPOWANIE DNI (nie hardcoded!):
        tz = pytz.timezone('Europe/Warsaw')
        now = datetime.now(tz)
        
        # Oblicz target_date na początku
        target_date = None
        target_day_name = None
        
        if requested_day.lower() == 'jutro':
            target_date = (now + timedelta(days=1)).date()
        elif requested_day.lower() == 'dzisiaj':
            target_date = now.date()
        elif requested_day.lower() == 'pojutrze':
            target_date = (now + timedelta(days=2)).date()
        else:
            # Dla konkretnych dni tygodnia
            day_mapping_num = {
                'poniedziałek': 0, 'wtorek': 1, 'środa': 2,
                'czwartek': 3, 'piątek': 4, 'sobota': 5
            }
            target_day_num = day_mapping_num.get(requested_day.lower())
            if target_day_num is not None:
                current_day = now.weekday()
                if target_day_num > current_day:
                    days_ahead = target_day_num - current_day
                elif target_day_num == current_day:
                    days_ahead = 0
                else:
                    days_ahead = 7 - (current_day - target_day_num)
                target_date = (now + timedelta(days=days_ahead)).date()
            else:
                target_date = now.date()
        
        # 🔧 KONWERTUJ target_date NA NAZWĘ DNIA:
        day_names_num_to_pl = {
            0: 'poniedziałek', 1: 'wtorek', 2: 'środa',
            3: 'czwartek', 4: 'piątek', 5: 'sobota'
        }
        target_day_name = day_names_num_to_pl.get(target_date.weekday())
        
        logger.info(f"📅 Requested: {requested_day} → Date: {target_date} → Day: {target_day_name}")
        
        # 🔧 POBIERZ DANE DLA PRAWIDŁOWEGO DNIA:
        slots_data = get_available_slots_for_day(target_day_name)
        
        if not slots_data:
            return f"😔 Niestety, nie mamy wolnych terminów na {requested_day}."
        
        # 🔧 MAPOWANIE ANGIELSKICH DNI NA POLSKIE:
        day_names_eng_to_pl = {
            'Monday': 'Poniedziałek',
            'Tuesday': 'Wtorek',
            'Wednesday': 'Środa',
            'Thursday': 'Czwartek',
            'Friday': 'Piątek',
            'Saturday': 'Sobota',
            'Sunday': 'Niedziela'
        }
        
        # Formatuj odpowiedź
        day_pl = day_names_num_to_pl.get(target_date.weekday(), 'nieznany')
        date_str = target_date.strftime('%d.%m.%Y')
        
        # 🔧 ZAMIEŃ ANGIELSKIE NAZWY DNI NA POLSKIE:
        slots_text_lines = []
        for slot in slots_data:
            original_display = slot['display']  # np. "Thursday 10.07 09:00"
            
            # Zamień angielską nazwę dnia na polską
            polish_display = original_display
            for eng_day, pl_day in day_names_eng_to_pl.items():
                if eng_day in original_display:
                    polish_display = original_display.replace(eng_day, pl_day)
                    break
            
            slots_text_lines.append(f"- *{polish_display}*")
        
        slots_text = "\n".join(slots_text_lines)
        
        return f"Terminy na {requested_day} ({day_pl}, {date_str}):\n{slots_text}\nKtóry z tych terminów Ci najbardziej odpowiada? 😊"
        
    except Exception as e:
        logger.error(f"❌ Błąd format_available_slots: {e}")
        return f"Przepraszam, wystąpił problem ze sprawdzaniem terminów na {requested_day}. Spróbuj ponownie. 😊"
