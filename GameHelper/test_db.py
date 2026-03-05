#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test GameHelper DB connection"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

from Base.Repository.register import register_game_helper_connection, register_default_connection
from Base.Repository.base.connectionManager import ConnectionManager
from GameHelper.models.gameEntityModel import GameEntityModel

print("Registering connections...")
register_default_connection()
register_game_helper_connection()

print("\nChecking connections...")
default_conn = ConnectionManager.get('default')
game_conn = ConnectionManager.get('game_helper')

print(f"  default DB: {default_conn.config['database'] if default_conn else 'N/A'}")
print(f"  game_helper DB: {game_conn.config['database'] if game_conn else 'N/A'}")

print("\nQuerying game_entity table...")
try:
    entities = GameEntityModel.find_by(game_name="英雄联盟", limit=3)
    print(f"  Found {len(entities)} entities:")
    for e in entities:
        print(f"    - {e.entity_name} (ID: {e.entity_code})")
except Exception as ex:
    print(f"  Error: {ex}")

print("\nDone!")
