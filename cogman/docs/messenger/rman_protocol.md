# Messenger & RMAN: The Tactical HUD

The Messenger and the **Rogue Manager (RMAN)** protocol provide the visual and communicative layer of Cogman. It is designed to look like a high-end tactical display for security operators.

## 📟 The RMAN Protocol (v2.0)

RMAN is a sequence of **Tactical Identifiers** that transform raw terminal output into structured signals.

| Ident | Tactical Meaning | Terminal Representation |
| :--- | :--- | :--- |
| **!** | **Metadata Event** | `[!] SYSTEM: ...` (Holographic blue) |
| **#** | **Phase Header** | `▐ PHASE: ... ▌` (Inverse blue) |
| **>** | **Active Execution** | `▶ EXEC: ...` (White) |
| **?** | **Tactical Alert** | `[?] ALERT: ...` (Cyberpunk red) |
| **\*** | **Procedural Item** | ` • ...` (Grey) |

## 📡 IPC Architecture

The Messenger handles communication between the detached build components:

1.  **Unix Domain Sockets**: High-speed, low-latency communication between processes on the same machine.
2.  **TLV Messaging**: (Type-Length-Value) ensures that messages are easily parsed by C (low-level HUD) and Rust (high-level logic).
3.  **Real-Time Rendering**: The HUD is updated as the Executor processes steps, providing immediate feedback on compilation progress.

## 🎨 Design System: The Holographic Void

The UI is built on a specific "Cyberpunk Terminal" aesthetic:
-   **Holographic Blue (`#00f3ff`)**: System-level information.
-   **Cyberpunk Red (`#ff003c`)**: Critical failures and security alerts.
-   **JetBrains Mono**: The chosen typeface for high-speed technical reading.

## 🛠️ Contributor Note: Adding HUD Features

If you want to add a new alert type:
1.  Define a new ASCII identifier in `rman.h`.
2.  Add a handler in `messenger/log_formatter.c` to assign it a color and icon.
3.  Implement the output macro in `executor/log/log.h`.
