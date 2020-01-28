import traceback
import asyncio
import logging
from aiogram import executor
from aiogram.utils import exceptions
from aiogram.utils.executor import start_webhook
from config import active_games, users_col, groups_col, bot, dp
from Perudo import actual_game
import random

loop = asyncio.get_event_loop()
logging.basicConfig(level=logging.WARNING)

developers = [500238135]


async def check_group_and_user(chat_id, user_id):
    group = groups_col.find_one({'group_id': chat_id})
    if not group:
        groups_col.insert_one({'group_id': chat_id,
                               'users': [user_id]})
        group = groups_col.find_one({'group_id': chat_id})
    user = users_col.find_one({'user_id': user_id})
    if not user:
        users_col.insert_one({'user_id': user_id,
                              'years': 100,
                              'games_finished': 0,
                              'loses': 0})
    if user_id not in group['users']:
        groups_col.update_one({'group_id': chat_id},
                              {'$push': {'users': user_id}})


@dp.message_handler(commands=['start'])
async def start_react(m):
    await check_group_and_user(m.chat.id, m.from_user.id)

    await bot.send_message(m.chat.id, 'Привет, че как, я бот для игры в ПЕРУДО - Игры в кости по версии Пиратов '
                                      'Карибского Моря ☠️, подробности игры Вы можете у знать в Хелпе! /help')


@dp.message_handler(commands=['stats'])
async def get_stats(m):
    await check_group_and_user(m.chat.id, m.from_user.id)

    user_doc = users_col.find_one({'user_id': m.from_user.id})
    member = await bot.get_chat_member(m.chat.id, m.from_user.id)
    name = member.user.first_name
    years_left = user_doc["years"] if user_doc["years"] != 0 else 'Свободен!'
    stats = f'*{name}*:\n' \
            f'Оставшиеся годы службы: {years_left}\n' \
            f'Всего игр: {user_doc["games_finished"]}\n' \
            f'Проигрыши: {user_doc["loses"]}'

    try:
        await bot.send_message(m.chat.id, stats, reply_to_message_id=m.message_id, parse_mode='markdown')
    except exceptions.MessageToReplyNotFound:
        await bot.send_message(m.chat.id, stats, parse_mode='markdown')


@dp.message_handler(commands=['help'])
async def help(m):
    await check_group_and_user(m.chat.id, m.from_user.id)

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


@dp.message_handler(commands=['adventure'])
async def get_in_adventure(m):
    await check_group_and_user(m.chat.id, m.from_user.id)

    user_doc = users_col.find_one({'user_id': m.from_user.id})
    last_adventure = user_doc.get('last_adventure')
    if not last_adventure:
        last_adventure = 0
    date = m.date.timestamp()
    if date - last_adventure < 60*60:
        await bot.send_message(m.chat.id, f'Вы еще не вернулись из предыдущего приключения,'
                                          f' осталось {(date - last_adventure)/60} минут')
        return

    inc_years = random.randint(0, 150)
    users_col.update_one({'user_id': m.from_user.id},
                         {'$set': {'last_adventure': date}})
    users_col.update_one({'user_id': m.from_user.id},
                         {'$inc': {'years': inc_years}})

    if inc_years == 0:
        await bot.send_message(m.chat.id, 'Вы вернулись из своего очередного приключения с новыми байками и золотом!,'
                                          'если Пасюк будет непротив, то на этот редкий случай (1/150) можно сделать, '
                                          'чтобы в его боте скачек прибавлялось рандомное количество денег хДДДДДДДД')
    elif user_doc['years'] == 0:
        await bot.send_message(m.chat.id, f'По неосторожности Вы оказались на борту голландца,'
                                          f' и должны отработать {inc_years} лет на его капитана!')
    else:
        await bot.send_message(m.chat.id, f'По неосторожности Вы прибавили себе {inc_years}'
                                          f' лет на службе на борту голландца!')


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['perudo'])
async def start_game(m):
    try:
        await check_group_and_user(m.chat.id, m.from_user.id)

        game_doc = active_games.find_one({'group': m.chat.id})
        if not game_doc:
            if len(m.text.split()) != 2:
                await bot.send_message(m.chat.id, '/perudo <ставка>')
                return
            if not m.text.split()[1].isdigit():
                await bot.send_message(m.chat.id,
                                       'Не всучивай нам эту безделицу, ставь ГОДЫ (ставка должна быть числом)!')
                return
            bet = m.text.split()[1]
            await actual_game.open_game(m.chat.id, m.from_user.id, bet)
            await bot.send_message(m.chat.id,
                                   'Эй вы там, этот юнец хочет сыграть в кости! '
                                   'Кто хочет скинуть пару лет службы на Голландце? 😈\n'
                                   'Присоединиться: /pjoin <ставка>')
            return
        if game_doc['status'] != 'recruitment':
            await bot.send_message(m.chat.id, 'Мы тут уже играем, обожди!')
            return
        if m.from_user.id not in game_doc['players']:
            await bot.send_message(m.chat.id, 'Ты не в игре!\nПрисоединиться: /pjoin <ставка>')
            return
        if len(active_games.find_one({'group': m.chat.id})['players']) == 1:
            await bot.send_message(m.chat.id,
                                   'Ты со столом играть собрался? Где твои противники?',
                                   reply_to_message_id=m.message_id)
            return

        await actual_game.start(m.chat.id, m.from_user.id)
    except:
        print(traceback.format_exc())


@dp.message_handler(lambda m: m.chat.type != 'private', commands=['pjoin'])
async def join_game(m):
    await check_group_and_user(m.chat.id, m.from_user.id)

    if len(m.text.split()) != 2:
        text = await actual_game.join(m.chat.id, m.from_user.id)
    elif not m.text.split()[1].isdigit():
        await bot.send_message(m.chat.id, 'Не всучивай нам эту безделицу, ставь ГОДЫ (ставка долдна быть числом)!')
        return
    else:
        bet = m.text.split()[1]
        text = await actual_game.join(m.chat.id, m.from_user.id, bet)
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
