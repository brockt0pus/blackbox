import kivy
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.atlas import Atlas

from config import atoms
from engine import Board

atlas = Atlas('assets/defaulttheme.atlas') # TODO: desaturate button press

# Fixed crashing on android!
Builder.load_file('main.kv')

kivy.require('1.10.0')

# Create the screen manager
sm = None

# Instantiate game board
game = None


class Scheme:
    """Contains color scheme & color variables."""
    def __init__(self):

        self.white = [1, 1, 1, 1]
        self.black = [0.31, 0.31, 0.30, 1]

        self.hit = get_color_from_hex('D66255')
        self.reflection = get_color_from_hex('EFC45F')

        self.red = get_color_from_hex('D66255')
        self.yellow = get_color_from_hex('EFC45F')
        self.green = get_color_from_hex('7AF996')

        self.next_color = 0

        self.marker_colors = [
            get_color_from_hex('E896A3'),
            get_color_from_hex('9ED6FF'),
            get_color_from_hex('8EFFF3'),
            get_color_from_hex('7AF996'),
            get_color_from_hex('70AA9C'),
            ]

    def next(self):

        color = self.marker_colors[self.next_color]
        self.next_color = (self.next_color + 1) % len(self.marker_colors)
        return color


# Color scheme object
scheme = Scheme()


# Declare screens
class MenuScreen(Screen):
    pass


class InstructionScreen(Screen):

    objective_text1 = StringProperty(
        'This is the black box. You cannot see inside of it, but five atoms are hidden within.\n\n'
        'Find the atoms by beaming rays into the black box.')
    objective_text2 = StringProperty(
        'When you think you\'ve found an atom, tap on the board to mark the spot. Find all five atoms to win.')
    hit_text1 = StringProperty(
        'When you send a ray into the box, it moves in a straight line until hitting an atom, encountering an atomic '
        'field, or leaving the box. You cannot see the rays as they travel through the black box, but their fates are '
        'logged on its outside.')
    hit_text2 = StringProperty(
        'When a ray hits an atom, it is indicated with a red marker.')
    detour_text = StringProperty(
        'The fields surrounding atoms can redirect passing rays. If a ray encounters an atomic field, it will be '
        'redirected away from the atom.')
    reflection_text1 = StringProperty(
        'If a ray enters the space directly between two atoms, it will be caught between the two fields and reflected '
        'back to its point of entry.')
    reflection_text2 = StringProperty(
        'But if your ray encounters two atoms directly next to each other, or more in a row, it will hit one before it '
        'can be reflected away!')
    reflection2_text1 = StringProperty(
        'Atoms at the edge of the box can also reflect rays. If you attempt to beam a ray next to one of these atoms, '
        'it will be reflected immediately. However, these atoms can still be hit by rays entering at the right spot.')
    reflection2_text2 = StringProperty(
        'Reflections are indicated with a yellow marker.')
    miss_text1 = StringProperty(
        'If a ray doesn\'t hit an atom along its journey, it will eventually leave the box. Though rays travel in'
        ' straight lines, they their paths can be full of turns.')
    miss_text2 = StringProperty(
        'The points where a ray enters and exits the box will be marked with matching symbols.')
    scoring_text1 = StringProperty(
        'Your goal is to find all the atoms with the lowest score possible.\n'
        'Each ray you beam into the box adds one point to your score. If that ray leaves the box, another point is '
        'added to your score.')
    scoring_text2 = StringProperty(
        'At the end of the game, atoms are added to your score. Each atom you didn\'t find is worth five points!')


class GameScreen(Screen):

    def __init__(self, **kwargs):
        super(Screen, self).__init__(**kwargs)

        # Populate game board
        board = self.ids.board
        space_n = 56
        for i in range(100):

            # Blank corner spaces
            corners = [0, 9, 90, 99]
            if i in corners:
                board.add_widget(Empty())

            # Markers
            elif 0 < i <= 8:  # Top
                number = int(33 - i)
                marker = game.markers[number]
                marker.index = i    # Hack allowing access of markers through board.children
                board.add_widget(Marker(id=str(number), number=number))
            elif i % 10 == 0:  # Left
                number = int(i / 10)
                marker = game.markers[number]
                marker.index = i
                board.add_widget(Marker(id=str(number), number=number))
            elif (i + 1) % 10 == 0:  # Right
                number = int((24) - ((i + 1) / 10 - 2))
                marker = game.markers[number]
                marker.index = i
                board.add_widget(Marker(id=str(number), number=number))
            elif i > 90:  # Bottom
                number = int(i - 82)
                marker = game.markers[number]
                marker.index = i
                board.add_widget(Marker(id=str(number), number=number))

            # Add board spaces
            else:

                space = game.spacelist[space_n]

                widget = Space(
                    id=str(space_n),
                    number=str(space_n),
                    atom=space.atom,
                    guess=space.guess,
                    correct=space.correct
                )

                board.add_widget(widget)

                # Renumbering to make ids correspond with Space[x, y].number in game.py
                space_n += 1
                if space_n % 8 == 0:
                    space_n -= 16

        return

    def reset(self):
        """Reset game UI to initial state."""

        self.ids.score.text = '0'
        self.ids.end_button.text = 'Submit'
        self.ids.end_button.disabled = True
        self.ids.end_button.opacity = 0

        board = self.ids.board

        for item in board.children:
            if isinstance(item, Space) is True:
                space = game.spacelist[int(item.number)]
                item.text = ''
                item.atom = space.atom
                item.guess = False
                item.correct = False
                item.disabled = False

            elif isinstance(item, Marker) is True:
                item.text = ''
                item.disabled = False

        for i in range(1, 6):
            self.ids['tracker' + str(i)].color = scheme.white

    def update(self):
        """Every time a change is made, update score and guess tracker."""

        # Update guess tracker
        for i in range(atoms):

            ident = 'tracker' + str(i + 1)

            if i < len(game.guesslist):
                color = scheme.red
            else:
                color = scheme.white

            self.ids[ident].color = color

        # Update score
        self.ids.score.text = str(game.score)

        # Check for end game conditions! Make button visible.
        if len(game.guesslist) == atoms:
            self.ids.end_button.disabled = False
            self.ids.end_button.opacity = 1

    def symbol(self, number, color):
        """Set marker symbol."""

        # Set UI marker symbol
        number = int(number)

        # Weird hack-y thing because spaces don't have ids, even though ids were specified at creation.
        marker = game.markers[number]
        board = self.ids.board
        board.children[-marker.index - 1].text = str(marker.symbol)
        board.children[-marker.index - 1].color = color

        # Update
        self.update()

    def highlight(self, number, state):
        """Toggle highlighting of marker's link."""

        marker = game.markers[number]
        link = game.markers[marker.link]
        board = self.ids.board
        ui_link = board.children[-link.index - 1]

        # Toggle highlighting on
        if state == 'on':
            ui_link.old_color = ui_link.color
            ui_link.color = scheme.white

        # Toggle highlighting off
        elif state == 'off':
            ui_link.color = ui_link.old_color

    def end_game(self):
        """End the game! Update final score and reveal results."""

        # End the game
        if game.game_over is False:

            correct = game.endscore()
            self.update()

            # Loop through every space and reveal atoms and guess results.
            won = 0
            missed = 0
            board = self.ids.board
            for item in board.children:
                # Disable spaces to prevent them from being pressed.
                item.disabled = True
                item.disabled_color = item.color
                if isinstance(item, Space) is True:
                    number = int(item.number)
                    space = game.spacelist[number]
                    # Guessed right
                    if space.correct is True:
                        item.text = 'O'
                        item.color = item.disabled_color = scheme.green
                    # Guessed wrong
                    elif space.guess is True and space.correct is False:
                        item.text = 'X'
                        item.color = item.disabled_color = scheme.black
                        missed += 1
                    # Missed atom
                    elif space.atom is True and space.guess is False:
                        item.text = 'O'
                        item.color = item.disabled_color = scheme.red

            for i in range(correct):
                self.ids['tracker' + str(i + 1)].color = scheme.green

            # Update end button
            if missed == 0:
                won = 1
                text = 'you found them all!'
            elif missed == 1:
                text = 'you missed an atom!'
            elif missed == 5:
                text = 'you missed \'em all!'
            else:
                text = 'you missed ' + str(missed) + ' atoms!'

            self.ids.end_button.text = text

        # Prep and send to end screen
        elif game.game_over is True:
            end_screen = sm.get_screen('end_screen')
            end_screen.ids.end_score.text = str(game.score)

            sm.current = 'end_screen'


class EndScreen(Screen):

    def reset(self):
        """Resets game engine and board UI to initial state."""

        game.reset()
        sm.get_screen('game_screen').reset()


class Space(Button):

    number = NumericProperty(0)
    atom = BooleanProperty(False)
    guess = BooleanProperty(False)
    correct = BooleanProperty(False)

    def press(self, number):
        """Toggle guess at space."""

        # IMPORTANT: ids from Space widgets must be cast as integers!
        # Toggle guess in engine
        space = game.spacelist[int(number)]
        game.guess(space.x_pos, space.y_pos)

        self.guess = space.guess

        # Update text
        if self.guess is False:
            self.text = ''
        elif self.guess is True:
            self.text = 'O'
            self.color = scheme.red

        # Update
        sm.get_screen('game_screen').update()


class Marker(Button):

    number = NumericProperty(0)

    def press(self, number, state):
        """If marker unused, send ray through and set marker. If already part of a pair, highlight partner."""

        number = int(number)
        marker = game.markers[number]

        # Highlight already linked markers
        if marker.symbol is not None and marker.symbol != 'R' and marker.symbol != 'H':

            toggle = ''

            # On press
            if state == 'press':
                toggle = 'on'
            if state == 'release':
                toggle = 'off'

            # Highlight marker's link
            if marker.symbol is not None and marker.symbol != 'R' and marker.symbol != 'H':
                sm.get_screen('game_screen').highlight(marker.number, toggle)

        # On release
        elif state == 'release':

            # Marker has not been used before
            if marker.symbol is None:

                # Send ray
                game.beam(number)

                # Update marker symbol
                self.text = str(marker.symbol)

                # Update color
                if self.text == 'H':
                    self.color = scheme.hit
                elif self.text == 'R':
                    self.color = scheme.reflection
                else:
                    self.color = scheme.black
                    self.color = scheme.next()

                # Update linked marker symbol, if applicable
                if marker.link is not None:
                    sm.get_screen('game_screen').symbol(marker.link, self.color)

        # Update
        sm.get_screen('game_screen').update()


class Empty(Button):
    pass


class Tracker(Label):
    pass


class BlackboxApp(App):

    def build(self):

        # Instantiate screen manager
        self.sm = ScreenManager()
        global sm
        sm = self.sm

        # Instantiate game engine
        self.game = Board()
        global game
        game = self.game

        # Set window size
        Window.size = 360, 640

        # Declare screen manager and add screens
        sm.add_widget(MenuScreen(name='menu_screen'))
        sm.add_widget(InstructionScreen(name='instruct_screen'))
        sm.add_widget(GameScreen(name='game_screen'))
        sm.add_widget(EndScreen(name='end_screen'))

        # return screen manager as root widget
        return sm

    def on_pause(self):
        return True


# if __name__ == '__main__':
BlackboxApp().run()
