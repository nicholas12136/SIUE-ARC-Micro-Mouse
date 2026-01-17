#  NRC 2026: Micromouse Challenge   
> **The official SIUE Automous Robotics Club Github repostiory for the 2026 NRC Micromouse Competition**

[![Competition](https://img.shields.io/badge/Competition-NRC_2026-red)](https://irp.cdn-website.com/9297868f/files/uploaded/NRCContestRules2026.pdf)
[![Platform](https://img.shields.io/badge/Platform-ESP32-blue)](https://randomnerdtutorials.com/getting-started-with-esp32/)
[![Language](https://img.shields.io/badge/Language-C++-green)](https://www.w3schools.com/cpp/default.asp)
[![License](https://img.shields.io/badge/Danger-!!!-purple)](https://www.youtube.com/watch?v=dQw4w9WgXcQ)

<p align="center">
  <img src="/.assets/images/rat-spinning.gif" width="50">
</p>

---

## 📌 Project Overview
Our team is developing an autonomous "Mouse" to compete in the **National Robotics Challenge**. The robot must navigate a $10 \times 10$ unit square maze, mapping the environment in real-time to find the fastest path to the center.

### ⚖️ Competition Constraints (NRC Rules)
* **Mouse Size:** Max $7" \times 7" \times 7"$.
* **Maze Size:** $10 \times 10$ of $10" \times 10"$ tiles.
* **Time:** 10-minute total run time.
* **Autonomy:** No external communication once the maze layout is disclosed.
* **Scoring:** Based on the fastest run + search time penalties.
* **Wall Hugging:** It is explicitly mentioned in the rules that steps will be taken to diminish this searching algorithm. 
* **Staring Place:** Mouse will always start in one of the four corners.
* **Finish Line:** Goal is to end up in the four-tile room int the middle.

![Micromouse Design Diagram](./.assets/images/NRC_maze_example.png)
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
| ☁️ | **[OneDrive Hub]** | [**Click here for OneDrive**](https://siuecougars-my.sharepoint.com/:f:/r/personal/ngarmon_siue_edu/Documents/ARC/Micro%20Mouse?csf=1&web=1&e=Olx0Ui) |

---

## 🛠️ Tech Stack
* **Microcontroller:** ESP32.
* **Sensors:** To Be Determined.
* **Actuators:** To Be Determined.
* **Design:** Custom 3D printed chassis.

---

## 🧠 Navigation Progress
We are currently iterating on two main logic paths:

-  **Flood Fill:** - Works by "pouring water" from the goal to the start, assigning distance values to cells. The mouse then moves toward lower-value cells, effectively calculating the shortest path.
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