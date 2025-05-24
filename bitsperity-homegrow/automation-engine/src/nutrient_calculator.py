#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, Tuple, Any, Optional
from .logger import get_logger

logger = get_logger(__name__)

class NutrientCalculator:
    """
    Klasse zur Berechnung der korrekten Nährstoffmengen zur Erreichung des Ziel-TDS-Werts
    unter Berücksichtigung der konfigurierten Nährstoffverhältnisse.
    
    Unterstützt die erweiterte Gerätekonfiguration, die das Wasservolumen und
    Lösungsstärken als Grundlage für Berechnungen verwendet.
    """
    
    # Standardwerte für die Lösungsstärken
    SOLUTION_STRENGTH_FACTORS = {
        "weak": 0.5,      # Schwache Lösung
        "standard": 1.0,  # Standardlösung
        "strong": 2.0     # Starke Lösung
    }
    
    # Standardwerte für Kalibrierungsfaktoren
    DEFAULT_CALIBRATION = {
        "tds_per_ml": 10.0,      # TDS-Erhöhung pro ml Nährstofflösung
        "ph_up_per_ml": 0.1,     # pH-Erhöhung pro ml pH-Up
        "ph_down_per_ml": 0.1    # pH-Senkung pro ml pH-Down
    }
    
    # Standardwerte für Dosierungslimits (als Prozentsatz des Wasservolumens)
    DEFAULT_DOSE_LIMITS = {
        "max_nutrient_percent": 0.1,    # 0.1% des Wasservolumens (20ml bei 20L)
        "min_nutrient_percent": 0.005,  # 0.005% des Wasservolumens (1ml bei 20L)
        "max_ph_percent": 0.025,        # 0.025% des Wasservolumens (5ml bei 20L)
        "min_ph_percent": 0.0025        # 0.0025% des Wasservolumens (0.5ml bei 20L)
    }
    
    # Standardwerte für Wartezeiten (in Minuten)
    DEFAULT_WAIT_TIMES = {
        "nutrient_minutes": 30,  # 30 Minuten zwischen Nährstoffaktionen
        "ph_minutes": 5          # 5 Minuten zwischen pH-Korrekturen
    }
    
    def __init__(self, device_config: Optional[Dict[str, Any]] = None):
        """
        Initialisiert den NutrientCalculator
        
        Args:
            device_config: Gerätekonfiguration mit optionalen Kalibrierungsdaten
        """
        self.device_config = device_config or {}
        
        # Hole die erweiterte Nährstoffkonfiguration
        self.nutrient_control = self.device_config.get('nutrient_control', {})
        
        # Wasservolumen des Pods
        self.water_volume_liters = self.nutrient_control.get('water_volume_liters', 20.0)
        
        # Lösungsstärken
        self.solution_strengths = self.nutrient_control.get('solution_strengths', {
            "nutrient1": "standard",
            "nutrient2": "standard",
            "nutrient3": "standard",
            "ph_up": "standard",
            "ph_down": "standard"
        })
        
        # Dosierungslimits
        self.dose_limits = self._get_dose_limits()
        
        # Kalibrierungswerte
        self.calibration = self._get_calibration()
    
    def _get_dose_limits(self) -> Dict[str, float]:
        """
        Holt die Dosierungslimits aus der Konfiguration oder verwendet Standardwerte.
        Rechnet Prozentsätze des Wasservolumens in absolute ml-Werte um.
        
        Returns:
            Dictionary mit Dosierungslimits in ml
        """
        config_limits = self.nutrient_control.get('dose_limits', {})
        percent_limits = self.DEFAULT_DOSE_LIMITS.copy()
        
        # Überschreibe Standardwerte mit konfigurierten Werten, falls vorhanden
        for key, value in config_limits.items():
            if key in percent_limits:
                percent_limits[key] = value
        
        # Umrechnung von Prozent in ml basierend auf dem Wasservolumen
        ml_limits = {
            # Nährstoffe
            "max_nutrient_ml": self.water_volume_liters * 1000 * percent_limits["max_nutrient_percent"],
            "min_nutrient_ml": self.water_volume_liters * 1000 * percent_limits["min_nutrient_percent"],
            # pH-Korrekturen
            "max_ph_ml": self.water_volume_liters * 1000 * percent_limits["max_ph_percent"],
            "min_ph_ml": self.water_volume_liters * 1000 * percent_limits["min_ph_percent"]
        }
        
        logger.debug(f"Dosierungslimits berechnet: {ml_limits}")
        
        return ml_limits
    
    def _get_calibration(self) -> Dict[str, float]:
        """
        Holt die Kalibrierungswerte aus der Konfiguration oder verwendet Standardwerte
        
        Returns:
            Dictionary mit Kalibrierungswerten
        """
        config_calibration = self.nutrient_control.get('calibration', {})
        calibration = self.DEFAULT_CALIBRATION.copy()
        
        # Überschreibe Standardwerte mit konfigurierten Werten, falls vorhanden
        for key, value in config_calibration.items():
            if key in calibration:
                calibration[key] = value
        
        return calibration
    
    def _get_solution_strength_factor(self, solution_type: str) -> float:
        """
        Berechnet den Stärkefaktor für eine Lösung
        
        Args:
            solution_type: Art der Lösung (z.B. "nutrient1", "ph_up")
            
        Returns:
            Stärkefaktor als Float
        """
        # Hole die konfigurierte Lösungsstärke oder Standardwert
        strength_name = self.solution_strengths.get(solution_type, "standard")
        
        # Konvertiere zu Stärkefaktor
        return self.SOLUTION_STRENGTH_FACTORS.get(strength_name, 1.0)
    
    def calculate_nutrient_amounts(self,
                                  current_tds: float,
                                  target_min_tds: float,
                                  target_max_tds: float,
                                  nutrient_ratio: Dict[str, float]) -> Tuple[bool, Dict[str, float]]:
        """
        Berechnet die benötigten Nährstoffmengen, um den Ziel-TDS-Bereich zu erreichen
        
        Args:
            current_tds: Aktueller TDS-Wert
            target_min_tds: Minimaler Ziel-TDS-Wert (ggf. Mitte)
            target_max_tds: Maximaler Ziel-TDS-Wert (ggf. Mitte)
            nutrient_ratio: Nährstoffverhältnis als Dictionary
        Returns:
            Tupel aus (Änderung notwendig, Nährstoffmengen-Dictionary)
        """
        logger.info(f"TDS-Korrektur berechnen: aktuell={current_tds:.1f}, Ziel-Min={target_min_tds:.1f}, Ziel-Max={target_max_tds:.1f}")
        logger.info(f"Wasservolumen im Tank: {self.water_volume_liters:.1f} Liter")
        logger.info(f"Nährstoffverhältnis: Nutrient1={nutrient_ratio.get('nutrient1_percent', 33.33):.1f}%, Nutrient2={nutrient_ratio.get('nutrient2_percent', 33.33):.1f}%, Nutrient3={nutrient_ratio.get('nutrient3_percent', 33.34):.1f}%")
        # Wenn min==max, dann ist das der Zielwert (Mitte)
        if target_min_tds == target_max_tds:
            tds_target = target_min_tds
            if abs(current_tds - tds_target) < 1.0:
                logger.info(f"TDS-Wert {current_tds:.1f} ist bereits am Zielwert {tds_target:.1f}. Keine Korrektur nötig.")
                return False, {'nutrient1_ml': 0, 'nutrient2_ml': 0, 'nutrient3_ml': 0}
            if current_tds >= tds_target:
                logger.info(f"TDS-Wert {current_tds:.1f} ist bereits über dem Zielwert {tds_target:.1f}. Keine Korrektur nötig.")
                return False, {'nutrient1_ml': 0, 'nutrient2_ml': 0, 'nutrient3_ml': 0}
            tds_increase = tds_target - current_tds
        else:
            if current_tds >= target_min_tds:
                logger.info(f"TDS-Wert {current_tds:.1f} ist bereits über dem Mindestwert {target_min_tds:.1f}. Keine Korrektur nötig.")
                return False, {'nutrient1_ml': 0, 'nutrient2_ml': 0, 'nutrient3_ml': 0}
            tds_target = (target_min_tds + target_max_tds) / 2
            tds_increase = tds_target - current_tds
        effective_tds_per_ml = self.calibration['tds_per_ml']
        if self.water_volume_liters > 20:
            volume_factor = (20 / self.water_volume_liters)
            effective_tds_per_ml = effective_tds_per_ml * volume_factor
        strength_factors = {
            'nutrient1': self._get_solution_strength_factor('nutrient1'),
            'nutrient2': self._get_solution_strength_factor('nutrient2'),
            'nutrient3': self._get_solution_strength_factor('nutrient3')
        }
        avg_strength_factor = (
            strength_factors['nutrient1'] * nutrient_ratio.get('nutrient1_percent', 33.33) +
            strength_factors['nutrient2'] * nutrient_ratio.get('nutrient2_percent', 33.33) +
            strength_factors['nutrient3'] * nutrient_ratio.get('nutrient3_percent', 33.34)
        ) / 100.0
        total_ml = tds_increase / (effective_tds_per_ml * avg_strength_factor)
        max_ml_per_addition = self.dose_limits['max_nutrient_ml']
        min_ml_per_addition = self.dose_limits['min_nutrient_ml']
        if total_ml > max_ml_per_addition:
            total_ml = max_ml_per_addition
        if total_ml < min_ml_per_addition:
            logger.info(f"Berechnete Menge {total_ml:.2f} ml ist unter Minimum {min_ml_per_addition:.2f} ml - keine Korrektur")
            return False, {'nutrient1_ml': 0, 'nutrient2_ml': 0, 'nutrient3_ml': 0}
        nutrient1_percent = nutrient_ratio.get('nutrient1_percent', 33.33)
        nutrient2_percent = nutrient_ratio.get('nutrient2_percent', 33.33)
        nutrient3_percent = nutrient_ratio.get('nutrient3_percent', 33.34)
        nutrient1_ml = total_ml * (nutrient1_percent / 100.0)
        nutrient2_ml = total_ml * (nutrient2_percent / 100.0)
        nutrient3_ml = total_ml * (nutrient3_percent / 100.0)
        nutrient1_ml = round(nutrient1_ml, 2)
        nutrient2_ml = round(nutrient2_ml, 2)
        nutrient3_ml = round(nutrient3_ml, 2)
        logger.info(f"Finale Nährstoffmengen: Nutrient1={nutrient1_ml} ml, Nutrient2={nutrient2_ml} ml, Nutrient3={nutrient3_ml} ml")
        return True, {
            'nutrient1_ml': nutrient1_ml,
            'nutrient2_ml': nutrient2_ml,
            'nutrient3_ml': nutrient3_ml
        }
    
    def calculate_ph_correction(self,
                               current_ph: float,
                               target_min_ph: float,
                               target_max_ph: float) -> Tuple[bool, str, float]:
        """
        Berechnet die benötigte pH-Korrekturmenge
        
        Args:
            current_ph: Aktueller pH-Wert
            target_min_ph: Minimaler Ziel-pH-Wert (ggf. Mitte)
            target_max_ph: Maximaler Ziel-pH-Wert (ggf. Mitte)
        Returns:
            Tuple aus (Änderung notwendig, Pumpentyp, Menge in ml)
            Pumpentyp ist entweder "ph_up" oder "ph_down"
        """
        zielbereich_str = f"[{target_min_ph:.2f}-{target_max_ph:.2f}]" if target_min_ph != target_max_ph else f"{target_min_ph:.2f}"
        if target_min_ph == target_max_ph:
            ph_target = target_min_ph
        else:
            ph_target = (target_min_ph + target_max_ph) / 2
        logger.info(f"pH-Korrektur: {current_ph:.2f} → Zielbereich {zielbereich_str}, Zielwert {ph_target:.2f}")
        logger.info(f"Wasservolumen im Tank: {self.water_volume_liters:.1f} Liter")

        # Wenn min==max, dann ist das der Zielwert (Mitte)
        if target_min_ph == target_max_ph:
            if abs(current_ph - ph_target) < 0.01:
                logger.info(f"pH-Wert {current_ph:.2f} ist bereits am Zielwert {ph_target:.2f}. Keine Korrektur nötig.")
                return False, "", 0
            # Richtung bestimmen
            if current_ph < ph_target:
                ph_difference = ph_target - current_ph
                pump_type = "ph_up"
            else:
                ph_difference = current_ph - ph_target
                pump_type = "ph_down"
        else:
            # Standard-Range-Logik (zur Sicherheit)
            if target_min_ph <= current_ph <= target_max_ph:
                logger.info(f"pH-Wert {current_ph:.2f} ist bereits im Zielbereich {zielbereich_str}. Keine Korrektur nötig.")
                return False, "", 0
            if current_ph < target_min_ph:
                ph_difference = ph_target - current_ph
                pump_type = "ph_up"
            else:
                ph_difference = current_ph - ph_target
                pump_type = "ph_down"

        ph_up_per_ml = self.calibration['ph_up_per_ml']
        ph_down_per_ml = self.calibration['ph_down_per_ml']
        ph_up_strength = self._get_solution_strength_factor('ph_up')
        ph_down_strength = self._get_solution_strength_factor('ph_down')
        ph_up_per_ml = ph_up_per_ml * ph_up_strength
        ph_down_per_ml = ph_down_per_ml * ph_down_strength
        if pump_type == "ph_up":
            correction_ml = ph_difference / ph_up_per_ml
        else:
            correction_ml = ph_difference / ph_down_per_ml
        # Dosierlimits
        max_ml_per_addition = self.dose_limits['max_ph_ml']
        min_ml_per_addition = self.dose_limits['min_ph_ml']
        if correction_ml > max_ml_per_addition:
            correction_ml = max_ml_per_addition
        if correction_ml < min_ml_per_addition:
            logger.info(f"Berechnete Menge {correction_ml:.2f} ml ist unter Minimum {min_ml_per_addition:.2f} ml - keine Korrektur")
            return False, "", 0
        correction_ml = round(correction_ml, 2)

        # Detailliertes Logging der Berechnungsschritte
        logger.info(
            f"pH-Korrektur-Berechnung:\n"
            f"  - Aktueller pH: {current_ph:.2f}\n"
            f"  - Ziel-pH: {ph_target:.2f} (Zielbereich: {target_min_ph:.2f}–{target_max_ph:.2f})\n"
            f"  - Differenz: {ph_difference:.2f} pH\n"
            f"  - Kalibrierung: {'{:.2f}'.format(ph_up_per_ml) if pump_type == 'ph_up' else '{:.2f}'.format(ph_down_per_ml)} pH/ml\n"
            f"  - Benötigte Menge: {ph_difference / (ph_up_per_ml if pump_type == 'ph_up' else ph_down_per_ml):.2f} ml\n"
            f"  - Min/Max-Limit: {min_ml_per_addition:.2f}/{max_ml_per_addition:.2f} ml\n"
            f"  - Dosierte Menge: {correction_ml:.2f} ml"
        )
        logger.info(f"Finale pH-Korrektur: {pump_type}, {correction_ml} ml")
        return True, pump_type, correction_ml
    
    def get_wait_time_seconds(self, action_type: str) -> int:
        """
        Gibt die Wartezeit für einen Aktionstyp in Sekunden zurück
        
        Args:
            action_type: Art der Aktion ('ph_up', 'ph_down', 'nutrients')
            
        Returns:
            Wartezeit in Sekunden
        """
        wait_times = self.nutrient_control.get('wait_times', self.DEFAULT_WAIT_TIMES)
        
        if action_type in ['ph_up', 'ph_down']:
            minutes = wait_times.get('ph_minutes', self.DEFAULT_WAIT_TIMES['ph_minutes'])
        else:  # 'nutrients'
            minutes = wait_times.get('nutrient_minutes', self.DEFAULT_WAIT_TIMES['nutrient_minutes'])
            
        return int(minutes * 60)
    
    def ml_to_pump_duration(self, pump_type: str, volume_ml: float) -> int:
        """
        Konvertiert ein Volumen in ml in eine Pumpenzeit in Millisekunden
        
        Args:
            pump_type: Art der Pumpe (z.B. "nutrient1", "ph_up")
            volume_ml: Volumen in ml
            
        Returns:
            Pumpendauer in Millisekunden
        """
        # Hole Pumpenflussraten aus der Gerätekonfiguration
        pump_rates = {}
        actuators = self.device_config.get('actuators', {})
        
        # Mappe Pumpentypen auf die entsprechenden Aktuatornamen
        pump_to_actuator = {
            'nutrient1': 'pump_nutrient_1',
            'nutrient2': 'pump_nutrient_2',
            'nutrient3': 'pump_nutrient_3',
            'ph_up': 'pump_ph_up',
            'ph_down': 'pump_ph_down',
            'water': 'pump_water'
        }
        
        # Extrahiere Flussraten aus der Aktuatorkonfiguration
        for pump, actuator in pump_to_actuator.items():
            if actuator in actuators and 'flow_rate' in actuators[actuator]:
                pump_rates[pump] = actuators[actuator]['flow_rate']
        
        # Standardwerte für Pumpenraten in ml/s, falls nicht konfiguriert
        default_rates = {
            'nutrient1': 1.0,  # 1 ml/s
            'nutrient2': 1.0,
            'nutrient3': 1.0,
            'ph_up': 1.0,
            'ph_down': 1.0,
            'water': 2.0       # 2 ml/s
        }
        
        # Verwende konfigurierte Flussrate oder Standardwert
        rate_ml_per_second = pump_rates.get(pump_type, default_rates.get(pump_type, 1.0))
        
        # Konvertiere ml zu Millisekunden - Flussrate ist in ml/s, nicht ml/min!
        # Formel: (volume_ml / rate_ml_per_second) * 1000
        if rate_ml_per_second <= 0:
            logger.warning(f"Ungültige Flussrate für Pumpe {pump_type}: {rate_ml_per_second} ml/s")
            rate_ml_per_second = default_rates.get(pump_type, 1.0)
            
        duration_ms = int((volume_ml / rate_ml_per_second) * 1000)
        
        # Begrenze auf sinnvolle Minimal- und Maximalwerte
        min_duration_ms = 500  # 0,5 Sekunden Mindestlaufzeit
        max_duration_ms = 10000  # 10 Sekunden maximale Laufzeit pro Korrektur
        
        if duration_ms < min_duration_ms:
            duration_ms = min_duration_ms
            logger.debug(f"Pumpenzeit für {pump_type} auf Minimalwert begrenzt: {min_duration_ms} ms")
        if duration_ms > max_duration_ms:
            duration_ms = max_duration_ms
            logger.warning(f"Pumpenzeit für {pump_type} auf Maximalwert begrenzt: {max_duration_ms} ms (ursprünglich: {(volume_ml / rate_ml_per_second) * 1000:.0f} ms)")
            
        logger.debug(f"Konvertiere {volume_ml} ml für Pumpe {pump_type} mit Flussrate {rate_ml_per_second} ml/s in {duration_ms} ms")
        
        return duration_ms 