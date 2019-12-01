import traceback
import asyncio
import logging
from aiogram import executor
from aiogram.utils import exceptions
from aiogram.utils.executor import start_webhook
from config import active_games, bot, dp
from Perudo import actual_game

loop = asyncio.get_event_loop()
logging.basicConfig(level=logging.WARNING)

developers = [500238135]


@dp.message_handler(commands=['start'])
async def start_react(m):
    await bot.send_message(m.chat.id, 'Привет, че как, я бот для игры в ПЕРУДО - Игры в кости по версии Пиратов' \
                                      ' Карибского Моря, подробности игры Вы можете у знать в Хелпе! /help')


@dp.message_handler(commands=['help'])
async def help(m):
    help = 'ПЕРУДО - ИГРА В КОСТИ (измененная версия "пиратов карибского моря")\n' \
           'В начале игры всем выдается по 5 кубиков, кубики подбрасываются.\n' \
           'Первый игрок называют ставку (кол-во кубиков определенного номинала на столе).' \
           'Кол-во кубиков в ставке ограничивается количеством кубиков на столе.\n'\
           'Следующий игрок может либо повысить ставку , либо сказать, что предыдущий соврал.' \
           ' Если предыдущий игрок соврал, то он проигрывает, в противном' \
           'случае проигрывает обвинитель.\n' \
           'Игрок врет, если количество кубиков названного номинала меньше, если же больше или столько же,' \
           'то игрок говорит правду.\n' \
           'В первый кон никто не знает ничьих кубиков, во второй кон все игроки узнают свои кубики.\n\n' \
           'Повышение ставки: Надо повысить количество, или номинал, при повышении количества - номинал можно' \
           ' изменять как угодно, если не повышать количество, то номинал может быть только выше,' \
           ' количество всегда можно только повышать!' \
           '/perudo - начать набор игру, или саму игру\n' \
           '/pjoin - присоедениться к игре\n' \
           '/call_liar - обвинить предыдущего игрока во лжи\n' \
           '/pabort - Прекратить игру'
    await bot.send_message(m.chat.id, help)


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['perudo'])
async def start_game(m):
    try:
        if not active_games.find_one({'group': m.chat.id}):
            await actual_game.open_game(m.chat.id, m.from_user.id)
            await bot.send_message(m.chat.id,
                                   'Эй вы там, этот юнец хочет сыграть в кости! Кто хочет выиграть пару золотых?')
            return
        if active_games.find_one({'group': m.chat.id})['status'] != 'recruitment':
            await bot.send_message(m.chat.id, 'Мы тут уже играем, обожди!')
            return
        if len(active_games.find_one({'group': m.chat.id})['players']) > 1:
            await actual_game.start(m.chat.id, m.from_user.id)
        else:
            await bot.send_message(m.chat.id,
                                   'Ты со столом играть собрался? Где твои противники?',
                                   reply_to_message_id=m.message_id)
    except:
        print(traceback.format_exc())


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['pjoin'])
async def join_game(m):
    text = await actual_game.join(m.chat.id, m.from_user.id)
    await bot.send_message(m.chat.id, text, reply_to_message_id=m.message_id)


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['call_liar'])
async def stop_game(m):
    x = await actual_game.call_liar(m.chat.id, m.from_user.id)
    await bot.send_message(m.chat.id, x, parse_mode='html')


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['pabort'])
async def stop_game(m):
    x = await actual_game.pabort(m.chat.id, m.from_user.id)
    await bot.send_message(m.chat.id, x)


@dp.message_handler(lambda m: m.chat.type != 'private' and m.text.replace(' ', '').isdigit(), content_types=['text'])
async def get_stake(m):
    if len(m.text.split()) != 2:
        return
    if not active_games.find_one({'group': m.chat.id}):
        return
    if m.from_user.id not in active_games.find_one({'group': m.chat.id})['players']:
        return
    stake = {'dice_quant': int(m.text.split()[0]),
             'dice_value': int(m.text.split()[1])}
    x = await actual_game.make_stake(m.chat.id, m.from_user.id, stake)
    if x:
        await bot.send_message(m.chat.id, x, reply_to_message_id=m.message_id)


@dp.callback_query_handler(lambda c: c.data == 'dices')
async def get_dices(c):
    await actual_game.show_dices(c.id, c.message.chat.id, c.from_user.id)

executor.start_polling(dp, loop=loop, skip_updates=True)
