from .comum import render_pagina_analise


def render():
    render_pagina_analise(
        tipo_contrato="ACORDO_COTISTAS_ACQUISITION",
        titulo="Análise - Acordo de Cotistas (Acquisition Phase)",
        label_upload="Envie o arquivo .docx do Acordo de Cotistas para análise:",
        key_prefix="acordo_cotistas_acquisition"
    )
