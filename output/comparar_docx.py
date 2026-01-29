"""
Comparar dois DOCX (problemas x solução) e salvar o documento de comparação.
Versão multiplataforma usando Python-Redlines.
"""
import io
import os
import sys
from typing import Optional

# Importações condicionais apenas para Windows
if sys.platform == 'win32':
    import pythoncom
    import win32com.client as win32
else:
    pythoncom = None
    win32 = None

from docx import Document

# Importar biblioteca de comparação multiplataforma
try:
    from redlines import Redlines
    REDLINES_DISPONIVEL = True
except ImportError:
    REDLINES_DISPONIVEL = False
    print("Aviso: biblioteca 'redlines' não instalada. Funcionalidade de comparação limitada.")


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


def comparar_docx_redlines(original_path, revisado_path, saida_path):
    """
    Compara dois documentos DOCX usando Python-Redlines (multiplataforma).
    Gera um documento com tracked changes igual ao Word.
    """
    if not REDLINES_DISPONIVEL:
        raise ImportError("Biblioteca 'redlines' não instalada. Execute: pip install redlines")
    
    try:
        # Ler os documentos como texto
        doc_original = Document(original_path)
        doc_revisado = Document(revisado_path)
        
        # Extrair texto completo
        texto_original = '\n'.join([para.text for para in doc_original.paragraphs])
        texto_revisado = '\n'.join([para.text for para in doc_revisado.paragraphs])
        
        # Criar comparação com tracked changes
        redline = Redlines(texto_original, texto_revisado)
        resultado_html = redline.output_markdown  # ou output_html
        
        # Criar documento de saída com as mudanças marcadas
        doc_saida = Document()
        doc_saida.add_heading("Documento Comparado - Track Changes", 0)
        
        # Processar o resultado e adicionar ao documento
        # (simplificado - você pode melhorar o parsing)
        for linha in resultado_html.split('\n'):
            doc_saida.add_paragraph(linha)
        
        doc_saida.save(saida_path)
        return True
        
    except Exception as e:
        print(f"Erro ao comparar documentos: {e}")
        return False


def comparar_docx(original_path, revisado_path, saida_path):
    """
    Compara dois documentos DOCX.
    - No Windows: usa Word se disponível
    - No Linux: usa Python-Redlines
    """
    original_path = os.path.abspath(original_path)
    revisado_path = os.path.abspath(revisado_path)
    saida_path = os.path.abspath(saida_path)
    
    # Tentar usar Word no Windows
    if sys.platform == 'win32' and pythoncom is not None and win32 is not None:
        try:
            pythoncom.CoInitialize()
            try:
                word = win32.gencache.EnsureDispatch("Word.Application")
                word.Visible = False

                try:
                    doc_original = word.Documents.Open(original_path)
                    doc_revisado = word.Documents.Open(revisado_path)

                    word.CompareDocuments(
                        doc_original,
                        doc_revisado,
                        Destination=win32.constants.wdCompareDestinationNew,
                        Granularity=win32.constants.wdGranularityWordLevel,
                        CompareFormatting=True
                    )

                    word.ActiveDocument.SaveAs(saida_path)

                finally:
                    try:
                        for d in list(word.Documents):
                            d.Close(SaveChanges=False)
                    except Exception:
                        pass
                    word.Quit()
            finally:
                pythoncom.CoUninitialize()
            return True
        except Exception as e:
            print(f"Erro ao usar Word: {e}. Tentando método alternativo...")
    
    # Usar Python-Redlines como fallback
    return comparar_docx_redlines(original_path, revisado_path, saida_path)


if __name__ == "__main__":
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

    if len(sys.argv) >= 4:
        problema = sys.argv[1]
        solucao = sys.argv[2]
        saida = sys.argv[3]
        
        if not os.path.isabs(problema) and not os.path.dirname(problema):
            problema = os.path.join(docs_dir, problema)
        if not os.path.isabs(solucao) and not os.path.dirname(solucao):
            solucao = os.path.join(docs_dir, solucao)
        if not os.path.isabs(saida) and not os.path.dirname(saida):
            saida = os.path.join(docs_dir, saida)
        
        if comparar_docx(problema, solucao, saida):
            print(f"Comparação concluída: {saida}")
        else:
            print("Erro na comparação")
    else:
        print("Uso: python comparar_docx.py <problemas_xxx.docx> <solucao_xxx.docx> <saida.docx>")
