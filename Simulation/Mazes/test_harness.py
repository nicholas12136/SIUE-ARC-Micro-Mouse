"""
Micromouse Headless Test Harness
=================================
Automatically compiles mouse.exe and runs it against every .maz file
in the mazes folder, simulating the mms stdin/stdout protocol.

Folder structure expected:
    C:\\Users\\npg20\\Documents\\ARC\\Micromouse\\mms\\
        mms-cpp\\       <- Main.cpp, API.cpp, API.h
        mazes\\         <- .maz files to test against

Usage:
    1. Open MSYS2 MINGW64 terminal
    2. Navigate to the mms folder:
           cd /c/Users/npg20/Documents/ARC/Micromouse/mms
    3. Run:
           python test_harness.py

Optional: generate fresh mazes before testing by setting
    GENERATE_MAZES = True  and  MAZE_COUNT = however many you want
"""

import os
import subprocess
import sys
from collections import deque

# =============================================================================
# CONFIGURATION — edit these paths if your folder structure changes
# =============================================================================

MMS_ROOT    = r"C:\Users\npg20\Documents\ARC\Micromouse\mms"
CPP_DIR     = os.path.join(MMS_ROOT, "mms-cpp")
MAZES_DIR   = os.path.join(MMS_ROOT, "mazes")
EXE_PATH    = os.path.join(CPP_DIR, "mouse.exe")
FAILURES_DIR = os.path.join(MMS_ROOT, "failures")  # failed mazes saved here

# If True, generate fresh mazes before running tests
GENERATE_MAZES = False
MAZE_COUNT     = 100   # how many mazes to generate if GENERATE_MAZES is True
MAZE_GENERATOR = os.path.join(MAZES_DIR, "generate_maze.py")  # path to generator

# Safety limit — if the mouse takes more than this many steps, it's stuck
MAX_STEPS = 5000

# Width/Height — must match what Main.cpp expects
MAZE_WIDTH  = 10
MAZE_HEIGHT = 10

# Center goal cells (local coordinates, always the same for a 10x10 maze)
CENTER_CELLS = {(4, 4), (4, 5), (5, 4), (5, 5)}


# =============================================================================
# STEP 1: COMPILE
# =============================================================================

def compile_mouse():
    """
    Runs g++ to compile Main.cpp and API.cpp into mouse.exe.
    Returns True if successful, False if compilation failed.
    """
    print("=" * 60)
    print("Compiling mouse.exe...")
    print("=" * 60)

    cmd = ["g++", "Main.cpp", "API.cpp", "-o", "mouse.exe", "-std=c++17", "-static-libgcc", "-static-libstdc++"]

    result = subprocess.run(
        cmd,
        cwd=CPP_DIR,          # run from the mms-cpp folder
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("COMPILATION FAILED:")
        print(result.stderr)
        return False

    print("Compilation successful.\n")
    return True


# =============================================================================
# STEP 2: MAZE PARSING
# =============================================================================

def load_maze(filepath):
    """
    Reads a .maz file and returns a wall lookup dictionary.

    .maz format: each line is  x y n e s w
    where 1 = wall present, 0 = open.

    Returns: dict of (x, y) -> {'n': bool, 'e': bool, 's': bool, 'w': bool}
    """
    walls = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            x, y, n, e, s, w = int(parts[0]), int(parts[1]), \
                                int(parts[2]), int(parts[3]), \
                                int(parts[4]), int(parts[5])
            walls[(x, y)] = {
                'n': bool(n),
                'e': bool(e),
                's': bool(s),
                'w': bool(w)
            }
    return walls


def wall_in_direction(walls, x, y, direction):
    """
    Returns True if there is a wall in the given absolute direction
    from cell (x, y).

    direction: 0=North, 1=East, 2=South, 3=West
    """
    dir_map = {0: 'n', 1: 'e', 2: 's', 3: 'w'}
    key = dir_map[direction]
    cell = walls.get((x, y))
    if cell is None:
        return True  # treat out-of-bounds as wall
    return cell[key]


# =============================================================================
# STEP 3: SIMULATE ONE MAZE RUN
# =============================================================================

def simulate(maze_filepath):
    """
    Runs mouse.exe against a single maze file, simulating the mms protocol.

    Returns a dict with:
        success  : bool   — did the mouse complete all three phases?
        steps    : int    — total moveForward calls made
        reason   : str    — human readable result description
    """
    walls = load_maze(maze_filepath)

    # Mouse internal state (mirrors what Main.cpp tracks)
    state = {
        'x':       0,
        'y':       0,
        'heading': 0,    # 0=N, 1=E, 2=S, 3=W
        'steps':   0,
        'phase':   'SEARCHING',  # for our tracking only
    }

    # Direction vectors: North, East, South, West
    dx = [0, 1, 0, -1]
    dy = [1, 0, -1, 0]

    def get_wall_front():
        return wall_in_direction(walls, state['x'], state['y'], state['heading'])

    def get_wall_right():
        return wall_in_direction(walls, state['x'], state['y'], (state['heading'] + 1) % 4)

    def get_wall_left():
        return wall_in_direction(walls, state['x'], state['y'], (state['heading'] + 3) % 4)

    def do_move_forward():
        h = state['heading']
        nx = state['x'] + dx[h]
        ny = state['y'] + dy[h]

        # Check if there is actually a wall in the way
        if wall_in_direction(walls, state['x'], state['y'], h):
            return "crash"  # mouse tried to move through a wall

        # Check bounds
        if nx < 0 or nx >= MAZE_WIDTH or ny < 0 or ny >= MAZE_HEIGHT:
            return "crash"

        state['x'] = nx
        state['y'] = ny
        state['steps'] += 1
        return "ack"

    # Launch mouse.exe as a subprocess, piping stdin/stdout
    try:
        process = subprocess.Popen(
            [EXE_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,   # captures log() calls from mouse
            text=True,
            bufsize=1                 # line buffered
        )
    except FileNotFoundError:
        return {'success': False, 'steps': 0, 'reason': 'mouse.exe not found'}

    success = False
    reason  = "Unknown"
    reached_center  = False
    reached_start   = False

    try:
        while True:
            # Check step limit
            if state['steps'] > MAX_STEPS:
                reason = f"Timeout: exceeded {MAX_STEPS} steps"
                process.kill()
                break

            # Read one command from the mouse
            line = process.stdout.readline()
            if not line:
                # Process ended — check if it finished cleanly
                if reached_center and reached_start:
                    success = True
                    reason = f"Fast run complete in {state['steps']} steps"
                elif reached_center:
                    reason = "Reached center but did not return to start"
                else:
                    reason = "Process exited without reaching center"
                break

            cmd = line.strip()

            # --- Respond to each API command ---

            if cmd == "mazeWidth":
                process.stdin.write(f"{MAZE_WIDTH}\n")
                process.stdin.flush()

            elif cmd == "mazeHeight":
                process.stdin.write(f"{MAZE_HEIGHT}\n")
                process.stdin.flush()

            elif cmd == "wallFront":
                result = "true" if get_wall_front() else "false"
                process.stdin.write(f"{result}\n")
                process.stdin.flush()

            elif cmd == "wallRight":
                result = "true" if get_wall_right() else "false"
                process.stdin.write(f"{result}\n")
                process.stdin.flush()

            elif cmd == "wallLeft":
                result = "true" if get_wall_left() else "false"
                process.stdin.write(f"{result}\n")
                process.stdin.flush()

            elif cmd.startswith("moveForward"):
                result = do_move_forward()
                process.stdin.write(f"{result}\n")
                process.stdin.flush()

                if result == "crash":
                    reason = f"Crash: mouse moved into a wall at ({state['x']},{state['y']}) heading {state['heading']}"
                    process.kill()
                    break

                # Track phase transitions based on position
                pos = (state['x'], state['y'])
                if pos in CENTER_CELLS and not reached_center:
                    reached_center = True
                elif pos == (0, 0) and reached_center and not reached_start:
                    reached_start = True

            elif cmd == "turnRight":
                state['heading'] = (state['heading'] + 1) % 4
                process.stdin.write("ack\n")
                process.stdin.flush()

            elif cmd == "turnLeft":
                state['heading'] = (state['heading'] + 3) % 4
                process.stdin.write("ack\n")
                process.stdin.flush()

            elif cmd == "wasReset":
                process.stdin.write("false\n")
                process.stdin.flush()

            elif cmd == "ackReset":
                process.stdin.write("ack\n")
                process.stdin.flush()

            # Visual commands — acknowledge silently, no response needed
            elif (cmd.startswith("setWall") or
                  cmd.startswith("clearWall") or
                  cmd.startswith("setColor") or
                  cmd.startswith("clearColor") or
                  cmd.startswith("clearAllColor") or
                  cmd.startswith("setText") or
                  cmd.startswith("clearText") or
                  cmd.startswith("clearAllText")):
                pass  # no response required for visual commands

            else:
                # Unknown command — log it but don't crash the harness
                pass

    except Exception as e:
        reason = f"Harness error: {str(e)}"
        try:
            process.kill()
        except:
            pass

    finally:
        try:
            process.wait(timeout=2)
        except:
            process.kill()

    return {
        'success': success,
        'steps':   state['steps'],
        'reason':  reason
    }


# =============================================================================
# STEP 4: BATCH RUNNER
# =============================================================================

def run_all_mazes():
    """
    Finds every .maz file in MAZES_DIR, runs the mouse against each one,
    and prints a summary report. Failed mazes are copied to FAILURES_DIR
    so you can load them into mms to inspect visually.
    """
    # Gather all maze files
    maze_files = sorted([
        os.path.join(MAZES_DIR, f)
        for f in os.listdir(MAZES_DIR)
        if f.endswith('.maz')
    ])

    if not maze_files:
        print(f"No .maz files found in {MAZES_DIR}")
        print("Run generate_maze.py first to create some mazes.")
        return

    total       = len(maze_files)
    passed      = 0
    failed      = 0
    failures    = []
    total_steps = 0

    # Create failures directory if needed
    if not os.path.exists(FAILURES_DIR):
        os.makedirs(FAILURES_DIR)

    print(f"Running {total} mazes...\n")
    print(f"{'#':<6} {'Maze':<30} {'Result':<10} {'Steps':<8} Reason")
    print("-" * 80)

    for i, maze_path in enumerate(maze_files, 1):
        maze_name = os.path.basename(maze_path)
        result = simulate(maze_path)

        status = "PASS" if result['success'] else "FAIL"
        print(f"{i:<6} {maze_name:<30} {status:<10} {result['steps']:<8} {result['reason']}")

        total_steps += result['steps']
        if result['success']:
            passed += 1
        else:
            failed += 1
            failures.append((maze_name, maze_path, result['reason']))

            # Copy failed maze to failures folder for mms inspection
            import shutil
            shutil.copy(maze_path, os.path.join(FAILURES_DIR, maze_name))

    # Summary
    print("\n" + "=" * 80)
    avg_steps = total_steps / total if total > 0 else 0
    print(f"RESULTS: {passed}/{total} passed,  {failed}/{total} failed")
    print(f"AVERAGE STEPS: {avg_steps:.1f}  (total: {total_steps})")

    if failures:
        print(f"\nFailed mazes saved to: {FAILURES_DIR}")
        print("Load any of these into mms to inspect them visually:\n")
        for name, path, reason in failures:
            print(f"  {name}  —  {reason}")
    else:
        print("\nAll mazes passed! Logic is solid.")

    print("=" * 80)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    # Step 1: Optionally generate fresh mazes
    if GENERATE_MAZES:
        print(f"Generating {MAZE_COUNT} mazes via generate_maze.py...\n")
        gen_result = subprocess.run(
            [sys.executable, MAZE_GENERATOR,
             "--count", str(MAZE_COUNT)],
            capture_output=True, text=True
        )
        if gen_result.returncode != 0:
            print("Maze generation failed:")
            print(gen_result.stderr)
            sys.exit(1)
        print(gen_result.stdout)

    # Step 2: Compile mouse.exe
    if not compile_mouse():
        sys.exit(1)

    # Step 3: Run all mazes
    run_all_mazes()