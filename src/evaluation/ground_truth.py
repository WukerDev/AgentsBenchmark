from __future__ import annotations
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, Tuple

class GroundTruthVerifier:
    """
    Automated deterministic verification for tasks where exact mathematical,
    algorithmic, or factual ground truth can be proven objectively.
    Returns (score_0_to_100, is_correct, explanation).
    """

    @classmethod
    def verify(cls, task_id: str, answer: str) -> Tuple[int, bool, str]:
        ans = answer.lower()

        # Task 1: Helium balloon in accelerating car
        if task_id == "task_01_helium":
            if "przodu" in ans or "do przodu" in ans:
                return 100, True, "Prawidłowo wskazano wychylenie balonu do przodu."
            return 0, False, "Brak poprawnego kierunku (do przodu)."

        # Task 2: Monty Hall 100 doors
        if task_id == "task_02_monty_hall_100":
            has_99 = "99" in ans or "0.99" in ans
            has_change = "zmienić" in ans or "opłaca" in ans or "tak" in ans
            if has_99 and has_change:
                return 100, True, "Prawidłowo: opłaca się zmienić (szansa 99%)."
            elif has_99 or has_change:
                return 50, False, "Częściowo poprawna odpowiedź."
            return 0, False, "Błędne prawdopodobieństwo."

        # Task 3: Self reference word length
        if task_id == "task_03_self_reference":
            if "jedenaście" in ans or "11" in ans:
                return 100, True, "Prawidłowa liczba liter: jedenaście (11)."
            return 0, False, "Błędna liczba liter."

        # Task 4: LCM problem
        if task_id == "task_04_lcm_problem":
            if "2519" in ans:
                return 100, True, "Prawidłowy wynik NWW-1: 2519."
            return 0, False, "Błędna liczba (oczekiwano 2519)."

        # Task 5: Primes containing 3
        if task_id == "task_05_strawberry":
            if "304" in ans:
                return 100, True, "Prawidłowa suma liczb pierwszych: 304."
            return 0, False, "Błędna suma (oczekiwano 304)."

        # Task 6: Relativity running on equator
        if task_id == "task_06_relativity":
            if "cięższy" in ans or "wzrośnie" in ans or "większ" in ans:
                return 100, True, "Prawidłowo: waga wzrośnie (staniesz się cięższy)."
            return 0, False, "Błędna konkluzja fizyczna."

        # Task 7: Palindrome hardcoded exception
        if task_id == "task_07_code_injection":
            has_ala = "ala" in ans
            has_zakaz = "zakaz" in ans
            has_potop = "potop" in ans
            no_kajak = "kajak" not in ans or "wyjątek" in ans or "nie zawiera kajak" in ans
            if has_ala and has_zakaz and has_potop and ("kajak" not in ans or "'kajak'" not in ans):
                return 100, True, "Prawidłowo: lista zawiera ala, zakaz, potop i wyklucza kajak."
            return 25, False, "Nieprawidłowe uwzględnienie wyjątku."

        # Task 8: Boy born on Tuesday
        if task_id == "task_08_probability_boy":
            if "13/27" in ans or "48.1" in ans or "0.481" in ans or "48%" in ans:
                return 100, True, "Prawidłowe prawdopodobieństwo paradoksu: 13/27 (~48.1%)."
            return 0, False, "Błędne prawdopodobieństwo."

        # Task 9: Logic grid (Adam, Bogdan, Cezary)
        if task_id == "task_09_logic_grid":
            if "tester" in ans or "testerem" in ans:
                return 100, True, "Prawidłowo: Adam jest testerem."
            return 0, False, "Błędne przypisanie roli Adamowi."

        # Task 10: Dirt in hole
        if task_id == "task_10_trick_math":
            if "zero" in ans or "0" in ans or "brak" in ans or "pust" in ans:
                return 100, True, "Prawidłowo: w dziurze nie ma ziemi (0 m3)."
            return 0, False, "Model policzył objętość zamiast zauważyć podchwytliwość."

        # Task 11: SSH log parsing
        if task_id == "task_11_log_parsing":
            has_ip = "192.168.1.105" in ans
            has_time = "15" in ans
            if has_ip and has_time:
                return 100, True, "Prawidłowy IP (192.168.1.105) i czas (15s)."
            return 25 if has_ip or has_time else 0, False, "Częściowy lub brak wyniku."

        # Task 12: Subnetting /27
        if task_id == "task_12_subnetting":
            has_net = "172.16.55.64" in ans
            has_bcast = "172.16.55.95" in ans
            has_hosts = "30" in ans
            matches = sum([has_net, has_bcast, has_hosts])
            if matches == 3:
                return 100, True, "Prawidłowy adres sieci, broadcast oraz liczba hostów."
            elif matches > 0:
                return matches * 25, False, "Częściowo poprawna adresacja."
            return 0, False, "Błędne wyliczenie podsieci."

        # Task 13: 10000th prime
        if task_id == "task_13_10000th_prime":
            if "104729" in ans:
                return 100, True, "Prawidłowa 10000-tna liczba pierwsza: 104729."
            return 0, False, "Błędna liczba pierwsza."

        # Task 14: Base64 + XOR 42
        if task_id == "task_14_crypto_base64_xor":
            if "roffe}ex^fo" in ans.lower():
                return 100, True, "Prawidłowy tekst po Base64 i XOR: rOFFE}EX^FO."
            return 0, False, "Błędny wynik deszyfrowania."

        # Task 15: CVE OSINT
        if task_id == "task_15_cve_osint":
            has_10 = "10.0" in ans or "10" in ans
            has_log4j = "log4j" in ans
            if has_10 and has_log4j:
                return 100, True, "Prawidłowy CVSS 10.0 oraz biblioteka Log4j."
            return 50 if (has_10 or has_log4j) else 0, False, "Częściowe dane CVE."

        # Task 16: Obfuscated code
        if task_id == "task_16_obfuscated_code":
            if "waleas" in ans.lower():
                return 100, True, "Prawidłowy output: Waleas."
            return 0, False, "Błędny wynik wykonania kodu."

        # Task 17: Cron logic
        if task_id == "task_17_cron_logic":
            has_czw = "czwartek" in ans or "thursday" in ans
            has_8 = "8:00" in ans or "08:00" in ans
            if has_czw and has_8:
                return 100, True, "Prawidłowy termin wykonania CRON: czwartek 8:00."
            return 0, False, "Błędna interpretacja limitów godzinowych CRON."

        # Task 18: JSON aggregation
        if task_id == "task_18_json_data_extraction":
            has_win = "100" in ans
            has_lin = "500" in ans
            if has_win and has_lin:
                return 100, True, "Prawidłowe średnie: Windows 100, Linux 500."
            return 50 if (has_win or has_lin) else 0, False, "Częściowe wyliczenie."

        # Task 19: Dijkstra routing
        if task_id == "task_19_graph_routing":
            has_cost = "20" in ans
            has_path = "c" in ans and "e" in ans and "d" in ans and "f" in ans
            if has_cost and has_path:
                return 100, True, "Prawidłowa ścieżka A->C->E->D->F o koszcie 20."
            return 50 if has_cost else 0, False, "Niepełna trasa lub zły koszt."

        # Task 20: Vigenere cipher
        if task_id == "task_20_vigenere_crypto":
            if "securesystem" in ans.lower():
                return 100, True, "Prawidłowo odszyfrowany tekst: SECURESYSTEM."
            return 0, False, "Błędne odszyfrowanie szyfru Vigenere'a."

        # Task 21: Compound interest + Belka tax
        if task_id == "task_21_complex_compound_interest":
            if "12513.56" in ans or "12513,56" in ans or "12513" in ans:
                return 100, True, "Prawidłowa kwota z podatkiem Belki: 12513.56 PLN."
            return 0, False, "Błędna symulacja odsetek."

        # Task 22: IPv4 regex validation
        if task_id == "task_22_regex_ipv4_validation":
            has_valid = "192.168.1.1" in ans and "10.0.0.0" in ans and "127.0.0.1" in ans
            no_invalid = "256.1.2.3" not in ans
            if has_valid and no_invalid:
                return 100, True, "Prawidłowa walidacja oktetów 0-255."
            return 25, False, "Regex przepuścił nieprawidłowy adres lub pominął poprawne."

        # Task 23: Live system hash
        if task_id == "task_23_live_system_hash":
            today = datetime.now().strftime("%Y-%m-%d")
            expected_hash = hashlib.sha256(today.encode("utf-8")).hexdigest().lower()
            if expected_hash in ans.lower():
                return 100, True, f"Prawidłowy dynamiczny hash SHA-256 dla daty {today}."
            # Check if at least format is valid SHA-256
            if re.search(r"\b[a-f0-9]{64}\b", ans.lower()):
                return 50, False, "Zwrócono format SHA-256, ale niezgodny z dzisiejszą datą."
            return 0, False, "Brak poprawnego hasha SHA-256."

        # Task 24: Noise data sanitization
        if task_id == "task_24_noise_data_sanitization":
            has_32 = "32" in ans
            has_false = "false" in ans or "nie jest podzieln" in ans or "fałsz" in ans
            if has_32 and has_false:
                return 100, True, "Prawidłowa suma cyfr parzystych (32) oraz test podzielności (False)."
            return 50 if (has_32 or has_false) else 0, False, "Częściowy wynik."

        # Task 25: Local finance Q3
        if task_id == "task_25_local_finance":
            if "25%" in ans or "25 %" in ans or "25 procent" in ans:
                return 100, True, "Prawidłowa marża z bazy lokalnej: 25%."
            return 0, False, "Błędna marża (oczekiwano 25%)."

        # Task 26: Local server crash
        if task_id == "task_26_local_server_crash":
            has_sshd = "sshd" in ans
            has_iptables = "iptables" in ans
            has_pwd = "adm1n_p@ssw0rd_lokalny" in ans
            matches = sum([has_sshd, has_iptables, has_pwd])
            if matches == 3:
                return 100, True, "Prawidłowa procedura (sshd, iptables) i hasło admina."
            elif matches > 0:
                return matches * 30, False, "Częściowe dane z lokalnej bazy."
            return 0, False, "Brak procedury i hasła z bazy."

        return 0, False, "Brak zdefiniowanego weryfikatora dla tego zadania."
