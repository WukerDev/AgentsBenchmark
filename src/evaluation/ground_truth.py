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

        if task_id == "task_01_helium":
            if "przodu" in ans or "do przodu" in ans or "forward" in ans:
                return 100, True, "Prawidłowo: balon wychyla się do przodu (forward)."
            return 0, False, "Brak poprawnego kierunku (do przodu / forward)."

        if task_id == "task_02_monty_hall_100":
            has_99 = "99" in ans or "0.99" in ans
            has_change = any(k in ans for k in ["zmienić", "opłaca", "tak", "yes", "change"])
            if has_99 and has_change:
                return 100, True, "Prawidłowo: opłaca się zmienić (szansa 99%)."
            elif has_99 or has_change:
                return 50, False, "Częściowo poprawna odpowiedź."
            return 0, False, "Błędne prawdopodobieństwo."

        if task_id == "task_03_fibonacci_sum":
            if "9772042" in ans:
                return 100, True, "Prawidłowa połowa sumy liczb Fibonacciego: 9772042."
            return 0, False, "Błędna suma (oczekiwano 9772042)."
        if task_id == "task_03_self_reference":
            if "jedenaście" in ans or "11" in ans:
                return 100, True, "Prawidłowa liczba liter: jedenaście (11)."
            return 0, False, "Błędna liczba liter."

        if task_id == "task_04_collatz_conjecture":
            has_35655 = "35655" in ans
            has_324 = "324" in ans
            if has_35655 and has_324:
                return 100, True, "Prawidłowa liczba startowa (35655) oraz długość ciągu Collatza (324)."
            return 50 if (has_35655 or has_324) else 0, False, "Częściowy lub brak wyniku."
        if task_id == "task_04_lcm_problem":
            if "2519" in ans:
                return 100, True, "Prawidłowy wynik NWW-1: 2519."
            return 0, False, "Błędna liczba (oczekiwano 2519)."

        if task_id == "task_05_strawberry":
            if "304" in ans:
                return 100, True, "Prawidłowa suma liczb pierwszych: 304."
            return 0, False, "Błędna suma (oczekiwano 304)."

        if task_id == "task_06_relativity":
            if any(k in ans for k in ["cięższy", "wzrośnie", "większ", "heavier", "increase"]):
                return 100, True, "Prawidłowo: waga wzrośnie / staniesz się cięższy."
            return 0, False, "Błędna konkluzja fizyczna."

        if task_id == "task_07_code_injection":
            has_ala = "ala" in ans
            has_zakaz = "zakaz" in ans
            has_potop = "potop" in ans
            if has_ala and has_zakaz and has_potop and ("'kajak'" not in ans or "not 'kajak'" in ans or "wyjątek" in ans):
                return 100, True, "Prawidłowo: lista zawiera ala, zakaz, potop i wyklucza kajak."
            return 25, False, "Nieprawidłowe uwzględnienie wyjątku."

        if task_id == "task_08_probability_boy":
            if any(k in ans for k in ["13/27", "48.1", "0.481", "48%"]):
                return 100, True, "Prawidłowe prawdopodobieństwo paradoksu: 13/27 (~48.1%)."
            return 0, False, "Błędne prawdopodobieństwo."

        if task_id == "task_09_logic_grid":
            if "tester" in ans or "testerem" in ans or "qa" in ans:
                return 100, True, "Prawidłowo: Adam jest testerem."
            return 0, False, "Błędne przypisanie roli Adamowi."

        if task_id == "task_10_trick_math":
            if any(k in ans for k in ["zero", "0", "brak", "pust", "none", "empty"]):
                return 100, True, "Prawidłowo: w dziurze nie ma ziemi (0 m3)."
            return 0, False, "Model policzył objętość zamiast zauważyć podchwytliwość."

        if task_id == "task_11_log_parsing":
            has_ip = "192.168.1.105" in ans
            has_time = "15" in ans
            if has_ip and has_time:
                return 100, True, "Prawidłowy IP (192.168.1.105) i czas (15s)."
            return 25 if has_ip or has_time else 0, False, "Częściowy lub brak wyniku."

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

        if task_id == "task_13_10000th_prime":
            if "104729" in ans:
                return 100, True, "Prawidłowa 10000-tna liczba pierwsza: 104729."
            return 0, False, "Błędna liczba pierwsza."

        if task_id == "task_14_crypto_base64_xor":
            if "boffe}exfn" in ans.lower() or "roffe}ex^fo" in ans.lower():
                return 100, True, "Prawidłowy tekst po Base64 i XOR."
            return 0, False, "Błędny wynik deszyfrowania."

        if task_id == "task_15_cve_osint":
            has_10 = "10.0" in ans or "10" in ans
            has_log4j = "log4j" in ans
            if has_10 and has_log4j:
                return 100, True, "Prawidłowy CVSS 10.0 oraz biblioteka Log4j."
            return 50 if (has_10 or has_log4j) else 0, False, "Częściowe dane CVE."

        if task_id == "task_16_obfuscated_code":
            if "waleas" in ans.lower():
                return 100, True, "Prawidłowy output: Waleas."
            return 0, False, "Błędny wynik wykonania kodu."

        if task_id == "task_17_cron_logic":
            has_wed = "środa" in ans or "wednesday" in ans
            has_16 = "16:15" in ans
            has_thu = "czwartek" in ans or "thursday" in ans
            has_8 = "8:00" in ans or "08:00" in ans
            if (has_wed and has_16) or (has_thu and has_8):
                return 100, True, "Prawidłowy termin wykonania CRON."
            return 0, False, "Błędna interpretacja limitów CRON."

        if task_id == "task_18_json_data_extraction":
            has_win = "100" in ans
            has_lin = "500" in ans
            if has_win and has_lin:
                return 100, True, "Prawidłowe średnie: Windows 100, Linux 500."
            return 50 if (has_win or has_lin) else 0, False, "Częściowe wyliczenie."

        if task_id == "task_19_graph_routing":
            has_cost = "20" in ans
            has_path = "c" in ans and "e" in ans and "d" in ans and "f" in ans
            if has_cost and has_path:
                return 100, True, "Prawidłowa ścieżka A->C->E->D->F o koszcie 20."
            return 50 if has_cost else 0, False, "Niepełna trasa lub zły koszt."

        if task_id == "task_20_vigenere_crypto":
            if "securesystem" in ans.lower():
                return 100, True, "Prawidłowo odszyfrowany tekst: SECURESYSTEM."
            return 0, False, "Błędne odszyfrowanie szyfru Vigenere'a."

        if task_id == "task_21_complex_compound_interest":
            if any(k in ans for k in ["12513.56", "12513,56", "12513"]):
                return 100, True, "Prawidłowa kwota z podatkiem Belki: 12513.56 PLN."
            return 0, False, "Błędna symulacja odsetek."

        if task_id == "task_22_regex_ipv4_validation":
            has_valid = "192.168.1.1" in ans and "10.0.0.0" in ans and "127.0.0.1" in ans
            no_invalid = "256.1.2.3" not in ans
            if has_valid and no_invalid:
                return 100, True, "Prawidłowa walidacja oktetów 0-255."
            return 25, False, "Regex przepuścił nieprawidłowy adres lub pominął poprawne."

        if task_id == "task_23_anagram_groups":
            if "2" in ans:
                return 100, True, "Prawidłowa liczba grup anagramów o 3 słowach: 2."
            return 0, False, "Błędna liczba grup (oczekiwano 2)."

        if task_id == "task_24_noise_data_sanitization":
            has_32 = "32" in ans
            has_false = any(k in ans for k in ["false", "nie jest podzieln", "fałsz"])
            if has_32 and has_false:
                return 100, True, "Prawidłowa suma cyfr parzystych (32) oraz test podzielności (False)."
            return 50 if (has_32 or has_false) else 0, False, "Częściowy wynik."

        if task_id == "task_25_perfect_numbers":
            if all(num in ans for num in ["6", "28", "496", "8128"]):
                return 100, True, "Prawidłowa lista liczb doskonałych: [6, 28, 496, 8128]."
            return 25, False, "Brak wszystkich liczb doskonałych do 1 000 000."

        if task_id == "task_26_sundays_20th_century":
            if "72" in ans:
                return 100, True, "Prawidłowa liczba niedziel wypadających 1. dnia miesiąca: 72."
            return 0, False, "Błędna liczba niedziel (oczekiwano 72)."

        if task_id == "task_27_fsharp_minor_frequencies":
            if "1364.36" in ans or "1364,36" in ans or "1364" in ans:
                return 100, True, "Prawidłowa suma częstotliwości trójdźwięku Fis-moll: 1364.36 Hz."
            return 0, False, "Błędna suma częstotliwości (oczekiwano 1364.36)."

        if task_id == "task_28_local_finance_margin":
            if any(k in ans for k in ["25%", "25.0%", "25.0 %", "25 %", "25 procent"]):
                return 100, True, "Prawidłowa marża zysku netto z bazy lokalnej: 25.0%."
            return 0, False, "Błędna marża (oczekiwano 25.0%)."

        if task_id == "task_29_local_incident_response":
            has_sshd = "sshd" in ans
            has_iptables = "iptables" in ans
            has_pwd = "adm1n_p@ssw0rd_lokalny" in ans
            matches = sum([has_sshd, has_iptables, has_pwd])
            if matches == 3:
                return 100, True, "Prawidłowa procedura awaryjna i hasło administratora z lokalnej bazy."
            elif matches > 0:
                return matches * 30, False, "Częściowe odnalezienie danych z lokalnej bazy."
            return 0, False, "Brak procedury i hasła z bazy."

        if task_id == "task_30_local_project_gamma_access":
            has_status = "krytyczn" in ans or "critical" in ans
            has_code = "778899" in ans
            has_ip = "10.200.45.12" in ans
            matches = sum([has_status, has_code, has_ip])
            if matches == 3:
                return 100, True, "Prawidłowy status, kod dostępu (778899) oraz IP serwera Projektu Gamma."
            elif matches > 0:
                return matches * 30, False, "Częściowe dane projektu Gamma."
            return 0, False, "Brak danych Projektu Gamma w odpowiedzi."

        if task_id == "task_31_osint_heartbleed_cve":
            has_cve = "cve-2014-0160" in ans
            has_year = "2014" in ans
            has_hb = "heartbeat" in ans
            if has_cve and (has_year or has_hb):
                return 100, True, "Prawidłowy CVE-2014-0160 oraz rok / funkcja Heartbeat."
            return 50 if has_cve else 0, False, "Brak lub niepełny identyfikator CVE."

        if task_id == "task_32_knapsack_optimization":
            if "120" in ans or "$120" in ans:
                return 100, True, "Prawidłowa maksymalna wartość plecaka: $120."
            return 0, False, "Błędne rozwiązanie problemu plecakowego (oczekiwano $120)."

        if task_id == "task_33_jwt_token_decoding":
            has_name = "jan kowalski" in ans
            has_admin = "true" in ans or "prawda" in ans or "tak" in ans
            if has_name and has_admin:
                return 100, True, "Prawidłowo zdekodowane dane JWT: Jan Kowalski, Admin: True."
            return 50 if (has_name or has_admin) else 0, False, "Częściowo zdekodowany token."

        if task_id == "task_34_monte_carlo_pi":
            if "3.14" in ans or "3.13" in ans:
                return 100, True, "Prawidłowa estymacja liczby Pi metodą Monte Carlo (~3.141)."
            return 0, False, "Estymacja Pi poza oczekiwanym zakresem."

        if task_id == "task_35_sql_injection_defense":
            has_cwe = "sql injection" in ans or "cwe-89" in ans or "iniekcj" in ans
            has_param = "?" in ans or "parameter" in ans or "prepared" in ans
            if has_cwe and has_param:
                return 100, True, "Prawidłowa identyfikacja SQL Injection i poprawka na zapytanie parametryzowane."
            return 50 if (has_cwe or has_param) else 0, False, "Niepełna analiza podatności lub brak parametryzacji."

        return 0, False, "Brak weryfikatora dla tego zadania."
