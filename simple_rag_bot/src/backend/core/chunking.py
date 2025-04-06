
import uuid
from tqdm import tqdm
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFTextSplitter:
  """Document splitter class for pdf text"""

  def __init__(self, file_uri, chunk_size=1000, chunk_overlap=200):
    """Initialize text splitter with required params"""
    self.file_uri = file_uri
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap
    self.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=self.chunk_size,
        chunk_overlap=self.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        length_function=len
    )

  def _clean_special_chars(self, text: str):
    """Remove special characters/unicodes in the text"""
    cleaned_text = text.replace("\t\n","").replace("\x08\n","").replace("\xa0","").replace("\t\r","").replace("\uf0b7","")

    return cleaned_text

  def get_page_info(self, pdf_path: str):
    """Get full text content of pdf and page info"""
    doc_id = str(uuid.uuid4())
    full_text = ""
    page_info = []

    pdf_doc = fitz.open(pdf_path)

    for page_num in range(pdf_doc.page_count):
      page = pdf_doc[page_num]
      text = page.get_text()
      page_start_idx = len(full_text)
      full_text += text
      page_end_idx = len(full_text)
      page_info.append({
          "doc_id": doc_id,
          "page_id": page_num,
          "page_number": page_num + 1,
          "start_char_idx": page_start_idx,
          "end_char_idx": page_end_idx,
      })
    full_text = self._clean_special_chars(full_text)

    return doc_id, full_text, page_info

  def get_chunks_with_info(self, pdf_uri: str, pdf_text: str, page_info: list, doc_id: str):
    """Split pdf content to chunks and return metadata dict"""
    chunks = []
    text_chunks = self.text_splitter.split_text(pdf_text)

    start_idx = 0
    chunk_positions = []

    # Find the chunk start and end index in the pdf text
    for chunk in tqdm(text_chunks):
      chunk_start = pdf_text.find(chunk, start_idx)
      if chunk_start == -1:
        continue

      chunk_end = chunk_start + len(chunk)
      chunk_positions.append((chunk_start, chunk_end))
      start_idx = chunk_start + 1

    # Identify which pages the chunk falls under, lowest and highest number of the page will be the page span
    for i, (chunk, (start_pos, end_pos)) in enumerate(zip(text_chunks, chunk_positions)):
      spanning_pages = []
      for page in page_info:
        if (start_pos < page["end_char_idx"] and end_pos > page["start_char_idx"]):
          spanning_pages.append(page["page_number"])

      if not spanning_pages:
        continue

      chunk_data = {
          "doc_id": doc_id,
          "chunk_id": f"{doc_id}/chunks/c{i}",
          "content": chunk,
          "page_span": spanning_pages,
          "chunk_metadata": {
              "start_char_idx": start_pos,
              "end_char_idx": end_pos
          },
          "document_metadata": {
              "url": pdf_uri,
              # Since windows uses \ paths instead of /, the logic below is modified
              # "title": pdf_uri.split("/")[-1]
              "title": pdf_uri.split("\\")[-1]
          }
      }

      chunks.append(chunk_data)

    return chunks

  def process_documents(self, file_uri: list=[]):
    """Process documents to chunks"""
    if not file_uri:
      file_uri = self.file_uri

    if not isinstance(file_uri, list):
      file_uri = [file_uri]

    chunked_file_data = []
    for pdf_path in file_uri:
      print(f"Processing {pdf_path}...")
      doc_id, pdf_text, page_info = self.get_page_info(pdf_path)
      chunks_data = self.get_chunks_with_info(pdf_path, pdf_text, page_info, doc_id)
      chunked_file_data.extend(chunks_data)

    print(f"Chunking completed for {pdf_path}.")
    return chunked_file_data
