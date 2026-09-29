# Conversor de AFND a AFD

Aplicación web hecha con Streamlit que convierte un autómata finito no determinista (AFND) en un autómata finito determinista (AFD) equivalente, usando el método de construcción de subconjuntos. Muestra las tablas de transiciones y los gráficos de ambos autómatas.

## Requisitos

- Python 3.9 o superior
- La librería `streamlit` (versión reciente)
- Conexión a internet al usar el programa (los gráficos cargan la librería vis-network desde la red)

## Instalación

```bash
pip install streamlit
```

## Ejecución

Desde la carpeta donde está el archivo, ejecuta:

```bash
streamlit run afnd_a_afd.py
```

Se abrirá el navegador con la aplicación. Si no se abre, entra a `http://localhost:8501`.

## Cómo usarlo

1. **Panel izquierdo (Configuración):**
   - Escribe el alfabeto separado por comas, por ejemplo `a,b`.
   - Escribe los estados separados por comas, por ejemplo `q0,q1,q2`.
   - Elige el estado inicial.
   - Elige uno o varios estados de aceptación.
2. **Tabla de transiciones del AFND:** en cada celda elige, con el desplegable, uno o varios estados destino. Si dejas la celda vacía, no hay transición.
3. **Gráfico del AFND:** se dibuja automáticamente con lo que llenaste.
4. **AFD equivalente:** debajo aparecen la tabla y el gráfico del AFD, que se actualizan solos cada vez que cambias algo.

## Cómo leer los gráficos

- **Flecha de entrada:** marca el estado inicial.
- **Doble círculo:** estado de aceptación.
- **Borde punteado (Ø):** estado muerto, al que se llega cuando no existe transición.
- **Etiquetas en las flechas:** símbolos del alfabeto. Si dos símbolos van al mismo destino, se muestran juntos, por ejemplo `a, b`.

En las tablas, `→` indica el estado inicial y `*` los estados de aceptación.

## Controles de los gráficos

- Arrastra un nodo para acomodarlo.
- Usa la rueda del mouse para acercar o alejar.
- Haz doble clic en el fondo del gráfico para volver a centrarlo.

## Ejemplo

Datos de entrada:

- Alfabeto: `a,b`
- Estados: `q0,q1,q2` (inicial `q0`, aceptación `q2`)
- `q0` con `a` va a `q0, q1`
- `q1` con `b` va a `q2`

Resultado (AFD):

| Estado      | a         | b         |
|-------------|-----------|-----------|
| → {q0}      | {q0, q1}  | Ø         |
| {q0, q1}    | {q0, q1}  | {q2}      |
| * {q2}      | Ø         | Ø         |
| Ø           | Ø         | Ø         |

## Archivos

- `afnd_a_afd.py`: código de la aplicación.
