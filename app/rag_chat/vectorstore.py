from langchain_community.vectorstores import Chroma
from app.rag_chat.embeddings import get_embeddings
# from langchain.schema import Document

_vectorstore = None

def get_vectorstore():
    global _vectorstore

    if _vectorstore is None:
        print("Initializing vector store ...")
        _vectorstore = Chroma(
            collection_name = "chat_context",
            embedding_function= get_embeddings(),
            persist_directory = "./chroma_db"
        )

    return _vectorstore
    # return Chroma( # the vector DB instance
    #     collection_name = 'chat_context', # SQL -> Table likewise VectorDB -> collection
    #     embedding_function = get_embeddings(), 
    #     # above ensures query is converted to vector using the selected embeddings model
    #     persist_directory = "./chroma_db"
    #     # persist_directory indicates the data is saved(persist) in disk, also it will create a chroma_db directory in the current directory as "./" is there.
    # )

# vs = get_vectorstore()

# vs.add_documents([
#     Document(
#         page_content = "How to Deploy app?",
#         metadata = {
#             "chat_id" : "1"
#         }
#     )
# ])

# results = vs.similarity_search("deployments", k = 1)

# print(results)