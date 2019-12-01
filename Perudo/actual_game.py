from config import active_games, bot
from aiogram import types
import random

dices_values = [1, 2, 3, 4, 5, 6]


async def open_game(chat_id, user_id):
    active_games.insert_one({'group': chat_id,
                             'players': [user_id],
                             'status': 'recruitment',
                             'creator': user_id,
                             'round': 0})


async def start(chat_id, user_id):
    game_doc = active_games.find_one({'group': chat_id})
    players = game_doc['players']
    players_usernames = ''
    for player in players:
        game_doc[str(player)] = {'dices': await flip_dices()}
        member = await bot.get_chat_member(chat_id, player)
        if game_doc['creator'] == player:
            end = '(!) '
        else:
            end = ' '
        if member.user.username:
            players_usernames += '@' + member.user.username + end
        else:
            players_usernames += member.user.first_name + end
    game_doc['status'] = 'started'
    game_doc['current_player'] = game_doc['creator']
    active_games.replace_one({'group': chat_id},
                             game_doc)
    await bot.send_message(chat_id, 'Игра начинается! Кидаем кости.')
    await bot.send_message(chat_id, players_usernames)
    await bot.send_message(chat_id, 'Делайте ваши ставки!')


async def join(chat_id, user_id):
    if 'players' not in active_games.find_one({'group': chat_id}):
        return 'Позови народ сначала! /perudo'
    if user_id in active_games.find_one({'group': chat_id})['players']:
        return 'Че ты хочешь, а? Тебя УЖЕ приняли в игру!! /perudo'
    if active_games.find_one({'group': chat_id})['status'] != 'recruitment':
        return 'Мы тут уже играем, обожди!'
    active_games.update_one({'group': chat_id},
                            {'$push': {'players': user_id}})
    return 'Еще один простак решил потерять свои деньги? Ну давай, присоединяйся. /perudo'


async def make_stake(chat_id, user_id, stake):
    game = active_games.find_one({'group': chat_id})
    if not game:
        return
    if game['current_player'] != user_id:
        return
    dices_global_quant = len(game['players'])*5
    if 'last_stake' in game:
        last_stake = game['last_stake']
        if stake['dice_quant'] < last_stake['dice_quant']:
            return 'Количество кубиков в ставке не должно уменьшаться'
        elif stake['dice_quant'] == last_stake['dice_quant']:
            if stake['dice_value'] <= last_stake['dice_value']:
                return 'Номинал кубиков должен быть выше, чем в предыдущей ставке, если количество не изменено!'
        if stake['dice_value'] > 6:
            return 'Кубики шестигранные, лол!'
    if stake['dice_quant'] > dices_global_quant:
        return 'Количество превышает количество кубиков на столе!'
    player = game[str(user_id)]
    player['stake'] = stake
    active_games.update_one({'group': chat_id},
                            {'$set': {str(user_id): player}})
    active_games.update_one({'group': chat_id},
                            {'$set': {'last_stake': stake}})
    active_games.update_one({'group': chat_id},
                            {'$set': {'last_player': user_id}})
    next_player = game['players'].index(game['current_player'])
    try:
        next_player = game['players'][next_player+1]
    except IndexError:
        next_player = game['players'][0]
        active_games.update_one({'group': chat_id},
                                {'$inc': {'round': 1}})
    active_games.update_one({'group': chat_id},
                            {'$set': {'current_player': next_player}})
    x = 0
    del player['stake']
    for player in game['players']:
        if 'stake' not in game[str(player)]:
            x += 1
    if x == 1 and game['round'] == 0:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton('Посмотреть кубики', callback_data='dices'))
        await bot.send_message(chat_id=chat_id,
                               text='Первый кон окончен, начинается второй кон, игроки, теперь посмотрите свои кубики',
                               reply_markup=kb)
    member = await bot.get_chat_member(chat_id, next_player)
    return f'Теперь ходит @{member.user.username}'


async def show_dices(call_id, chat_id, user_id):
    game = active_games.find_one({'group': chat_id})
    if not game:
        return
    if user_id not in game['players']:
        await bot.answer_callback_query(call_id, 'Ты не играешь, и бутылка рома!')
    else:
        dices = str(game[str(user_id)]['dices']).replace('[', '').replace(']', '')
        await bot.answer_callback_query(call_id, dices, show_alert=True)


async def call_liar(chat_id, user_id):
    game = active_games.find_one({'group': chat_id})
    if not game:
        return 'Игра не начата.'
    if game['status'] != 'started':
        return 'Игра еще даже не началась!'
    if 'last_player' not in game:
        return 'Некого обвинять, никто ещё не походил'
    if user_id != game['current_player']:
        return 'Не твой ход, салага!'
    last_player = game['last_player']
    last_stake = game['last_stake']
    all_dices = []
    for player in game['players']:
        all_dices += game[str(player)]['dices']
    count_dices = all_dices.count(last_stake['dice_value'])
    member_lier = await bot.get_chat_member(chat_id, game['last_player'])
    member_lier = f'@{member_lier.user.username}' if member_lier.user.username else member_lier.user.first_name
    member_prosecutor = await bot.get_chat_member(chat_id, user_id)
    member_prosecutor = f'@{member_prosecutor.user.username}' if member_prosecutor.user.username else member_prosecutor.user.first_name
    active_games.delete_one({'group': chat_id})
    results = await get_game_results(game)
    if count_dices >= last_stake['dice_quant']:
        return f'{member_lier} не врал! {member_prosecutor} проиграл!\n\n{results}'
    else:
        return f'{member_lier} соврал и проиграл! {member_prosecutor} выиграл!\n\n{results}'


async def pabort(chat_id, user_id):
    game = active_games.find_one({'group': chat_id})
    member = await bot.get_chat_member(chat_id, user_id)
    if not game:
        return 'Да мы в общем-то и не собирались играть, давай лучше выпьем!'
    if user_id != game['creator'] and member.status not in ['creator', 'administrator']:
        return 'Игра может быть остановлена только ее создателем или капитаном корабля и его ближайшими друзьями!'
    active_games.delete_one({'group': chat_id})
    if game['status'] == 'started':
        return 'Игра окончена!'
    else:
        return 'Набор игроков прекращен, все разошлись'


async def flip_dices():
    dices = []
    for i in range(0, 5):
        dices.append(random.randint(1, 6))
    return dices


async def get_game_results(game):
    print(game)
    players = {}
    for player in game['players']:
        players[str(player)] = game[str(player)]
    results = 'Кубики игроков:\n'
    print(players)
    for player in players:
        player_username = await bot.get_chat_member(game['group'], player)
        player_username = player_username.user.username
        dices = str(game[player]['dices']).replace('[', '').replace(']', '').replace(game['last_stake']['dice_value'],
                                                                                     f'<b>{game["last_stake"]["dice_value"]}</b>')
        results += player_username + ': ' + dices + '\n'
    return results
