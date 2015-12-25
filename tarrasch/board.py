import json
import random
import cPickle

from chess import Board, SQUARES_180, pgn

from .database import singleton as db

class TarraschNoBoardException(Exception):
    pass

class TarraschBoard(Board):
    """An augmented Board from python-chess which also knows
    how to do useful things like persist itself, build itself
    from its persistence layer, render itself using jinchess diagrams,
    all sorts of fun stuff."""

    def __init__(self, channel, white_user, black_user, *args, **kwargs):
        super(TarraschBoard, self).__init__(*args, **kwargs)
        self.channel = channel
        self.white_user = white_user
        self.black_user = black_user
        self.last_move_time = 0

    @classmethod
    def from_backend(cls, channel):
        """Return the saved TarraschBoard for the given channel, or
        raise a TarraschNoBoardException if there is none."""
        record = db.get(channel)
        if not record:
            raise TarraschNoBoardException('No board found for channel {}'.format(channel))
        payload = json.loads(record)
        board = cls(channel, payload['white_user'], payload['black_user'])
        board.last_move_time = payload.get('last_move_time', 0)
        # Restore board positions from FEN
        board.set_fen(payload['fen'])
        # Restore state variables
        board.move_stack = cPickle.loads(str(payload['stacks']['move']))
        board.halfmove_clock_stack = cPickle.loads(str(payload['stacks']['halfmove_clock']))
        board.captured_piece_stack = cPickle.loads(str(payload['stacks']['captured_piece']))
        board.castling_right_stack = cPickle.loads(str(payload['stacks']['castling_right']))
        board.ep_square_stack = cPickle.loads(str(payload['stacks']['ep_square']))
        board.attacks_valid_stack = cPickle.loads(str(payload['stacks']['attacks_valid']))
        board.attacks_from_stack = cPickle.loads(str(payload['stacks']['attacks_from']))
        board.attacks_to_stack = cPickle.loads(str(payload['stacks']['attacks_to']))
        board.transpositions = cPickle.loads(str(payload['transpositions']))
        return board

    def save(self, last_move_time=None):
        payload = {'fen': self.fen(),
                   'white_user': self.white_user,
                   'black_user': self.black_user,
                   'last_move_time': last_move_time or self.last_move_time,
                   'stacks': {'move': cPickle.dumps(self.move_stack),
                              'halfmove_clock': cPickle.dumps(self.halfmove_clock_stack),
                              'captured_piece': cPickle.dumps(self.captured_piece_stack),
                              'castling_right': cPickle.dumps(self.castling_right_stack),
                              'ep_square': cPickle.dumps(self.ep_square_stack),
                              'attacks_valid': cPickle.dumps(self.attacks_valid_stack),
                              'attacks_from': cPickle.dumps(self.attacks_from_stack),
                              'attacks_to': cPickle.dumps(self.attacks_to_stack)},
                   'transpositions': cPickle.dumps(self.transpositions)}
        db.set(self.channel, json.dumps(payload))

    def kill(self):
        db.delete(self.channel)

    def get_url(self):
        render_string = ''
        for square in SQUARES_180:
            piece = self.piece_at(square)
            if piece:
                render_string += piece.symbol()
            else:
                render_string += '-'
        # We add some noise at the end to force Slack to render our shit
        return 'http://www.jinchess.com/chessboard/?s=s&cm=r&p={}#{}'.format(render_string, random.randint(0, 10000000))

    @property
    def current_turn_username(self):
        return self.white_user if self.turn else self.black_user

    def get_pgn(self):
        """Returns a string representing the PGN for the current board state (and
        the moves leading up to it)."""
        root = pgn.Game()
        root.headers['Event'] = 'Tarrasch Chess Bot'
        root.headers['White'] = self.white_user
        root.headers['Black'] = self.black_user

        next = root
        for move in self.move_stack:
            next = next.add_main_variation(move)

        return root.__str__()
