# Fantasmas — proyecto Java inicial (prototipo 0.1)

**No es un mod terminado ni probado.** Código fuente inicial para Minecraft Fabric 1.21.1 / Java 21. El objetivo inmediato es verificar que el proyecto compile con GitHub Actions. No instalar en el servidor principal.

## Contiene
- Registro de cuatro entidades, cuatro huevos y cuatro esencias.
- Comandos `/fantasmas atravesar on|off` y `/fantasmas terror on|off` (interruptores de estado, **todavía no aplican los efectos**).
- IA básica de persecución y movimiento vertical experimental; **NO** navegación 3D completa, ni IA de manada, ni colisiones especiales.
- Drops de esencia del 25%.
- Texturas y sonidos originales, modelos Blockbench guardados en `blockbench_originales/`.
- GitHub Actions para intentar compilar con Gradle.

## Importante
- **No hay renderizadores cliente ni conversión GeckoLib** todavía: las entidades no se verán con sus modelos personalizados. Este proyecto es un primer paso técnico, no una versión jugable final.
- Los sonidos están copiados pero falta conectarlos a las entidades.
- La vida/daño/velocidad aún no están equilibrados por variante.
- El sistema de atravesar paredes, sustos y coordinación están pendientes.
- Las APIs de Minecraft pueden necesitar ajustes tras el primer resultado de GitHub Actions; **compilación no verificada** porque no se ha ejecutado Gradle aquí.
- Requiere Fabric API en el servidor y los clientes. No se ha verificado compatibilidad con Arclight.

## Compilar
1. Crea un repositorio GitHub y sube **el contenido de esta carpeta** (no el ZIP como único archivo).
2. Abre `Actions` → `Compilar Fantasmas` → `Run workflow`.
3. Si falla, comparte el log de `gradle build`; si funciona, descarga el artifact `fantasmas-jar`.
