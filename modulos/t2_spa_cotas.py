from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="SPA_COTAS",
        titulo="Análise - SPA de cotas de fundos (secundários)",
        label_upload="Envie o arquivo .docx do SPA de cotas para análise:",
        key_prefix="spa_cotas"
    )
