from langchain.schema import Document
from app.rag_chat.vectorstore import get_vectorstore
from app.schemas.messages import MessageResponse


def ingest_chunk(
        user_msg : MessageResponse,
        assistant_msg : MessageResponse, 
        chat_id : str
    ):
    vectorstore = get_vectorstore()

    doc = Document(
        page_content = f"<USER>{user_msg.content}<USER><ASSISTANT>{assistant_msg.content}<ASSISTANT>",
        metadata={
            "user_msg_id": str(user_msg.id),
            "assistant_msg_id" : str(assistant_msg.id),
            "chat_id": chat_id,
            "created_at" : user_msg.created_at.isoformat()
        }
    )

    vectorstore.add_documents([doc])

# ingest_single_message(
#     {"sender" : "user", "content" : "How to Deploy?", "id" : "1", "created_at" : "2026-04-01T10:00:00"},
#     chat_id = "chat_1"
# )

# ingest_single_message(
#     {"sender" : "assistant", "content" : "Use Docker", "id" : "2", "created_at" : "2026-04-01T10:01:00"},
#     chat_id = "chat_1"
# )

# vs = get_vectorstore()

# results = vs.similarity_search("deploy", k = 2)

# print(results) for running the commented code if you would execute this file then the model and store would be initiated every time hence it would take a time of approx 10 secs to answer.