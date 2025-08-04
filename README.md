<img width="241" height="74" alt="image" src="https://github.com/user-attachments/assets/5dcb4973-419a-4327-9c4b-de4dea8ebef1" />


# Surf-Info-Overlay-by-Cr0mb
A lightweight Windows overlay displaying real-time local player coordinates, velocity, and speed for Counter-Strike 2 (CS2). Designed as a foundation for surf/hack info boxes with smooth draggable GUI.


Here's a practical, clear GitHub README for your surf info overlay script designed for game hacking and Minecraft server use. It highlights purpose, usage, dependencies, and technical notes with a forward-thinking tone:

---

# Surf Info Overlay by Cr0mb

A lightweight Windows overlay displaying real-time local player coordinates, velocity, and speed for **Counter-Strike 2** (CS2). Designed as a foundation for surf/hack info boxes with smooth draggable GUI.

This tool showcases advanced process memory reading and overlay rendering using Python, Win32 APIs, and static offsets — pushing the limits of external game info extraction and rendering techniques.

---

## Features

* Real-time position (X, Y, Z) display
* Velocity vector readout
* Speed (units/sec) calculation and display
* Draggable transparent overlay window
* Efficient Win32 GDI drawing with double buffering
* Uses static offsets for precise memory reading
* Robust process and module handle management

---

## Prerequisites

* Windows 10+

* Python 3.8+

* Dependencies (install via pip):

  ```
  pip install pywin32
  ```

* `Process.offsets` module with your game-specific static offsets (adjust `Offsets.py` accordingly)

---

## Usage

1. Run the script **while CS2 is running** and its main window title is `"Counter-Strike 2"`.
2. A draggable overlay window labeled `"Surf Box"` will appear showing your current coordinates, velocity, and speed.
3. Drag the info box anywhere on the screen with the mouse left button.

---

## How It Works

* Finds CS2 process and retrieves client module base address.
* Reads player pawn address, then position and velocity vectors from memory using static offsets.
* Calculates speed from velocity vector.
* Uses a custom Win32 overlay window with double-buffered GDI drawing for smooth text and shapes.
* Allows moving the overlay with mouse drag events.

---

## Code Structure

* `Vec3`: Ctypes structure for 3D vector data.
* `read_bytes()`: Safe memory reading helper.
* `Overlay` class: Handles Win32 overlay window creation, drawing, font caching, and input handling.
* `main()`: Main loop reading game data and updating the overlay at \~144 FPS.

---

## Customization

* Adjust offsets in `Process/offsets.py` for different game versions.
* Modify overlay size, colors, and font settings inside the `Overlay` class.
* Extend with more game info (e.g., timers, tricks, or stats) by reading additional memory addresses.


---

## Contact

For questions, contributions, or collaboration:
**Discord:** cr0mbleonthegame
