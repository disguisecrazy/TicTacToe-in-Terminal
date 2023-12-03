import os
import sys
import time
import itertools
import sqlite3 as sql
from typing import Literal

import pick
from termcolor import colored
from tabulate import tabulate


def resource_path(relative_path):
    """Function to get the absolute path to a resource (used for PyInstaller compatibility)"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


DIVIDER = "\n══════════════════════════════════════════════════════\n"

# Load Tic-Tac-Toe ASCII logo from a file
with open(resource_path("tictactoe_logo.txt"), "r", encoding="utf-8") as file:
    TTT_LOGO = file.read()

# Database path for Tic-Tac-Toe data
TTT_DB_PATH = resource_path("tictactoe.db")

# All possible winning combinations in Tic-Tac-Toe
winning_combos = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 9),  # Horizontal
    (1, 4, 7),
    (2, 5, 8),
    (3, 6, 9),  # Vertical
    (1, 5, 9),
    (3, 5, 7),  # Diagonal
)


def clear_screen():
    """Clears the terminal screen."""

    os.system("cls" if os.name == "nt" else "clear")
    print(cyanify(TTT_LOGO))


def redify(text: str):
    """Returns text in red."""
    return colored(text, "red")


def greenify(text: str):
    """Returns text in green."""
    return colored(text, "green")


def blueify(text: str):
    """Returns text in blue."""
    return colored(text, "blue")


def magentify(text: str):
    """Returns text in magenta."""
    return colored(text, "magenta")


def cyanify(text: str):
    """Returns text in cyan."""
    return colored(text, "cyan")


def yellowify(text: str):
    """Returns text in yellow."""
    return colored(text, "yellow")


def boldify(text: str):
    """Returns text in bold."""
    return colored(text, attrs=["bold"])


def underlinify(text: str):
    """Returns text in underlined."""
    return colored(text, attrs=["underline"])


def normalify(text: str):
    """Returns text in normal font."""
    return text[5:-4]


def reset_data(specific_data: Literal["Leaderboard", "History"] = None):
    """Resets the data in the database."""
    with dbopen(TTT_DB_PATH) as cursor:
        if specific_data is None:
            query = "DELETE FROM scores"
            cursor.execute(query)

            query = "DELETE FROM history"
            cursor.execute(query)

        elif specific_data == "Leaderboard":
            query = "DELETE FROM scores"
            cursor.execute(query)

        elif specific_data == "History":
            query = "DELETE FROM history"
            cursor.execute(query)

        else:
            raise ValueError("Invalid data type!")


class dbopen:
    """A context manager for sqlite3 connections."""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sql.connect(self.path)
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_class, exc, traceback):
        self.conn.commit()
        self.conn.close()


class Player:
    """Represents a player in the game."""

    def __init__(self, name: str, marker: str):
        self.name = name.title()
        self.marker = marker
        self.moves = []
        self.score = 0

    def __str__(self):
        return (
            blueify(self.name)
            if self.marker == blueify(boldify("X"))
            else redify(self.name)
        )

    def add_move(self, move: int):
        self.moves.append(move)
        self.moves.sort()

    def reset_moves(self):
        self.moves = []

    def add_score(self):
        self.score += 1

        with dbopen(TTT_DB_PATH) as cursor:
            try:
                query = "INSERT INTO scores VALUES (?, 1)"
                cursor.execute(query, (self.name,))
            except sql.IntegrityError:
                query = "UPDATE scores SET score = score + 1 WHERE name = ?"
                cursor.execute(query, (self.name,))


class Board:
    """Represents the game board."""

    def __init__(self):
        self.board = {}

    def add_move(self, move: int, player: Player):
        if move in self.board:
            return False  # The move already exists!
        else:
            self.board[move] = player.marker
            player.add_move(move)

            return True

    def is_full(self):
        return len(self.board) == 9

    def draw(self, round_num: int, winning_combo: tuple = None):
        if winning_combo and not len(winning_combo) == 3:
            raise ValueError("Winning combo must be a tuple of 3 values!")

        raw_table = []
        for i in range(1, 10):
            if i in self.board:
                raw_table.append(self.board[i])
            else:
                raw_table.append(i)

        if winning_combo:
            for index in winning_combo:
                raw_table[index - 1] = greenify(normalify(raw_table[index - 1]))

        table_data = []

        for i in range(0, len(raw_table), 3):
            table_data.append(raw_table[i : i + 3])

        print(boldify(underlinify(f"Game Round #{round_num}")), end="\n\n")

        print(
            greenify("1. Enter a number between 1-9 to mark a cell."),
            greenify("2. The first player to mark 3 cells in a row wins!"),
            greenify("3. The markers (X and O) are swapped every round."),
            "4. Use `?stop` to return to the main menu at any time.",
            sep="\n",
            end="\n\n",
        )

        print(tabulate(table_data, tablefmt="fancy_grid"), end="\n\n")

    @staticmethod
    def check_winner(player: Player):
        for combo in winning_combos:
            if all(move in player.moves for move in combo):
                return True, combo

        return False


class Game:
    """Represents a game of Tic-Tac-Toe."""

    def __init__(self, round_num: int = 1):
        self.board = Board()
        self.players = []
        self.winner = None
        self.round_num = round_num

    def draw_scoreboard(self):
        print(boldify(underlinify("Scoreboard")), end="\n\n")

        p1 = self.players[0]
        p2 = self.players[1]

        names = [blueify(f"{p1.name} (X)"), redify(f"{p2.name} (O)")]
        scores = [[str(p1.score), str(p2.score)]]

        colored_scoreboard = tabulate(scores, headers=names, tablefmt="pretty")
        print(colored_scoreboard)
        print(DIVIDER)

        names = [f"{p1.name} (X)", f"{p2.name} (O)"]
        uncolored_scoreboard = tabulate(scores, headers=names, tablefmt="pretty")

        return uncolored_scoreboard

    def save(self):
        self.round_num += 1

        timestamp = int(time.time())
        p1_name = self.players[0].name
        p2_name = self.players[1].name
        winner = self.winner.name if self.winner else None

        with dbopen(TTT_DB_PATH) as cursor:
            query = "INSERT INTO history VALUES (?, ?, ?, ?)"
            cursor.execute(query, (p1_name, p2_name, winner, timestamp))

    def start(self):
        players_iter = itertools.cycle(self.players)

        clear_screen()
        self.draw_scoreboard()
        self.board.draw(round_num=self.round_num)

        while True:
            cur_player = next(players_iter)

            while True:
                move = input(
                    magentify(f"Host: {underlinify(cur_player)}, what is your move? ")
                )

                if move.lower() == "?stop":
                    return

                if (
                    move.isdigit()
                    and 1 <= int(move) <= 9
                    and self.board.add_move(int(move), cur_player)
                ):
                    break
                else:
                    print(redify("That is not a valid move!"))

            clear_screen()
            self.draw_scoreboard()
            self.board.draw(round_num=self.round_num)

            winner = self.board.check_winner(cur_player)
            if winner:
                cur_player.add_score()

                clear_screen()
                self.draw_scoreboard()
                self.board.draw(round_num=self.round_num, winning_combo=winner[1])

                print(greenify(f"{cur_player} has won! GGs!"), end="\n\n")
                self.winner = cur_player

                self.save()

                input("Press Enter key to continue...")

                break

            if self.board.is_full():
                for player in self.players:
                    player.add_score()

                clear_screen()
                self.draw_scoreboard()
                self.board.draw(round_num=self.round_num)

                print(greenify("It's a draw! GGs!"), end="\n\n")

                self.save()

                input("Press Enter key to continue...")

                break

        scoreboard = self.draw_scoreboard()
        text = f"{TTT_LOGO}{scoreboard}\n\nUp for a rematch?"
        options = ["Bring it!", "Nop, I'm out!"]
        _, index = pick.pick(options, text, indicator=" → ", default_index=0)

        if index == 0:
            game = Game(round_num=self.round_num)

            # Resetting the moves and swapping the markers for next round!
            game.players = []
            for index, player in enumerate(self.players[::-1]):
                
                player.reset_moves()
                player.marker = (
                    blueify(boldify("X")) if index == 0 else redify(boldify("O"))
                )

                game.players.append(player)

            game.start()


def main():
    while True:
        # Displaying the main menu screen!
        about_text = (
            "Tic-Tac-Toe is a classic two-player game played on a 3x3 grid. \n"
            "The players take turns marking a vacant cell with their respective \n"
            "symbols (usually 'X' and 'O') until one player achieves a row of\n"
            "three symbols horizontally, vertically, or diagonally, or until the \n"
            "grid is filled, resulting in a draw."
        )
        welcome_text = (
            f"{TTT_LOGO}\n{about_text}\n\n"
            "...Written by Anon...\n"
            "Please use the arrow keys to navigate "
            "and Enter to select."
        )

        # Options for the main menu screen!
        options = [
            "1. Play",
            "2. Match History",
            "3. Leaderboard",
            "4. Reset Data",
            "5. Exit Game",
        ]
        _, index = pick.pick(options, welcome_text, indicator=" → ", default_index=0)

        clear_screen()

        if index == 1:
            with dbopen(TTT_DB_PATH) as cursor:
                query = "SELECT * FROM history"
                cursor.execute(query)
                history = cursor.fetchall()

                print(boldify(underlinify("Match History")), end="\n\n")

                if not history:
                    print(
                        yellowify(
                            "All the rounds you play will be logged here "
                            "in Match History! Game on!"
                        ),
                        end="\n\n",
                    )

                else:
                    headers = ["Played On", "Player 1", "Player 2", "Winner"]
                    table_data = []
                    for row in history:
                        timestamp = time.strftime(
                            "%b %d, %Y %I:%M %p", time.localtime(row[3])
                        )

                        player1 = blueify(row[0])
                        player2 = redify(row[1])

                        winner = greenify("Draw") if row[2] is None else row[2]

                        if not winner == "Draw":
                            winner = (
                                blueify(winner) if winner == row[0] else redify(winner)
                            )

                        table_data.append([timestamp, player1, player2, winner])

                    print(
                        tabulate(table_data, headers=headers, tablefmt="pretty"),
                        end="\n\n",
                    )

                input("Press Enter key to continue...")
                print(greenify("Returning to the main menu..."))

                time.sleep(0.5)

                continue

        elif index == 2:
            with dbopen(TTT_DB_PATH) as cursor:
                query = "SELECT * FROM scores ORDER BY score DESC"
                cursor.execute(query)
                leaderboard = cursor.fetchall()

            print(boldify(underlinify("Leaderboard")), end="\n\n")

            if not leaderboard:
                print(
                    yellowify(
                        "Any scores ever earned will be displayed here in "
                        "in the form of a leaderboard! It's a battle to the top!"
                    ),
                    end="\n\n",
                )

            else:
                headers = ["Player", "Wins"]
                table_data = []
                for row in leaderboard:
                    name = cyanify(row[0])
                    score = row[1]

                    table_data.append([name, score])

                print(
                    tabulate(table_data, headers=headers, tablefmt="pretty"), end="\n\n"
                )

            input("Press Enter key to continue...")
            print(greenify("Returning to the main menu..."))

            time.sleep(0.5)

            continue
        
        elif index == 3:
            with dbopen(TTT_DB_PATH) as cursor:
                query = "SELECT COUNT(*) FROM scores"
                cursor.execute(query)
                scores_length = cursor.fetchone()[0]

                query = "SELECT COUNT(*) FROM history"
                cursor.execute(query)
                history_length = cursor.fetchone()[0]

                reset_text = (
                    f"{TTT_LOGO}Data Reset\n-----------\n\n"
                    "WARNING: This action is irreversible!\n\n"
                    f"1. Leaderboard has {scores_length} entries.\n"
                    f"2. Match History has {history_length} entries.\n\n"
                    "What would you like to reset?"
                )

                options = ["1. All", "2. History", "3. Leaderboard", "4. Cancel"]
                option, index = pick.pick(
                    options, reset_text, indicator=" → ", default_index=3
                )

                if index == 3:
                    print(greenify("Returning to the main menu..."))

                    time.sleep(0.5)

                    continue

                elif index == 0:
                    reset_data()

                elif index == 1:
                    reset_data("History")

                elif index == 2:
                    reset_data("Leaderboard")

                print(greenify(f"Data reset successful for {option[3:]}!"), end="\n\n")
                input("Press Enter key to continue...")
                print(greenify("Returning to the main menu..."))

                time.sleep(0.5)

                continue

        elif index == 4:
            exit()

        print(
            greenify(f"Starting TicTacToe..."),
            "use `?stop` to return to the main menu at any time!",
            end="\n\n",
        )

        print(
            "(Tip: It is recommended to use the same names every "
            "time to keep the leaderboard consistent)",
            end="\n\n",
        )

        name1 = str(
            input(magentify("Host: What'd you like to be called, Player 1?\nYou: "))
        )
        if name1.lower() == "?stop":
            print(greenify("\n\nReturning to the main menu..."))
            time.sleep(0.5)
            continue

        name2 = str(
            input(magentify("\n\nHost: Gotcha! What about you, Player 2?\nYou: "))
        )
        if name2.lower() == "?stop":
            print(greenify("\n\nReturning to the main menu..."))
            time.sleep(0.5)
            continue

        name1 = name1 if name1 else "Player 1"
        name2 = name2 if name2 else "Player 2"

        player1 = Player(name1, blueify(boldify("X")))
        player2 = Player(name2, redify(boldify("O")))

        game = Game()
        game.players = [player1, player2]
        game.start()

        print(greenify("Returning to the main menu..."))

        time.sleep(0.5)

        continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print(redify("Exiting TicTacToe..."))
        exit()
