from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.core.image import Image as CoreImage
from kivy.animation import Animation
from Food_Crusher_Android import Grid, Candy, LogicEngine

# Phone-like screen dimensions (16:9 aspect ratio)
PHONE_WIDTH, PHONE_HEIGHT = 720, 1280
ROWS, COLS = 8, 8  # Keeping an 8x8 grid
GRID_SIZE = min(PHONE_WIDTH, PHONE_HEIGHT * 0.75)  # Grid size to fit in 75% of the height
CANDY_SIZE = GRID_SIZE // COLS  # Candy size adjusted to fit the grid

# Store image file paths
CANDY_IMAGES_PATHS = {
    'red': 'candies/red_candy.png',
    'green': 'candies/green_candy.png',
    'blue': 'candies/blue_candy.png',
    'yellow': 'candies/yellow_candy.png',
    'orange': 'candies/orange_candy.png',
    'purple': 'candies/purple_candy.png'
}

# Preload the images into memory without interpolation for pixel art
preloaded_images = {}

for candy_type, image_path in CANDY_IMAGES_PATHS.items():
    preloaded_images[candy_type] = CoreImage(image_path, mipmap=False).texture

# Disable texture filtering to preserve pixel art sharpness
for texture in preloaded_images.values():
    texture.mag_filter = 'nearest'  # Nearest neighbor scaling for sharp pixel art
    texture.min_filter = 'nearest'  # Nearest neighbor scaling for smaller sizes


# Load sounds
swap_sound = SoundLoader.load('swap_sound.wav')
match_sound = SoundLoader.load('match_sound.wav')

# Ensure sounds are loaded properly
if not swap_sound or not match_sound:
    print("Error loading sound files!")

# Global variables to track selected candies
selected_candy = None


class CandyWidget(Widget):
    """Widget representing an individual candy in the game."""

    def __init__(self, candy, **kwargs):
        super().__init__(**kwargs)
        self.candy = candy
        self.size = (CANDY_SIZE, CANDY_SIZE)  # Candy size adjusted for phone dimensions
        self.update_position()

    def update_position(self):
        """Update the widget's position based on candy's position."""
        self.pos = (self.candy.position[0] * self.size[0], self.candy.position[1] * self.size[1])

    def animate_position(self, new_position, callback=None):
        """Animate the candy to a new position."""
        anim = Animation(pos=new_position, duration=0.3)
        if callback:
            anim.bind(on_complete=lambda *args: callback())
        anim.start(self)

    def draw_candy(self):
        """Draw the candy widget on the screen using preloaded images."""
        # Clear previous drawings
        self.canvas.clear()

        # Get the preloaded texture for the candy type
        candy_texture = preloaded_images.get(self.candy.candy_type)

        if candy_texture:
            with self.canvas:
                # Draw the image texture at the widget's position
                Rectangle(texture=candy_texture, pos=self.pos, size=self.size)
        else:
            # If no image is found, default to drawing a solid color
            with self.canvas:
                Rectangle(pos=self.pos, size=self.size)

    def on_touch_down(self, touch):
        """Handle touch events to select and swap candies."""
        if self.collide_point(*touch.pos):
            global selected_candy
            if selected_candy is None:
                # Select the first candy
                selected_candy = self
                print(f"Selected first candy at {self.candy.position}")
            else:
                # Try to swap the second candy with the first one
                print(f"Selected second candy at {self.candy.position}")
                if self.can_swap_with(selected_candy):
                    # Perform the swap via the LogicEngine
                    result = app.logic_engine.swap_candies(self.candy.position, selected_candy.candy.position)

                    if result['action'] == 'update':
                        # Animate the swap
                        self.animate_position(selected_candy.pos)
                        selected_candy.animate_position(self.pos)

                        # After animation, update the grid and score
                        def update_after_animation():
                            app.grid_widget.update_grid()
                            if match_sound:
                                match_sound.play()
                            app.increase_score(len(result['matches']) * 10)  # Increase score based on matches

                        self.animate_position(self.pos, update_after_animation)
                    # Reset selected candy
                    selected_candy = None
                else:
                    print("Invalid swap")
                    selected_candy = None

    def can_swap_with(self, other_candy_widget):
        """Check if this candy can swap with the selected candy (must be adjacent)."""
        x1, y1 = self.candy.position
        x2, y2 = other_candy_widget.candy.position
        return abs(x1 - x2) + abs(y1 - y2) == 1  # Must be adjacent


class GameGrid(GridLayout):
    """Grid widget that manages the grid of candy widgets."""

    def __init__(self, game_grid, **kwargs):
        super().__init__(**kwargs)
        self.game_grid = game_grid
        self.cols = self.game_grid.width
        self.rows = self.game_grid.height
        self.candy_widgets = {}

        # Set the size of the grid to fit the screen
        self.size_hint = (None, None)
        self.size = (GRID_SIZE, GRID_SIZE)

        self.build_grid()

    def build_grid(self):
        """Build the grid and add candy widgets."""
        for row in self.game_grid.grid:
            for candy in row:
                if candy:
                    candy_widget = CandyWidget(candy=candy)
                    candy_widget.draw_candy()
                    self.add_widget(candy_widget)
                    self.candy_widgets[candy.position] = candy_widget

    def update_grid(self):
        """Update all candy widgets to match the game grid."""
        for candy_widget in self.candy_widgets.values():
            candy_widget.update_position()
            candy_widget.draw_candy()

        if not self.check_for_possible_moves():
            app.end_game()

    def check_for_possible_moves(self):
        """Check if any valid moves are left on the grid."""
        for y in range(self.game_grid.height):
            for x in range(self.game_grid.width):
                # Check adjacent positions for possible swaps
                if self.game_grid.is_in_bounds(x+1, y) and self.game_grid.swap_candies((x, y), (x+1, y)):
                    return True
                if self.game_grid.is_in_bounds(x, y+1) and self.game_grid.swap_candies((x, y), (x, y+1)):
                    return True
        return False


class BorderWidget(Widget):
    """Widget that draws a border around the grid."""
    def __init__(self, grid_size, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (grid_size, grid_size)
        self.pos = (0, 0)
        self.draw_border()

    def draw_border(self):
        """Draw the border around the game grid."""
        with self.canvas:
            Color(1, 1, 1, 1)  # White border color
            Rectangle(pos=self.pos, size=self.size)


class FoodCrusherApp(App):
    """Main app for Food Crusher game using Kivy."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score = 0

    def increase_score(self, points):
        """Increase the score by a certain number of points."""
        self.score += points
        self.score_label.text = f"Score: {self.score}"

    def build(self):
        # Create a BoxLayout to organize the score and game area
        layout = BoxLayout(orientation='vertical', padding=10)

        # Create the score label at the top
        self.score_label = Label(text=f"Score: {self.score}", font_size=24, size_hint=(1, 0.1))

        # Create the game grid (logic part)
        self.game_grid = Grid(width=COLS, height=ROWS, candy_types=["red", "blue", "green", "yellow", "orange", "purple"])
        self.grid_widget = GameGrid(game_grid=self.game_grid)

        # Create a border widget around the grid
        border_widget = BorderWidget(grid_size=GRID_SIZE)

        # Create a relative layout to hold the grid and border
        game_area = RelativeLayout(size_hint=(1, 0.9))
        game_area.add_widget(border_widget)  # Add the border behind the grid
        game_area.add_widget(self.grid_widget)  # Add the grid on top of the border

        # Add the score label and game area to the layout
        layout.add_widget(self.score_label)
        layout.add_widget(game_area)

        # Initialize the LogicEngine with the game grid
        self.logic_engine = LogicEngine(self.game_grid)

        # Set window size to phone-like resolution
        Window.size = (PHONE_WIDTH, PHONE_HEIGHT)
        return layout

    def on_start(self):
        """Set up any startup logic or animations."""
        pass  # For now, nothing special on startup

    def end_game(self):
        """End the game when no more moves are possible."""
        self.score_label.text = "Game Over! Final Score: " + str(self.score)
        # Further game-over handling could be implemented here (e.g., restart button)


if __name__ == '__main__':
    app = FoodCrusherApp()
    app.run()
