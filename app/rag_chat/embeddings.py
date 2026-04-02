from langchain_community.embeddings import HuggingFaceEmbeddings

_embeddings = None

def get_embeddings():
    global _embeddings

    if _embeddings is None:
        print("Initializing embedding model ...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
    
    return _embeddings

# emb = get_embeddings()

# vector = emb.embed_query("How to deploy app?") 
# embed_query only converts the raw text into vector. It doesn't store it in vectorDB.
# print(len(vector)) # this was just for test that is the get_embeddings running or not.

