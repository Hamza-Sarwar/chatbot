import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import AgentTokenBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage, AIMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from langchain.utilities.serpapi import SerpAPIWrapper
from langchain.utilities.sql_database import SQLDatabase
from langchain.vectorstores.faiss import FAISS
from langchain_community.agent_toolkits import create_sql_agent, SQLDatabaseToolkit

from string_variables import SQL_TOOL_DESCRIPTION, SEARCH_TOOL_DESCRIPTION, DOCUMENT_TOOL_DESCRIPTION, PROMPT

# Set up Streamlit page
st.set_page_config(page_title="Chat With Me", page_icon="🦜", layout="wide", initial_sidebar_state="collapsed")

# Load environment variables
load_dotenv()

# Car Brands Dictionary
CAR_BRANDS = {"Honda": 1, "BMW": 2, "Audi": 3, "Nissan": 4, "Toyota": 5}

# Streamlit Interface Components
selected_brand = st.selectbox("Choose a car brand", list(CAR_BRANDS.keys()), index=0,
                              placeholder="Select a car brand...")

if not selected_brand:
    st.warning("Please select a car brand to proceed.")
    st.stop()

# Constants and Configurations
PDF_DIR = "./brands_docs/"
DB_URI = 'postgresql+psycopg2://postgres:root@localhost:5432/inventory360'
# DB_URI = psycopg2.connect(host='172.212.83.28', dbname='inventory360', user='postgres', password='root')
SYSTEM_CONTENT_MESSAGE = (
    f"You are an Customer Support agent and you are bound to answer questions related to the {selected_brand} Cars."
    f"You have documents if user asks somethings related to policies and general information related to cars."
    f"You have whole inventory database if you ask something related to inventory."
    f"If something general is asked related to vehicles modules which you think may not be available in documents"
    f"and inventory then google search it."
)


# Function Definitions
@st.cache_resource(ttl="1h")
def get_pdf_text(pdf_path):
    pdf_reader = PdfReader(pdf_path)
    text = "".join([page.extract_text() for page in pdf_reader.pages])
    return text


def configure_retriever(pdf_text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_text(text=pdf_text)
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(chunks, embeddings)
    return vectorstore.as_retriever(search_kwargs={"k": 4})


def setup_document_tool(pdf_text):
    return create_retriever_tool(
        configure_retriever(pdf_text),
        name=f"search_{selected_brand}_docs",
        description=DOCUMENT_TOOL_DESCRIPTION
    )


def setup_search_tool():
    return Tool(
        name="google_search",
        func=SerpAPIWrapper().run,
        description=SEARCH_TOOL_DESCRIPTION
    )


def setup_sql_tool(llm):
    try:
        db = SQLDatabase.from_uri(DB_URI, include_tables=['inventorylog'])
    except Exception as e:
        print(f"Error connecting to Postgres Database: {str(e)}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm, )
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        toolkit=toolkit,
        prompt=PROMPT,
        verbose=True
    )
    return Tool(
        name="sql_database_tool",
        func=agent_executor.run,
        description=SQL_TOOL_DESCRIPTION
    )


def create_agent(llm, tools):
    message = SystemMessage(content=SYSTEM_CONTENT_MESSAGE)
    prompt = OpenAIFunctionsAgent.create_prompt(
        system_message=message,
        extra_prompt_messages=[MessagesPlaceholder(variable_name="history")],
    )

    return OpenAIFunctionsAgent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        handle_parsing_errors=True,
    )


# Main Application Logic
pdf_path = f"{PDF_DIR}{selected_brand}.pdf"
pdf_text = get_pdf_text(pdf_path)
llm = ChatOpenAI(temperature=0, model='gpt-4-0613', streaming=True)
document_tool = setup_document_tool(pdf_text)
search_tool = setup_search_tool()
sql_tool = setup_sql_tool(llm)
tools = [document_tool, search_tool, sql_tool]
agent = create_agent(llm, tools)
agent_executor = AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=True, handle_parsing_errors=True)
memory = AgentTokenBufferMemory(llm=llm)

# Streamlit Chat Interface
starter_message = f"Ask me anything about {selected_brand}!"
if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [AIMessage(content=starter_message)]

for msg in st.session_state.messages:
    st.chat_message("assistant").write(msg.content)
    memory.chat_memory.add_message(msg)

prompt = st.chat_input(placeholder=starter_message)
if prompt:
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        # st_callback = StreamlitCallbackHandler(st.container())
        response = agent_executor(
            inputs={"input": prompt, "history": st.session_state.messages, },
            callbacks=[],
            include_run_info=True,
        )
        output_msg = AIMessage(content=response["output"])
        st.session_state.messages.append(output_msg)
        st.write(output_msg.content)
        memory.save_context({"input": prompt}, response)
        st.session_state["messages"] = memory.buffer
