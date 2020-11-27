import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count
        self.safe_cells = set()
        self.mines_cells = set()

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        return self.mines_cells

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        return self.safe_cells

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell not in self.cells:
            return
        self.cells.remove(cell)
        self.mines_cells.add(cell)
        self.count -= 1
        self.conclude()

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell not in self.cells:
            return
        self.cells.remove(cell)
        self.safe_cells.add(cell)
        self.conclude()

    def conclude(self):
        """
        Try to update the internal knowledge representation
        given the fact a sentence with count 0 must update all the safe cells
        given the fact a sentence with count == reaming_cells_count must all be mines
        """
        if self.count == 0:
            self.safe_cells.update(self.cells)
            self.cells.clear()

        if self.count == len(self.cells):
            self.mines_cells.update(self.cells)
            self.cells.clear()


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []
        self.parent = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def get_sentence(self, cell, score):
        """
        give a cell (i,j) and initial score of cell
        return a new sentence based on knowledge base and it's new score
        """
        neighbors = set()

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue
                if 0 <= i < self.height and 0 <= j < self.width:
                    if (i, j) in self.mines:
                        score -= 1

                    if (i, j) not in self.mines and (i, j) not in self.safes:
                        neighbors.add((i, j))
        return Sentence(neighbors, score)

    def inferences(self, sentence_a, sentence_b):
        """
        infer a new sentence if possible to infer from sentence a and b
        any time we have two sentences set1 = count1 and set2 = count2
        where set1 is a subset of set2,
        then we can construct the new sentence set2 - set1 = count2 - count1
        return None if no inferences is possible
        """
        # if one sentence is empty we will return noun because we don't want to duplicate the other sentence
        if len(sentence_a.cells) == 0:
            return None
        if sentence_a.cells.issubset(sentence_b.cells):
            new_sentence = Sentence(
                sentence_b.cells.difference(sentence_a.cells),
                sentence_b.count - sentence_a.count
            )
            if len(new_sentence.cells) != 0:
                return new_sentence
        return None

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
               based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
               if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
               if they can be inferred from existing knowledge
        """
        self.moves_made.add(cell)
        self.mark_safe(cell)
        self.knowledge.append(self.get_sentence(cell, count))
        # parent sentence of the new sentence is itself
        self.parent.append(len(self.knowledge) - 1)

        for sentence in self.knowledge:
            sentence.conclude()
            self.safes.update(sentence.known_safes())
            self.mines.update(sentence.known_mines())

        for i in range(len(self.knowledge)):
            for j in range(len(self.knowledge)):
                # same element or sentence i was driven from sentence j
                if i == j or self.parent[i] == j:
                    continue
                sent = self.inferences(self.knowledge[i], self.knowledge[j])
                if sent is not None and len(sent.cells) != 0:
                    self.knowledge.append(sent)
                    self.parent.append(j)

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        for move in self.safes:
            if move not in self.moves_made:
                return move
        return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        possible_places = []
        for i in range(self.height):
            for j in range(self.width):
                if (i, j) not in self.moves_made and (i, j) not in self.mines:
                    possible_places.append((i, j))
        if len(possible_places) == 0:
            return None
        return random.sample(possible_places, 1)[0]
