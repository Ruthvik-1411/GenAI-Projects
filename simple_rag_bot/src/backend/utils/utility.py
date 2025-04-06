import os
from os import listdir
from os.path import isfile, join
import json

def get_files_in_dir(path):
  """Get complete path of the pdf files in dir"""
  files_list = []
  curr_dir = os.getcwd()
  for file in listdir(path):
    file_path = join(path, file)
    if file_path.endswith(".pdf") and isfile(file_path):
      absolute_file_path = os.path.join(curr_dir, file_path)
      files_list.append(absolute_file_path)

  return files_list

def save_embeddings(embeddings_data, path):
  
  try:
    with open(path, 'w') as outfile:
      for entry in embeddings_data:
          json.dump(entry, outfile)
          outfile.write('\n')
    
    return True
  except Exception as e:
    print(f"Unable to save embeddings data due to {e}.")
    return False

def load_embeddings(path):
  """Load embeddings from jsonl file"""
  with open(path, 'r') as json_file:
    json_data = [json.loads(line) for line in json_file]

  return json_data