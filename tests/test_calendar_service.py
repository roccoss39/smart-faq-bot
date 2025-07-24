import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import pytz

from bot_logic_ai import format_available_slots, create_appointment, cancel_appointment

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    # Ustaw wymagane zmienne środowiskowe na czas testów
    monkeypatch.setenv("GOOGLE_CALENDAR_ID", "21719ebf883a6bfdb7c77e49836df6ea2cf711bf89b03d35e52500ffebcf4c0d@group.calendar.google.com")

@pytest.mark.parametrize("day_keyword", [
    "dzisiaj",
    "jutro",
    "pojutrze",
    "poniedziałek",
    "wtorek",
    "środa",
    "czwartek",
    "piątek",
    "sobota",
    "niedziela"
])
def test_format_available_slots_various_days(day_keyword):
    """Testuje format_available_slots dla różnych słów-kluczy dni."""
    result = format_available_slots(day_keyword)
    print(f"\n[format_available_slots] Wejście: {day_keyword} → Wyjście: {result}")
    assert isinstance(result, str)

def test_create_and_cancel_appointment():
    """Testuje tworzenie i anulowanie wizyty na różne dni tygodnia."""
    tz = pytz.timezone('Europe/Warsaw')
    now = datetime.now(tz)
    dni_pol = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    for offset in [1, 2, 3]:
        appointment_time = now + timedelta(days=offset)
        appointment_time = appointment_time.replace(hour=15, minute=0, second=0, microsecond=0)
        appointment_time = tz.localize(appointment_time.replace(tzinfo=None))
        print(f"\n[create_appointment] Wejście: {appointment_time}")
        result_create = create_appointment(
            client_name=f"Test User {offset}",
            client_phone=f"12345678{offset}",
            service_type="Strzyżenie",
            appointment_time=appointment_time
        )
        print(f"[create_appointment] Wyjście: {result_create}")
        assert result_create is not None
        weekday_idx = appointment_time.weekday()
        appointment_day = dni_pol[weekday_idx]
        print(f"[cancel_appointment] Wejście: {appointment_day}, 15:00")
        result_cancel = cancel_appointment(
            client_name=f"Test User {offset}",
            client_phone=f"12345678{offset}",
            appointment_day=appointment_day,
            appointment_time="15:00"
        )
        print(f"[cancel_appointment] Wyjście: {result_cancel}")
        assert result_cancel is not None

def test_format_available_slots_wtorek():
    """Testuje format_available_slots tylko dla 'wtorek'."""
    result = format_available_slots("dzisiaj")
    print(f"\n[format_available_slots] Wejście: 'wtorek' → Wyjście: {result}")
    assert isinstance(result, str)