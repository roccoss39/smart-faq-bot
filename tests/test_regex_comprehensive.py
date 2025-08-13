# ZASTĄP CAŁY PLIK test_regex_comprehensive.py:

from bot_logic import analyze_intent_regex_only

def run_comprehensive_regex_test():
    """500 przypadków testowych dla regex - wyważone"""
    
    test_cases = [
        # ===========================================
        # 1. CANCEL_VISIT (50 przypadków)
        # ===========================================
        
        # Podstawowe anulowanie
        ('anuluj wizytę', 'CANCEL_VISIT'),
        ('anuluj', 'CANCEL_VISIT'),
        ('rezygnuję z wizyty', 'CANCEL_VISIT'),
        ('rezygnuj', 'CANCEL_VISIT'),
        ('odwołaj wizytę', 'CANCEL_VISIT'),
        ('odwołuję wizytę', 'CANCEL_VISIT'),
        ('zrezygnować', 'CANCEL_VISIT'),
        ('cancel appointment', 'CANCEL_VISIT'),
        ('cancel', 'CANCEL_VISIT'),
        ('chcę anulować', 'CANCEL_VISIT'),
        
        # Z dodatkowymi słowami
        ('chcę anulować wizytę', 'CANCEL_VISIT'),
        ('muszę anulować termin', 'CANCEL_VISIT'),
        ('potrzebuję anulować', 'CANCEL_VISIT'),
        ('anuluj proszę', 'CANCEL_VISIT'),
        ('anuluj mój termin', 'CANCEL_VISIT'),
        ('rezygnuję z terminu', 'CANCEL_VISIT'),
        ('odwołuję termin', 'CANCEL_VISIT'),
        ('nie mogę przyjść, anuluj', 'CANCEL_VISIT'),
        ('anulowanie wizyty', 'CANCEL_VISIT'),
        ('chcę zrezygnować z wizyty', 'CANCEL_VISIT'),
        
        # Różne formy
        ('ANULUJ', 'CANCEL_VISIT'),
        ('Anuluj wizytę', 'CANCEL_VISIT'),
        ('REZYGNUJĘ', 'CANCEL_VISIT'),
        ('Odwołuję', 'CANCEL_VISIT'),
        ('anuluj!!!', 'CANCEL_VISIT'),
        ('anuluj...', 'CANCEL_VISIT'),
        ('anuluj?', 'CANCEL_VISIT'),
        ('anuluj.', 'CANCEL_VISIT'),
        ('anuluj, proszę', 'CANCEL_VISIT'),
        ('anuluj wizytę na jutro', 'CANCEL_VISIT'),
        
        # Błędy ortograficzne
        ('annuluj wizyte', 'CANCEL_VISIT'),
        ('anuluj wiyzyte', 'CANCEL_VISIT'),
        ('odwolaj wizyte', 'CANCEL_VISIT'),
        ('rezygnuje z wizyty', 'CANCEL_VISIT'),
        ('anulluj termin', 'CANCEL_VISIT'),
        ('cancel wizyta', 'CANCEL_VISIT'),
        ('anuluj moja wizyte', 'CANCEL_VISIT'),
        ('odwoluje termin', 'CANCEL_VISIT'),
        ('rezyguje', 'CANCEL_VISIT'),
        ('anulowac wizyte', 'CANCEL_VISIT'),
        
        # Z kontekstem
        ('niestety muszę anulować', 'CANCEL_VISIT'),
        ('przykro mi, ale anuluj', 'CANCEL_VISIT'),
        ('z powodu choroby anuluj', 'CANCEL_VISIT'),
        ('nie dam rady, anuluj', 'CANCEL_VISIT'),
        ('zmiana planów - anuluj', 'CANCEL_VISIT'),
        ('anuluj z powodu wyjazdu', 'CANCEL_VISIT'),
        ('pilne - anuluj wizytę', 'CANCEL_VISIT'),
        ('dzisiaj nie mogę - anuluj', 'CANCEL_VISIT'),
        ('wypadek - anuluj termin', 'CANCEL_VISIT'),
        ('nagły przypadek - rezygnuję', 'CANCEL_VISIT'),
        
        # ===========================================
        # 2. CONTACT_DATA (75 przypadków)
        # ===========================================
        
        # Standardowe formaty
        ('Jan Kowalski, 123456789', 'CONTACT_DATA'),
        ('Anna Nowak, 987654321', 'CONTACT_DATA'),
        ('Piotr Wiśniewski, 555666777', 'CONTACT_DATA'),
        ('Maria Kowalczyk, 111222333', 'CONTACT_DATA'),
        ('Tomasz Kamiński, 444555666', 'CONTACT_DATA'),
        ('Katarzyna Lewandowska, 777888999', 'CONTACT_DATA'),
        ('Michał Zieliński, 222333444', 'CONTACT_DATA'),
        ('Barbara Szymańska, 888999000', 'CONTACT_DATA'),
        ('Krzysztof Woźniak, 666777888', 'CONTACT_DATA'),
        ('Magdalena Dąbrowska, 333444555', 'CONTACT_DATA'),
        
        # Z polskimi znakami
        ('Józef Łukasiński, 123456789', 'CONTACT_DATA'),
        ('Błażej Świątek, 987654321', 'CONTACT_DATA'),
        ('Żaneta Różańska, 555666777', 'CONTACT_DATA'),
        ('Ćwikła Łódź, 111222333', 'CONTACT_DATA'),
        ('Święta Góra, 444555666', 'CONTACT_DATA'),
        ('Czesław Ściborski, 777888999', 'CONTACT_DATA'),
        ('Ała Łęska, 222333444', 'CONTACT_DATA'),
        ('Źródło Życia, 888999000', 'CONTACT_DATA'),
        ('Żuław Żółty, 666777888', 'CONTACT_DATA'),
        ('Ćma Ścienna, 333444555', 'CONTACT_DATA'),
        
        # Różne separatory
        ('Jan Kowalski 123456789', 'CONTACT_DATA'),
        ('Anna Nowak  987654321', 'CONTACT_DATA'),
        ('Piotr Wiśniewski,123456789', 'CONTACT_DATA'),
        ('Maria Kowalczyk , 987654321', 'CONTACT_DATA'),
        ('Tomasz Kamiński ,123456789', 'CONTACT_DATA'),
        ('Katarzyna Lewandowska   987654321', 'CONTACT_DATA'),
        ('Michał Zieliński,  123456789', 'CONTACT_DATA'),
        ('Barbara Szymańska  ,987654321', 'CONTACT_DATA'),
        ('Krzysztof Woźniak    123456789', 'CONTACT_DATA'),
        ('Magdalena Dąbrowska,987654321', 'CONTACT_DATA'),
        
        # Formaty z myślnikami
        ('Jan Kowalski, 123-456-789', 'CONTACT_DATA'),
        ('Anna Nowak, 987-654-321', 'CONTACT_DATA'),
        ('Piotr Wiśniewski, 555-666-777', 'CONTACT_DATA'),
        ('Maria Kowalczyk, 111-222-333', 'CONTACT_DATA'),
        ('Tomasz Kamiński, 444-555-666', 'CONTACT_DATA'),
        
        # Formaty ze spacjami
        ('Jan Kowalski, 123 456 789', 'CONTACT_DATA'),
        ('Anna Nowak, 987 654 321', 'CONTACT_DATA'),
        ('Piotr Wiśniewski, 555 666 777', 'CONTACT_DATA'),
        ('Maria Kowalczyk, 111 222 333', 'CONTACT_DATA'),
        ('Tomasz Kamiński, 444 555 666', 'CONTACT_DATA'),
        
        # Długie wiadomości z danymi
        ('hej, nazywam się Jan Kowalski i mój numer to 123456789', 'CONTACT_DATA'),
        ('dzień dobry, jestem Anna Nowak, telefon 987654321', 'CONTACT_DATA'),
        ('witam, nazywam się Piotr Wiśniewski 555666777', 'CONTACT_DATA'),
        ('cześć, jestem Maria Kowalczyk, nr tel: 111222333', 'CONTACT_DATA'),
        ('moje dane to Tomasz Kamiński 444555666', 'CONTACT_DATA'),
        
        # Wielkie litery
        ('JAN KOWALSKI, 123456789', 'CONTACT_DATA'),
        ('ANNA NOWAK, 987654321', 'CONTACT_DATA'),
        ('PIOTR WIŚNIEWSKI, 555666777', 'CONTACT_DATA'),
        ('Jan KOWALSKI, 123456789', 'CONTACT_DATA'),
        ('anna nowak, 987654321', 'CONTACT_DATA'),
        
        # Błędy w nazwiskach
        ('Jan Kowalsky, 123456789', 'CONTACT_DATA'),
        ('Anna Novak, 987654321', 'CONTACT_DATA'),
        ('Piotr Wisnewski, 555666777', 'CONTACT_DATA'),
        ('Maria Kowalczik, 111222333', 'CONTACT_DATA'),
        ('Tomasz Kaminski, 444555666', 'CONTACT_DATA'),
        
        # Z dodatkowymi informacjami
        ('Jan Kowalski, 123456789, strzyżenie', 'CONTACT_DATA'),
        ('Anna Nowak 987654321 farbowanie', 'CONTACT_DATA'),
        ('Piotr Wiśniewski, tel. 555666777', 'CONTACT_DATA'),
        ('Maria Kowalczyk, numer: 111222333', 'CONTACT_DATA'),
        ('Tomasz Kamiński, telefon 444555666', 'CONTACT_DATA'),
        
        # Formaty mieszane
        ('Jan Kowalski 123-456-789', 'CONTACT_DATA'),
        ('Anna Nowak,987 654 321', 'CONTACT_DATA'),
        ('Piotr Wiśniewski  555-666-777', 'CONTACT_DATA'),
        ('Maria Kowalczyk, 111 222 333', 'CONTACT_DATA'),
        ('Tomasz Kamiński:444555666', 'CONTACT_DATA'),
        
        # Imiona podwójne
        ('Jan Krzysztof Kowalski, 123456789', 'CONTACT_DATA'),
        ('Anna Maria Nowak, 987654321', 'CONTACT_DATA'),
        ('Piotr Jan Wiśniewski, 555666777', 'CONTACT_DATA'),
        ('Maria Katarzyna Kowalczyk, 111222333', 'CONTACT_DATA'),
        ('Tomasz Michał Kamiński, 444555666', 'CONTACT_DATA'),
        
        # Kropki w skrótach
        ('Jan Kowalski, 123456789.', 'CONTACT_DATA'),
        ('Anna Nowak, 987654321!', 'CONTACT_DATA'),
        ('Piotr Wiśniewski, 555666777?', 'CONTACT_DATA'),
        ('Maria Kowalczyk, 111222333...', 'CONTACT_DATA'),
        ('Tomasz Kamiński, 444555666 :)', 'CONTACT_DATA'),
        
        # ===========================================
        # 3. BOOKING (100 przypadków)
        # ===========================================
        
        # Podstawowe bookings
        ('poniedziałek 10:00', 'BOOKING'),
        ('wtorek 11:00', 'BOOKING'),
        ('środa 12:00', 'BOOKING'),
        ('czwartek 13:00', 'BOOKING'),
        ('piątek 14:00', 'BOOKING'),
        ('sobota 15:00', 'BOOKING'),
        ('niedziela 16:00', 'BOOKING'),
        ('pon 09:00', 'BOOKING'),
        ('wt 10:30', 'BOOKING'),
        ('śr 11:15', 'BOOKING'),
        
        # Z dodatkowymi słowami
        ('umawiam się na poniedziałek 10:00', 'BOOKING'),
        ('chcę na wtorek 11:00', 'BOOKING'),
        ('rezerwuję środa 12:00', 'BOOKING'),
        ('na czwartek 13:00', 'BOOKING'),
        ('piątek 14:00 na strzyżenie', 'BOOKING'),
        ('sobota 15:00 proszę', 'BOOKING'),
        ('umawiam się niedziela 16:00', 'BOOKING'),
        ('pon 09:00 na farbowanie', 'BOOKING'),
        ('chcę wt 10:30', 'BOOKING'),
        ('rezerwacja śr 11:15', 'BOOKING'),
        
        # Różne formaty czasu
        ('poniedziałek 10:30', 'BOOKING'),
        ('wtorek 11:15', 'BOOKING'),
        ('środa 12:45', 'BOOKING'),
        ('czwartek 13:30', 'BOOKING'),
        ('piątek 14:15', 'BOOKING'),
        ('sobota 15:45', 'BOOKING'),
        ('niedziela 16:30', 'BOOKING'),
        ('pon 09:15', 'BOOKING'),
        ('wt 10:45', 'BOOKING'),
        ('śr 11:30', 'BOOKING'),
        
        # Z różnymi usługami
        ('poniedziałek 10:00 strzyżenie', 'BOOKING'),
        ('wtorek 11:00 farbowanie', 'BOOKING'),
        ('środa 12:00 pasemka', 'BOOKING'),
        ('czwartek 13:00 refleksy', 'BOOKING'),
        ('piątek 14:00 koloryzacja', 'BOOKING'),
        ('sobota 15:00 ombre', 'BOOKING'),
        ('niedziela 16:00 baleyage', 'BOOKING'),
        ('pon 09:00 na strzyżenie', 'BOOKING'),
        ('wt 10:30 na farbowanie', 'BOOKING'),
        ('śr 11:15 na pasemka', 'BOOKING'),
        
        # Odmiany dni
        ('w poniedziałek 10:00', 'BOOKING'),
        ('we wtorek 11:00', 'BOOKING'),
        ('w środę 12:00', 'BOOKING'),
        ('w czwartek 13:00', 'BOOKING'),
        ('w piątek 14:00', 'BOOKING'),
        ('w sobotę 15:00', 'BOOKING'),
        ('w niedzielę 16:00', 'BOOKING'),
        ('na poniedziałek 10:00', 'BOOKING'),
        ('na wtorek 11:00', 'BOOKING'),
        ('na środę 12:00', 'BOOKING'),
        
        # Błędy ortograficzne dni
        ('poniedzialek 10:00', 'BOOKING'),
        ('sroda 12:00', 'BOOKING'),
        ('piatek 14:00', 'BOOKING'),
        ('sobote 15:00', 'BOOKING'),
        ('niedziele 16:00', 'BOOKING'),
        ('srodę 12:30', 'BOOKING'),
        ('czwartke 13:45', 'BOOKING'),
        ('pon. 09:00', 'BOOKING'),
        ('wtor 11:00', 'BOOKING'),
        ('sob 15:30', 'BOOKING'),
        
        # Różne formaty
        ('PONIEDZIAŁEK 10:00', 'BOOKING'),
        ('Wtorek 11:00', 'BOOKING'),
        ('środa 12:00!', 'BOOKING'),
        ('czwartek 13:00?', 'BOOKING'),
        ('piątek 14:00.', 'BOOKING'),
        ('sobota 15:00...', 'BOOKING'),
        ('niedziela 16:00 !!!', 'BOOKING'),
        ('pon 09:00 :)', 'BOOKING'),
        ('wt 10:30 💇', 'BOOKING'),
        ('śr 11:15, proszę', 'BOOKING'),
        
        # Z kontekstem
        ('chciałbym poniedziałek 10:00', 'BOOKING'),
        ('może wtorek 11:00?', 'BOOKING'),
        ('preferuję środa 12:00', 'BOOKING'),
        ('wolałbym czwartek 13:00', 'BOOKING'),
        ('najlepiej piątek 14:00', 'BOOKING'),
        ('pasuje mi sobota 15:00', 'BOOKING'),
        ('mogę niedziela 16:00', 'BOOKING'),
        ('dostępny pon 09:00', 'BOOKING'),
        ('proponuję wt 10:30', 'BOOKING'),
        ('sugeruję śr 11:15', 'BOOKING'),
        
        # Godziny graniczne
        ('poniedziałek 09:00', 'BOOKING'),
        ('wtorek 09:30', 'BOOKING'),
        ('środa 18:00', 'BOOKING'),
        ('czwartek 18:30', 'BOOKING'),
        ('piątek 19:00', 'BOOKING'),
        ('sobota 08:00', 'BOOKING'),
        ('niedziela 20:00', 'BOOKING'),
        ('pon 07:30', 'BOOKING'),
        ('wt 21:00', 'BOOKING'),
        ('śr 17:45', 'BOOKING'),
        
        # ===========================================
        # 4. ASK_AVAILABILITY (50 przypadków)
        # ===========================================
        
        # Podstawowe pytania
        ('jakie są wolne terminy?', 'ASK_AVAILABILITY'),
        ('kiedy mają państwo wolne?', 'ASK_AVAILABILITY'),
        ('dostępne godziny?', 'ASK_AVAILABILITY'),
        ('wolne terminy na wtorek?', 'ASK_AVAILABILITY'),
        ('kiedy można się umówić?', 'ASK_AVAILABILITY'),
        ('jakie terminy dostępne?', 'ASK_AVAILABILITY'),
        ('godziny na środę?', 'ASK_AVAILABILITY'),
        ('mają państwo wolne na czwartek?', 'ASK_AVAILABILITY'),
        ('dostępne terminy w piątek?', 'ASK_AVAILABILITY'),
        ('wolne w sobotę?', 'ASK_AVAILABILITY'),
        
        # Różne formy
        ('czy są wolne terminy?', 'ASK_AVAILABILITY'),
        ('są jakieś wolne godziny?', 'ASK_AVAILABILITY'),
        ('kiedy jest wolne?', 'ASK_AVAILABILITY'),
        ('dostępne w tym tygodniu?', 'ASK_AVAILABILITY'),
        ('terminy na następny tydzień?', 'ASK_AVAILABILITY'),
        ('wolne miejsca jutro?', 'ASK_AVAILABILITY'),
        ('godziny na dziś?', 'ASK_AVAILABILITY'),
        ('kiedy można przyjść?', 'ASK_AVAILABILITY'),
        ('jakie są dostępne terminy?', 'ASK_AVAILABILITY'),
        ('mają państwo coś wolnego?', 'ASK_AVAILABILITY'),
        
        # Konkretne dni
        ('wolne terminy w poniedziałek?', 'ASK_AVAILABILITY'),
        ('dostępne godziny we wtorek?', 'ASK_AVAILABILITY'),
        ('jakie terminy w środę?', 'ASK_AVAILABILITY'),
        ('godziny w czwartek?', 'ASK_AVAILABILITY'),
        ('wolne w piątek?', 'ASK_AVAILABILITY'),
        ('dostępne w sobotę?', 'ASK_AVAILABILITY'),
        ('terminy w niedzielę?', 'ASK_AVAILABILITY'),
        ('godziny na jutro?', 'ASK_AVAILABILITY'),
        ('wolne na dziś?', 'ASK_AVAILABILITY'),
        ('dostępne na weekend?', 'ASK_AVAILABILITY'),
        
        # Różne warianty
        ('co macie wolnego?', 'ASK_AVAILABILITY'),
        ('jakie możliwości?', 'ASK_AVAILABILITY'),
        ('dostępność terminów?', 'ASK_AVAILABILITY'),
        ('wolne sloty?', 'ASK_AVAILABILITY'),
        ('kiedy przyjmujecie?', 'ASK_AVAILABILITY'),
        ('godziny przyjęć?', 'ASK_AVAILABILITY'),
        ('terminy do wyboru?', 'ASK_AVAILABILITY'),
        ('możliwe godziny?', 'ASK_AVAILABILITY'),
        ('opcje terminów?', 'ASK_AVAILABILITY'),
        ('co jest dostępne?', 'ASK_AVAILABILITY'),
        
        # Z kontekstem
        ('szukam wolnego terminu', 'ASK_AVAILABILITY'),
        ('potrzebuję sprawdzić dostępność', 'ASK_AVAILABILITY'),
        ('chciałbym zobaczyć wolne terminy', 'ASK_AVAILABILITY'),
        ('czy mogę poznać dostępne godziny?', 'ASK_AVAILABILITY'),
        ('interesują mnie wolne miejsca', 'ASK_AVAILABILITY'),
        ('poproszę o wolne terminy', 'ASK_AVAILABILITY'),
        ('chcę sprawdzić dostępność', 'ASK_AVAILABILITY'),
        ('możecie podać wolne godziny?', 'ASK_AVAILABILITY'),
        ('jakie terminy są otwarte?', 'ASK_AVAILABILITY'),
        ('chciałabym poznać opcje', 'ASK_AVAILABILITY'),
        
        # ===========================================
        # 5. OTHER_QUESTION (125 przypadków)
        # ===========================================
        
        # Powitania
        ('hej', 'OTHER_QUESTION'),
        ('cześć', 'OTHER_QUESTION'),
        ('dzień dobry', 'OTHER_QUESTION'),
        ('witaj', 'OTHER_QUESTION'),
        ('hello', 'OTHER_QUESTION'),
        ('hi', 'OTHER_QUESTION'),
        ('siema', 'OTHER_QUESTION'),
        ('dobry wieczór', 'OTHER_QUESTION'),
        ('miłego dnia', 'OTHER_QUESTION'),
        ('pozdrawiam', 'OTHER_QUESTION'),
        ('dobry', 'OTHER_QUESTION'),
        ('witam', 'OTHER_QUESTION'),
        ('dzień dobry państwu', 'OTHER_QUESTION'),
        ('hej tam', 'OTHER_QUESTION'),
        ('siemka', 'OTHER_QUESTION'),
        
        # Pytania o ceny
        ('ile kosztuje strzyżenie?', 'OTHER_QUESTION'),
        ('cena strzyżenia damskiego?', 'OTHER_QUESTION'),
        ('ile płacę za farbowanie?', 'OTHER_QUESTION'),
        ('koszt pasemek?', 'OTHER_QUESTION'),
        ('cennik usług?', 'OTHER_QUESTION'),
        ('ile kosztuje męskie strzyżenie?', 'OTHER_QUESTION'),
        ('cena koloryzacji?', 'OTHER_QUESTION'),
        ('ile za refleksy?', 'OTHER_QUESTION'),
        ('koszt ombre?', 'OTHER_QUESTION'),
        ('ile kosztuje baleyage?', 'OTHER_QUESTION'),
        ('ceny w salonie?', 'OTHER_QUESTION'),
        ('ile zapłacę za wizytę?', 'OTHER_QUESTION'),
        ('koszt usług?', 'OTHER_QUESTION'),
        ('jaki cennik macie?', 'OTHER_QUESTION'),
        ('cena za strzyżenie?', 'OTHER_QUESTION'),
        
        # Pytania o lokalizację
        ('gdzie jesteście?', 'OTHER_QUESTION'),
        ('adres salonu?', 'OTHER_QUESTION'),
        ('jak dojechać?', 'OTHER_QUESTION'),
        ('lokalizacja?', 'OTHER_QUESTION'),
        ('ulica?', 'OTHER_QUESTION'),
        ('gdzie się znajdujecie?', 'OTHER_QUESTION'),
        ('adres dokładny?', 'OTHER_QUESTION'),
        ('jak was znaleźć?', 'OTHER_QUESTION'),
        ('w którym miejscu?', 'OTHER_QUESTION'),
        ('położenie salonu?', 'OTHER_QUESTION'),
        ('gdzie mieścicie się?', 'OTHER_QUESTION'),
        ('jaki adres?', 'OTHER_QUESTION'),
        ('lokalizacja salonu?', 'OTHER_QUESTION'),
        ('gdzie można was znaleźć?', 'OTHER_QUESTION'),
        ('dojazd do salonu?', 'OTHER_QUESTION'),
        
        # Pytania o kontakt
        ('numer telefonu?', 'OTHER_QUESTION'),
        ('telefon do salonu?', 'OTHER_QUESTION'),
        ('jak się skontaktować?', 'OTHER_QUESTION'),
        ('kontakt telefoniczny?', 'OTHER_QUESTION'),
        ('telefon receptji?', 'OTHER_QUESTION'),
        ('numer do rezerwacji?', 'OTHER_QUESTION'),
        ('kontakt?', 'OTHER_QUESTION'),
        ('jak zadzwonić?', 'OTHER_QUESTION'),
        ('telefon proszę?', 'OTHER_QUESTION'),
        ('numer salonu?', 'OTHER_QUESTION'),
        ('dane kontaktowe?', 'OTHER_QUESTION'),
        ('telefon do umówienia?', 'OTHER_QUESTION'),
        ('numer do rezerwacji?', 'OTHER_QUESTION'),
        ('jak się z wami skontaktować?', 'OTHER_QUESTION'),
        ('jaki numer telefonu?', 'OTHER_QUESTION'),
        
        # Pytania o godziny otwarcia
        ('godziny otwarcia?', 'OTHER_QUESTION'),
        ('kiedy otwarcie?', 'OTHER_QUESTION'),
        ('o której otwieracie?', 'OTHER_QUESTION'),
        ('do której czynne?', 'OTHER_QUESTION'),
        ('godziny pracy?', 'OTHER_QUESTION'),
        ('czy jesteście otwarci?', 'OTHER_QUESTION'),
        ('kiedy pracujecie?', 'OTHER_QUESTION'),
        ('godziny w sobotę?', 'OTHER_QUESTION'),
        ('czy w niedzielę otwarte?', 'OTHER_QUESTION'),
        ('godziny w weekend?', 'OTHER_QUESTION'),
        ('o której zamykacie?', 'OTHER_QUESTION'),
        ('godziny funkcjonowania?', 'OTHER_QUESTION'),
        ('kiedy jest salon otwarty?', 'OTHER_QUESTION'),
        ('godziny działania?', 'OTHER_QUESTION'),
        ('kiedy można przyjść?', 'OTHER_QUESTION'),
        
        # Pytania o usługi
        ('jakie usługi oferujecie?', 'OTHER_QUESTION'),
        ('co robicie w salonie?', 'OTHER_QUESTION'),
        ('jakiej specjalizacji?', 'OTHER_QUESTION'),
        ('czy robicie farbowanie?', 'OTHER_QUESTION'),
        ('czy strzyżecie męskie?', 'OTHER_QUESTION'),
        ('jakie zabiegi?', 'OTHER_QUESTION'),
        ('czy robicie pasemka?', 'OTHER_QUESTION'),
        ('oferta salonu?', 'OTHER_QUESTION'),
        ('lista usług?', 'OTHER_QUESTION'),
        ('czy robicie refleksy?', 'OTHER_QUESTION'),
        ('jakie są wasze usługi?', 'OTHER_QUESTION'),
        ('co można zrobić?', 'OTHER_QUESTION'),
        ('zakres usług?', 'OTHER_QUESTION'),
        ('czy robicie ombre?', 'OTHER_QUESTION'),
        ('specjalizacja salonu?', 'OTHER_QUESTION'),
        
        # Różne pytania
        ('jak długo trwa wizyta?', 'OTHER_QUESTION'),
        ('czy potrzebna rezerwacja?', 'OTHER_QUESTION'),
        ('jak umówić się?', 'OTHER_QUESTION'),
        ('czy można bez rezerwacji?', 'OTHER_QUESTION'),
        ('jak płacić?', 'OTHER_QUESTION'),
        ('czy kartą?', 'OTHER_QUESTION'),
        ('gotówką czy kartą?', 'OTHER_QUESTION'),
        ('formy płatności?', 'OTHER_QUESTION'),
        ('czy macie parking?', 'OTHER_QUESTION'),
        ('ile trwa strzyżenie?', 'OTHER_QUESTION'),
        ('jak długo farbowanie?', 'OTHER_QUESTION'),
        ('czy dojadę komunikacją?', 'OTHER_QUESTION'),
        ('metro w pobliżu?', 'OTHER_QUESTION'),
        ('przystanek autobusowy?', 'OTHER_QUESTION'),
        ('czy macie klimatyzację?', 'OTHER_QUESTION'),
        
        # Długie pytania
        ('dzień dobry, czy mogłabym zapytać ile kosztuje strzyżenie damskie?', 'OTHER_QUESTION'),
        ('witam, chciałbym wiedzieć gdzie się państwo znajdują?', 'OTHER_QUESTION'),
        ('cześć, możecie podać godziny otwarcia salonu?', 'OTHER_QUESTION'),
        ('hej, jaki jest numer telefonu do salonu?', 'OTHER_QUESTION'),
        ('dzień dobry, jakie usługi oferuje salon?', 'OTHER_QUESTION'),
        ('witam, ile kosztuje farbowanie włosów?', 'OTHER_QUESTION'),
        ('cześć, czy mogę zapytać o ceny w salonie?', 'OTHER_QUESTION'),
        ('hej, chciałabym poznać ofertę salonu', 'OTHER_QUESTION'),
        ('dzień dobry, jak można się z państwem skontaktować?', 'OTHER_QUESTION'),
        ('witam, czy salon jest otwarty w soboty?', 'OTHER_QUESTION'),
        
        # ===========================================
        # 6. WANT_APPOINTMENT (100 przypadków)
        # ===========================================
        
        # Podstawowe chęci umówienia
        ('chcę się umówić', 'WANT_APPOINTMENT'),
        ('chce sie umówić', 'WANT_APPOINTMENT'),
        ('potrzebuję wizyty', 'WANT_APPOINTMENT'),
        ('umów mnie', 'WANT_APPOINTMENT'),
        ('rezerwacja', 'WANT_APPOINTMENT'),
        ('wizyta', 'WANT_APPOINTMENT'),
        ('umawiam wizytę', 'WANT_APPOINTMENT'),
        ('potrzebuję się ostrzyc', 'WANT_APPOINTMENT'),
        ('chcę strzyżenie', 'WANT_APPOINTMENT'),
        ('potrzebuję fryzjera', 'WANT_APPOINTMENT'),
        
        # Różne formy
        ('chciałbym się umówić', 'WANT_APPOINTMENT'),
        ('chciałabym wizytę', 'WANT_APPOINTMENT'),
        ('potrzebuję terminu', 'WANT_APPOINTMENT'),
        ('szukam wizyty', 'WANT_APPOINTMENT'),
        ('może jakiś termin?', 'WANT_APPOINTMENT'),
        ('chcę zarezerwować', 'WANT_APPOINTMENT'),
        ('umówienie się', 'WANT_APPOINTMENT'),
        ('rezerwuję wizytę', 'WANT_APPOINTMENT'),
        ('potrzebuję się umówić', 'WANT_APPOINTMENT'),
        ('chcę wizytę', 'WANT_APPOINTMENT'),
        
        # Z usługami (bez czasu)
        ('chcę strzyżenie damskie', 'WANT_APPOINTMENT'),
        ('potrzebuję farbowania', 'WANT_APPOINTMENT'),
        ('chcę pasemka', 'WANT_APPOINTMENT'),
        ('potrzebuję refleksów', 'WANT_APPOINTMENT'),
        ('chcę koloryzację', 'WANT_APPOINTMENT'),
        ('potrzebuję ombre', 'WANT_APPOINTMENT'),
        ('chcę baleyage', 'WANT_APPOINTMENT'),
        ('strzyżenie męskie', 'WANT_APPOINTMENT'),
        ('potrzebuję ostrzyc', 'WANT_APPOINTMENT'),
        ('chcę się ostrzyc', 'WANT_APPOINTMENT'),
        
        # Usługi bez słów kluczowych
        ('strzyżenie', 'WANT_APPOINTMENT'),
        ('farbowanie', 'WANT_APPOINTMENT'),
        ('pasemka', 'WANT_APPOINTMENT'),
        ('refleksy', 'WANT_APPOINTMENT'),
        ('koloryzacja', 'WANT_APPOINTMENT'),
        ('ombre', 'WANT_APPOINTMENT'),
        ('baleyage', 'WANT_APPOINTMENT'),
        ('fryzjer', 'WANT_APPOINTMENT'),
        ('ostrzyc się', 'WANT_APPOINTMENT'),
        ('zrobić włosy', 'WANT_APPOINTMENT'),
        
        # Dłuższe frazy
        ('chciałbym się umówić na wizytę', 'WANT_APPOINTMENT'),
        ('potrzebuję umówić się na strzyżenie', 'WANT_APPOINTMENT'),
        ('chcę zarezerwować termin na farbowanie', 'WANT_APPOINTMENT'),
        ('szukam terminu na wizytę', 'WANT_APPOINTMENT'),
        ('mogę się umówić na strzyżenie?', 'WANT_APPOINTMENT'),
        ('chciałabym wizytę na pasemka', 'WANT_APPOINTMENT'),
        ('potrzebuję terminu do fryzjera', 'WANT_APPOINTMENT'),
        ('chcę umówić wizytę na refleksy', 'WANT_APPOINTMENT'),
        ('mogę się zapisać na koloryzację?', 'WANT_APPOINTMENT'),
        ('chciałbym rezerwację na ombre', 'WANT_APPOINTMENT'),
        
        # Różne warianty
        ('wizyta u fryzjera', 'WANT_APPOINTMENT'),
        ('zapisać się', 'WANT_APPOINTMENT'),
        ('zarezerwować miejsce', 'WANT_APPOINTMENT'),
        ('umówić termin', 'WANT_APPOINTMENT'),
        ('zrobić rezerwację', 'WANT_APPOINTMENT'),
        ('chcę iść do fryzjera', 'WANT_APPOINTMENT'),
        ('potrzebuję zrobić włosy', 'WANT_APPOINTMENT'),
        ('chcę poprawić fryzurę', 'WANT_APPOINTMENT'),
        ('czas na fryzjera', 'WANT_APPOINTMENT'),
        ('trzeba iść do salonu', 'WANT_APPOINTMENT'),
        
        # Kontekst potrzeby
        ('włosy za długie', 'WANT_APPOINTMENT'),
        ('trzeba się ostrzyc', 'WANT_APPOINTMENT'),
        ('pora na fryzjera', 'WANT_APPOINTMENT'),
        ('chcę zmienić fryzurę', 'WANT_APPOINTMENT'),
        ('potrzebuję nowej fryzury', 'WANT_APPOINTMENT'),
        ('chcę odświeżyć kolor', 'WANT_APPOINTMENT'),
        ('czas na strzyżenie', 'WANT_APPOINTMENT'),
        ('włosy wyrosły', 'WANT_APPOINTMENT'),
        ('potrzebuję obciąć włosy', 'WANT_APPOINTMENT'),
        ('chcę krótsze włosy', 'WANT_APPOINTMENT'),
        
        # Formalne
        ('proszę o umówienie wizyty', 'WANT_APPOINTMENT'),
        ('chciałbym zarezerwować termin', 'WANT_APPOINTMENT'),
        ('czy mogę się umówić?', 'WANT_APPOINTMENT'),
        ('proszę o rezerwację', 'WANT_APPOINTMENT'),
        ('chciałabym się zapisać', 'WANT_APPOINTMENT'),
        ('mogę prosić o termin?', 'WANT_APPOINTMENT'),
        ('czy jest możliwość umówienia?', 'WANT_APPOINTMENT'),
        ('proszę o wizytę', 'WANT_APPOINTMENT'),
        ('chciałbym się zapisać na wizytę', 'WANT_APPOINTMENT'),
        ('czy mogę zarezerwować termin?', 'WANT_APPOINTMENT'),
        
        # Długie kontekstowe
        ('witam bardzo serdecznie, chciałbym się umówić na wizytę w państwa salonie', 'WANT_APPOINTMENT'),
        ('dzień dobry, czy mogę się umówić na strzyżenie?', 'WANT_APPOINTMENT'),
        ('cześć, potrzebuję się ostrzyc, czy można się umówić?', 'WANT_APPOINTMENT'),
        ('hej, chciałabym umówić wizytę na farbowanie włosów', 'WANT_APPOINTMENT'),
        ('witam, czy mogę zarezerwować termin na pasemka?', 'WANT_APPOINTMENT'),
        ('dzień dobry, chcę się umówić na koloryzację', 'WANT_APPOINTMENT'),
        ('cześć, szukam terminu na refleksy, czy można się umówić?', 'WANT_APPOINTMENT'),
        ('hej, potrzebuję wizyty na ombre, jak się umówić?', 'WANT_APPOINTMENT'),
        ('witam, chciałbym rezerwację na strzyżenie męskie', 'WANT_APPOINTMENT'),
        ('dzień dobry, czy mogę się zapisać na baleyage?', 'WANT_APPOINTMENT')
    ]
    
    print(f"🧪 ROZPOCZYNAM TEST {len(test_cases)} PRZYPADKÓW")
    print("=" * 60)
    
    correct = 0
    errors = []
    
    for i, (message, expected) in enumerate(test_cases, 1):
        try:
            result = analyze_intent_regex_only(message)
            
            if result == expected:
                correct += 1
                if i % 100 == 0:
                    print(f"✅ {i}/500 - {correct/i*100:.1f}% accuracy")
            else:
                errors.append({
                    'case': i,
                    'message': message,
                    'expected': expected,
                    'got': result
                })
                if len(errors) <= 20:  # Pokaż tylko pierwsze 20 błędów
                    print(f"❌ #{i}: '{message}' → {result} (expected: {expected})")
                    
        except Exception as e:
            errors.append({
                'case': i,
                'message': message,
                'expected': expected,
                'got': f"ERROR: {e}"
            })
            print(f"💥 #{i}: '{message}' → ERROR: {e}")
    
    # PODSUMOWANIE
    print("\n" + "=" * 60)
    print(f"📊 WYNIKI TESTU REGRESYJNEGO")
    print("=" * 60)
    print(f"✅ Poprawne: {correct}/{len(test_cases)} ({correct/len(test_cases)*100:.1f}%)")
    print(f"❌ Błędne: {len(errors)} ({len(errors)/len(test_cases)*100:.1f}%)")
    
    if errors:
        print(f"\n🔍 PIERWSZYCH 10 BŁĘDÓW:")
        for error in errors[:10]:
            print(f"  • #{error['case']}: '{error['message'][:50]}...' → {error['got']} (expected: {error['expected']})")
    
    # STATYSTYKI PO KATEGORIACH
    categories = {}
    category_errors = {}
    
    for message, expected in test_cases:
        categories[expected] = categories.get(expected, 0) + 1
        
    for error in errors:
        cat = error['expected']
        category_errors[cat] = category_errors.get(cat, 0) + 1
    
    print(f"\n📈 STATYSTYKI PO KATEGORIACH:")
    for category in sorted(categories.keys()):
        total = categories[category]
        err_count = category_errors.get(category, 0)
        accuracy = (total - err_count) / total * 100
        print(f"  • {category}: {total-err_count}/{total} ({accuracy:.1f}%)")
    
    return correct, len(errors), errors

# URUCHOM TEST
if __name__ == "__main__":
    run_comprehensive_regex_test()