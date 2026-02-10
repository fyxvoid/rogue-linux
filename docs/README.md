# Rogue Linux Documentation

Welcome to the official documentation for **Rogue Linux** and the **Cogman** build system.

## 📚 Documentation Structure

- [📐 Architecture](./architecture/)
Technical deep dives into the core systems.
- **[System Design](./architecture/ARCHITECTURE.md)**: Kernel, Init System, and Userland structure.
- **[AI Advisor](./architecture/ai_architecture.md)**: Model selection and Training pipeline.
- **[Data Flow](./architecture/DATA-FLOW.md)**: Immutable data transformation.
- **[Failure Model](./architecture/FAILURE-MODEL.md)**: How Cogman handles errors.
- **[Determinism](./architecture/DETERMINISM.md)**: Reproducible build strategies.
- **[AI Boundaries](./architecture/AI-BOUNDARIES.md)**: System safety and interaction limits.
- **[RootFS Contract](./architecture/ROOTFS-CONTRACT.md)**: Interface between package manager and filesystem.

### [🛠️ Implementation](./implementation/)
Details on the specific implementation of Cogman and its components.
- **[Execution Engine](./implementation/EXECUTION.md)**: How build plans are executed.
- **[Package Lifecycle](./implementation/PACKAGE-LIFECYCLE.md)**: From source to binary.
- **[Metadata](./implementation/METADATA.md)**: `package.toml` schema and parsing.
- **[Logging](./implementation/LOGGING.md)**: The "Butler" persona logging system.

### [🚀 Project & Meta](./project/)
High-level project information, history, and status.
- **[Final Wrap-up Report](./project/FINAL_REPORT.md)**: Executive summary of achievements.
- **[History & Evolution](./project/HISTORY.md)**: The journey from LFS to Cyberpunk.
- **[Cogman Identity](./project/COGMAN-IDENTITY.md)**: Defining the AI persona.

### [🎨 Design](./design/)
Visual identity and user experience guidelines.
- **[Brand Identity](./design/brand_identity.md)**: Color palettes (Holographic Blue/Red), Typography, and Persona Voice.
- **[Website SSG](./design/website_ssg.md)**: How the custom Static Site Generator and Fragments work.

### [📖 Guides](./guides/)
Hands-on instructions for operators and developers.
- **[Installation Variants](./guides/INSTALL-VARIANTS.md)**: Different ways to deploy Rogue Linux.
- **[Testing](./guides/TESTING.md)**: Verification strategies.
- **[Benchmarking](./guides/BENCHMARKING.md)**: Performance metrics.

### [⚖️ Decisions (ADR)](./adr/)
Architectural Decision Records. The "Why" behind our technical choices.
- **[001: Python-based Static Site Generation](./adr/001_python_ssg.md)**
- **[002: Fragment-based Web Architecture](./adr/002_web_fragments.md)**
- **[003: Cyberpunk Brand Identity](./adr/003_brand_identity.md)**

## 🚀 Getting Started
1. Read the **[Final Wrap-up Report](./project/FINAL_REPORT.md)** for a project overview.
2. Check **[Architecture](./architecture/ARCHITECTURE.md)** for system internals.
3. Consult **[Guides](./guides/)** to start building packages.
