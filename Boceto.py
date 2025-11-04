# ...Lo hizo githup copilot entonces duden...
import os
import glob
import time
import sys

MASK64 = (1 << 64) - 1
BASE = 257

def elegir_archivo_txt():
    prompt = "Introduce la ruta o nombre de un archivo .txt (o pulsa Enter para listar .txt en la carpeta actual): "
    ruta = input(prompt).strip()
    if ruta:
        return ruta
    archivos = sorted(glob.glob("*.txt"))
    if not archivos:
        print("No se encontraron archivos .txt en el directorio actual.")
        return None
    print("Archivos .txt encontrados:")
    for i, f in enumerate(archivos, 1):
        print(f"{i}: {f}")
    while True:
        elec = input("Elige un archivo por número (o 'q' para cancelar): ").strip()
        if elec.lower() in ("q", "quit", "exit"):
            return None
        if elec.isdigit() and 1 <= int(elec) <= len(archivos):
            return archivos[int(elec) - 1]
        print("Elección inválida, inténtalo de nuevo.")

def leer_archivo_texto(ruta):
    try:
        with open(ruta, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        print("Archivo no encontrado:", ruta)
    except IsADirectoryError:
        print("La ruta es un directorio:", ruta)
    except PermissionError:
        print("Permiso denegado al leer el archivo:", ruta)
    except Exception as e:
        print("Error al leer el archivo:", e)
    return None

def word_hash(s: str) -> int:
    """Hash polinómico sencillo con truncamiento a 64 bits."""
    h = 0
    for ch in s:
        h = ((h * BASE) + ord(ch)) & MASK64
    return h

def tokenize(text: str):
    """
    Tokeniza texto en palabras (secuencias alfanuméricas).
    Devuelve lista ordenada de tokens con forma:
    {'word_orig': original, 'word': lowercase, 'start': offset, 'line': linea}
    """
    tokens = []
    cur = []
    start = 0
    line = 1
    i = 0
    while i < len(text):
        c = text[i]
        if c.isalnum():
            if not cur:
                start = i
            cur.append(c)
        else:
            if cur:
                w_orig = ''.join(cur)
                w = w_orig.lower()
                tokens.append({'word_orig': w_orig, 'word': w, 'start': start, 'line': line})
                cur = []
            if c == '\n':
                line += 1
        i += 1
    if cur:
        w_orig = ''.join(cur)
        w = w_orig.lower()
        tokens.append({'word_orig': w_orig, 'word': w, 'start': start, 'line': line})
    return tokens

# Trie simple para búsquedas por prefijo (case-insensitive, usa palabras en minúsculas)
class TrieNode:
    def __init__(self):
        self.children = {}
        self.indices = []  # índices de tokens donde aparece la palabra que termina aquí (o pasa por aquí)

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, index):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            node.indices.append(index)
        # también almacenamos en el último nodo (redundante por índice acumulado)

    def find_prefix_indices(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return node.indices[:]  # copio la lista

def build_index_and_trie(tokens):
    """
    Construye:
    - hashes: lista de hashes (basado en palabra lowercase) para Merkle
    - index_by_hash_ci: hash(lower) -> list(indices)  (case-insensitive index)
    - index_by_hash_cs: hash(original) -> list(indices)  (case-sensitive index, original exact)
    - trie: para prefijos (lowercase)
    """
    hashes = []
    index_by_hash_ci = {}
    index_by_hash_cs = {}
    trie = Trie()
    for idx, t in enumerate(tokens):
        h_ci = word_hash(t['word'])
        h_cs = word_hash(t['word_orig'])
        hashes.append(h_ci)
        index_by_hash_ci.setdefault(h_ci, []).append(idx)
        index_by_hash_cs.setdefault(h_cs, []).append(idx)
        # insertar en trie para búsqueda por prefijo (lowercase)
        trie.insert(t['word'], idx)
    return hashes, index_by_hash_ci, index_by_hash_cs, trie

def build_merkle_root(hashes):
    """
    Merkle simple: combina hashes de hojas hasta la raíz re-hasheando la concat de hex.
    """
    if not hashes:
        return 0
    level = hashes[:]
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i+1]
            combined = word_hash(hex(left) + hex(right))
            next_level.append(combined)
        level = next_level
    return level[0]

def buscar_palabra_con_hash_cs(palabra, tokens, index_by_hash_cs):
    """Búsqueda optimizada case-sensitive (exacta)."""
    h = word_hash(palabra)
    posiciones = index_by_hash_cs.get(h, [])
    resultados = []
    for pos in posiciones:
        if tokens[pos]['word_orig'] == palabra:
            resultados.append((pos, tokens[pos]['line'], tokens[pos]['start']))
    return resultados

def buscar_palabra_con_hash_ci(palabra, tokens, index_by_hash_ci):
    """Búsqueda optimizada case-insensitive (exacta)."""
    palabra_l = palabra.lower()
    h = word_hash(palabra_l)
    posiciones = index_by_hash_ci.get(h, [])
    resultados = []
    for pos in posiciones:
        if tokens[pos]['word'] == palabra_l:
            resultados.append((pos, tokens[pos]['line'], tokens[pos]['start']))
    return resultados

def buscar_palabra_mala_cs(palabra, tokens):
    """Versión mala (lineal) case-sensitive exacta."""
    resultados = []
    for idx, t in enumerate(tokens):
        if t['word_orig'] == palabra:
            resultados.append((idx, t['line'], t['start']))
    return resultados

def buscar_palabra_mala_ci(palabra, tokens):
    """Versión mala (lineal) case-insensitive exacta."""
    pl = palabra.lower()
    resultados = []
    for idx, t in enumerate(tokens):
        if t['word'] == pl:
            resultados.append((idx, t['line'], t['start']))
    return resultados

def prefijo_buscar(prefix, tokens, trie):
    """Busca palabras por prefijo (case-insensitive). Devuelve set de palabras encontradas y sus indices ordenados."""
    p = prefix.lower()
    indices = trie.find_prefix_indices(p)
    if not indices:
        return [], []
    # obtener palabras únicas en orden de aparición
    seen = {}
    ordered_indices = []
    for idx in indices:
        w = tokens[idx]['word']
        if w not in seen:
            seen[w] = []
        seen[w].append(idx)
    unique_words = list(seen.keys())
    # para primera y última palabra encontrada según aparición: buscar min/max index por palabra
    # devolver palabras y para cada palabra su primera línea (min index)
    return unique_words, seen

def tiempo_milisegundos(func, *args, **kwargs):
    t0 = time.perf_counter()
    res = func(*args, **kwargs)
    t1 = time.perf_counter()
    ms = (t1 - t0) * 1000.0
    return res, ms

def print_occurrences_summary(results):
    if not results:
        print("No se encontraron ocurrencias.")
        return
    count = len(results)
    first = results[0]
    last = results[-1]
    print(f"Cantidad de apariciones: {count}")
    print(f"Primera ocurrencia: línea {first[1]} (offset {first[2]})")
    print(f"Última ocurrencia: línea {last[1]} (offset {last[2]})")

def menu():
    print("\n--- Menú Principal ---")
    print("1. Cargar Archivo")
    print("2. Búsqueda Exacta (sensible a mayúsculas)")
    print("3. Búsqueda Simple (no sensible a mayúsculas)")
    print("4. Búsqueda por Prefijo")
    print("5. Estadísticas del Archivo")
    print("6. Buscar palabra NoX")
    print("7. Análisis Comparativo de Búsqueda (optimizada vs mala)")
    print("8. Salir")

def main():
    archivo_cargado = False
    tokens = []
    hashes = []
    index_ci = {}
    index_cs = {}
    trie = None
    merkle_root = 0
    ruta = None

    while True:
        menu()
        opcion = input("Elige una opción: ").strip()
        if opcion == '1':
            ruta_sel = elegir_archivo_txt()
            if not ruta_sel:
                continue
            contenido = leer_archivo_texto(ruta_sel)
            if contenido is None:
                continue
            tokens = tokenize(contenido)
            hashes, index_ci, index_cs, trie = build_index_and_trie(tokens)
            merkle_root = build_merkle_root(hashes)
            archivo_cargado = True
            ruta = ruta_sel
            print(f"Archivo '{ruta}' cargado. Tokens: {len(tokens)}. Raíz Merkle: {hex(merkle_root)}")
        elif opcion == '2':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            palabra = input("Introduce la palabra exacta (sensible a mayúsculas): ").strip()
            if not palabra:
                print("Entrada vacía.")
                continue
            # optimizada
            results_opt, ms_opt = tiempo_milisegundos(buscar_palabra_con_hash_cs, palabra, tokens, index_cs)
            # ordenar por índice
            results_opt.sort(key=lambda x: x[0])
            print(f"\n[Optimizada] Tiempo: {ms_opt:.3f} ms")
            print_occurrences_summary(results_opt)
        elif opcion == '3':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            palabra = input("Introduce la palabra (no sensible a mayúsculas): ").strip()
            if not palabra:
                print("Entrada vacía.")
                continue
            results_opt, ms_opt = tiempo_milisegundos(buscar_palabra_con_hash_ci, palabra, tokens, index_ci)
            results_opt.sort(key=lambda x: x[0])
            print(f"\n[Optimizada CI] Tiempo: {ms_opt:.3f} ms")
            print_occurrences_summary(results_opt)
        elif opcion == '4':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            prefix = input("Introduce el prefijo (no sensible a mayúsculas): ").strip()
            if not prefix:
                print("Entrada vacía.")
                continue
            # medir tiempo de búsqueda por prefijo
            (words, mapping), ms_pref = tiempo_milisegundos(lambda p, t: (prefijo_buscar(p, t, trie)), prefix, tokens)
            # prefijo_buscar devolvió (unique_words, seen) por diseño -- corregir llamado
            unique_words, seen = words, mapping if isinstance(mapping, dict) else (words, mapping)
            # la llamada anterior es adaptada: prefijo_buscar devuelve (unique_words, seen)
            # compute first/last word by first occurrence index
            if not unique_words:
                print(f"No se encontraron palabras con prefijo '{prefix}'. Tiempo {ms_pref:.3f} ms")
                continue
            # ordenar unique_words por la primera aparición (min index)
            word_first_idx = []
            for w in unique_words:
                idxs = seen[w]
                word_first_idx.append((min(idxs), w))
            word_first_idx.sort()
            first_word = word_first_idx[0][1]
            last_word = word_first_idx[-1][1]
            first_line = tokens[seen[first_word][0]]['line']
            last_line = tokens[seen[last_word][-1]]['line']
            print(f"Tiempo: {ms_pref:.3f} ms")
            print(f"Palabras encontradas ({len(unique_words)}): {', '.join(unique_words[:20])}{'...' if len(unique_words)>20 else ''}")
            print(f"Primera palabra que cumple prefijo: '{first_word}' en línea {first_line}")
            print(f"Última palabra que cumple prefijo: '{last_word}' en línea {last_line}")
        elif opcion == '5':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            total = len(tokens)
            if total == 0:
                print("El archivo no contiene palabras.")
                continue
            primera = tokens[0]['word_orig']
            ultima = tokens[-1]['word_orig']
            # palabra "del medio" según regla: si no es entero, tomar siguiente
            mitad = (total + 1) // 2  # 1-based index of middle, rounding up
            palabra_mitad = tokens[mitad - 1]['word_orig']
            print(f"Total de palabras: {total}")
            print(f"Palabra No1: {primera}")
            print(f"Palabra No{total}: {ultima}")
            print(f"Palabra No{mitad} (mitad): {palabra_mitad}")
        elif opcion == '6':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            num = input("Introduce el número (1-based) de la palabra a buscar: ").strip()
            if not num.isdigit():
                print("Número inválido.")
                continue
            idx = int(num)
            total = len(tokens)
            if idx < 1 or idx > total:
                print(f"Número fuera de rango. El archivo tiene {total} palabras.")
                continue
            # tiempo de acceso (muy rápido, pero se mide)
            def acceso(n):
                return tokens[n-1]
            (tok,), ms = tiempo_milisegundos(lambda n: (acceso(n),), idx)
            token = tok
            print(f"Palabra No{idx}: '{token['word_orig']}' (línea {token['line']}, offset {token['start']}) -- Tiempo {ms:.3f} ms")
        elif opcion == '7':
            if not archivo_cargado:
                print("Primero debes cargar un archivo (opción 1).")
                continue
            palabra = input("Introduce la palabra exacta para comparar (sensible a mayúsculas): ").strip()
            if not palabra:
                print("Entrada vacía.")
                continue
            # optimizada (hash cs)
            res_opt, ms_opt = tiempo_milisegundos(buscar_palabra_con_hash_cs, palabra, tokens, index_cs)
            res_opt.sort(key=lambda x: x[0])
            # mala (lineal)
            res_bad, ms_bad = tiempo_milisegundos(buscar_palabra_mala_cs, palabra, tokens)
            res_bad.sort(key=lambda x: x[0])
            print("\n--- Resultado Optimizada ---")
            print(f"Tiempo: {ms_opt:.3f} ms")
            print_occurrences_summary(res_opt)
            print("\n--- Resultado Versión Mala ---")
            print(f"Tiempo: {ms_bad:.3f} ms")
            print_occurrences_summary(res_bad)
            diff = ms_bad - ms_opt
            print(f"\nDiferencia (mala - optimizada): {diff:.3f} ms")
        elif opcion == '8':
            print("Saliendo. Fin del programa.")
            break
        else:
            print("Opción inválida. Intenta de nuevo.")

if __name__ == "__main__":
    main()