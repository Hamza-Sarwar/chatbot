import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import (AgentTokenBufferMemory, )
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools import Tool
from langchain.utilities.serpapi import SerpAPIWrapper
from langchain.utilities.sql_database import SQLDatabase
from langchain.vectorstores.faiss import FAISS
from langchain_experimental.sql import SQLDatabaseChain
from langsmith import Client

from string_variables import *

client = Client()
load_dotenv()
st.set_page_config(
    page_title="Chat With Me",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# upload a PDF file
pdf = st.file_uploader("Upload your PDF", type='pdf')
"# Chat🦜🔗"

db = SQLDatabase.from_uri("sqlite:///vehicles.db")


# Check if a PDF file is uploaded
if pdf is not None:
    @st.cache_resource(ttl="1h")
    def configure_retriever(pdf):
        # loader = RecursiveUrlLoader("https://docs.smith.langchain.com/")
        # raw_documents = loader.load()
        # docs = Html2TextTransformer().transform_documents(raw_documents)

        pdf_reader = PdfReader(pdf)

        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text=text)
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_texts(chunks, embeddings)
        return vectorstore.as_retriever(search_kwargs={"k": 4})

    # making LLM (Language Model)
    llm = ChatOpenAI(temperature=0, streaming=True, model='gpt-3.5-turbo-0613')

# ************************************************* Tools *****************************************

    document_tool = create_retriever_tool(
        configure_retriever(pdf),
        name="search_used_imports_auto_llc_docs",
        description=DOCUMENT_TOOL_DESCRIPTION,
    )

    search = SerpAPIWrapper()
    search_tool = Tool(
        name="google_search",
        func=search.run,
        description=SEARCH_TOOL_DESCRIPTION,
    )


    db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True,)
    sql_tool = Tool(
        name="sql_database_tool",
        func=db_chain.run,
        description=SQL_TOOL_DESCRIPTION,
    )

    # agent excess tool in a list
    tools = [document_tool, search_tool, sql_tool]

# **************************************** Tools End ***************************************************************

    message = SystemMessage(content=SYSTEM_CONTENT_MESSAGE)
    prompt = OpenAIFunctionsAgent.create_prompt(
        system_message=message,
        extra_prompt_messages=[MessagesPlaceholder(variable_name="history")],
    )

    agent = OpenAIFunctionsAgent(
        llm=llm,
        tools=tools,
        prompt=prompt,
        handle_parsing_errors=True,
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
    )
    memory = AgentTokenBufferMemory(llm=llm)
    starter_message = STARTER_MESSAGE
    if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
        st.session_state["messages"] = [AIMessage(content=starter_message)]

    def send_feedback(run_id, score):
        client.create_feedback(run_id, "user_score", score=score)


    for msg in st.session_state.messages:
        if isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
            print(f"1- {msg.content}")
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
            print(f"2- {msg.content}")
        memory.chat_memory.add_message(msg)

    prompt = st.chat_input(placeholder=starter_message)
    if prompt:
        st.chat_message("user").write(prompt)
        print(f"3- {prompt}")
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            response = agent_executor(
                inputs={"input": prompt, "history": st.session_state.messages},
                callbacks=[st_callback],
                include_run_info=True,
            )
            st.session_state.messages.append(AIMessage(content=response["output"]))
            st.write(response["output"])
            print(f"4- {response['output']}")
            memory.save_context({"input": prompt}, response)
            st.session_state["messages"] = memory.buffer
            run_id = response["__run"].run_id

            # col_blank, col_text, col1, col2 = st.columns([10, 2, 1, 1])
            # with col_text:
            #     st.text("Feedback:")

            # with col1:
            #     st.button("👍", on_click=send_feedback, args=(run_id, 1))
            #
            # with col2:
            #     st.button("👎", on_click=send_feedback, args=(run_id, 0))
