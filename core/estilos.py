"""Estilos de Luxxon: paleta naranja, azul y gris, y animación de carga con figuras."""

import streamlit as st

CSS = """<style>
:root{--lx-naranja:#F97316;--lx-naranja-osc:#EA580C;--lx-azul:#1D4ED8;--lx-azul-osc:#0F2A5C;--lx-gris:#F4F5F7;--lx-gris-med:#E5E7EB;--lx-gris-osc:#4B5563;}
.stApp{background:var(--lx-gris);}
[data-testid="stHeader"]{background:transparent;}
[data-testid="stStatusWidget"]{display:none !important;}
h1{color:var(--lx-azul-osc) !important;font-weight:800 !important;}
.lx-marca{color:var(--lx-naranja);font-weight:800;font-size:1.1rem;letter-spacing:.35em;text-transform:uppercase;}
[data-testid="stSidebar"]{background:var(--lx-azul-osc);border-right:4px solid var(--lx-naranja);}
[data-testid="stSidebar"] *{color:#F3F4F6;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.25);}
.stButton>button{background:var(--lx-naranja);color:#fff;border:none;border-radius:8px;font-weight:600;}
.stButton>button:hover{background:var(--lx-naranja-osc);color:#fff;}
[data-testid="stChatMessage"]{background:#fff;border:1px solid var(--lx-gris-med);border-left:5px solid var(--lx-naranja);border-radius:10px;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:#EEF3FF;border-left-color:var(--lx-azul);}
.lx-exito{background:#EEF3FF;border-left:5px solid var(--lx-naranja);color:var(--lx-azul-osc);padding:12px 16px;border-radius:8px;font-weight:600;margin:8px 0;}
.lx-cargando{display:flex;align-items:center;gap:14px;padding:4px 0;}
.lx-cargando-texto{color:var(--lx-gris-osc);font-weight:500;}
.lx-formas{position:relative;width:56px;height:56px;flex:none;}
.lx-forma{position:absolute;opacity:0;animation:lx-ciclo 3.5s infinite;}
.lx-circulo{left:6px;top:6px;width:44px;height:44px;border-radius:50%;background:var(--lx-naranja);animation-delay:0s;}
.lx-cuadrado{left:9px;top:9px;width:38px;height:38px;background:var(--lx-azul);animation-delay:.7s;}
.lx-triangulo{left:5px;top:6px;width:46px;height:44px;background:var(--lx-gris-osc);clip-path:polygon(50% 0%,100% 100%,0% 100%);animation-delay:1.4s;}
.lx-rectangulo{left:2px;top:15px;width:52px;height:26px;background:var(--lx-naranja);animation-delay:2.1s;}
.lx-octagrama{left:0;top:0;width:56px;height:56px;background:var(--lx-azul);clip-path:polygon(50% 0%,60.36% 25%,85.36% 14.64%,75% 39.64%,100% 50%,75% 60.36%,85.36% 85.36%,60.36% 75%,50% 100%,39.64% 75%,14.64% 85.36%,25% 60.36%,0% 50%,25% 39.64%,14.64% 14.64%,39.64% 25%);animation-delay:2.8s;}
@keyframes lx-ciclo{0%{opacity:0;transform:scale(.3) rotate(-30deg);}5%{opacity:1;transform:scale(1) rotate(0deg);}17%{opacity:1;transform:scale(1) rotate(0deg);}20%,100%{opacity:0;transform:scale(.3) rotate(30deg);}}
</style>"""

# Sin saltos de línea ni sangrías: el Markdown de Streamlit rompería el bloque HTML.
CARGANDO_HTML = (
    '<div class="lx-cargando"><div class="lx-formas">'
    '<span class="lx-forma lx-circulo"></span>'
    '<span class="lx-forma lx-cuadrado"></span>'
    '<span class="lx-forma lx-triangulo"></span>'
    '<span class="lx-forma lx-rectangulo"></span>'
    '<span class="lx-forma lx-octagrama"></span>'
    "</div>"
    '<span class="lx-cargando-texto">Luxxon está procesando tu solicitud…</span></div>'
)

EXITO_HTML = '<div class="lx-exito">✅ ¡Reserva realizada con éxito!</div>'


def aplicar_estilos() -> None:
    """Inyecta los estilos de Luxxon en la página."""
    st.markdown(CSS, unsafe_allow_html=True)