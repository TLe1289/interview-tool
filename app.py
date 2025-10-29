from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Streamlit Chat", page_icon="💬")
st.title("Chatbot")

# We need to track when the setup is complete
# so that we can avoid re-initializing the session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if  "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True
def show_feedback():
    st.session_state.feedback_shown = True

# Checks if the session_state is false
if not st.session_state.setup_complete:
    st.subheader("Personal information", divider = "rainbow")

    #inititalize session state variables storing personal infromation
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""
    
    #Save the "values" into session state varaibles
    st.session_state["name"] = st.text_input(label="Name", max_chars = None, value = st.session_state["name"], placeholder="Enter your name")
    st.session_state["experience"] = st.text_area(label="Experience", value = st.session_state["experience"], height = None, max_chars = None, placeholder = "Describe your experience")
    st.session_state["skills"] = st.text_area(label = "Skills", value = st.session_state["skills"], height = None, max_chars = None, placeholder = "List your skills")

    st.subheader("Company and Position", divider = "rainbow")

    #Initialize company position state variables, but with default values
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    #Save the "values" into session state varaibles
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            "Choose level",
            key = "visibility", 
            options = ["Junior" , "Mid-Level", "Senior"],
        )
    with col2:
        st.session_state["position"]= st.selectbox(
            "Choose position",
            ("Data Scientist", "Data engineer", "ML Engineer", "BI Analyst", "Financial Analyst")
        )
    st.session_state["company"] = st.selectbox(
        "Choose company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify")
    )

    #Button to complete setup
    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")                 

# (1) If the setup is complete then we will begin the chat interface. 
#Setup must be set to true to avoid re-initializing session state variables
#!!! (2) make sure feedback is not shown and (3) chat is not complete
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info("""
            Start by introducing yourself.
            """,
            icon= "💡"
            )

    client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    # Initialize session state variables
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"
    #You can add a system mesage within session_state to set the behavior of the assistant
    #This works because you are adding a system message within the history of messages sent to OpenAI API
    if not st.session_state.messages:  
        st.session_state.messages = [{"role": "system", "content": (f"You are an HR executive that interviews an interviewee called {st.session_state["name"]}"
                                                                    f"with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}."
                                                                    f"You should interview him for the position {st.session_state["level"]} {st.session_state["position"]}" 
                                                                    f"at the {st.session_state["company"]}")
                                                                    }]
    # st.session_state.messages is [] --> empty false.
    # So (not false) is true --> enter the block 


    ## because streamlist reset everything. We should have a session_state and a for loop to display the entire chat history
    # you can also just do not "system" to hide system messages from the chat history
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"] ):
                st.markdown(message["content"])
        else: 
            pass


    #limits the users messages to 5. RECAP: prompt is the user input from st.chat_input
    if st.session_state.user_message_count < 5:
        if prompt := st.chat_input("Your answer.", max_chars = 1000):
            # log the user input message and display it in chat-message container
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            #The AI stop responding after specific number of user messages
            if st.session_state.user_message_count < 4:
                # generate AI response using OpenAI
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        #initialize the model with GPT-3.5-Turbo
                        model = st.session_state["openai_model"],

                        #creates a dictionary of messages, defining the role and content, by taking the messages from 
                        #the session state as a for loop. Iterating and recieving the entire chat history to be used for user message.
                        messages = [{"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.messages],

                        #setting to make it a stream fo message, not instant response
                        stream = True,
                    )
                    #because we are still within st.chat_message("assistant"), we can write stream within this container
                    response = st.write_stream(stream)
                #include the AI response in the session state emssages
                st.session_state.messages.append({"role": "assistant", "content": response}) 

            #increment the message count everytime the user sends a message. Should stop at 5
            st.session_state.user_message_count += 1

    #message count reaches 5, end the chat and show feedback
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click = show_feedback):
        st.write("Fetching feedback ...")

if st.session_state.feedback_shown:
    st.subheader("Feedback")
    # Process the message history with a for loop as a single string and "\n". Save into conversation_history
    conversation_history = "\n".join([f"{msg["role"]}: {msg["content"]}" for msg in st.session_state.messages])
    # Setup a second OpenAI client for feedback
    feedback_client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])

    feedback_completion = feedback_client.chat.completions.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": """You are a helpful tool that provides feedback yon an interviewee performance.
             Before the Feedback, give a score of 1-10.
             Follow this format: 
             Overall Score: //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questions.
             """},
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that your are only a tool and you shouldn't engage in a conversation. {conversation_history}"}
        ]   
    )
    st.write(feedback_completion.choices[0].message.content)

    # Refresh the page, which also resets the session state variables. Smart way to restart the interview
    if st.button("Restart Interview", type = "primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")


    #Personal Notes: Interviewer is not in depth enough. Start Improving the model once you upload to Github
    # - Prompt Engineering for better prompts
    # - change the settings (temperature or top-p) of the model to improve the results
    # - could implement a question by question evaluation instead of overall interview

