# 🐭 NRC 2026: Micromouse Challenge
> **Official Repository for the Robotics Club Maze-Solving Project**

![Competition](https://img.shields.io/badge/Competition-NRC_2026-red)
![Platform](https://img.shields.io/badge/Platform-ESP32-blue)
![Language](https://img.shields.io/badge/Language-C++-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Project Overview
Our team is developing an autonomous "Mouse" to compete in the **National Robotics Challenge**. The robot must navigate a $10 \times 10$ unit square maze, mapping the environment in real-time to find the fastest path to the center.

### ⚖️ Competition Constraints (NRC Rules)
* **Size:** Max $7" \times 7" \times 7"$.
* **Time:** 10-minute total run time.
* **Autonomy:** No external communication once the maze layout is disclosed.
* **Scoring:** Based on the fastest run + search time penalties.

---

## 📂 Repository Structure

| Icon | Folder | Purpose |
| :--- | :--- | :--- |
| 🧠 | [`/algorithms`](./algorithms) | Maze-solving logic (Flood Fill, DFS). |
| 🔌 | [`/firmware`](./firmware) | ESP32 source code & PID control. |
| 🏗️ | [`/hardware`](./hardware) | Fusion 360 CAD & PCB Schematics. |
| 📊 | [`/simulations`](./simulations) | Logic testing environments. |
| 📋 | [`/doc`](./doc) | NRC Rules & Engineering Notebook. |

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