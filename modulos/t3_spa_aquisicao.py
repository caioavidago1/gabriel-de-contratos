from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="SPA_AQUISICAO",
        titulo="Análise - SPA de aquisição de companhia",
        label_upload="Envie o arquivo .docx do SPA de aquisição para análise:",
        key_prefix="spa_aquisicao"
    )
