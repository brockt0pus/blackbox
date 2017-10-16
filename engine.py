from config import dimension, atoms
from random import randint


class Marker:
    """
    Numbered markers around the board edge. May contain beam results or links to other markers.
    """

    def __init__(self, number, index=False):
        """Initializes game board edges."""

        self.number = number
        self.link = None
        self.symbol = None
        self.text = self.symbol
        self.index = None

        if index is not False:
            self.index = index


class Space:
    """
    Numbered game board spaces in which an atom, field, or guess may exist.
    """

    def __init__(self, number, atom, field, x_pos, y_pos):
        """Initializes game spaces."""

        self.number = number
        self.atom = atom
        self.field = field
        self.guess = False
        self.correct = False
        self.x_pos = x_pos
        self.y_pos = y_pos

class Ray:
    """
    Rays travel in straight paths and are redirected by fields until they strike an atom or leave the board.
    """

    def __init__(self, origin):
        """Set ray direction and starting position based on its marker of origin."""

        self.origin = origin

        # Determine ray direction and starting position
        # East: 1 - 8
        if self.origin <= dimension:
            self.direction = 'e'
            self.x = 0
            self.y = dimension - self.origin
        # North: 9 - 16
        elif dimension < self.origin <= 2 * dimension:
            self.direction = 'n'
            self.x = self.origin - dimension - 1
            self.y = 0
        # West: 17 - 24
        elif 2 * dimension < self.origin <= 3 * dimension:
            self.direction = 'w'
            self.x = dimension - 1
            self.y = self.origin - (2 * dimension) - 1
        # South: 24 - 32
        elif 3 * dimension < self.origin <= 4 * dimension:
            self.direction = 's'
            self.x = (4 * dimension) - self.origin
            self.y = dimension - 1

    def turn(self, field):
        """Turn ray away from atom upon encountering its field."""

        if field == 1:
            if self.direction == 'w':
                self.direction = 'n'
            elif self.direction == 's':
                self.direction = 'e'
        if field == 2:
            if self.direction == 'e':
                self.direction = 'n'
            elif self.direction == 's':
                self.direction = 'w'
        if field == 3:
            if self.direction == 'e':
                self.direction = 's'
            elif self.direction == 'n':
                self.direction = 'w'
        if field == 4:
            if self.direction == 'n':
                self.direction = 'e'
            elif self.direction == 'w':
                self.direction = 's'

    def advance(self):
        """Advance ray in a straight path."""

        if self.direction == 'e':
            self.x += 1
        elif self.direction == 'n':
            self.y += 1
        elif self.direction == 'w':
            self.x -= 1
        elif self.direction == 's':
            self.y -= 1

    def edge(self):
        """Check if ray leaves the game board and return the marker of its exit."""

        end = 'null'

        if self.x < 0:
            end = dimension - self.y
        elif self.x > 7:
            end = self.y + 1 + (dimension * 2)
        elif self.y < 0:
            end = self.x + 1 + dimension
        elif self.y > 7:
            end = (dimension * 4) - self.x
        else:
            end = 'null'
        return end


class Board:
    """
    Game board composed of a grid of spaces.
    """

    def __init__(self):
        """
        Game board is created. Atoms randomly assigned positions. Fields determined. Score initialized.

        atomlist    List of the coordinates of atoms.
        guesslist   List of the coordinates of guesses.
        symbols  List of the letters used as board markers, beginning with 'A.'
        markers     Dict of used markers. markers[number: 'hit'/'reflection'/letter]
        score       Game score.
        spaces      Dict of spaces (see: class Spaces) composing the game board. spaces[(x, y)]
        spacelist   Dict of spaces organized by number, used for access by main.py
        """

        # Create lists and dicts
        self.atomlist = []
        self.guesslist = []
        self.markers = {}
        self.symbols = [ord('@')]
        self.score = 0
        self.spaces = {}
        self.spacelist = {}
        self.game_over = False

        # Create board
        self.reset(True)

    def reset(self, init=False):
        """
        Game board is reset. Marker indexes are the only thing preserved.
        """

        # Reset lists and dicts
        self.atomlist = []
        self.guesslist = []
        self.symbols = [ord('@')]
        self.score = 0
        self.spaces = {}
        self.spacelist = {}
        self.game_over = False

        # Assign atom coordinates randomly, and forbid overlapping
        i = 0
        while i < atoms:
            while True:
                x = randint(1, dimension - 1)
                y = randint(1, dimension - 1)
                if (x, y) not in self.atomlist:
                    break
            self.atomlist.append((x, y))
            i += 1

        # Populate board spaces
        i, x, y = 0, 0, 0
        while i < (dimension * dimension):
            while x < dimension:
                # Check for atom
                if (x, y) in self.atomlist:
                    self.spaces[(x, y)] = Space(i, True, 0, x, y)
                    self.spacelist[i] = self.spaces[(x, y)]
                    x += 1
                    i += 1
                # Empty space
                else:
                    self.spaces[(x, y)] = Space(i, False, 0, x, y)
                    self.spacelist[i] = self.spaces[(x, y)]
                    x += 1
                    i += 1
            y += 1
            x %= dimension

        # Set fields for each atom
        # Corner (X) fields
        for atom in self.atomlist:
            x, y = atom
            self.field(x + 1, y + 1, 1)
            self.field(x - 1, y + 1, 2)
            self.field(x - 1, y - 1, 3)
            self.field(x + 1, y - 1, 4)

        # Cross fields overwrite
        for atom in self.atomlist:
            x, y = atom
            self.field(x + 1, y, 6)
            self.field(x - 1, y, 6)
            self.field(x, y + 1, 6)
            self.field(x, y - 1, 6)

        # Populate dict of markers, keys are numbered
        for i in range(dimension * 4):
            if init is True:
                self.markers[i + 1] = Marker(i + 1)

            # Preserve marker index on reset
            else:
                for i in range(dimension * 4):
                    index = self.markers[i + 1].index
                    self.markers[i + 1] = Marker(i + 1, index)

    def field(self, x, y, quad):
        """
        Apply field of given quadrant to given space. Check for fields overlap.

        'quad' indicates the location of the field relative to the atom:
        1 - 4 are corner fields (corresponding to graph quadrants), causing detours
        5 indicates a mirror, caused by overlapping corner fields
        6 is a cross field, which cancels corner fields

        Returns 1 if given coordinates are not located on game board.
        """

        # Do nothing if coordinates are off the board
        if x > 7 or y > 7 or x < 0 or y < 0:
            return 1

        # Create mirror if there is already a corner field present
        elif 0 < self.spaces[(x, y)].field < 5 and quad != 6:
            self.spaces[(x, y)].field = 5

        # Cross fields overwrite corners
        elif quad == 6:
            self.spaces[(x, y)].field = 6

        # Write corner fields to space
        else:
            self.spaces[(x, y)].field = quad

    def setmarker(self, origin, result, end=0):
        """
        Sets the result of the given marker to indicate a hit, reflection, or detour.

        'origin' is the number of the ray's origin.
        'result' indicates whether the ray experienced a 'hit' or 'reflection.'
        'end' is the number at which the ray exited, if it left the board.

        If the ray left the board, the numbers of origin and exit are given markers of matching letters.
        """

        # TODO: check if symbols is capable of outputting enough letters

        # If marker left the board
        if end != 0:
            # Get a letter (not 'R' or 'H' which indicate other results)
            while True:
                letter = chr(self.symbols.pop() + 1)
                self.symbols.append(ord(letter))
                if letter is 'R' or letter is 'H':
                    continue
                break

            # Assign letter to pair of markers
            self.symbols.append(ord(letter))
            self.markers[origin].symbol = letter
            self.markers[end].symbol = letter

            # Link markers together
            self.markers[origin].link = end
            self.markers[end].link = origin

        else:
            self.markers[origin].symbol = result

    def onboard(self, x=0, y=0):
        """
        Returns True if given coordinates are on the game board, else returns False.
        x and y are given default values so that coordinates do not need to be checked in pairs.
        """

        if x >= dimension or x < 0:
            return False
        if y >= dimension or y < 0:
            return False
        else:
            return True

    def check(self, x, y):
        """Checks game board for atoms or fields at given coordinates. Returns field's value or 9 for an atom."""

        # Check that coordinates are on game board
        if self.onboard(x, y) is False:
            return 0
        # Check for atom
        elif self.spaces[(x, y)].atom is True:
            return 9
        # Check for field
        elif self.spaces[(x, y)].field != 'null':
            return self.spaces[(x, y)].field
        else:
            return 0

    def reflection(self, ray):
        """Returns True if there are atoms adjacent to the given ray's point of entry."""

        # Alias variables
        direction = ray.direction
        x = ray.x
        y = ray.y

        # Entering from the sides
        if direction == 'e' or direction == 'w':
            if self.check(x, y + 1) == 9 or self.check(x, y - 1) == 9:
                return True
            else:
                return False
        # Entering from the top or bottom
        elif direction == 'n' or direction == 's':
            if self.check(x + 1, y) == 9 or self.check(x - 1, y) == 9:
                return True
            else:
                return False

    def beam(self, number):
        """
        Send ray through board at given marker number. Returns fate of ray and adjusts score accordingly.

        Possible return values are 'reflection', 'hit', or number of exit.
        Score increases by for every marker assigned:
        +1 for every hit or reflection and +2 if the ray leaves the board.
        """

        # Create ray
        ray = Ray(number)
        result = 'null'
        end = 0

        # Check for edgecase reflection immediately
        if self.reflection(ray) is True:
            result = 'R'
            self.setmarker(number, result, end)
            return result

        # Check spaces in a straight path until interruption
        while True:
            check = self.check(ray.x, ray.y)

            # Ray encounters atom
            if check == 9:
                result = 'H'
                break

            # Ray reflects
            if check == 5:
                result = 'R'
                break

            # Ray encounters field
            if 0 < check < 5:
                ray.turn(check)

            # Advance ray forward
            # Must be done before edge check
            ray.advance()

            # Check if ray has hit edge of board
            if ray.edge() != 'null':
                end = ray.edge()
                break

        # Return result, add to score, and change markers
        self.setmarker(number, result, end)

        # Hit or reflection means end is not set
        if end != 0:
            self.score += 2
            return end
        else:
            self.score += 1
            return result

    def guess(self, x, y):
        """
        Toggles player's guess on board at given coordinates.

        Returns 1 if coordinates are off board or already used.
        Returns 2 if all guesses have already been used.
        """

        # Toggle guess if present
        if (x, y) in self.guesslist:
            self.guesslist.remove((x, y))
            self.spaces[(x, y)].guess = False
            return 0

        # Limit number of guesses to number of atoms
        if len(self.guesslist) == len(self.atomlist):
            return 2

        # Confirm that given coordinates are on game board
        if self.onboard(x, y) is False:
            return 1

        # Log guess on board and append to list
        else:
            self.guesslist.append((x, y))
            self.spaces[(x, y)].guess = True
            return 0

    def endscore(self):
        """
        Check player guesses and score game. Incorrect guesses add 5 to score. Return number of atoms correct.
        """

        correct = 0

        # Check guesslist against atomlist
        for guess in self.guesslist:

            # Guess is wrong, add to score
            if guess not in self.atomlist:
                self.spaces[guess].correct = False
                self.score += 5

            # Mark guess as correct
            else:
                self.spaces[guess].correct = True
                correct += 1

        self.game_over = True
        return correct
