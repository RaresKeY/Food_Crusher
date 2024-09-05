from random import choice


class Candy:
    def __init__(self, candy_type, position):
        self.candy_type = candy_type
        self.position = position

    def move(self, new_position):
        self.position = new_position

    def __repr__(self):
        return f"Candy(type={self.candy_type}, position={self.position})"


class Grid:
    def __init__(self, width, height, candy_types):
        self.width = width
        self.height = height
        self.candy_types = candy_types
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.populate_grid()

    def populate_grid(self):
        """Fill the grid with random candies."""
        for y in range(self.height):
            for x in range(self.width):
                self.add_candy(Candy(choice(self.candy_types), (x, y)), x, y)

    def add_candy(self, candy, x, y):
        """Add a candy to the grid at position (x, y)."""
        if self.is_in_bounds(x, y):
            self.grid[y][x] = candy
            candy.move((x, y))

    def swap_candies(self, pos1, pos2):
        """Swap candies between two positions."""
        x1, y1 = pos1
        x2, y2 = pos2
        if self.is_in_bounds(x1, y1) and self.is_in_bounds(x2, y2):
            self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
            self.grid[y1][x1].move((x1, y1))
            self.grid[y2][x2].move((x2, y2))

    def is_in_bounds(self, x, y):
        """Check if the position is within the grid."""
        return 0 <= x < self.width and 0 <= y < self.height

    def remove_matches(self):
        """Find and remove matches of three or more candies in a row or column."""
        matched_positions = set()

        # Horizontal matches
        for y in range(self.height):
            for x in range(self.width - 2):
                if (self.grid[y][x] and self.grid[y][x + 1] and self.grid[y][x + 2] and
                        self.grid[y][x].candy_type == self.grid[y][x + 1].candy_type == self.grid[y][x + 2].candy_type):
                    matched_positions.update([(x, y), (x + 1, y), (x + 2, y)])

        # Vertical matches
        for x in range(self.width):
            for y in range(self.height - 2):
                if (self.grid[y][x] and self.grid[y + 1][x] and self.grid[y + 2][x] and
                        self.grid[y][x].candy_type == self.grid[y + 1][x].candy_type == self.grid[y + 2][x].candy_type):
                    matched_positions.update([(x, y), (x, y + 1), (x, y + 2)])

        # Remove matched candies
        if matched_positions:
            for x, y in matched_positions:
                self.grid[y][x] = None  # Remove the candy

        return matched_positions

    def drop_candies(self):
        """Make candies fall down if there are empty spaces."""
        for x in range(self.width):
            for y in range(self.height - 1, 0, -1):
                if self.grid[y][x] is None:
                    # Look for candies above to fall down
                    for upper_y in range(y - 1, -1, -1):
                        if self.grid[upper_y][x]:
                            self.grid[y][x], self.grid[upper_y][x] = self.grid[upper_y][x], None
                            break

    def refill_grid(self):
        """Refill the grid with new candies after matches are cleared."""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] is None:
                    self.add_candy(Candy(choice(self.candy_types), (x, y)), x, y)

    def process_turn(self):
        """Process a turn in the game: remove matches, drop candies, refill the grid."""
        matches = self.remove_matches()
        if matches:
            self.drop_candies()
            self.refill_grid()
            return matches
        return None


class LogicEngine:
    """Handles game logic and interaction between Kivy and the core game mechanics."""

    def __init__(self, grid):
        self.grid = grid

    def swap_candies(self, pos1, pos2):
        """Handle the swapping of two candies and process the result."""
        self.grid.swap_candies(pos1, pos2)

        # After the swap, check for matches and return the required result
        matches = self.grid.process_turn()

        # If matches were found, we should trigger an animation or update
        if matches:
            return {
                'grid': self.grid,  # The updated grid state
                'matches': matches,  # Positions where matches occurred
                'action': 'update'  # Command to trigger Kivy to update the visuals
            }
        return {
            'grid': self.grid,
            'action': 'no_match'  # No match found, return the grid as-is
        }
