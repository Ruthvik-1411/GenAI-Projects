"""Modules for retriever client"""
import time
from pymilvus import MilvusClient

class CustomMilvusClient:
	"""Custom class for Milvus Client to create, update and query a milvus collection"""
	def __init__(self, uri: str):
		self.uri = uri
		self.milvus_client = MilvusClient(uri=self.uri)

	def create_collection(self, collection_name: str="", embedding_dimension: int=0,
					   vector_field_name: str="", primary_field_name: str="",
					   max_id_length: int=50):
		"""Create collection with given fields into milvus vector db"""
		if self.milvus_client.has_collection(collection_name):
			print(f"Collection with {collection_name} already exists. \
		  Over writing existing collection.")
			self.milvus_client.drop_collection(collection_name)

		try:
			self.milvus_client.create_collection(collection_name=collection_name,
												dimension=embedding_dimension,
												vector_field_name=vector_field_name,
												metric_type="COSINE",
												primary_field_name=primary_field_name,
												id_type="string",
												max_length=max_id_length)
			print(f"Collection '{collection_name}' successfully created.")
		except Exception as e:
			print(e)

	def insert_data_to_collection(self, collection_name: str, data: list):
		"""Insert data into created collection in milvus db"""
		if self.milvus_client.has_collection(collection_name):
			self.milvus_client.insert(collection_name=collection_name,
								data=data)
			print(f"Data successfully inserted to collection '{collection_name}'.")
		else:
			raise ValueError(f"Collection with name '{collection_name}' does not exist. Please \
					insert into another or create a new collection using .create_collection.")

	def query_collection(self, collection_name: str, query_embedding: list,
					  limit: int, output_fields: list):
		"""Get relevant docs based on similarity between query embedding and vectors in DB"""
		start_time = time.time()
		if self.milvus_client.has_collection(collection_name):
			retriever_result = self.milvus_client.search(collection_name=collection_name,
												data=[query_embedding],
												limit=limit,
												output_fields=output_fields)
			end_time = time.time()
			execution_time = end_time - start_time
			print(f"Retrieved in {execution_time:.6f}s.")
			return retriever_result
		
		end_time = time.time()
		execution_time = end_time - start_time
		print(f"Error retrieving results: {execution_time:.6f}s.")
		raise ValueError(f"Collection with {collection_name} does not exist. Please query \
				on another collection or create a new collection using .create_collection.")
