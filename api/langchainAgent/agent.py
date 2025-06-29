import os
import logging
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langgraph.checkpoint.memory import MemorySaver
from langmem import create_manage_memory_tool, create_search_memory_tool
from langgraph.prebuilt import create_react_agent

from api.langchainAgent.Tools.add_transaction_tool import add_transaction
from api.langchainAgent.Tools.optimize_budget import optimize_budgets
from api.langchainAgent.Tools.goal_tracker_tool import goal_tracker
from api.langchainAgent.Tools.financial_insight_tool import financial_insight

# ✅ Load environment variables
load_dotenv()

# ✅ Logging config
logging.basicConfig(level=logging.INFO)

# ✅ Agent system prompt
AGENT_PROMPT = """
You are FinPilot — an intelligent personal finance assistant.

🎯 Your job:
- Help users manage their **expenses**, **income**, **budgets**, and **savings goals**
- Support them by adding transactions, optimizing budgets, tracking goals, and recalling memory

⚠️ Rules:
- Never process more than **one transaction per message**
- If the user provides multiple entries in one sentence (e.g., "Spent ₹100 on food and ₹200 on Uber"), politely ask them to split it

🧠 Memory:
- You can **search memory** when the user says things like:
    - "What did I spend last week?"
    - "Did I mention rent before?"
    - "What was my last income?"

🧰 Tools:
You have access to tools for adding transactions, budgeting, insights, memory search, and goal tracking. Use them when needed.

📌 Keep responses friendly, helpful, and financially aware.
"""

# ✅ Google API keys setup
google_api_keys = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    os.getenv("GOOGLE_API_KEY_3"),
]
google_api_keys = [key for key in google_api_keys if key]
if not google_api_keys:
    logging.error("Missing GOOGLE_API_KEY environment variables.")
    raise ValueError("Missing GOOGLE_API_KEY environment variables.")

# ✅ LLM failover
def get_gemini_llm_with_failover():
    last_exception = None
    for api_key in google_api_keys:
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=api_key,
                temperature=0.2,
                verbose=True,
            )
            logging.info(f"✅ Gemini model loaded with key ending in {api_key[-4:]}")
            return llm
        except Exception as e:
            if "quota" in str(e).lower() or "resource exhausted" in str(e).lower():
                logging.warning(f"⚠️ Quota issue with API key ending in {api_key[-4:]}, trying next...")
                continue
            last_exception = e
    raise Exception("❌ All Gemini API keys exhausted.") if last_exception is None else last_exception

# ✅ Load LLM
llm = get_gemini_llm_with_failover()

# ✅ MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("Missing MONGO_URI environment variable.")

mongo_client = MongoClient(MONGO_URI)
mongo_collection = mongo_client["expensestracker"]["UserMemory"]

# ✅ Embeddings
embedding_fn = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=google_api_keys[0]
)

# ✅ Vector memory store
vectorstore = MongoDBAtlasVectorSearch(
    collection=mongo_collection,
    embedding=embedding_fn,
    index_name="default"
)

store = vectorstore
checkpointer = MemorySaver()

# ✅ Per-user memory tools
def get_user_tools(user_id):
    namespace = (user_id,)
    return [
        create_manage_memory_tool(namespace=namespace),
        create_search_memory_tool(namespace=namespace)
    ]


# ✅ Create agent
def create_user_agent(user_id: str):
    tools = [
        add_transaction,
        optimize_budgets,
        goal_tracker,
        financial_insight,
        *get_user_tools(user_id)
    ]

    try:
        agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=AGENT_PROMPT,
            store=store,
            checkpointer=checkpointer
        )
        logging.info(f"✅ Agent created for user {user_id}")
        return agent
    except Exception as e:
        logging.error(f"[Agent Creation Error] user_id={user_id} | {e}")
        traceback.print_exc()
        raise RuntimeError("🚨 Agent creation failed. Please try again later.")


