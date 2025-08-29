import tiktoken
import PyPDF2

def load_file(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return "".join(page.extract_text() or "" for page in reader.pages)
        
    
report = load_file("reportPDFS/nvidia_10k.pdf")
enc = tiktoken.encoding_for_model("gpt-4o")

print(len(enc.encode(report)))