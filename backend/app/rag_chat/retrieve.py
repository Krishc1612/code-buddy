from app.rag_chat.vectorstore import get_vectorstore


def retrieve_similar_chunks (query: str, chat_id: str, k: int = 3):
    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search(
        query,
        k=k,
        filter={"chat_id": chat_id}
    )

    sorted_results = sorted( # sorting the results we just got back with respect to time
        results, 
        key = lambda x : x.metadata["created_at"]
    )

    return [
        {
            "user_msg_id": doc.metadata["user_msg_id"],
            "assistant_msg_id" : doc.metadata["assistant_msg_id"],
            "created_at": doc.metadata["created_at"],
            "chat_id" : chat_id
        }
        for doc in sorted_results
    ]

# the "k" here is very important parameter, it determines the return the top k results of the search.