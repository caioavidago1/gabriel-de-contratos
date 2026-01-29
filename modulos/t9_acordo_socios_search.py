from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="ACORDO_SOCIOS_SEARCH",
        titulo="Análise - Acordo de Sócios (Search Phase)",
        label_upload="Envie o arquivo .docx do Acordo de Sócios para análise:",
        key_prefix="acordo_socios_search"
    )
