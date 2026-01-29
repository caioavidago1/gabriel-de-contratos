from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="REG_FIP",
        titulo="Análise - Regulamento de FIPs (primário)",
        label_upload="Envie o arquivo .docx do Regulamento de FIP para análise:",
        key_prefix="reg_fip"
    )
