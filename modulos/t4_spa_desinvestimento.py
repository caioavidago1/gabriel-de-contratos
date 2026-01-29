from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="SPA_DESINVESTIMENTO",
        titulo="Análise - SPA de desinvestimento de companhia",
        label_upload="Envie o arquivo .docx do SPA de desinvestimento para análise:",
        key_prefix="spa_desinvestimento"
    )
