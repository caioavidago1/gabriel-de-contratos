from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="REG_FIDC",
        titulo="Análise - Regulamento de FIDCs (primário)",
        label_upload="Envie o arquivo .docx do Regulamento de FIDC para análise:",
        key_prefix="reg_fidc"
    )
