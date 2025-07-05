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

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, credentials_file='credentials.json', calendar_id=None):
        self.credentials_file = credentials_file
        # Użyj zmiennej środowiskowej lub domyślny ID
        self.calendar_id = calendar_id or os.getenv(
            'GOOGLE_CALENDAR_ID', 
            '21719ebf883a6bfdb7c77e49836df6ea2cf711bf89b03d35e52500ffebcf4c0d@group.calendar.google.com'
        )
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
            while days_checked < days_ahead and current_day < 14:  # Max 14 dni
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
            return available_slots[:10]
            
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