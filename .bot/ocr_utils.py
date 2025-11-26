# Core OCR utilities
import pytesseract
import pyautogui


# Adicione esta linha para apontar para a instalação do Tesseract
# Verifique se este é o caminho correto no seu PC após a instalação
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_text_from_screen(region=None):
    """
    Captura uma screenshot da região especificada e extrai o texto usando OCR.
    Se nenhuma região for especificada, captura a tela inteira.
    """
    try:
        screenshot = pyautogui.screenshot(region=region)
        # Adicionado 'por' para português
        text = pytesseract.image_to_string(screenshot, lang='por')
        return text
    except pytesseract.TesseractNotFoundError:
        print("Erro: Tesseract não encontrado. Verifique a instalação e o caminho em 'ocr_utils.py'.")
        return ""  # Retorna string vazia para não quebrar o loop principal
    except Exception as e:
        print(f"Erro inesperado no OCR: {e}")
        return "" 
