import pymongo
from aiogram import Bot, types, executor
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import os

client = pymongo.MongoClient(os.environ['perudo_db'])
perudo_db = client.Perudo
active_games = perudo_db.active_games

API_TOKEN = os.environ['perudo_token']
loop = asyncio.get_event_loop()

storage = MemoryStorage()
bot = Bot(API_TOKEN)
dp = Dispatcher(bot, storage=storage)
