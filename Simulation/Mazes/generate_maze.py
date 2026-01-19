
import os
import random

def generate_and_save_maze(filename="random_test.maz", width=10, height=10):
    # 1. Define the specific target directory
    target_dir = r" *INSERT PATH TO generated_mazes FOLDER* "
    
    # 2. Ensure the directory exists (creates it if it doesn't)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"Created directory: {target_dir}")

    # 3. Create the full absolute path
    full_path = os.path.join(target_dir, filename)

    # horiz[y][x] is the wall ABOVE cell (x, y)
    # vert[y][x] is the wall to the RIGHT of cell (x, y)
    horiz = [[True for _ in range(width)] for _ in range(height)]
    vert = [[True for _ in range(width)] for _ in range(height)]
    visited = [[False for _ in range(width)] for _ in range(height)]

    # 1. Prim's Algorithm for connectivity
    walls = []
    def add_walls(x, y):
        if x > 0: walls.append((x-1, y, x, y, 'v'))
        if x < width - 1: walls.append((x, y, x+1, y, 'v'))
        if y > 0: walls.append((x, y-1, x, y, 'h'))
        if y < height - 1: walls.append((x, y, x, y+1, 'h'))

    visited[0][0] = True
    add_walls(0, 0)

    while walls:
        x1, y1, x2, y2, dtype = walls.pop(random.randint(0, len(walls) - 1))
        if visited[y1][x1] ^ visited[y2][x2]:
            if dtype == 'v': vert[y1][x1] = False
            else: horiz[y1][x1] = False
            new_x, new_y = (x2, y2) if not visited[y2][x2] else (x1, y1)
            visited[new_y][new_x] = True
            add_walls(new_x, new_y)

    # 2. Enforce 2x2 Middle Area (4,4), (4,5), (5,4), (5,5)
    # Clear internal walls
    vert[4][4] = vert[5][4] = horiz[4][4] = horiz[4][5] = False
    
    # Identify external walls of the 2x2
    center_perimeter = [
        (4,3,'h'), (5,3,'h'), (4,5,'h'), (5,5,'h'), # South/North
        (3,4,'v'), (3,5,'v'), (5,4,'v'), (5,5,'v')  # West/East
    ]
    for x, y, t in center_perimeter:
        if t == 'h': horiz[y][x] = True
        else: vert[y][x] = True

    # Open exactly one entrance
    ex, ey, et = random.choice(center_perimeter)
    if et == 'h': horiz[ey][ex] = False
    else: vert[ey][ex] = False

    # 3. Enforce (0,0) starting rule (3 walls)
    # Boundaries (S/W) are already walls. We add one more on N or E.
    if random.choice([True, False]):
        horiz[0][0] = True  # Wall North
        vert[0][0] = False  # Path East
    else:
        horiz[0][0] = False # Path North
        vert[0][0] = True   # Wall East

    # 4. Export to .maz format
    with open(full_path, 'w') as f:
        for x in range(width):
            for y in range(height):
                # [Your existing logic to calculate n, e, s, w]
                # For example:
                n = 1 if y == height - 1 or horiz[y][x] else 0
                e = 1 if x == width - 1 or vert[y][x] else 0
                s = 1 if y == 0 or horiz[y-1][x] else 0
                w = 1 if x == 0 or vert[y][x-1] else 0
                f.write(f"{x} {y} {n} {e} {s} {w}\n")

    print(f"Successfully generated {filename}")

# Run the generator
generate_and_save_maze()