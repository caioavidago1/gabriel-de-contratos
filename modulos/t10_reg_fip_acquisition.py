from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="REG_FIP_ACQUISITION",
        titulo="Análise - Regulamento de FIP (Acquisition Phase)",
        label_upload="Envie o arquivo .docx do Regulamento de FIP para análise:",
        key_prefix="reg_fip_acquisition"
    )
