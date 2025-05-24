#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HomeGrow Server - Startskript

Dieses Skript startet den HomeGrow Server.
"""

import os
import sys
import argparse

# Füge das Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.main import HomeGrowServer

def parse_arguments():
    """Parst die Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(description='HomeGrow Server')
    parser.add_argument('-c', '--config', help='Pfad zur Konfigurationsdatei')
    return parser.parse_args()

def main():
    """Hauptfunktion"""
    # Parse Kommandozeilenargumente
    args = parse_arguments()
    
    # Starte den Server
    server = HomeGrowServer(args.config)
    server.start()

if __name__ == '__main__':
    main() 