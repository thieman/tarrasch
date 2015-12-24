from .board import TarraschBoard, TarraschNoBoardException
from .config import MESSAGE_PREFIX as MP

# Used to get a game going, since we require multiple user
# inputs to do this we need to save some state in-memory
# between those inputs
STARTUP_STATE = {}

def _render(client, channel, board=None):
    if not board:
        board = TarraschBoard.from_backend(channel)
    client.rtm_send_message(channel, board.get_url())
    color = 'white' if board.turn else 'black'
    user = board.white_user if color == 'white' else board.black_user
    client.rtm_send_message(channel, '*{}* ({}) to play.'.format(user, color))

def _start_game(client, channel, white_user, black_user):
    board = TarraschBoard(channel, white_user, black_user)
    board.save()
    _render(client, channel, board=board)

def _handle_claim(client, channel, user_name, rest):
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
    client.rtm_send_message(channel, "Let's start a new game! I need two players to say `{0} claim white` or `{0} claim black`.".format(MP))

def _handle_quit(client, channel, user_name, rest):
    board = TarraschBoard.from_backend(channel)
    client.rtm_send_message(channel, 'Ending the game between {} and {}.'.format(board.white_user, board.black_user))
    board.kill()

def _handle_board(client, channel, user_name, rest):
    _render(client, channel)

def _handle_move(client, channel, user_name, rest):
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
    if board.is_game_over():
        _handle_game_over(client, channel)
    else:
        _render(client, channel, board=board)

def _handle_takeback(client, channel, user_name, rest):
    board = TarraschBoard.from_backend(channel)
    if user_name != board.current_turn_username:
        return client.rtm_send_message(channel, 'Only the current player, *{}*, can take back the last move.'.format(board.current_turn_username))
    board.pop()
    board.save()
    _render(client, channel, board=board)

def _handle_game_over(client, channel):
    pass

def _handle_record(client, channel, user_name, rest):
    pass

def _handle_leaderboard(client, channel, user_name, rest):
    pass

def _handle_help(client, channel, user_name, rest):
    pass

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
    'quit': _handle_quit,
    'board': _handle_board,
    'move': _handle_move,
    'takeback': _handle_takeback,
    'record': _handle_record,
    'leaderboard': _handle_leaderboard,
    'help': _handle_help,
}
