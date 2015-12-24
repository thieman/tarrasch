import json

from prettytable import PrettyTable

from .board import TarraschBoard, TarraschNoBoardException
from .config import MESSAGE_PREFIX as MP
from .database import singleton as db

# Used to get a game going, since we require multiple user
# inputs to do this we need to save some state in memory
# between those inputs
STARTUP_STATE = {}

def _render(client, channel, board=None):
    if not board:
        board = TarraschBoard.from_backend(channel)
    client.rtm_send_message(channel, board.get_url())
    color = 'white' if board.turn else 'black'
    user = board.white_user if color == 'white' else board.black_user
    if not board.is_game_over():
        client.rtm_send_message(channel, '*{}* ({}) to play.'.format(user, color))

def _start_game(client, channel, white_user, black_user):
    board = TarraschBoard(channel, white_user, black_user)
    board.save()
    _render(client, channel, board=board)

def _handle_claim(client, channel, user_name, rest):
    """Claim a side in the next game. Used after a start command."""
    if channel not in STARTUP_STATE:
        return client.rtm_send_message(channel, 'Say `{} start` to start a new game.'.format(MP))
    if not rest or rest[0].lower() not in ['white', 'black']:
        return client.rtm_send_message(channel, 'Say `{} claim white` or `{} claim black` to pick your side.'.format(MP))

    color = rest[0].lower()
    STARTUP_STATE[channel][color] = user_name
    client.rtm_send_message(channel, '*{}* will play as {}.'.format(user_name, color))

    if 'white' in STARTUP_STATE[channel] and 'black' in STARTUP_STATE[channel]:
        _start_game(client, channel, STARTUP_STATE[channel]['white'], STARTUP_STATE[channel]['black'])
        del STARTUP_STATE[channel]

def _handle_start(client, channel, user_name, rest):
    """Start a new game in the current channel."""
    try:
        board = TarraschBoard.from_backend(channel)
    except TarraschNoBoardException:
        board = None

    if board:
        return client.rtm_send_message(channel, 'A game is already going on in this channel between {} and {}'.format(board.white_user, board.black_user))
    STARTUP_STATE[channel] = {}
    client.rtm_send_message(channel, "Let's play chess! I need two players to say `{0} claim white` or `{0} claim black`.".format(MP))

def _handle_board(client, channel, user_name, rest):
    """Show the current board state for the game in this channel."""
    _render(client, channel)

def _handle_move(client, channel, user_name, rest):
    """Make a new move. Use algebraic notation, e.g. `move Nc3`"""
    board = TarraschBoard.from_backend(channel)
    if user_name != board.current_turn_username: # not this person's turn
        return

    if not rest:
        return
    move = rest[0]
    try:
        board.push_san(move)
    except ValueError:
        return client.rtm_send_message(channel, 'This move is illegal.')
    board.save()
    _render(client, channel, board=board)
    if board.is_game_over():
        _handle_game_over(client, channel, board)

def _handle_takeback(client, channel, user_name, rest):
    """Take back the last move. Can only be done by the current player."""
    board = TarraschBoard.from_backend(channel)
    if user_name != board.current_turn_username:
        return client.rtm_send_message(channel, 'Only the current player, *{}*, can take back the last move.'.format(board.current_turn_username))
    board.pop()
    board.save()
    _render(client, channel, board=board)

def _handle_forfeit(client, channel, user_name, rest):
    """Forfeit the current game."""
    board = TarraschBoard.from_backend(channel)
    if board.turn:
        _handle_game_over(client, channel, board, 'loss')
    else:
        _handle_game_over(client, channel, board, 'win')

def _handle_game_over(client, channel, board, result=None):
    if not result:
        if board.result() == '1-0':
            result = 'win'
        elif board.result() == '0-1':
            result = 'loss'
        elif board.result() == '*':
            raise ValueError('Result undetermined in game over handler, should not have gotten here')
        else:
            result = 'draw'
    _update_records(board.white_user, board.black_user, result)
    board.kill()
    if result != 'draw':
        winner = board.white_user if result == 'win' else board.black_user
        color = 'white' if result == 'win' else 'black'
        client.rtm_send_message(channel, '*{}* ({}) wins! Say `{} start` to play another game.'.format(winner, color, MP))
    else:
        client.rtm_send_message(channel, "It's a draw! Say `{} start` to play another game.".format(MP))

def _update_records(white_user, black_user, result):
    white_result = 'win' if result == 'win' else 'loss'
    black_result = 'loss' if result == 'win' else 'win'
    if result == 'draw':
        white_result, black_result = 'draw', 'draw'
    _update_record(white_user, black_user, white_result)
    _update_record(black_user, white_user, black_result)
    db.sadd('players', white_user)
    db.sadd('players', black_user)

def _update_record(user, against, result):
    record = json.loads(str(db.get(user) or {}))
    if against not in record:
        record[against] = {'win': 0, 'loss': 0, 'draw': 0}
    record[against][result] += 1
    db.set(user, json.dumps(record))

def _handle_record(client, channel, user_name, rest):
    """Show your record against each of your opponents."""
    record = db.get(user_name)
    if not record:
        return client.rtm_send_message(channel, 'User *{}* has not played any games.'.format(user_name))
    record = json.loads(str(record))
    table = PrettyTable(['Opponent', 'Games', 'Wins', 'Losses', 'Draws'])
    for opponent, results in record.iteritems():
        table.add_row([opponent, results['win'] + results['loss'] + results['draw'],
                       results['win'], results['loss'], results['draw']])
    table_string = table.get_string(sortby='Games', reversesort=True)
    client.rtm_send_message(channel, '```\n{}```'.format(table_string))

def _handle_leaderboard(client, channel, user_name, rest):
    """Show the overall W/L/D for all players."""
    table = PrettyTable(['Player', 'Games', 'Wins', 'Losses', 'Draws'])
    for player in db.smembers('players'):
        record = db.get(player)
        if not record:
            continue
        record = json.loads(str(record))
        wins, losses, draws = 0, 0, 0
        for opponent, results in record.iteritems():
            wins += results['win']
            losses += results['loss']
            draws += results['draw']
        table.add_row([player, wins + losses + draws,
                       wins, losses, draws])
    table_string = table.get_string(sortby='Wins', reversesort=True)
    client.rtm_send_message(channel, '```\n{}```'.format(table_string))

def _handle_help(client, channel, user_name, rest):
    help_string = ""
    for command in sorted(COMMANDS.keys()):
        if command == 'help':
            continue
        help_string += '{}: {}\n'.format(command, COMMANDS[command].__doc__)
    help_string += '\nYou can read all about algebraic notation here: https://goo.gl/OOquFQ\n'
    client.rtm_send_message(channel, help_string)

def handle_message(client, channel, user_name, message):
    words = map(lambda word: word.strip(), message.split())
    command, rest = words[0].lower(), words[1:]
    if command in COMMANDS:
        try:
            COMMANDS[command](client, channel, user_name, rest)
        except TarraschNoBoardException:
            client.rtm_send_message(channel, 'No board found for this channel, say `{} start` to start a new game.'.format(MP))

COMMANDS = {
    'start': _handle_start,
    'claim': _handle_claim,
    'board': _handle_board,
    'move': _handle_move,
    'takeback': _handle_takeback,
    'forfeit': _handle_forfeit,
    'record': _handle_record,
    'leaderboard': _handle_leaderboard,
    'help': _handle_help,
}
