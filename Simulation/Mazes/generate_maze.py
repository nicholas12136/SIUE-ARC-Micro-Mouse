import os
import random
from collections import deque

# -----------------------------------------------------------------------
# CHANGES FROM PREVIOUS VERSION:
#
# 1. CENTER PERIMETER FIX: After Prim's runs, forcing all center perimeter
#    walls back to True can seal off cells that were only reachable through
#    those walls, breaking the maze's connectivity. Fix: we now run a
#    connectivity check after enforcing center rules and retry generation
#    from scratch if the maze is broken.
#
# 2. CONNECTIVITY VALIDATION: A flood fill from (0,0) confirms that every
#    single cell in the finished maze is reachable before saving. If any
#    cell is unreachable, the maze is thrown out and regenerated. This is
#    the safety net that catches any issue — not just the center perimeter
#    problem — that could produce an unsolvable maze.
#
# 3. START CORNER KEPT AT (0,0): The start is always bottom-left for full
#    compatibility with the mms simulator. Testing different physical start
#    corners is handled in Main.cpp via the heading detection logic, not
#    by changing the maze file. The random North/East wall choice from the
#    previous version is preserved so the start cell still has exactly 3
#    walls with one random open passage, which exercises the heading
#    detection code properly.
# -----------------------------------------------------------------------

def is_fully_connected(horiz, vert, width, height):
    """
    Flood fill from (0,0) through the maze using the horiz/vert wall arrays.
    Returns True if every cell is reachable, False if any cell is isolated.

    Wall convention:
        horiz[y][x] = True means there is a wall ABOVE cell (x, y)
        vert[y][x]  = True means there is a wall to the RIGHT of cell (x, y)
    
    So to move from (x, y) to (x, y+1): check horiz[y][x] — must be False
    To move from (x, y) to (x+1, y): check vert[y][x]  — must be False
    To move from (x, y) to (x, y-1): check horiz[y-1][x] — must be False
    To move from (x, y) to (x-1, y): check vert[y][x-1]  — must be False
    """
    visited = [[False for _ in range(width)] for _ in range(height)]
    queue = deque()
    queue.append((0, 0))
    visited[0][0] = True
    count = 1

    while queue:
        x, y = queue.popleft()

        # Try moving North: wall above (x,y) must be absent
        if y < height - 1 and not horiz[y][x] and not visited[y+1][x]:
            visited[y+1][x] = True
            count += 1
            queue.append((x, y+1))

        # Try moving East: wall to right of (x,y) must be absent
        if x < width - 1 and not vert[y][x] and not visited[y][x+1]:
            visited[y][x+1] = True
            count += 1
            queue.append((x+1, y))

        # Try moving South: wall above (x, y-1) must be absent
        if y > 0 and not horiz[y-1][x] and not visited[y-1][x]:
            visited[y-1][x] = True
            count += 1
            queue.append((x, y-1))

        # Try moving West: wall to right of (x-1, y) must be absent
        if x > 0 and not vert[y][x-1] and not visited[y][x-1]:
            visited[y][x-1] = True
            count += 1
            queue.append((x-1, y))

    return count == width * height


def generate_maze(width=10, height=10):
    """
    Generates a single valid maze using Prim's algorithm, then enforces
    competition rules. Retries automatically if the result fails the
    connectivity check.

    Returns (horiz, vert) wall arrays for the valid maze.
    """
    attempts = 0

    while True:
        attempts += 1

        # ------------------------------------------------------------------
        # STEP 1: Prim's Algorithm
        # Start from (0,0) and randomly carve passages until all cells are
        # connected. This guarantees a perfect maze (no loops, fully
        # connected) before we apply any competition-specific rules.
        # ------------------------------------------------------------------
        horiz = [[True for _ in range(width)] for _ in range(height)]
        vert  = [[True for _ in range(width)] for _ in range(height)]
        seen  = [[False for _ in range(width)] for _ in range(height)]

        candidate_walls = []

        def add_walls(x, y):
            if x > 0:          candidate_walls.append((x-1, y, x,   y,   'v'))
            if x < width - 1:  candidate_walls.append((x,   y, x+1, y,   'v'))
            if y > 0:          candidate_walls.append((x,   y-1, x, y,   'h'))
            if y < height - 1: candidate_walls.append((x,   y,  x,  y+1, 'h'))

        seen[0][0] = True
        add_walls(0, 0)

        while candidate_walls:
            x1, y1, x2, y2, dtype = candidate_walls.pop(
                random.randint(0, len(candidate_walls) - 1)
            )
            # Only remove the wall if exactly one side has been visited
            if seen[y1][x1] ^ seen[y2][x2]:
                if dtype == 'v':
                    vert[y1][x1] = False
                else:
                    horiz[y1][x1] = False
                new_x, new_y = (x2, y2) if not seen[y2][x2] else (x1, y1)
                seen[new_y][new_x] = True
                add_walls(new_x, new_y)

        # ------------------------------------------------------------------
        # STEP 2: Enforce the 2x2 center goal area
        #
        # The four center cells are (4,4), (4,5), (5,4), (5,5).
        # Rules:
        #   - All internal walls within the 2x2 must be removed
        #   - All external perimeter walls around the 2x2 must be present
        #   - Exactly one perimeter wall is opened as the single entrance
        #
        # IMPORTANT: Forcing perimeter walls back to True after Prim's may
        # disconnect parts of the maze. That's why we validate connectivity
        # afterwards and retry if needed.
        # ------------------------------------------------------------------

        # Clear the two internal walls of the 2x2 center
        # vert[4][4]: wall between (4,4) and (5,4) — remove it
        # vert[5][4]: wall between (5,4) and... wait, that's the east boundary
        # Let's be precise:
        #   Internal vertical wall: between (4,4)&(5,4) = vert[4][4]
        #                           between (4,5)&(5,5) = vert[5][4] -- NO
        # vert[y][x] is the wall to the RIGHT of (x,y), so:
        #   Wall between (4,4) and (5,4): vert[4][4]  (right of x=4 at y=4)
        #   Wall between (4,5) and (5,5): vert[5][4]  (right of x=4 at y=5)
        # Internal horizontal wall:
        #   Wall between (4,4) and (4,5): horiz[4][4] (above y=4 at x=4)
        #   Wall between (5,4) and (5,5): horiz[4][5] (above y=4 at x=5)
        vert[4][4]  = False  # between (4,4) and (5,4)
        vert[5][4]  = False  # between (4,5) and (5,5)
        horiz[4][4] = False  # between (4,4) and (4,5)
        horiz[4][5] = False  # between (5,4) and (5,5)

        # Define the 8 external perimeter walls around the 2x2.
        # Format: (x, y, wall_type) where wall_type is 'h' or 'v'
        # 'h' entry means horiz[y][x], 'v' entry means vert[y][x]
        center_perimeter = [
            (4, 3, 'h'),  # South wall of (4,4): horiz[3][4]  — wall above y=3
            (5, 3, 'h'),  # South wall of (5,4): horiz[3][5]
            (4, 5, 'h'),  # North wall of (4,5): horiz[5][4]  — wall above y=5
            (5, 5, 'h'),  # North wall of (5,5): horiz[5][5]
            (3, 4, 'v'),  # West wall of (4,4):  vert[4][3]   — right of x=3
            (3, 5, 'v'),  # West wall of (4,5):  vert[5][3]
            (5, 4, 'v'),  # East wall of (5,4):  vert[4][5]   — right of x=5
            (5, 5, 'v'),  # East wall of (5,5):  vert[5][5]
        ]

        # Force all perimeter walls ON
        for x, y, t in center_perimeter:
            if t == 'h':
                horiz[y][x] = True
            else:
                vert[y][x] = True

        # Open exactly one perimeter wall as the single entrance
        ex, ey, et = random.choice(center_perimeter)
        if et == 'h':
            horiz[ey][ex] = False
        else:
            vert[ey][ex] = False

        # ------------------------------------------------------------------
        # STEP 3: Enforce start cell (0,0) has exactly 3 walls
        #
        # South and West boundaries are already walls (edge of maze).
        # Randomly place the third wall on either North or East, leaving
        # exactly one open passage. This exercises the heading detection
        # code in Main.cpp which figures out which way to face at startup.
        # ------------------------------------------------------------------
        if random.choice([True, False]):
            horiz[0][0] = True   # Wall to the North of (0,0)
            vert[0][0]  = False  # Open passage to the East
        else:
            horiz[0][0] = False  # Open passage to the North
            vert[0][0]  = True   # Wall to the East of (0,0)

        # ------------------------------------------------------------------
        # STEP 4: Connectivity validation
        #
        # Flood fill from (0,0) through the finished maze. If every cell
        # is reachable, the maze is valid and we save it. If not, the
        # center perimeter enforcement disconnected something — discard
        # this maze and try again from scratch.
        # ------------------------------------------------------------------
        if is_fully_connected(horiz, vert, width, height):
            if attempts > 1:
                print(f"  (Took {attempts} attempts to get a connected maze)")
            return horiz, vert
        else:
            print(f"  Attempt {attempts}: connectivity check failed, retrying...")


def save_maze(horiz, vert, filename, width=10, height=10, target_dir=None):
    """
    Converts horiz/vert wall arrays to the .maz file format and saves it.

    .maz format: each line is  x y n e s w
    where n/e/s/w are 1 (wall present) or 0 (open).
    Maze boundary edges are always walls.
    """
    if target_dir is None:
        target_dir = r"C:\Users\npg20\Documents\ARC\Micromouse\mms\mazes"

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

    full_path = os.path.join(target_dir, filename)

    with open(full_path, 'w') as f:
        for x in range(width):
            for y in range(height):
                n = 1 if y == height - 1 or horiz[y][x]    else 0
                e = 1 if x == width  - 1 or vert[y][x]     else 0
                s = 1 if y == 0          or horiz[y-1][x]  else 0
                w = 1 if x == 0          or vert[y][x-1]   else 0
                f.write(f"{x} {y} {n} {e} {s} {w}\n")

    return full_path


def generate_and_save_maze(filename="random_test.maz", width=10, height=10,
                           target_dir=None):
    """
    Main entry point. Generates a valid maze and saves it to disk.
    """
    print(f"Generating {filename}...")
    horiz, vert = generate_maze(width, height)
    path = save_maze(horiz, vert, filename, width, height, target_dir)
    print(f"Successfully saved: {path}")
    return path


def generate_batch(count=10, prefix="maze", target_dir=None):
    """
    Generates multiple maze files in one call.
    Useful for building a test suite.

    Example: generate_batch(500) produces maze_001.maz ... maze_500.maz
    """
    print(f"Generating {count} mazes...")
    for i in range(1, count + 1):
        filename = f"{prefix}_{i:03d}.maz"
        generate_and_save_maze(filename, target_dir=target_dir)
    print(f"Done. {count} mazes generated.")


# -----------------------------------------------------------------------
# Entry point — change generate_batch count to however many you need
# -----------------------------------------------------------------------
if __name__ == "__main__":
    generate_batch(500)