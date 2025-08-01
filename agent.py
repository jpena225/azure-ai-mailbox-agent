import os, time
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool
from azure.ai.agents import AgentsClient
import requests



#create my function
def get_mailbox(name: str):
    """
    Gets Information about a users mailbox

    :param name: the email address of the user
    :return: Mailbox information for the email address    
    """
    print("Inside get_Mailbox")

    base_url = "https://mbxcall-hgd7exg4dhhwembd.westus-01.azurewebsites.net/api/mbxtrigger?"
    complete_url = f"{base_url}name={name}&code={os.environ['AZURE_FUNCTION_KEY']}"
    response = requests.get(complete_url, timeout=10)
    
    return {
        "status_code": response.status_code,
        "content": response.text, 
        "headers": dict(response.headers),
        "url": response.url
    }


# Define user functions for the agent
user_functions = [get_mailbox]   

load_dotenv()

# Retrieve the project endpoint from environment variables
project_endpoint = os.environ["PROJECT_ENDPOINT"]

# Initialize the AIProjectClient
project_client = AgentsClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(
        exclude_environment_credentials=True,  # Exclude environment credentials for security
        exclude_managed_identity_credentials=True,  # Exclude managed identity credentials
    )
)

# Initialize the FunctionTool with user-defined functions
functions = FunctionTool(functions=user_functions)

project_client.enable_auto_function_calls([get_mailbox])

with project_client:
    # Create an agent with custom functions
    agent = project_client.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-agent",
        instructions="""You are a technical support agent. 
                    When a user asks you for infomration about there mailbox get there email address and use that value to call the function available to you.
                """,
        tools=functions.definitions,
    )
    print(f"Created agent, ID: {agent.id}")

    thread = project_client.threads.create()
    print(f"Created thread, ID: {thread.id}")

    print(f"agent_tools: {agent.tools}")

    while True:
        input_text = input("Enter a message (or 'exit' to quit): ")
        if input_text.lower() == 'exit':
            break
        if len(input_text) == 0:
            print("Please enter a valid message.")
            continue
        
        # Send a message to the agent.
        message = project_client.messages.create(
            thread_id=thread.id,
            role="user",
            content=input_text
        )

        # Process the agent's response
        run = project_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

        if run.status == "failed":
            print(f"Run failed. Please check the agent's configuration. {run.last_error}")
            continue

        # Get the latest messages from the thread to find the agent's response
        messages = project_client.messages.list(thread_id=thread.id)
        # Find the most recent assistant message
        agent_response = None
        for msg in messages:
            if msg.role == "assistant":
                agent_response = msg
                break
        
        if agent_response:
            print(f"Agent response: {agent_response.content}")
        else:
            print("No response from agent")

    # Delete the agent after use
    project_client.delete_agent(agent.id)
    print("Deleted agent")

    # Print the conversation log
    print("\nConversation Log:")
    for message in project_client.messages.list(thread_id=thread.id):
        print(f"{message.role.capitalize()}: {message.content}")

