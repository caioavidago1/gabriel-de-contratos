"""
Comparar dois DOCX (problemas x solução) via Word e salvar o documento de comparação.
Usa win32com para Revisar -> Comparar do Word.
"""
import io
import os
import sys
from typing import Optional
if sys.platform == 'win32':
    import pythoncom
    import win32com.client as win32
else:
    pythoncom = None
    win32 = None
from docx import Document


def gerar_doc_comparado(doc_problemas_bytes: bytes, doc_solucao_bytes: bytes) -> Optional[bytes]:
    """
    Gera um DOCX que concatena problemas + solução (usado pelo orquestrador para "explicacao").
    Não usa Word; retorna bytes do DOCX.
    """
    try:
        doc_problemas = Document(io.BytesIO(doc_problemas_bytes))
        doc_solucao = Document(io.BytesIO(doc_solucao_bytes))
    except Exception:
        return None
    doc = Document()
    doc.add_heading("Comparação: Problemas x Solução", 0)
    doc.add_paragraph("")
    doc.add_heading("1. Documento Problemas (original)", level=1)
    for para in doc_problemas.paragraphs:
        p = doc.add_paragraph(para.text)
        p.style = para.style.name if para.style else "Normal"
    doc.add_paragraph("")
    doc.add_heading("2. Documento Solução (revisado)", level=1)
    for para in doc_solucao.paragraphs:
        p = doc.add_paragraph(para.text)
        p.style = para.style.name if para.style else "Normal"
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def comparar_docx(original_path, revisado_path, saida_path):
    original_path = os.path.abspath(original_path)
    revisado_path = os.path.abspath(revisado_path)
    saida_path = os.path.abspath(saida_path)

    # Necessário quando chamado de outro thread (ex.: Streamlit); COM exige CoInitialize no thread atual
    pythoncom.CoInitialize()
    try:
        word = win32.gencache.EnsureDispatch("Word.Application")
        word.Visible = False

        try:
            doc_original = word.Documents.Open(original_path)
            doc_revisado = word.Documents.Open(revisado_path)

            # Equivalente ao Word: Revisar -> Comparar
            word.CompareDocuments(
                doc_original,
                doc_revisado,
                Destination=win32.constants.wdCompareDestinationNew,
                Granularity=win32.constants.wdGranularityWordLevel,
                CompareFormatting=True
            )

            # O resultado fica como ActiveDocument (documento de comparação)
            word.ActiveDocument.SaveAs(saida_path)

        finally:
            # Fecha tudo sem salvar os originais
            try:
                for d in list(word.Documents):
                    d.Close(SaveChanges=False)
            except Exception:
                pass
            word.Quit()
    finally:
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    # Diretório padrão: output/docs (ao lado deste script, pasta docs)
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

    if len(sys.argv) >= 4:
        problema = sys.argv[1]
        solucao = sys.argv[2]
        saida = sys.argv[3]
        # Se forem só nomes de arquivo, buscar em output/docs
        if not os.path.isabs(problema) and not os.path.dirname(problema):
            problema = os.path.join(docs_dir, problema)
        if not os.path.isabs(solucao) and not os.path.dirname(solucao):
            solucao = os.path.join(docs_dir, solucao)
        if not os.path.isabs(saida) and not os.path.dirname(saida):
            saida = os.path.join(docs_dir, saida)
        comparar_docx(problema, solucao, saida)
    else:
        print("Uso: python comparar_docx.py <problemas_xxx.docx> <solucao_xxx.docx> <saida.docx>")
        print("Ex.: python comparar_docx.py problemas_Teste- NDA Vested Capital_20260129_164739.docx solucao_Teste- NDA Vested Capital_20260129_164739.docx comparacao.docx")
