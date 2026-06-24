---
name: r2u-install-plantuml
description: Install the local PlantUML runtime. Use when the user asks to install, prepare, or configure PlantUML, or when Java, Graphviz, and the PlantUML JAR are needed for local rendering of .puml, .plantuml, or UML diagrams.
---

## Instructions

- Check whether Java is installed in the current environment.
- If Java is missing, run the bundled installer script to install Java.
- Check whether Graphviz is installed in the current environment.
- If Graphviz is missing, run the bundled installer script to install Graphviz.
- Before downloading PlantUML, check whether `<R2U_PLUGIN_ROOT>/skills/r2u-install-plantuml/assets/plantuml.jar` already exists.
- If the target JAR already exists, skip the download.
- If the target JAR is missing, download the latest PlantUML JAR from the official PlantUML download page and place it at `<R2U_PLUGIN_ROOT>/skills/r2u-install-plantuml/assets/plantuml.jar`.

## Command

Run this from the workspace:

```bash
python3 <R2U_PLUGIN_ROOT>/skills/r2u-install-plantuml/scripts/r2u_install_plantuml.py
```

If `python3` is unavailable, use any available Python interpreter for the same script.

## Verification

After installation, run:

```bash
java -jar <R2U_PLUGIN_ROOT>/skills/r2u-install-plantuml/assets/plantuml.jar -version
dot -V
```

Both commands must succeed before reporting that the PlantUML runtime is ready.

## Constraints

- Prefer the latest GPL compiled JAR URL parsed from the official PlantUML download page: `https://plantuml.com/download`.
- Fall back to `https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar` only when the official page cannot be read or parsed.
- Java or Graphviz installation may require admin rights, a package manager, and network access. If installation fails, report the script output and the manual install command suggestion.
- Do not place the PlantUML JAR in any other directory; the target is fixed to `<R2U_PLUGIN_ROOT>/skills/r2u-install-plantuml/assets/plantuml.jar`.

