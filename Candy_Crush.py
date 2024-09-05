import pygame
import random
import numpy as np
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 600 * 1.5
ROWS, COLS = 12, 8
CANDY_SIZE = WIDTH // COLS

# Game Colors
BACKGROUND_COLOR = (50, 50, 50)
GRID_COLOR = (100, 100, 100)
FONT_COLOR = (255, 255, 255)

# Load candy images
CANDY_IMAGES = [
    pygame.transform.scale(pygame.image.load('candies/red_candy.png'), (CANDY_SIZE, CANDY_SIZE)),
    pygame.transform.scale(pygame.image.load('candies/green_candy.png'), (CANDY_SIZE, CANDY_SIZE)),
    pygame.transform.scale(pygame.image.load('candies/blue_candy.png'), (CANDY_SIZE, CANDY_SIZE)),
    pygame.transform.scale(pygame.image.load('candies/yellow_candy.png'), (CANDY_SIZE, CANDY_SIZE)),
    pygame.transform.scale(pygame.image.load('candies/orange_candy.png'), (CANDY_SIZE, CANDY_SIZE)),
    pygame.transform.scale(pygame.image.load('candies/purple_candy.png'), (CANDY_SIZE, CANDY_SIZE))
]

swap_or_fall_occurred = False  # Track if a swap or fall happened

# Load sounds
swap_sound = pygame.mixer.Sound('swap_sound.wav')
match_sound = pygame.mixer.Sound('match_sound.wav')

# Initialize screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Candy Crush")

# Define grid
grid = [[random.choice(range(len(CANDY_IMAGES))) for _ in range(COLS)] for _ in range(ROWS)]

# Selected candy
selected = None

# Score tracking
score = 0
font = pygame.font.SysFont('Arial', 24)


# Easing function for bounce effect (cubic easing for smooth animation)
def ease_out_bounce(t):
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def draw_grid():
    for row in range(ROWS):
        for col in range(COLS):
            candy_type = grid[row][col]
            if candy_type is not None:  # Only draw candies that are not None
                screen.blit(CANDY_IMAGES[candy_type], (col * CANDY_SIZE, row * CANDY_SIZE))
            pygame.draw.rect(screen, GRID_COLOR, (col * CANDY_SIZE, row * CANDY_SIZE, CANDY_SIZE, CANDY_SIZE), 1)


def draw_score():
    score_surface = font.render(f"Score: {score}", True, FONT_COLOR)
    screen.blit(score_surface, (10, 10))


def swap(candy1, candy2):
    r1, c1 = candy1
    r2, c2 = candy2
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]

    return candy1, candy2


def check_match(updated_positions):
    """ Check for matches only involving the updated positions after a swap or fall. """
    visited = set()
    matched = set()

    def dfs(row, col, candy_type):
        """ Perform DFS to find all connected candies of the same type. """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Only check NSEW for now
        stack = [(row, col)]
        connected = set()

        while stack:
            r, c = stack.pop()
            if (r, c) not in visited and 0 <= r < ROWS and 0 <= c < COLS and grid[r][c] == candy_type:
                visited.add((r, c))
                connected.add((r, c))
                # Explore neighbors (NSEW)
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in visited and grid[nr][nc] == candy_type:
                        stack.append((nr, nc))
        return connected

    # Check only around the updated positions
    for row, col in updated_positions:
        if (row, col) not in visited and grid[row][col] is not None:
            connected_candies = dfs(row, col, grid[row][col])
            if len(connected_candies) >= 3:  # Only consider it a match if 3 or more candies are connected
                matched.update(connected_candies)

    if matched:
        match_sound.play()

    return matched


def remove_matches(matched):
    global score
    all_pieces = []  # To store all pieces from all matched candies

    for r, c in matched:
        pos = (c * CANDY_SIZE, r * CANDY_SIZE)  # Position of the candy

        # Make the candy disappear first (remove it from the grid)
        candy_type = grid[r][c]
        grid[r][c] = None  # Remove the candy from the grid before animation

        # Split the candy image into pieces
        pieces = split_candy_image(CANDY_IMAGES[candy_type], 2, 2)  # 2x2 split

        # Collect pieces and their center for explosion animation
        center = (pos[0] + CANDY_SIZE // 2, pos[1] + CANDY_SIZE // 2)
        all_pieces.append((pieces, center))  # Store the pieces with their respective centers

        score += 10  # Increment score after destruction

    # After collecting all pieces, animate them exploding together
    animate_simultaneous_explosion(all_pieces)


def animate_simultaneous_explosion(all_pieces, duration=15):
    """ Animate the explosion of all matched candy pieces outward in contained, slower movements without blocking. """
    fade_steps = 255 // duration  # How fast to fade out the pieces
    all_velocities = []  # Store velocities for all pieces

    # Precalculate random velocities for each piece in each matched candy
    for pieces, center in all_pieces:
        velocities = []
        for piece, _ in pieces:
            direction_x = random.uniform(-0.5, 0.5)
            direction_y = random.uniform(-0.5, 0.5)
            distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

            if distance == 0:
                direction = (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
            else:
                direction = (direction_x / distance, direction_y / distance)

            speed = random.uniform(2, 4)
            velocities.append((direction[0] * speed, direction[1] * speed))

        all_velocities.append(velocities)

    for step in range(duration):
        screen.fill(BACKGROUND_COLOR)
        draw_grid()
        draw_score()

        for (pieces, center), velocities in zip(all_pieces, all_velocities):
            for i, (piece, _) in enumerate(pieces):
                velocity = velocities[i]
                x, y = center[0] - piece.get_width() // 2, center[1] - piece.get_height() // 2
                x += velocity[0] * step
                y += velocity[1] * step
                alpha = max(255 - fade_steps * step, 0)
                piece.set_alpha(alpha)
                screen.blit(piece, (x, y))

        pygame.display.flip()
        pygame.time.delay(10)
        pygame.event.pump()  # Allow other events to be processed


def split_candy_image(image, rows, cols):
    """ Split an image into smaller pieces. """
    width, height = image.get_size()
    piece_width = width // cols
    piece_height = height // rows
    pieces = []

    for row in range(rows):
        for col in range(cols):
            piece_rect = pygame.Rect(col * piece_width, row * piece_height, piece_width, piece_height)
            piece = image.subsurface(piece_rect).copy()  # Create a subimage
            pieces.append((piece, piece_rect.topleft))  # Store the piece and its original position
    return pieces


def drop_candies(existing_fall_complete=False):
    new_candies = []
    falling_steps = 40  # Reduced steps for faster fall
    falling_speed = 10  # Increased speed to make it faster

    if existing_fall_complete:
        for col in range(COLS):
            empty_row = ROWS - 1
            for row in range(ROWS - 1, -1, -1):
                if grid[row][col] is None:
                    candy_type = random.randint(0, len(CANDY_IMAGES) - 1)
                    start_pos = np.array([col * CANDY_SIZE, -(empty_row - row + 1) * CANDY_SIZE])
                    end_pos = np.array([col * CANDY_SIZE, row * CANDY_SIZE])

                    new_candies.append((candy_type, start_pos, end_pos, row, col))

        # Animate candies falling from offscreen with adjusted easing for smoother effect
        for step in range(falling_steps):
            screen.fill(BACKGROUND_COLOR)
            draw_grid()  # Draw current grid state without new candies
            draw_score()

            for candy, start_pos, end_pos, row, col in new_candies:
                t = ease_out_bounce2(step / falling_steps)
                intermediate_pos = start_pos + (end_pos - start_pos) * t
                screen.blit(CANDY_IMAGES[candy], intermediate_pos)

            pygame.display.flip()
            pygame.time.delay(falling_speed)

        for candy, _, _, row, col in new_candies:
            grid[row][col] = candy

        return [(row, col) for _, _, _, row, col in new_candies]
    else:
        return []


def ease_out_bounce2(t):
    """ Even softer bounce effect by further reducing multipliers and thresholds. """
    if t < 1 / 2.75:
        return 6.0 * t * t  # Further reduced multiplier for softer initial bounce
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 6.0 * t * t + 0.5  # Reduced bounce intensity further
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 6.0 * t * t + 0.75  # Softer final bounce with lower coefficient
    else:
        t -= 2.625 / 2.75
        return 6.0 * t * t + 0.9  # Minimized bounce on impact, very subtle



def animate_swap(candy1, candy2):
    # Play swap sound
    swap_sound.play()

    r1, c1 = candy1
    r2, c2 = candy2
    pos1 = np.array([c1 * CANDY_SIZE, r1 * CANDY_SIZE])
    pos2 = np.array([c2 * CANDY_SIZE, r2 * CANDY_SIZE])

    # Store original candies to avoid blitting wrong ones
    original_candy1 = grid[r1][c1]
    original_candy2 = grid[r2][c2]

    # Clear the original positions before animating
    grid[r1][c1] = None
    grid[r2][c2] = None

    for i in range(15):
        screen.fill(BACKGROUND_COLOR)
        draw_grid()
        draw_score()

        t = ease_out_bounce(i / 15.0)  # Apply easing for smooth movement
        intermediate_pos1 = pos1 + (pos2 - pos1) * t
        intermediate_pos2 = pos2 + (pos1 - pos2) * t

        # Only draw the candies in their intermediate positions
        screen.blit(CANDY_IMAGES[original_candy1], intermediate_pos1)
        screen.blit(CANDY_IMAGES[original_candy2], intermediate_pos2)

        pygame.display.update([pygame.Rect(pos1[0], pos1[1], CANDY_SIZE, CANDY_SIZE),
                               pygame.Rect(pos2[0], pos2[1], CANDY_SIZE, CANDY_SIZE)])  # Update only affected areas
        pygame.time.delay(30)

    # Finalize the swap
    grid[r1][c1] = original_candy2
    grid[r2][c2] = original_candy1


def animate_falling():
    falling_steps = 60
    falling_speed = 2
    falling_candies = []
    updated_positions = []

    for col in range(COLS):
        for row in range(ROWS - 1, -1, -1):
            if grid[row][col] is None:
                for above_row in range(row - 1, -1, -1):
                    if grid[above_row][col] is not None:
                        start_pos = np.array([col * CANDY_SIZE, above_row * CANDY_SIZE])
                        end_pos = np.array([col * CANDY_SIZE, row * CANDY_SIZE])
                        moving_candy = grid[above_row][col]
                        grid[above_row][col] = None
                        falling_candies.append((moving_candy, start_pos, end_pos, row, col))
                        updated_positions.append((row, col))
                        break

    for step in range(falling_steps):
        screen.fill(BACKGROUND_COLOR)
        draw_grid()
        draw_score()

        for candy, start_pos, end_pos, row, col in falling_candies:
            t = ease_out_bounce(step / falling_steps)
            intermediate_pos = start_pos + (end_pos - start_pos) * t
            screen.blit(CANDY_IMAGES[candy], intermediate_pos)

        pygame.display.flip()
        pygame.time.delay(falling_speed)
        pygame.event.pump()  # Allow other events to be processed

    for candy, _, _, row, col in falling_candies:
        grid[row][col] = candy

    new_candies = drop_candies(existing_fall_complete=True)
    updated_positions.extend(new_candies)

    return updated_positions


def is_adjacent(candy1, candy2):
    r1, c1 = candy1
    r2, c2 = candy2

    # Check if candy2 is exactly one grid away from candy1 (N, S, E, W)
    return (abs(r1 - r2) == 1 and c1 == c2) or (abs(c1 - c2) == 1 and r1 == r2)


def handle_candy_selection(pos):
    global selected
    x, y = pos
    row, col = y // CANDY_SIZE, x // CANDY_SIZE

    if selected:
        if is_adjacent(selected, (row, col)):  # Only allow swaps with adjacent cells
            animate_swap(selected, (row, col))
            updated_positions = [selected, (row, col)]  # Track updated candies
            matched = check_match(updated_positions)

            if matched:
                # Handle the matches, fall animation, and check for cascading matches
                remove_matches(matched)
                updated_positions = animate_falling()

                # Check for cascading matches after falling (allow chained matches)
                while True:
                    matched = check_match(updated_positions)
                    if matched:
                        remove_matches(matched)
                        updated_positions = animate_falling()  # Get new updated positions
                    else:
                        break
            else:
                # Swap back if no match is found
                animate_swap(selected, (row, col))  # Reverse the swap if no match is made
        selected = None
    else:
        selected = (row, col)


def main():
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_candy_selection(pygame.mouse.get_pos())

        screen.fill(BACKGROUND_COLOR)
        draw_grid()
        draw_score()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
