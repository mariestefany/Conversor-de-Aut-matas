import html
import json
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# CONSTANTES Y ESTILO
# ==========================================
ESTADO_VACIO = "Ø"

COLORES = {
    "inicial":    {"bg": "#CDE7F7", "borde": "#7FB6DD"},   # celeste
    "normal":     {"bg": "#E4D9F6", "borde": "#B29DDB"},   # lila
    "aceptacion": {"bg": "#F9D3E3", "borde": "#E68DB4"},   # rosado
    "muerto":     {"bg": "#ADF3DB", "borde": "#2EDDA3"},   # verde menta
}

CSS = """
<style>
    #MainMenu, footer, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
    [data-testid="stToolbarActions"], [data-testid="stDecoration"],
    [data-testid="InputInstructions"] { display: none !important; }

    [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display: flex !important; visibility: visible !important; }

    .stApp { background: linear-gradient(160deg, #F6F1FC 0%, #EEF6FC 55%, #FCF0F6 100%); }
    header[data-testid="stHeader"] { background: transparent !important; box-shadow: none !important; }
    .block-container { padding-top: 2rem !important; }
    section[data-testid="stSidebar"] { background: #EFE8FA; }

    .cabecera {
        padding: 1.5rem 2rem; border-radius: 20px; margin-bottom: 1.4rem;
        background: linear-gradient(120deg, #ADF3DB 100%);
    }
    .cabecera h1 { margin: 0; font-size: 2rem; color: #3B3057; }
    .cabecera p  { margin: .3rem 0 0; color: #5A4D7A; }

    h2, h3 { color: #3B3057 !important; }

    .leyenda span {
        display: inline-block; padding: .25rem .9rem; margin: 0 .5rem .5rem 0;
        border-radius: 999px; font-size: .85rem; color: #3B3057; border: 1.5px solid;
    }

    .cab-tabla, .celda-estado {
        padding: .5rem .9rem; border-radius: 12px; font-weight: 600; color: #3B3057;
    }
    .cab-tabla { background: #DCCFF3; margin-bottom: .8rem; }

    span[data-baseweb="tag"] { background-color: #DCCFF3 !important; color: #3B3057 !important; }
    span[data-baseweb="tag"] * { color: #3B3057 !important; }
    div[data-baseweb="select"] > div { background: #FFFFFF; border: 1px solid #DCCFF3; }

    table.tabla { width: 100%; border-collapse: separate; border-spacing: 0; overflow: hidden;
                  border-radius: 14px; border: 1px solid #DCCFF3; background: #fff; }
    table.tabla th { background: #DCCFF3; color: #3B3057; padding: .65rem 1rem; text-align: left; }
    table.tabla td { padding: .6rem 1rem; color: #3B3057; border-top: 1px solid #EEE7F8; }
    table.tabla tr:nth-child(even) td { background: #FAF7FE; }
    table.tabla td.est { font-weight: 600; }
    table.tabla td.vacio { color: #9A90B0; }
</style>
"""


# ==========================================
# 1. LÓGICA: AFND -> AFD (construcción de subconjuntos)
# ==========================================
def conversion_afnd_a_afd(alfabeto, trans_afnd, inicial_afnd, aceptacion_afnd):
    inicial = frozenset([inicial_afnd])
    vistos = {inicial}
    cola = [inicial]
    trans = {}
    aceptacion = set()

    while cola:
        actual = cola.pop(0)
        trans[actual] = {}
        if actual & aceptacion_afnd:
            aceptacion.add(actual)

        for simbolo in alfabeto:
            destino = set()
            for e in actual:
                destino |= trans_afnd.get(e, {}).get(simbolo, set())
            destino = frozenset(destino)
            trans[actual][simbolo] = destino
            if destino not in vistos:
                vistos.add(destino)
                cola.append(destino)

    return trans, inicial, aceptacion


def nombre_conjunto(conjunto):
    if not conjunto:
        return ESTADO_VACIO
    return "{" + ", ".join(sorted(conjunto)) + "}"


def tipo_de(estado, nombre, inicial, aceptacion):
    if nombre(estado) == ESTADO_VACIO:
        return "muerto"
    if estado == inicial:
        return "inicial"
    if estado in aceptacion:
        return "aceptacion"
    return "normal"


# ==========================================
# 2. GRÁFICO (vis-network; no usa pyvis ni paquetes extra de Python)
#    Convención: flecha de entrada al inicial y doble círculo en aceptación
# ==========================================
def svg_nodo(texto, tipo, doble):
    c = COLORES[tipo]
    n = max(len(texto), 1)
    fs = min(26, 68 / (0.6 * n))
    dash = ' stroke-dasharray="9 7"' if tipo == "muerto" else ""
    anillo = (f'<circle cx="50" cy="50" r="37" fill="none" stroke="{c["borde"]}" stroke-width="3"/>'
              if doble else "")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<circle cx="50" cy="50" r="48" fill="{c["bg"]}"/>'
        f'<circle cx="50" cy="50" r="46" fill="none" stroke="{c["borde"]}" stroke-width="4"{dash}/>'
        f'{anillo}'
        f'<text x="50" y="50" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Segoe UI, Arial, sans-serif" font-weight="600" font-size="{fs:.1f}" '
        f'fill="#3B3057">{html.escape(texto)}</text></svg>'
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def dibujar_automata(estados, aristas_raw, inicial, aceptacion, nombre=str, altura=460):
    """aristas_raw: lista de (origen, simbolo, destino)."""
    nodos = []
    radio_inicial = 28
    for e in estados:
        texto = nombre(e)
        radio = max(28, int(3.4 * len(texto)) + 20)
        if e == inicial:
            radio_inicial = radio
        nodos.append({
            "id": texto, "shape": "circularImage", "size": radio, "borderWidth": 0,
            "image": svg_nodo(texto, tipo_de(e, nombre, inicial, aceptacion), e in aceptacion),
        })

    # Une los símbolos con igual origen y destino: "a, b"
    agrupadas = {}
    for o, s, d in aristas_raw:
        agrupadas.setdefault((nombre(o), nombre(d)), []).append(s)

    aristas = [
        {"from": o, "to": d, "label": ", ".join(ss),
         "arrows": {"to": {"enabled": True, "scaleFactor": 0.7}},
         "color": {"color": "#9C8BB8", "highlight": "#5A4D7A"},
         "font": {"size": 15, "color": "#3B3057", "strokeWidth": 4, "strokeColor": "#FAF6FD"},
         "smooth": {"type": "curvedCW", "roundness": 0.22}}
        for (o, d), ss in agrupadas.items()
    ]

    opciones = {
        "physics": {"barnesHut": {"gravitationalConstant": -5000, "springLength": 170,
                                  "springConstant": 0.03}},
        "interaction": {"dragNodes": True, "zoomView": True, "zoomSpeed": 0.4},
    }

    pagina = f"""
    <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
    <div id="g" style="height:{altura - 10}px;border-radius:18px;background:#FAF6FD;
         border:1px solid #E6DAF3;"></div>
    <script>
      const INI = {json.dumps(nombre(inicial))}, R = {radio_inicial};
      const nodes = new vis.DataSet({json.dumps(nodos)});
      const edges = new vis.DataSet({json.dumps(aristas)});
      const net = new vis.Network(document.getElementById('g'), {{nodes, edges}}, {json.dumps(opciones)});

      let listo = false;
      function congelar() {{
        if (listo) return;
        listo = true;
        net.setOptions({{physics: false}});
        net.fit();
        net.moveTo({{scale: net.getScale() * 0.85}});
      }}
      net.once('stabilizationIterationsDone', congelar);
      setTimeout(congelar, 3000);

      // Límites de zoom: evita que el gráfico se achique hasta desaparecer
      net.on('zoom', () => {{
        const s = net.getScale();
        if (s < 0.35) net.moveTo({{scale: 0.35}});
        else if (s > 2.5) net.moveTo({{scale: 2.5}});
      }});

      // Doble clic en el fondo: vuelve a centrar todo el gráfico
      net.on('doubleClick', () => net.fit());

      // Flecha de entrada al estado inicial
      net.on('afterDrawing', ctx => {{
        const p = net.getPositions([INI])[INI];
        if (!p) return;
        const x1 = p.x - R - 3, x0 = x1 - 46;
        ctx.save();
        ctx.strokeStyle = ctx.fillStyle = '#7B6BA8';
        ctx.lineWidth = 2.4;
        ctx.beginPath(); ctx.moveTo(x0, p.y); ctx.lineTo(x1 - 9, p.y); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x1, p.y); ctx.lineTo(x1 - 12, p.y - 6.5);
        ctx.lineTo(x1 - 12, p.y + 6.5); ctx.closePath(); ctx.fill();
        ctx.restore();
      }});
    </script>
    """
    components.html(pagina, height=altura)


# ==========================================
# 3. TABLA HTML A COLOR
# ==========================================
def tabla_html(encabezados, filas):
    """filas: lista de (tipo, [celdas]); la primera celda es el estado."""
    cab = "".join(f"<th>{html.escape(h)}</th>" for h in encabezados)
    cuerpo = ""
    for tipo, celdas in filas:
        c = COLORES[tipo]
        primera = (f'<td class="est" style="background:{c["bg"]};border-left:6px solid {c["borde"]}">'
                   f"{html.escape(celdas[0])}</td>")
        resto = "".join(
            f'<td class="{"vacio" if x == ESTADO_VACIO else ""}">{html.escape(x)}</td>'
            for x in celdas[1:]
        )
        cuerpo += f"<tr>{primera}{resto}</tr>"
    return f'<table class="tabla"><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table>'


def leyenda_html():
    items = [("inicial", "Estado inicial (flecha de entrada)"), ("normal", "Estado normal"),
             ("aceptacion", "Estado de aceptación (doble círculo)"), ("muerto", "Estado muerto Ø")]
    chips = "".join(
        f'<span style="background:{COLORES[k]["bg"]};border-color:{COLORES[k]["borde"]}">{t}</span>'
        for k, t in items
    )
    return f'<div class="leyenda">{chips}</div>'


# ==========================================
# 4. INTERFAZ
# ==========================================
st.set_page_config(page_title="Conversor de AFND a AFD", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)
st.markdown(
    '<div class="cabecera"><h1>Conversor de AFND a AFD</h1>'
    "<p>Método de construcción de subconjuntos. Puedes arrastrar los nodos de los gráficos.</p></div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuración")
    alfabeto_txt = st.text_input("Alfabeto (separado por comas)", "a,b")
    estados_txt = st.text_input("Estados (separados por comas)", "q0,q1,q2")

    alfabeto = list(dict.fromkeys(x.strip() for x in alfabeto_txt.split(",") if x.strip()))
    estados = list(dict.fromkeys(x.strip() for x in estados_txt.split(",") if x.strip()))

    estado_inicial = st.selectbox("Estado inicial", estados) if estados else None
    estados_aceptacion = st.multiselect(
        "Estados de aceptación", estados, default=[estados[-1]] if estados else []
    )

if not (estados and alfabeto):
    st.info("Define los estados y el alfabeto en el panel izquierdo para comenzar.")
    st.stop()

aceptacion_afnd = set(estados_aceptacion)

# ---------- Tabla de transiciones (desplegables) ----------
st.header("Tabla de transiciones del AFND")
st.caption("En cada celda elige uno o varios estados destino. Si la dejas vacía, no hay transición.")

sufijo = abs(hash((tuple(estados), tuple(alfabeto))))
anchos = [1.2] + [2] * len(alfabeto)

cab = st.columns(anchos)
cab[0].markdown('<div class="cab-tabla">Estado</div>', unsafe_allow_html=True)
for j, s in enumerate(alfabeto):
    cab[j + 1].markdown(f'<div class="cab-tabla">Con «{html.escape(s)}»</div>', unsafe_allow_html=True)

trans_afnd = {e: {} for e in estados}
for e in estados:
    fila = st.columns(anchos)
    t = tipo_de(e, str, estado_inicial, aceptacion_afnd)
    c = COLORES[t]
    marca = ("→ " if e == estado_inicial else "") + ("* " if e in aceptacion_afnd else "")
    fila[0].markdown(
        f'<div class="celda-estado" style="background:{c["bg"]};border-left:6px solid {c["borde"]}">'
        f"{marca}{html.escape(e)}</div>",
        unsafe_allow_html=True,
    )
    for j, s in enumerate(alfabeto):
        elegidos = fila[j + 1].multiselect(
            f"{e} con {s}", estados, key=f"t_{sufijo}_{e}_{s}",
            placeholder="Sin transición", label_visibility="collapsed",
        )
        if elegidos:
            trans_afnd[e][s] = set(elegidos)

st.caption("→ estado inicial   ·   * estado de aceptación")

# ---------- Gráfico del AFND ----------
st.header("Gráfico del AFND")
st.markdown(leyenda_html(), unsafe_allow_html=True)
aristas_afnd = [(o, s, d) for o, caminos in trans_afnd.items()
                for s, destinos in caminos.items() for d in sorted(destinos)]
dibujar_automata(estados, aristas_afnd, estado_inicial, aceptacion_afnd)

# ---------- Resultado: AFD ----------
st.header("AFD equivalente")
trans_afd, ini_afd, acep_afd = conversion_afnd_a_afd(
    alfabeto, trans_afnd, estado_inicial, aceptacion_afnd
)

filas = []
for origen, caminos in trans_afd.items():
    marca = ("→ " if origen == ini_afd else "") + ("* " if origen in acep_afd else "")
    celdas = [marca + nombre_conjunto(origen)] + [nombre_conjunto(caminos[s]) for s in alfabeto]
    filas.append((tipo_de(origen, nombre_conjunto, ini_afd, acep_afd), celdas))

st.subheader("Tabla de transiciones del AFD")
st.markdown(tabla_html(["Estado"] + [f"Con «{s}»" for s in alfabeto], filas), unsafe_allow_html=True)

st.subheader("Gráfico del AFD")
aristas_afd = [(o, s, d) for o, caminos in trans_afd.items() for s, d in caminos.items()]
dibujar_automata(list(trans_afd.keys()), aristas_afd, ini_afd, acep_afd, nombre=nombre_conjunto)