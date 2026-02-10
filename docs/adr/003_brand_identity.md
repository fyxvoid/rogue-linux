# ADR 003: Cyberpunk Brand Identity

## Context
Linux distributions often have generic or overly corporate branding. Rogue Linux caters to a niche audience: pentesters, hackers, and privacy extremists. The brand needed to reflect this "Elite" status.

## Decision
We adopted a **"Holographic Void" Cyberpunk aesthetic**.
-   **Colors**: Deep Black (`#020205`) background with Neon Blue (`#00f3ff`) and Red (`#ff003c`) accents.
-   **Typography**: `Orbitron` for headers (futuristic) and `JetBrains Mono` for content (technical).
-   **UI Style**: Glassmorphism (HUD effect) and Glitch animations.

## Consequences
### Positive
-   **Differentiation**: Instantly recognizable against competitors like Kali or Parrot.
-   **Immersion**: The UI feels like a tool from a sci-fi movie, enhancing the user's feeling of being an "operator."

### Negative
-   **Accessibility**: High contrast neon on black can be straining; careful color balancing is required.
-   **Performance**: Glassmorphism filters (`backdrop-filter`) can be GPU intensive on very low-end hardware.

## Status
ACCEPTED
