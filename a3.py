import tkinter as tk
import os
import math
from tkinter import messagebox

from model import TowerGame
from tower import SimpleTower, MissileTower, EnergyTower, AbstractTower
from enemy import SimpleEnemy, KillByEnergy, AbstractEnemy
from tower_view import TowerView
from high_score_manager import HighScoreManager
from utilities import Stepper
from view import GameView
from level import AbstractLevel

BACKGROUND_COLOUR = "#4a2f48"

__author__ = "Victor Ngo - 44592200"
__copyright__ = ""

#store images file
coinsImg = os.path.join("images", "coins.gif")
livesImg = os.path.join("images","heart.gif")

# Could be moved to a separate file, perhaps levels/simple.py, and imported
class MyLevel(AbstractLevel):
    """A simple game level containing examples of how to generate a wave"""
    waves = 6

    def get_wave(self, wave):
        """Returns enemies in the 'wave_n'th wave

        Parameters:
            wave_n (int): The nth wave

        Return:
            list[tuple[int, AbstractEnemy]]: A list of (step, enemy) pairs in the
                                             wave, sorted by step in ascending order
        """
        enemies = []

        if wave == 1:
            # A hardcoded singleton list of (step, enemy) pairs

            enemies = [(10, KillByEnergy())]
        elif wave == 2:
            # A hardcoded list of multiple (step, enemy) pairs

            enemies = [(10, SimpleEnemy()), (15, SimpleEnemy()), (30, SimpleEnemy())]
        elif 3 <= wave < 10:
            # List of (step, enemy) pairs spread across an interval of time (steps)

            steps = int(40 * (wave ** .5))  # The number of steps to spread the enemies across
            count = wave * 2  # The number of enemies to spread across the (time) steps

            for step in self.generate_intervals(steps, count):
                enemies.append((step, SimpleEnemy()))

        elif wave == 10:
            # Generate sub waves
            sub_waves = [
                # (steps, number of enemies, enemy constructor, args, kwargs)
                (50, 10, SimpleEnemy, (), {}),  # 10 enemies over 50 steps
                (100, None, None, None, None),  # then nothing for 100 steps
                (50, 10, SimpleEnemy, (), {})  # then another 10 enemies over 50 steps
            ]

            enemies = self.generate_sub_waves(sub_waves)

        else:  # 11 <= wave <= 20
            # Now it's going to get hectic

            sub_waves = [
                (
                    int(13 * wave),  # total steps
                    int(25 * wave ** (wave / 50)),  # number of enemies
                    SimpleEnemy,  # enemy constructor
                    (),  # positional arguments to provide to enemy constructor
                    {},  # keyword arguments to provide to enemy constructor
                ),
                # ...
            ]
            enemies = self.generate_sub_waves(sub_waves)

        return enemies

class TowerGameApp(Stepper):
    """Top-level GUI application for a simple tower defence game"""

    # All private attributes for ease of reading
    _current_tower = None
    _paused = False
    _won = None

    _level = None
    _wave = None
    _score = None
    _coins = None
    _lives = None

    _master = None
    _game = None
    _view = None

    def __init__(self, master: tk.Tk, delay: int = 20):
        """Construct a tower defence game in a root window

        Parameters:
            master (tk.Tk): Window to place the game into
        """

        self._master = master
        super().__init__(master, delay=delay)

        self._game = game = TowerGame()

        self.setup_menu()

        # create a game view and draw grid borders
        self._view = view = GameView(master, size=game.grid.cells,
                                     cell_size=game.grid.cell_size,
                                     bg='antique white')
        view.pack(side=tk.LEFT, expand=True)

        # Task 1.3 (Status Bar): instantiate status bar
        # ...
        self._player = tk.Frame(master, bg='pink')
        self._player.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self._status = StatusBar(self._player)

        # Task 1.5 (Play Controls): instantiate widgets here
        # ...
        self._controlsArea = tk.Frame(self._player)
        self._controlsArea.pack(side=tk.BOTTOM)

        self._nextWave = tk.Button(self._controlsArea, text='Next wave', command=self.next_wave)
        self._nextWave.pack(side=tk.LEFT)

        self._pause = tk.Button(self._controlsArea, text='Play', command=self._toggle_paused)
        self._pause.pack(side=tk.LEFT)

        self._highscorefile = HighScoreManager()

        # bind game events
        game.on("enemy_death", self._handle_death)
        game.on("enemy_escape", self._handle_escape)
        game.on("cleared", self._handle_wave_clear)

        # Task 1.2 (Tower Placement): bind mouse events to canvas here
        # ...
        self._view.bind("<Motion>", self._move)
        self._view.bind("<Button-1>", self._left_click)
        self._view.bind("<Leave>", self._mouse_leave)
        self._view.bind("<Button-3>",self._right_click)

        # Level
        self._level = MyLevel()

        self.select_tower(SimpleTower)

        view.draw_borders(game.grid.get_border_coordinates())

        # Get ready for the game
        self._setup_game()

        # Remove the relevant lines while attempting the corresponding section
        # Hint: Comment them out to keep for reference

        # Task 1.2 (Tower Placement): remove these lines
        towers = [
            ([(2, 2), (3, 0), (4, 1), (4, 2), (4, 3)], MissileTower),
            ([(2, 5)], EnergyTower)
        ]

        for positions, tower in towers:
            for position in positions:
                game.place(position, tower_type=tower)

        # Task 1.5 (Tower Placement): remove these lines
        #game.queue_wave([], clear=True)
        #self.next_wave()

        # Task 1.5 (Play Controls): remove this line
        #self.start()
        #shop
        towers = [
        SimpleTower,
        MissileTower,
        EnergyTower
        ]

        # Create views for each tower & store to update if availability changes
        self._tower_views = []
        for tower_class in towers:
            tower = tower_class(self._game.grid.cell_size // 2)

            # bg=BACKGROUND_COLOUR, highlight="#4b3b4a",
            shopView = ShopTowerView(self._player, tower, click_command=lambda class_=tower_class: self.select_tower(class_))
            shopView.pack(side=tk.TOP)

            # Can use to check if tower is affordable when refreshing view
            self._tower_views.append((tower, shopView))

        self.refresh_view()

    def setup_menu(self):
        """Sets up the application menu"""
        # Task 1.4: construct file menu here
        # ...
        gameMenu = tk.Menu(self._master)
        fileMenu = tk.Menu(gameMenu, tearoff=0)
        fileMenu.add_cascade(label='New game', command=self._new_game)
        fileMenu.add_cascade(label='High score', command=self._highscore)
        fileMenu.add_cascade(label='Exit', command=self._exit)
        gameMenu.add_cascade(label='File', menu=fileMenu)
        self._master.config(menu=gameMenu)

    def _toggle_paused(self, paused=None):
        """Toggles or sets the paused state

        Parameters:
            paused (bool): Toggles/pauses/unpauses if None/True/False, respectively
        """
        if paused is None:
            paused = not self._paused

        # Task 1.5 (Play Controls): Reconfigure the pause button here
        # ...
        if paused:
            self._pause.config(text="Play")
            self.pause()
        else:
            self._pause.config(text="Pause")
            self.start()

        self._paused = paused

    def _setup_game(self):
        """Sets up the game"""
        self._wave = 0
        self._score = 0
        self._coins = 100
        self._lives = 20

        self._won = False

        # Task 1.3 (Status Bar): Update status here
        # ...
        self._status.set_wave(self._wave, self._level.get_max_wave())
        self._status.set_score(self._score)
        self._status.set_goldCoin(self._coins)
        self._status.set_lives(self._lives)

        # Task 1.5 (Play Controls): Re-enable the play controls here (if they were ever disabled)
        # ...
        self._nextWave.config(fg='black', state=tk.ACTIVE)
        self._pause.config(fg='black', state=tk.ACTIVE)
        self._game.reset()

        # Auto-start the first wave
        self.next_wave()
        self._toggle_paused(paused=True)

    def create_new_game(self):
        """create a new game when players finish their current game, lost or choose to restart"""
        self._wave = 0
        self._game.queue_wave([], clear=True)
        self._game.reset()
        self._setup_game()
        self.refresh_view()
        self._toggle_paused(paused=True)

    # Task 1.4 (File Menu): Complete menu item handlers here (including docstrings!)
    #
    def _new_game(self):
        """new game"""
        if messagebox.askyesno("New game", "Begin new game?"):
            self.create_new_game()

    def _exit(self):
        """exit"""
        if messagebox.askyesno("Exit", "Exit the game?"):
            self._master.quit()

    def _highscore(self):
        """highscore"""
        self._highscorewindow = HighScore()

    #
    def refresh_view(self):
        """Refreshes the game view"""
        if self._step_number % 2 == 0:
            self._view.draw_enemies(self._game.enemies)
        self._view.draw_towers(self._game.towers)
        self._view.draw_obstacles(self._game.obstacles)

        for towers in self._tower_views:
            if towers[0].get_value() > self._coins:
                towers[1].set_available(False)
            else:
                towers[1].set_available(True)

    def _step(self):
        """
        Perform a step every interval

        Triggers a game step and updates the view

        Returns:
            (bool) True if the game is still running
        """
        self._game.step()
        self.refresh_view()

        return not self._won

    # Task 1.2 (Tower Placement): Complete event handlers here (including docstrings!)
    # Event handlers: _move, _mouse_leave, _left_click

    def _move(self, event):
        """
        Handles the mouse moving over the game view canvas

        Parameter:
            event (tk.Event): Tkinter mouse event
        """
        # move the shadow tower to mouse position
        position = event.x, event.y
        self._current_tower.position = position

        legal, grid_path = self._game.attempt_placement(position)

        if self._current_tower.get_value() > self._coins:
            legal = False

        # find the best path and covert positions to pixel positions
        path = [self._game.grid.cell_to_pixel_centre(position)
                for position in grid_path.get_shortest()]

        # Task 1.2 (Tower placement): Draw the tower preview here
        # ...
        self._view.draw_preview(self._current_tower, legal)
        self._view.draw_path(path)
        self.refresh_view()

    def _mouse_leave(self, event):
        """remove preview and enemy path when the cursor leaves the game window"""
        # Task 1.2 (Tower placement): Delete the preview
        # Hint: Relevant canvas items are tagged with: 'path', 'range', 'shadow'
        #       See tk.Canvas.delete (delete all with tag)
        self._view.delete('path','shadow','range')

    def _left_click(self, event):
        #Build the selected tower at the cursor's position
        # retrieve position to place tower
        if self._current_tower is None:
            return

        legal = True
        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)

        if self._current_tower.get_value() > self._coins:
            legal = False

        if legal:
            # Task 1.2 (Tower Placement): Attempt to place the tower being previewed
            if self._game.place(cell_position, tower_type=self._current_tower.__class__):
                self._coins -= self._current_tower.get_value()
                self._status.set_goldCoin(self._coins)
            else:
                legal = False

        self._view.draw_preview(self._current_tower, legal)
        self.refresh_view()

    def _right_click(self, event):
        """sell tower"""
        if self._current_tower is None:
            return

        position = event.x, event.y
        cell_position = self._game.grid.pixel_to_cell(position)

        sold_tower = self._game.remove(cell_position)
        self._coins += int(sold_tower.get_value()*0.8)
        self._status.set_goldCoin(self._coins)
        self.refresh_view()

    def next_wave(self):
        """Sends the next wave of enemies against the player"""
        if self._wave == self._level.get_max_wave():
            return

        self._wave += 1

        # Task 1.3 (Status Bar): Update the current wave display here
        # ...
        self._status.set_wave(self._wave, self._level.get_max_wave())

        # Task 1.5 (Play Controls): Disable the add wave button here (if this is the last wave)
        # ...
        if self._wave == self._level.get_max_wave():
            self._nextWave.config(state=tk.DISABLED, fg='gray')

        # Generate wave and enqueue
        wave = self._level.get_wave(self._wave)
        for step, enemy in wave:
            enemy.set_cell_size(self._game.grid.cell_size)

        self._game.queue_wave(wave)

    def select_tower(self, tower):
        """
        Set 'tower' as the current tower

        Parameters:
            tower (AbstractTower): The new tower type
        """
        self._current_tower = tower(self._game.grid.cell_size)

    def _handle_death(self, enemies):
        """
        Handles enemies dying

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which died in a step
        """
        bonus = len(enemies) ** .5
        for enemy in enemies:
            self._coins += enemy.points
            self._score += int(enemy.points * bonus)

        # Task 1.3 (Status Bar): Update coins & score displays here
        # ...
        self._status.set_score(self._score)
        self._status.set_goldCoin(self._coins)

    def _handle_escape(self, enemies):
        """
        Handles enemies escaping (not being killed before moving through the grid

        Parameters:
            enemies (list<AbstractEnemy>): The enemies which escaped in a step
        """
        self._lives -= len(enemies)
        if self._lives < 0:
            self._lives = 0

        for enemy in enemies:
            enemy.health = 0
        # Task 1.3 (Status Bar): Update lives display here
        # ...
        self._status.set_lives(self._lives)

        # Handle game over
        if self._lives == 0:
            self._handle_game_over(won=False)

    def _handle_wave_clear(self):
        """Handles an entire wave being cleared (all enemies killed)"""
        if self._wave == self._level.get_max_wave():
            self._handle_game_over(won=True)

        # Task 1.5 (Play Controls): remove this line
        #self.next_wave()

    def _handle_game_over(self, won=False):
        """Handles game over

        Parameter:
            won (bool): If True, signals the game was won (otherwise lost)
        """
        self._won = won
        self.stop()
        self._nextWave.config(fg='gray', state=tk.DISABLED)
        self._pause.config(fg='gray', state=tk.DISABLED)
        # Task 1.4 (Dialogs): show game over dialog here
        # ...
        if self._won == True:
            if messagebox.askyesno("You win", "Congratulations, you win. Do you want to start again?"):
                self.create_new_game()
            else:
                self._master.quit()
        else:
            if messagebox.askyesno("You lose", "Too bad. Do you want to start again?"):
                self.create_new_game()
            else:
                self._master.quit()

class StatusBar(tk.Frame):
    """create status bar"""
    def __init__(self, masterFrame, *arg, **kwargs):
        super().__init__(*arg, **kwargs)
        self._wave= tk.Label(masterFrame, bg='white', text='')
        self._wave.pack(side=tk.TOP, fill=tk.X)

        self._score = tk.Label(masterFrame, bg='white', text='')
        self._score.pack(side=tk.TOP, fill=tk.X)

        self._coinLives = tk.Frame(masterFrame)
        self._coinLives.pack(side=tk.TOP, fill=tk.X)

        self._coinsImg = tk.PhotoImage(file=coinsImg)
        self._goldCoin = tk.Label(self._coinLives, bg='white',
        text='', image=self._coinsImg, compound=tk.LEFT)
        self._goldCoin.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self._lives = tk.PhotoImage(file=livesImg)
        self._livesRemaining = tk.Label(self._coinLives, bg='white',
        text='', image=self._lives,compound=tk.LEFT)
        self._livesRemaining.pack(side=tk.RIGHT, expand=True, fill=tk.X)

    def set_wave(self, wave, max_wave):
        """update wave"""
        self._wave.config(text="Wave: " + str(wave) + "/" + str(max_wave))

    def set_score(self, score):
        """update score"""
        self._score.config(text="Score: " + str(score))

    def set_goldCoin(self, coins):
        """update coins"""
        self._goldCoin.config(text="Coins: "+ str(coins))

    def set_lives(self, life):
        """update lives"""
        self._livesRemaining.config(text="Lives: "+ str(life))

#ShopClass
class ShopTowerView(tk.Frame):
    """create tower shop"""
    def __init__(self, masterFrame, tower, click_command, *arg, **kwargs):
        super().__init__(*arg, **kwargs)

        self._shopDisplay = tk.Frame(masterFrame, bg='pink')
        self._shopDisplay.pack(fill=tk.X)

        self._towerIcon = tk.Canvas(self._shopDisplay, height=tower.cell_size, width=tower.cell_size, bg='pink', highlightbackground='pink', highlightthickness=0)
        self._towerIcon.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self._towerName = tk.Label(self._shopDisplay, text="{0}\nCoins: {1}".format(tower.name, tower.get_value()), bg='pink')
        self._towerName.pack(side=tk.LEFT, expand=True, fill=tk.X)

        tower.position = (tower.cell_size // 2, tower.cell_size // 2)  # Position in centre
        tower.rotation = 3 * math.pi / 2  # Point up
        TowerView.draw(self._towerIcon, tower, tower.cell_size)

        self._towerIcon.bind("<Button-1>", lambda event: click_command())
        self._towerName.bind("<Button-1>", lambda event: click_command())

        self._towerIcon.bind("<Enter>", self.mouse_enter)
        self._towerName.bind("<Enter>", self.mouse_enter)

        self._towerIcon.bind("<Leave>", self.mouse_leave)
        self._towerName.bind("<Leave>", self.mouse_leave)

    def mouse_enter(self, event):
        """set background color when mouse enter shop widget"""
        self._towerIcon.config(bg="#ff47ff", highlightbackground="#ff47ff")
        self._towerName.config(bg="#ff47ff")
        self._shopDisplay.config(bg="#ff47ff")

    def mouse_leave(self, event):
        """set color when mouse leave shop widget"""
        self._towerIcon.config(bg="pink", highlightbackground="pink")
        self._towerName.config(bg="pink")
        self._shopDisplay.config(bg="pink")

    def set_available(self, available=True):
        """set availability of a tower"""
        if available:
            self._towerName.config(fg="black")
        else:
            self._towerName.config(fg="red")

#highscore windows
class HighScore(tk.Frame):
    """High score windows"""
    def __init__(self, *arg, **kwargs):
        self._master = tk.Toplevel()
        self._master.title("Highscore")

        self._toplabel = tk.Frame(self._master)
        self._toplabel.pack(side=tk.TOP, fill=tk.X)

        self._topname = tk.Label(self._toplabel, text="Name")
        self._topname.pack(side=tk.LEFT, fill=tk.X, expand=1)

        self._topscore = tk.Label(self._toplabel, text="Score")
        self._topscore.pack(side=tk.LEFT, fill=tk.X, expand=1)

        self._topdata = tk.Label(self._toplabel, text="Note")
        self._topdata.pack(side=tk.LEFT, fill=tk.X, expand=1)

        self._labellist = []

    def load_data(self, data):
        """create high score entry

            Parameters:
                iterable : an iterable object of entries
                tuples in the format ('name','score','data')

            Returns:
                list: list of label
        """
        for entry in data:
            mainlabel = tk.Frame(self._master)
            mainlabel.pack(side=tk.TOP)
            namelabel = tk.Label(mainlabel, text="{0}".format(entry[0]))
            namelabe.pack(side=tk.LEFT)
            scorelabel = tk.Label(mainlabel, text="{0}".format(entry[1]))
            scorelabel.pack(side=tk.LEFT)
            datalabel = tk.Label(mainlabel, text="{0}".format(entry[2]))
            datalabel.pack(side=tk.LEFT)

            self._labellist.append((namelabel, scorelabel, datalabel))

# Task 1.1 (App Class): Instantiate the GUI here
# ...
def main():
    """Main GUI"""
    rootWindow = tk.Tk()
    rootWindow.title("Tower defense")
    TowerGameApp(rootWindow)
    rootWindow.mainloop()

if __name__ == "__main__" :
    main()
