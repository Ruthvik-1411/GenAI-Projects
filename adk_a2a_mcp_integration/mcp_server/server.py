import os
import logging
import tempfile
import requests
import arxiv
import pymupdf4llm
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("ArxivExplorer")

@mcp.tool
def search_arxiv(query: str, max_results: int = 5) -> dict:
   """
   Searches arXiv for a given query and returns the top papers.
   Args:
       query: The search keyword or query.
       max_results: The maximum number of results to return.
   Returns:
       A list of dictionaries, where each dictionary represents a paper
       and contains its ID, title, summary, authors, and PDF URL.
   """
   try:
       search = arxiv.Search(
           query=query,
           max_results=max_results,
           sort_by=arxiv.SortCriterion.Relevance
       )

       papers = []
       for result in search.results():
           logger.info(f"{result.title}")
           paper_info = {
               'id': result.get_short_id(),
               'title': result.title,
               'summary': result.summary,
               'authors': [author.name for author in result.authors],
               'pdf_url': result.pdf_url
           }
           papers.append(paper_info)

       return {
           "status": "success",
           "result": papers
       }
   except Exception as e:
       return {
           "status": "error",
           "error_message": str(e)
       }

@mcp.tool()
def get_paper_md(paper_id: str) -> dict:
   """
   Retrieves the text content of an arXiv paper in Markdown format.
   Args:
       paper_id: The ID of the paper (e.g., '1706.03762v7').
   Returns:
       The text content of the paper as a Markdown string.
       Returns an error message if any step fails.
   """
   try:
       search = arxiv.Search(id_list=[paper_id])
       paper = next(search.results())
       pdf_url = paper.pdf_url
       logger.info(f"Found paper: '{paper.title}'")
       logger.info(f"Downloading from: {pdf_url}")

   except StopIteration:
       return {"status": "error", "error_message": f"Paper with ID '{paper_id}' not found on arXiv."}
   except Exception as e:
       return {"status": "error", "error_message": f"Error searching for the paper: {e}"}

   try:
       # Download the PDF content
       response = requests.get(pdf_url)
       response.raise_for_status()
       pdf_bytes = response.content
       logger.info("PDF downloaded successfully.")

   except requests.exceptions.RequestException as e:
       return {"status": "error", "error_message": f"Error downloading the PDF file, request failure: {e}"}
   except Exception as e:
       return {"status": "error", "error_message": f"Error downloading the PDF file: {e}"}

   temp_pdf_path = None
   try:
       with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
           temp_file.write(pdf_bytes)
           temp_pdf_path = temp_file.name # Get the path of the temporary file
      
       logger.info(f"PDF content written to temporary file: {temp_pdf_path}")
       logger.info("Converting PDF to Markdown...")
       # Pass the file path to the conversion function
       md_text = pymupdf4llm.to_markdown(temp_pdf_path)
      
       logger.info("Conversion complete.")
       if temp_pdf_path and os.path.exists(temp_pdf_path):
           os.remove(temp_pdf_path)
           logger.info(f"Temporary file {temp_pdf_path} deleted.")
       return {"status": "success", "result": md_text}

   except Exception as e:
       return {"status": "error", "error_message": f"Error converting PDF to Markdown: {e}"}

# To pass the paper directly as media to llm, to be used later
# @mcp.tool()
# def get_paper_raw(paper_id: str) -> dict:
#    """
#    Retrieves the raw PDF file of an arXiv paper.
#    Args:
#        paper_id: The ID of the paper (e.g., '1706.03762v7').
#    Returns:
#        The raw bytes of the PDF file, or None if the paper is not found.
#    """
#    try:
#        # Search for the paper by its ID
#        search = arxiv.Search(id_list=[paper_id])
#        paper = next(search.results())

#        # Download the PDF content
#        response = requests.get(paper.pdf_url)
#        response.raise_for_status()
#        return {
#            "status": "success",
#            "result":response.content
#        }
#    except StopIteration:
#        return {"status": "error", "error_message": f"Paper with ID {paper_id} not found on arXiv."}
#    except requests.exceptions.RequestException as e:
#        logger.info(f"Error downloading PDF: {e}")
#        return {"status": "error", "error_message": f"Error downloading PDF: {e}"}
#    except Exception as e:
#        logger.info(f"Error: {e}")
#        return {"status": "error", "error_message": f"Error: {e}"}

if __name__ == "__main__":
   mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
