from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="NDA",
        titulo="Análise - NDA",
        label_upload="Envie o arquivo .docx do NDA para análise:",
        key_prefix="nda"
    )