# Fantasmas v0.3 — GeckoLib (versión de prueba)

Integra las geometrías y texturas de los cuatro fantasmas desde los archivos Blockbench originales. Animaciones `volando` y `golpear` originales para blanco y amarillo; rojo y negro conservan `golpear` y reciben los canales compatibles de `volando` del blanco.

## Dependencias
- Fabric 1.21.1, Fabric API, Java 21 y GeckoLib para Fabric 1.21.1.
- **GeckoLib es obligatorio también en el cliente y en el servidor.**

## Estado de prueba
- **No compilado ni probado en ejecución en este entorno**. Comprueba GitHub Actions antes de instalar.
- Las animaciones de ataque están incluidas como datos, pero todavía no se activan en el controlador: el controlador reproduce vuelo continuamente.
- Las esencias mantienen iconos 2D de momento.
- Los comandos de atravesar/terror todavía son prototipos, sin comportamiento completo.
- Prueba primero en un mundo de pruebas y conserva una copia de seguridad.
