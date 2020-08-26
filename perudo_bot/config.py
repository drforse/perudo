import asyncio
import os

import pymongo
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

client = pymongo.MongoClient(os.environ['perudo_db'])
perudo_db = client.Perudo
active_games = perudo_db.active_games
groups_col = perudo_db.groups
users_col = perudo_db.users

API_TOKEN = os.environ['perudo_token']
loop = asyncio.get_event_loop()

storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot, storage=storage)
