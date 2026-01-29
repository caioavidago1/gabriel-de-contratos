"""
Comparar dois DOCX (problemas x solução) e salvar o documento de comparação.
Versão multiplataforma com tracked changes NATIVOS.
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


def comparar_docx_libreoffice(original_path, revisado_path, saida_path):
    """
    Compara documentos usando LibreOffice com tracked changes NATIVOS.
    Os tracked changes funcionarão no Microsoft Word.
    """
    try:
        import uno
        from com.sun.star.beans import PropertyValue
        
        # Conectar ao LibreOffice
        local_context = uno.getComponentContext()
        resolver = local_context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_context
        )
        
        # Tentar conectar ao LibreOffice
        try:
            ctx = resolver.resolve(
                "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
            )
        except:
            # Iniciar LibreOffice em background
            import subprocess
            subprocess.Popen([
                'soffice',
                '--headless',
                '--accept=socket,host=localhost,port=2002;urp;',
                '--nofirststartwizard'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            import time
            time.sleep(3)
            ctx = resolver.resolve(
                "uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
            )
        
        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        
        # Converter caminhos para URLs
        def path_to_url(path):
            return uno.systemPathToFileUrl(os.path.abspath(path))
        
        original_url = path_to_url(original_path)
        revisado_url = path_to_url(revisado_path)
        saida_url = path_to_url(saida_path)
        
        # Abrir documento original
        doc_original = desktop.loadComponentFromURL(original_url, "_blank", 0, ())
        
        # Ativar tracked changes
        doc_original.recordChanges = True
        
        # Comparar com documento revisado usando a função nativa do LibreOffice
        doc_original.compareDocuments(revisado_url)
        
        # Salvar com tracked changes no formato Word
        store_props = (
            PropertyValue("FilterName", 0, "MS Word 2007 XML", 0),
            PropertyValue("Overwrite", 0, True, 0),
        )
        doc_original.storeToURL(saida_url, store_props)
        
        # Fechar documento
        doc_original.close(True)
        
        print("✓ Comparação com tracked changes nativos concluída (LibreOffice)")
        return True
        
    except ImportError:
        print("❌ LibreOffice não está instalado ou python3-uno não disponível")
        print("   Instale com: sudo apt-get install libreoffice python3-uno")
        return False
    except Exception as e:
        print(f"❌ Erro ao usar LibreOffice: {e}")
        return False


def comparar_docx(original_path, revisado_path, saida_path):
    """
    Compara dois documentos DOCX com tracked changes NATIVOS.
    - No Windows: usa Microsoft Word
    - No Linux: usa LibreOffice
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
                    print("✓ Comparação com Microsoft Word concluída")
                    return True

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
            print(f"❌ Erro ao usar Word: {e}")
            return False
    
    # Usar LibreOffice no Linux
    else:
        return comparar_docx_libreoffice(original_path, revisado_path, saida_path)


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
            print(f"✓ Arquivo gerado: {saida}")
        else:
            print("❌ Erro na comparação")
    else:
        print("Uso: python comparar_docx.py <problemas_xxx.docx> <solucao_xxx.docx> <saida.docx>")
