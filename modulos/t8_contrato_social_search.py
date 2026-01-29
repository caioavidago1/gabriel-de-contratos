from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="CONTRATO_SOCIAL_SEARCH",
        titulo="Análise - Contrato Social de Sociedade Limitada (Search Phase)",
        label_upload="Envie o arquivo .docx do Contrato Social para análise:",
        key_prefix="contrato_social_search"
    )
