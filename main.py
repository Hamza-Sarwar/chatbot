import streamlit as st
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from langchain.agents import OpenAIFunctionsAgent, AgentExecutor
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.agents.openai_functions_agent.agent_token_buffer_memory import (AgentTokenBufferMemory,)
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import MessagesPlaceholder
from langchain.schema import SystemMessage, AIMessage, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.faiss import FAISS
from langsmith import Client

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

    # making tool for agent
    tool = create_retriever_tool(
        configure_retriever(pdf),
        "search_used_imports_auto_llc_docs",
        "Searches and returns texts regarding USED IMPORTS AUTO LLC."
        "The provided text appears to be a set of frequently asked questions (FAQs) "
        "or guidelines for a business i.e USED IMPORTS AUTO LLC dealing with vehicles. "
        "It covers various topics related to vehicle condition, vehicle history issues, "
        "pricing, trade appraisal, ending conversations with customers, updating tasks and "
        "notes, marking situations as lost, and offering a referral program. It also mentions "
        "the option to switch vehicles using a filter from the website or inventory module. "
        "These guidelines seem to be aimed at employees or representatives who interact with "
        "customers in the context of buying or selling vehicles. You do not know anything about "
        "USED IMPORTS AUTO LLC, so if you are ever asked about USED IMPORTS AUTO LLC you should use this tool.",
    )

    # agent excess tool in a list
    tools = [tool]

    # making LLM (Language Model)
    llm = ChatOpenAI(temperature=0, streaming=True, model="gpt-4")
    message = SystemMessage(
        content=(
            "You are a helpful chatbot who is tasked with answering questions about USED IMPORTS AUTO LLC."
            "Act as USED IMPORTS AUTO LLC's employee. Don't use them or their but use our or ours."
            "Unless otherwise explicitly stated, it is probably fair to assume that questions are "
            "about USED IMPORTS AUTO LLC.If there is any ambiguity, you probably assume they are about that."
        )
    )
    prompt = OpenAIFunctionsAgent.create_prompt(
        system_message=message,
        extra_prompt_messages=[MessagesPlaceholder(variable_name="history")],
    )
    agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
    )
    memory = AgentTokenBufferMemory(llm=llm)
    starter_message = "Ask me anything about USED IMPORTS AUTO LLC!"
    if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
        st.session_state["messages"] = [AIMessage(content=starter_message)]


    def send_feedback(run_id, score):
        client.create_feedback(run_id, "user_score", score=score)


    for msg in st.session_state.messages:
        if isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        memory.chat_memory.add_message(msg)

    prompt = st.chat_input(placeholder=starter_message)
    if prompt:
        st.chat_message("user").write(prompt)
        with st.chat_message("assistant"):
            st_callback = StreamlitCallbackHandler(st.container())
            response = agent_executor(
                {"input": prompt, "history": st.session_state.messages},
                callbacks=[st_callback],
                include_run_info=True,
            )
            st.session_state.messages.append(AIMessage(content=response["output"]))
            st.write(response["output"])
            memory.save_context({"input": prompt}, response)
            st.session_state["messages"] = memory.buffer
            run_id = response["__run"].run_id

            col_blank, col_text, col1, col2 = st.columns([10, 2, 1, 1])
            with col_text:
                st.text("Feedback:")

            with col1:
                st.button("👍", on_click=send_feedback, args=(run_id, 1))

            with col2:
                st.button("👎", on_click=send_feedback, args=(run_id, 0))
