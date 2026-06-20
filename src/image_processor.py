from PIL import Image
import pytesseract

text = pytesseract.image_to_string(Image.open("/home/smitvyas/Projects/Office/document_processor/case 1-1.png"))
print(text)
