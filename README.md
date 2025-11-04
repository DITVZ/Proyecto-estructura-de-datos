# Proyecto: Estructura de Datos y Búsqueda de Palabras

Resumen
-------
Proyecto final para la materia "Estructura de Datos y Algoritmos". Implementa un lector de archivos .txt y un sistema de búsquedas de palabras optimizado (exacta, insensible a mayúsculas, prefijo), junto a una versión “mala” para comparación de tiempos.

Estado
------
Código principal: `Boceto.py`  
Entorno de desarrollo: contenedor dev en Ubuntu 24.04.2 LTS  
Lenguaje: Python 3 (compatible con 3.8+)

Requisitos
----------
- Python 3 instalado en el contenedor/host.
- No se usan librerías externas (solo stdlib).
- Archivos .txt disponibles en el directorio de trabajo o indicar ruta completa.

Estructuras y decisiones técnicas
---------------------------------
- Tabla de índices por hash polinómico (implementado desde cero):
  - Hash polinómico con base = 257 y truncado a 64 bits (MASK64).
  - Índices separados para búsqueda case-sensitive (hash de palabra original) y case-insensitive (hash de word.lower()).
  - Ventaja: búsquedas exactas en tiempo aproximadamente O(k + m) donde k es tiempo de hash de la palabra y m es número de ocurrencias retornadas.
  - Desventaja: posibilidad de colisiones (se verifica igualdad de palabra para evitar falsos positivos).

- Trie (árbol prefijo) implementado desde cero:
  - Soporta búsquedas por prefijo de manera eficiente; obtiene los índices de tokens que comparten un prefijo en O(p + r) donde p = longitud del prefijo y r = número de índices retornados.
  - Ventaja: consulta por prefijo rápida y directa.
  - Desventaja: usa memoria adicional (nodos por cada carácter insertado).

- Merkle root (opcional, informativo):
  - Construido sobre los hashes de las palabras para demostrar una raíz compacta del contenido.
  - No se usa para protección criptográfica, es solo demostrativo.

Complejidad (resumen)
---------------------
- Tokenización: O(N) tiempo y O(W) espacio (N = tamaño del texto en caracteres, W = número de palabras).
- Construcción índices (hash + trie): O(W * L) tiempo (L = longitud promedio palabra).
- Búsqueda exacta optimizada: cálculo hash O(L) + acceso al bucket O(occ).
- Búsqueda lineal (“versión mala”): O(W * L) tiempo por consulta.
- Búsqueda por prefijo (trie): O(p + r).

Cómo ejecutar
-------------
Abrir una terminal en el workspace y ejecutar:

    python3 /workspaces/Proyecto-estructura-de-datos/Boceto.py

Flujo:
1. Seleccionar opción 1 para cargar un archivo `.txt` (puedes escribir la ruta o dejar Enter para listar .txt en la carpeta).
2. Usar las demás opciones del menú para realizar búsquedas, estadísticas y comparativas de tiempos.
3. Salir con la opción 8.

Medición de tiempos
-------------------
- Los tiempos de búsqueda se miden con `time.perf_counter()` y se muestran en milisegundos.
- La medición comienza cuando el usuario presiona Enter tras introducir la palabra/prefijo y termina cuando se obtienen los resultados listos para imprimir.

Archivos relevantes
-------------------
- `Boceto.py` — implementación completa (tokenización, índices, trie, menú y medición de tiempos).
- `README.md` — este archivo.
- Cualquier `*.txt` para probar (colocar en el mismo directorio o indicar ruta).

Ejemplo de uso rápido
---------------------
1. Colocar `documento.txt` en el directorio del proyecto.
2. Ejecutar:
   `python3 Boceto.py`
3. Elegir: 1 → seleccionar `documento.txt`
4. Elegir: 3 → buscar palabra sin distinción de mayúsculas (ej: `casa`)
5. Elegir: 4 → buscar prefijo (ej: `pre`)

Buenas prácticas y notas
------------------------
- El hash truncado a 64 bits acelera índices pero no es criptográficamente seguro; siempre se verifica la igualdad de cadenas tras buscar por hash.
- El Trie acumula índices en cada nodo para acelerar la recolección de resultados; esto aumenta el uso de memoria pero reduce tiempos de consulta por prefijo.
- Si el archivo es muy grande (decenas de MB), se recomienda ejecutar en hardware con suficiente RAM o implementar lectura/índices por bloques (posible mejora futura).

Sugerencias para entrega e informe
---------------------------------
- Incluir en el informe: justificación de estructuras (ventajas/desventajas), análisis de complejidad, resultados de comparación de tiempos (ejecutar búsquedas sobre el mismo conjunto de palabras y registrar ms), conclusiones.
- Preparar una demo que muestre: carga del archivo, búsqueda exacta vs versión mala, búsqueda por prefijo y estadísticas.

Contacto y ayuda
----------------
Para abrir documentación DNS u otras páginas desde el contenedor, usar: `"$BROWSER" <url>` (si el host tiene la variable $BROWSER expuesta).

Licencia
--------
Código del proyecto: uso académico. No incluye dependencias externas.
