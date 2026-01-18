<table border="0">
  <tr>
    <td valign="center">
      <img src=".assets/images/rat-spinning.gif" width="100">
    </td>
    <td>
      <h1>NRC 2026: Micromouse Competition</h1>
      <blockquote>
        The official SIUE Autonomous Robotics Club GitHub repository for the 2026 NRC Micromouse Competition
      </blockquote>
    </td>
    <td valign="center">
      <img src=".assets/images/siue-arc-logo.jpg" width="100">
    </td>
  </tr>
</table>



[![Competition](https://img.shields.io/badge/Competition-NRC_2026-red)](https://irp.cdn-website.com/9297868f/files/uploaded/NRCContestRules2026.pdf)
[![Platform](https://img.shields.io/badge/Platform-ESP32-blue)](https://randomnerdtutorials.com/getting-started-with-esp32/)
[![Language](https://img.shields.io/badge/Language-C++-green)](https://www.w3schools.com/cpp/default.asp)
[![License](https://img.shields.io/badge/Danger-!!!-purple)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)



---

## 📌 Project Overview
Our team is developing an autonomous "Mouse" to compete in the **National Robotics Challenge**. The robot must navigate a $10 \times 10$ unit square maze, mapping the environment in real-time to find the fastest path to the center.

### 📐 Competition Constraints (NRC Rules)
**Some Basics:**
* **Mouse Size:** Max $7" \times 7" \times 7"$.
* **Maze Size:** $10 \times 10$ of $10" \times 10"$ tiles.
* **Time:** 10-minute total run time.
* **Autonomy:** No external communication once the maze layout is disclosed.
* **Scoring:** Based on a factor of things but overall shortest time wins.

<details>
<summary><b>Click for more extensive rules</b></summary>

**Maze Criteria:**
* No inaccessible locations
* Mouse will always start in one of the four corners
* Exactly three starting walls
* Only one entrance to the center, , multiple paths to the destination square are allowed and are to be expected
* Has a hollow center, i.e., the center peg has no walls attached to it
* Has walls attached to every peg except the center peg
* Is unsolvable by a wall-following robot 
**Time Criteria:**
* If a robot re-enters the start square before entering the destination square on a run that run is aborted and a new run will begin with a new time that starts when the starting square is exited.
* The robot may, after reaching the destination square, continue to navigate the maze for as long
as their total maze time allows. The time taken will not count toward any run.
* The minimum run time shall be the robot's official time (Dash Attempt).
</ul>
</details>
 

<p align="center">
  <img src=".assets/images/NRC_maze_example.png" width="600">
</p> 

> *Example maze provided in 2026 NRC Contest Manual.*
---

## 📂 Repository Structure

| Icon | Folder | Purpose |
| :--- | :--- | :--- |
| 🧠 | [`/algorithms`](./algorithms) | Maze-solving logic (Flood Fill, DFS). |
| 🔌 | [`/firmware`](./firmware) | ESP32 source code & PID control. |
| 🏗️ | [`/hardware`](./hardware) | CAD & PCB Schematics. |
| 📊 | [`/simulations`](./simulations) | Logic testing environments. |
| 📋 | [`/doc`](./doc) | NRC Rules & Engineering Notebook. |
| 🪟 | **[OneDrive Hub]** | [**Click here for OneDrive**](https://siuecougars-my.sharepoint.com/:f:/r/personal/ngarmon_siue_edu/Documents/ARC/Micro%20Mouse?csf=1&web=1&e=Olx0Ui) |

---

## 🛠️ Tech Stack
* **Microcontroller:** ESP32.
* **Sensors:** To Be Determined.
* **Actuators:** To Be Determined.
* **Design:** Custom 3D printed chassis.

---

## 🧠 Navigation Progress
We are currently iterating on two main logic paths:

-  **Flood Fill:** - Works by "pouring water" from the goal to the start, assigning distance values to cells. The mouse then moves toward lower-value cells, effectively calculating the shortest path. ([**Video explanation**](https://www.youtube.com/watch?v=ktn3C7aXVR0))
-  **Depth Search:** - Explores as far as possible along each branch before backtracking. It is "blind" to the shortest path until it has explored all options.

---

## 🏁 Development Setup

<details>
<summary><b>Click to expand: Software Installation</b></summary>

1. **Install VS Code**
2. **Install PlatformIO Extension** (for ESP32 development).
3. **Clone the Repo:**
   ```bash 
   git clone [https://github.com/](https://github.com/)[your-username]/[your-repo-name].git
</ul>
</details>

---

## 📈 Recent Progress

<table border="0">
  <tr>
    <td width="50%" align="center">
      <img src=".assets/images/mazev1.png" width="100%">
    </td>
    <td width="50%" align="center">
      <img src=".assets/images/mouse-running.gif" width="100%">
      </img>
    </td>
  </tr>
  <tr>
    <td align="center">
      <i>Visualization of the <b>Flood Fill Algorithm</b> mapping the 10x10 maze.</i>
    </td>
    <td align="center">
      <i>Mouse running the course with <b>preliminary navigation logic</b>.</i>
    </td>
  </tr>
</table>

 > *Maze provided is also a work in progress.*
---
