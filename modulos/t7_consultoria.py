from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="CONSULTORIA_SIDE_LETTER",
        titulo="Análise - Contrato de Consultoria/Side Letter",
        label_upload="Envie o arquivo .docx do Contrato de Consultoria/Side Letter para análise:",
        key_prefix="consultoria"
    )
