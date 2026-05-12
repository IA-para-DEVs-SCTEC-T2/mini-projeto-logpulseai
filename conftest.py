"""Configuração global do pytest — adiciona raiz do projeto ao sys.path."""

import sys
import os

# Garante que o diretório raiz está no path para imports de src.*
sys.path.insert(0, os.path.dirname(__file__))
