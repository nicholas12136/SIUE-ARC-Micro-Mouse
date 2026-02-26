#include <iostream>
#include <string>
#include <queue>
#include <vector>
#include "API.h"

const int WIDTH  = 10;
const int HEIGHT = 10;

// =============================================================================
// STATE MACHINE
// =============================================================================
// The mouse operates in four sequential phases:
//
//   SEARCHING  — Explore the maze using flood fill, building wall_map as we go.
//                Navigate toward the center 2x2 goal. Sensors are active.
//                Every move is recorded in explorationPath as a safety net.
//
//   RETURNING  — After reaching the center, take the SHORTEST path back to
//                (0,0) through visited cells only (reliable wall data).
//                Falls back to reversing explorationPath if no shorter route
//                is found. No sensors needed during this phase.
//
//   FAST_RUN   — Execute the precomputed optimal path from (0,0) to center.
//                Computed using complete wall_map after RETURNING finishes.
//                No sensing, no decisions — pure execution.
//                This is the timed competition run.
//
//   FINISHED   — Fast run complete. Stop all activity.
//
enum State { SEARCHING, RETURNING, FAST_RUN, FINISHED };
State currentState = SEARCHING;

// =============================================================================
// GLOBAL STATE
// =============================================================================

int current_x = 0;
int current_y = 0;
int heading   = 0; // 0:North  1:East  2:South  3:West

// wall_map[x][y] bitmask: bit0=North, bit1=East, bit2=South, bit3=West
int wall_map[WIDTH][HEIGHT];

// distances[x][y] = flood fill distance to current goal. 255 = unreachable.
int distances[WIDTH][HEIGHT];

// visited[x][y] = true once the mouse has physically entered that cell.
// Critical for restricting flood fill to known territory.
bool visited[WIDTH][HEIGHT];

// explorationPath records every direction moved during SEARCHING.
// Used as a fallback for the return trip if the smarter path fails.
std::vector<int> explorationPath;

// returnPath and fastPath hold precomputed move sequences.
// Both are executed step by step with no sensor input.
std::vector<int> returnPath;
std::vector<int> fastPath;

void log(const std::string& text) { std::cerr << text << std::endl; }

// =============================================================================
// VISUAL DISPLAY
// =============================================================================

void updateAllMazeText() {
    for (int x = 0; x < WIDTH; x++) {
        for (int y = 0; y < HEIGHT; y++) {
            if (visited[x][y] && distances[x][y] != 255) {
                API::setText(x, y, std::to_string(distances[x][y]));
            } else {
                API::setText(x, y, "");
            }
        }
    }
}

// =============================================================================
// MOVEMENT WRAPPERS
// =============================================================================

void turnRight() { API::turnRight(); heading = (heading + 1) % 4; }
void turnLeft()  { API::turnLeft();  heading = (heading + 3) % 4; }

void moveForward() {
    API::moveForward();
    if      (heading == 0) current_y++;
    else if (heading == 1) current_x++;
    else if (heading == 2) current_y--;
    else if (heading == 3) current_x--;
    visited[current_x][current_y] = true;

    // Record every move during SEARCHING as a fallback return route
    if (currentState == SEARCHING) {
        explorationPath.push_back(heading);
    }
}

// =============================================================================
// WALL REGISTRATION
// =============================================================================

void setWall(int x, int y, int direction) {
    if      (direction == 0) wall_map[x][y] |= 1;
    else if (direction == 1) wall_map[x][y] |= 2;
    else if (direction == 2) wall_map[x][y] |= 4;
    else if (direction == 3) wall_map[x][y] |= 8;

    if      (direction == 0 && y < HEIGHT - 1) wall_map[x][y+1] |= 4;
    else if (direction == 1 && x < WIDTH  - 1) wall_map[x+1][y] |= 8;
    else if (direction == 2 && y > 0)          wall_map[x][y-1] |= 1;
    else if (direction == 3 && x > 0)          wall_map[x-1][y] |= 2;

    char dirChars[] = {'n', 'e', 's', 'w'};
    API::setWall(x, y, dirChars[direction]);
}

void updateWalls() {
    if (API::wallFront()) setWall(current_x, current_y, heading);
    if (API::wallLeft())  setWall(current_x, current_y, (heading + 3) % 4);
    if (API::wallRight()) setWall(current_x, current_y, (heading + 1) % 4);
}

// =============================================================================
// FLOOD FILL — VISITED CELLS ONLY
// =============================================================================
// Restricts BFS to cells the mouse has physically visited.
// Unvisited cells have incomplete wall data and are treated as impassable.
// This ensures every path computed only travels through trusted territory.

void floodFillVisited(const std::vector<std::pair<int, int>>& targets) {
    for (int x = 0; x < WIDTH; x++)
        for (int y = 0; y < HEIGHT; y++)
            distances[x][y] = 255;

    std::queue<std::pair<int, int>> q;
    for (auto const& target : targets) {
        // Only seed targets that have actually been visited
        if (visited[target.first][target.second]) {
            distances[target.first][target.second] = 0;
            q.push(target);
        }
    }

    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        int d = distances[x][y];

        // North — only expand if neighbor was actually visited
        if (y < HEIGHT-1 && visited[x][y+1] &&
            !(wall_map[x][y] & 1) && distances[x][y+1] == 255)
            { distances[x][y+1] = d+1; q.push({x, y+1}); }
        // East
        if (x < WIDTH-1 && visited[x+1][y] &&
            !(wall_map[x][y] & 2) && distances[x+1][y] == 255)
            { distances[x+1][y] = d+1; q.push({x+1, y}); }
        // South
        if (y > 0 && visited[x][y-1] &&
            !(wall_map[x][y] & 4) && distances[x][y-1] == 255)
            { distances[x][y-1] = d+1; q.push({x, y-1}); }
        // West
        if (x > 0 && visited[x-1][y] &&
            !(wall_map[x][y] & 8) && distances[x-1][y] == 255)
            { distances[x-1][y] = d+1; q.push({x-1, y}); }
    }
}

// =============================================================================
// FLOOD FILL — FULL (all cells, for SEARCHING navigation)
// =============================================================================

void floodFill(const std::vector<std::pair<int, int>>& targets) {
    for (int x = 0; x < WIDTH; x++)
        for (int y = 0; y < HEIGHT; y++)
            distances[x][y] = 255;

    std::queue<std::pair<int, int>> q;
    for (auto const& target : targets) {
        distances[target.first][target.second] = 0;
        q.push(target);
    }

    while (!q.empty()) {
        auto [x, y] = q.front(); q.pop();
        int d = distances[x][y];

        if (y < HEIGHT-1 && !(wall_map[x][y] & 1) && distances[x][y+1] == 255)
            { distances[x][y+1] = d+1; q.push({x, y+1}); }
        if (x < WIDTH-1  && !(wall_map[x][y] & 2) && distances[x+1][y] == 255)
            { distances[x+1][y] = d+1; q.push({x+1, y}); }
        if (y > 0        && !(wall_map[x][y] & 4) && distances[x][y-1] == 255)
            { distances[x][y-1] = d+1; q.push({x, y-1}); }
        if (x > 0        && !(wall_map[x][y] & 8) && distances[x-1][y] == 255)
            { distances[x-1][y] = d+1; q.push({x-1, y}); }
    }
}

// =============================================================================
// PATH TRACING (shared by return and fast run)
// =============================================================================
// After a flood fill has been run, traces the shortest path from (startX,
// startY) to the nearest goal by following decreasing distance values.
// Respects the visited-only restriction if useVisitedOnly is true.

std::vector<int> tracePath(int startX, int startY, bool useVisitedOnly) {
    std::vector<int> path;

    int dx[] = {0, 1,  0, -1};
    int dy[] = {1, 0, -1,  0};

    int x = startX, y = startY;
    int safetyLimit = WIDTH * HEIGHT;
    int steps = 0;

    while (distances[x][y] != 0 && steps < safetyLimit) {
        int currentDist = distances[x][y];
        bool moved = false;

        for (int dir = 0; dir < 4; dir++) {
            if (wall_map[x][y] & (1 << dir)) continue;

            int nx = x + dx[dir];
            int ny = y + dy[dir];
            if (nx < 0 || nx >= WIDTH || ny < 0 || ny >= HEIGHT) continue;
            if (useVisitedOnly && !visited[nx][ny]) continue;

            if (distances[nx][ny] == currentDist - 1) {
                path.push_back(dir);
                x = nx;
                y = ny;
                moved = true;
                break;
            }
        }

        if (!moved) {
            log("WARNING: Path trace stuck at (" +
                std::to_string(x) + "," + std::to_string(y) + ")");
            path.clear(); // Signal failure by returning empty path
            break;
        }
        steps++;
    }

    return path;
}

// =============================================================================
// BUILD RETURN PATH
// =============================================================================
// Strategy:
//   1. SMART: Try a visited-only flood fill from (0,0). This finds the
//             shortest path home through known territory. Much faster than
//             retracing but still guaranteed safe.
//   2. FALLBACK: If no visited-only path exists, reverse the exploration
//             path. Always works — just longer.

std::vector<int> buildReturnPath(int centerX, int centerY) {

    // --- Attempt 1: Shortest path through visited cells ---
    std::vector<std::pair<int, int>> startGoal = {{0, 0}};
    floodFillVisited(startGoal);

    if (distances[centerX][centerY] != 255) {
        // A valid path through visited cells exists — trace it
        std::vector<int> smartPath = tracePath(centerX, centerY, true);

        if (!smartPath.empty()) {
            log("Return path: smart route. Move count: " +
                std::to_string(smartPath.size()));
            return smartPath;
        }
    }

    // --- Attempt 2: Reverse the exploration path (guaranteed fallback) ---
    log("Smart return failed. Using reversed exploration path as fallback.");
    std::vector<int> fallback;
    fallback.reserve(explorationPath.size());
    for (int i = (int)explorationPath.size() - 1; i >= 0; i--) {
        fallback.push_back((explorationPath[i] + 2) % 4); // Flip direction 180
    }
    log("Return path: fallback retrace. Move count: " +
        std::to_string(fallback.size()));
    return fallback;
}

// =============================================================================
// BUILD FAST PATH
// =============================================================================
// Called once after RETURNING completes. Uses visited-only flood fill to
// find the shortest path from (0,0) to the center through trusted territory.

std::vector<int> buildFastPath(
    const std::vector<std::pair<int, int>>& centerGoal)
{
    floodFillVisited(centerGoal);

    if (distances[0][0] == 255) {
        log("ERROR: No visited-only path from (0,0) to center.");
        return {};
    }

    std::vector<int> path = tracePath(0, 0, true);
    log("Fast path ready. Move count: " + std::to_string(path.size()));
    return path;
}

// =============================================================================
// EXECUTE ONE STEP OF A PRECOMPUTED PATH
// =============================================================================

void executePathStep(const std::vector<int>& path, int index) {
    int nextDir = path[index];
    while (heading != nextDir) {
        if ((nextDir - heading + 4) % 4 == 3) turnLeft();
        else turnRight();
    }
    moveForward();
}

// =============================================================================
// SEARCHING MOVEMENT
// =============================================================================

void moveToBestNeighbor() {
    int bestDir  = -1;
    int minScore = 10000;

    int dx[] = {0, 1,  0, -1};
    int dy[] = {1, 0, -1,  0};

    for (int dir = 0; dir < 4; dir++) {
        if (wall_map[current_x][current_y] & (1 << dir)) continue;

        int nx = current_x + dx[dir];
        int ny = current_y + dy[dir];
        if (nx < 0 || nx >= WIDTH || ny < 0 || ny >= HEIGHT) continue;

        int score = distances[nx][ny] * 10;
        if (dir != heading) score += 1;
        if (score < minScore) { minScore = score; bestDir = dir; }
    }

    if (bestDir != -1) {
        while (heading != bestDir) {
            if ((bestDir - heading + 4) % 4 == 3) turnLeft();
            else turnRight();
        }
        moveForward();
    }
}

// =============================================================================
// MAIN
// =============================================================================

int main() {

    // -------------------------------------------------------------------------
    // INITIALIZATION
    // -------------------------------------------------------------------------
    for (int i = 0; i < WIDTH; i++)
        for (int j = 0; j < HEIGHT; j++) {
            visited[i][j]  = false;
            wall_map[i][j] = 0;
        }

    visited[0][0] = true;
    API::setColor(0, 0, 'G');

    // -------------------------------------------------------------------------
    // REGISTER KNOWN BOUNDARY WALLS
    // -------------------------------------------------------------------------
    setWall(0, 0, 2); // South boundary
    setWall(0, 0, 3); // West boundary

    // -------------------------------------------------------------------------
    // DETECT INITIAL HEADING
    // -------------------------------------------------------------------------
    if (!API::wallFront()) {
        log("Open passage: Front. Heading: North.");
    } else if (!API::wallRight()) {
        turnRight();
        log("Open passage: Right. Heading: East.");
    } else if (!API::wallLeft()) {
        turnLeft();
        log("Open passage: Left. Heading: West.");
    } else {
        log("ERROR: No open passage detected at start. Check sensor setup.");
    }

    setWall(0, 0, (heading + 2) % 4);

    // -------------------------------------------------------------------------
    // GOAL DEFINITIONS
    // -------------------------------------------------------------------------
    std::vector<std::pair<int, int>> centerGoal = {{4,4}, {4,5}, {5,4}, {5,5}};

    int returnPathIndex = 0;
    int fastPathIndex   = 0;

    // -------------------------------------------------------------------------
    // MAIN LOOP
    // -------------------------------------------------------------------------

    while (currentState != FINISHED) {

        // --- RETURNING: execute precomputed return path ---
        if (currentState == RETURNING) {

            if (returnPathIndex >= (int)returnPath.size()) {
                // Finished return path — should be at (0,0)
                log("Back at Start. Building fast path...");
                API::setColor(0, 0, 'R');

                fastPath      = buildFastPath(centerGoal);
                fastPathIndex = 0;
                currentState  = FAST_RUN;
                log("Commencing FAST RUN...");
                continue;
            }

            executePathStep(returnPath, returnPathIndex++);
            continue;
        }

        // --- FAST RUN: execute optimal precomputed path ---
        if (currentState == FAST_RUN) {

            if (fastPathIndex >= (int)fastPath.size()) {
                log("Fast Run Complete. Mission Successful.");
                currentState = FINISHED;
                break;
            }

            executePathStep(fastPath, fastPathIndex++);

            // Stop as soon as we enter any center cell
            for (auto const& cell : centerGoal) {
                if (current_x == cell.first && current_y == cell.second) {
                    log("Fast Run Complete. Mission Successful.");
                    currentState = FINISHED;
                    break;
                }
            }

            continue;
        }

        // --- SEARCHING: sensor-based flood fill navigation ---

        updateWalls();
        floodFill(centerGoal);
        updateAllMazeText();

        if (distances[current_x][current_y] == 0) {
            log("Center Reached! Building return path...");
            API::setColor(current_x, current_y, 'B');

            // Build return path — tries smart shortest route first,
            // falls back to reversed exploration if needed
            returnPath      = buildReturnPath(current_x, current_y);
            returnPathIndex = 0;
            currentState    = RETURNING;
            continue;
        }

        moveToBestNeighbor();
    }

    return 0;
}