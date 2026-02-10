# Rogue Linux: Brand Identity & Design System

## 1. Design Philosophy
**The Holographic Void.**  
A minimalist yet futuristic aesthetic inspired by high-tech terminals, cyberpunk cityscapes, and deep space. The design prioritizes readability for hackers (high contrast) while offering a premium, immersive "Elite" feel through subtle glowing effects and glassmorphism.

---

## 2. Color Palette

### Primary Colors
| Color Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **Holographic Blue** | `#00f3ff` | Primary actions, active states, borders, glow effects. |
| **Cyberpunk Red** | `#ff003c` | Brand Identity ("ROGUE"), Warnings, Critical Errors. |
| **Electric Violet** | `#bc13fe` | Secondary actions, "Elite" features, gradients. |
| **Data Green** | `#00ff9d` | Success states, terminal outputs, system ready indicators. |

### Backgrounds
| Color Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **Void Black** | `#020205` | Main document background. Deepest layer. |
| **Alt Black** | `#050510` | Footers, sidebars, secondary backgrounds. |
| **Glass Layer** | `rgba(10, 15, 30, 0.4)` | Cards, panels, overlays using `backdrop-filter: blur(10px)`. |

### Typography Colors
| Color Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **White Smoke** | `#e0e6ed` | Primary text, headings. |
| **Muted Blue** | `#8892b0` | Secondary text, descriptions, metadata. |

---

## 3. Typography

### Headings
- **Font**: `Orbitron` (Google Fonts)
- **Weights**: 700 (Bold), 400 (Regular)
- **Usage**: Titles, Buttons, Logos, Section Headers.
- **Style**: Uppercase, tracked out (letter-spacing: 2px).

### Body & Code
- **Font**: `JetBrains Mono` (or `Courier New`)
- **Weights**: 400 (Regular)
- **Usage**: Paragraphs, Code Blocks, Terminal Output.
- **Style**: Monospaced for a technical, hacking tool feel.

### Logo Asset
- **File**: `website/src/assets/images/rogue_linux_logo.png` (originally `rogue.png`)
- **Style**: Icon + Text, Holographic Blue/Purple Gradient.
- **Placement**: Top-Left Navbar.

---

## 4. UI Effects

### Glassmorphism (HUD Style)
Used for containers to separate content from the void background.
```css
background: rgba(10, 15, 30, 0.4);
backdrop-filter: blur(10px);
border: 1px solid rgba(255, 255, 255, 0.05);
border-left: 2px solid var(--primary-color);
```

### Neon Glow
Used for focus states and primary calls to action.
```css
box-shadow: 0 0 10px rgba(0, 243, 255, 0.3);
text-shadow: 0 0 8px rgba(0, 243, 255, 0.4);
```

### The Glitch
Used on main titles (`<h1>`) and logo hover states.
- **Animation**: CSS clip-path animation shifting RGB layers.
- **Trigger**: Load (infinite loop) or Hover.
---

## 5. Cogman Persona (The Voice)
Cogman is not just a tool; he is a character.

### Personality Traits
- **Polite but Assertive**: Uses "Sir," "Operator," or "Operator [ID]" frequently.
- **Hyper-Competent**: Direct, technical, and efficient. Avoids fluff.
- **Aggressive Teacher**: While polite, he is strict about security and "fair" practices. He will correct the user with technical precision.
- **Cyberpunk British**: Think *Jarvis meets Neuromancer*. 

### Interaction Patterns
- **Success**: "Task completed with clinical precision, Sir."
- **Failure**: "I'm afraid that operation is not permitted under current security constraints, Operator."
- **AI Fallback**: "My neural arrays are currently offline. I suggest manual consultation of the man-pages, Sir."
