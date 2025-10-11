import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** Utility Functions *************************

def generate_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    return state.values.get('messages', [])

def get_latest_message(thread_id):
    """Returns the latest message (user or assistant) from a given thread."""
    messages = load_conversation(thread_id)
    if not messages:
        return "Current Chat"
    
    last_msg = messages[-1]
    if isinstance(last_msg, HumanMessage):
        prefix = "You: "
    else:
        prefix = ""

    # Limit length for better sidebar readability
    text = last_msg.content.strip().replace("\n", " ")
    return prefix + (text[:10] + "..." if len(text) > 40 else text)


# **************************************** Session Setup ******************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('➕ New Chat'):
    reset_chat()

st.sidebar.header('🗂 My Conversations')

# Display latest messages instead of thread IDs
for thread_id in st.session_state['chat_threads'][::-1]:
    latest_message = get_latest_message(thread_id)
    if st.sidebar.button(latest_message, help=str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages


# **************************************** Main UI ************************************

# Display previous conversation
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

# Chat input box
user_input = st.chat_input('Type your message here...')

if user_input:
    # Add user message to chat history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Stream assistant response
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        ai_message = st.write_stream(ai_only_stream())

    # Add assistant message to session history
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})
