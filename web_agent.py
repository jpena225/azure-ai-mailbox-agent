import email
import os
import secrets
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
import uuid
import requests

## Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Use environment variable for secret key in production, generate one if not set
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Your function
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


def get_Email_Details(subject: str):
    """
    Gets Information about an email subject that was sent to a user

    :param subject: the subject of the email.
    :return: The message trace details to the user.
    """
    print("Inside get_Email_Details")

    base_url = "https://mbxcall-hgd7exg4dhhwembd.westus-01.azurewebsites.net/api/MessageTrace?"
    complete_url = f"{base_url}subject={subject}&code={os.environ['AZURE_FUNCTION_KEY']}"
    response = requests.get(complete_url, timeout=10)
    
    return {
        "status_code": response.status_code,
        "content": response.json(), 
        "headers": dict(response.headers),
        "url": response.url
    }


# Define user functions for the agent
user_functions = [get_mailbox, get_Email_Details]

# Initialize Azure client (you'll need to handle this properly with error handling)
try:
    project_endpoint = os.environ["PROJECT_ENDPOINT"]
    project_client = AgentsClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(
            exclude_environment_credentials=True,
            exclude_managed_identity_credentials=True,
        )
    )
    
    # Initialize the FunctionTool with user-defined functions
    functions = FunctionTool(functions=user_functions)
    project_client.enable_auto_function_calls([get_mailbox, get_Email_Details])
    
    # Create agent (you might want to do this per session or reuse)
    agent = project_client.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-agent",
        instructions="""You are a technical support agent. 
                    When a user asks you for infomration about there mailbox get there email address and use that value to call the function available to you.
                    When a user asks for details about an email subject, extract the subject and call the function available to you to retrieve message trace details.
                """,
        tools=functions.definitions,
    )
    
    print(f"Created agent, ID: {agent.id}")
    
except Exception as e:
    print(f"Error initializing Azure client: {e}")
    project_client = None
    agent = None

@app.route('/')
def index():
    """Render the main chat interface"""
    return render_template('index.html')

import re

def parse_agent_response(text):
    pattern = r"\*\*(.*?)\*\*:\s*(\d+)"
    matches = re.findall(pattern, text)

    parsed_data = {}
    for key, value in matches:
        parsed_data[key.strip()] = int(value)

    return parsed_data

def build_chart_payload(email_data):
    labels = []
    values = []
    print("Building chart payload from email data", email_data)
    for key, val in email_data.items():
        if isinstance(val, int):  # Only chart numeric fields
            labels.append(key)
            values.append(val)

    title = f"Email Analysis: {email_data.get('SubjectQueried', 'Subject')}"
    return {
        "title": title,
        "labels": labels,
        "values": values
    }

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        if not project_client or not agent:
            return jsonify({'error': 'Azure client not initialized'}), 500
        
        user_message = request.json.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Get or create thread for this session
        if 'thread_id' not in session:
            thread = project_client.threads.create()
            session['thread_id'] = thread.id
        
        thread_id = session['thread_id']
        
        # Send message to agent
        message = project_client.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Process the agent's response
        run = project_client.runs.create_and_process(thread_id=thread_id, agent_id=agent.id)
        
        if run.status == "failed":
            return jsonify({
                'error': f'Run failed: {run.last_error}',
                'user_message': user_message
            }), 500
        
        # Get the latest messages from the thread
        messages = project_client.messages.list(thread_id=thread_id)
        
        agent_response = None
        tool_result_data = None

        print("Before for loop to print messages")
        for msg in messages:
            print("Printing Role:", msg.role)
            print("Printing Content:", msg.content)
            if msg.role == "assistant":
                print("Response Text:", msg.content[0].text.value)
                response_text = msg.content[0].text.value
                email_stats = parse_agent_response(response_text)
                print("Parsed email stats:", email_stats)
                # Extract text content from MessageTextContent object
                if hasattr(msg.content, '__iter__') and not isinstance(msg.content, str):
                    print("Tool result data found:", tool_result_data)
                    for content_item in msg.content:
                        if hasattr(content_item, 'text'):
                            agent_response = content_item.text.value
                            print("Agent response found:", agent_response)
                            break
                elif hasattr(msg.content, 'text'):
                    agent_response = msg.content.text.value
                else:
                    agent_response = str(msg.content)
                print("Agent Text:", agent_response)


            elif msg.role == "tool_result":
                if hasattr(msg.content, 'tool_name') and msg.content.tool_name == "get_Email_Details":
                    tool_result_data = msg.content.output  # This is the returned JSON

        email_stats = parse_agent_response(agent_response)
        print("Parsed email stats:", email_stats)

        if not agent_response:
            agent_response = "No response from agent"
        
        image_base64 = None

        print("Tool result data:", tool_result_data)

        if email_stats:
            chart_payload = build_chart_payload(email_stats)
            chart_response = requests.post(
                "http://localhost:8000/generate-chart",
                json=chart_payload
            )
            image_base64 = chart_response.json().get("image_base64")

        return jsonify({
            'user_message': user_message,
            'agent_response': agent_response,
            'status': 'success',
            'image_base64': image_base64
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_chat():
    """Clear the current chat session"""
    session.pop('thread_id', None)
    return jsonify({'status': 'cleared'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'azure_client': project_client is not None,
        'agent': agent is not None
    })


import matplotlib.pyplot as plt
import io
from flask import send_file
import base64



@app.route('/generate-chart', methods=['POST'])
def generate_chart():
    """Generate a bar chart and return as base64 string"""
    try:
        data = request.get_json()
        title = data.get("title", "Chart")
        labels = data.get("labels", [])
        values = data.get("values", [])

        if not labels or not values or len(labels) != len(values):
            return jsonify({'error': 'Labels and values must be non-empty and of equal length'}), 400

        # Create chart
        fig, ax = plt.subplots()
        #colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1']  # Add more if needed

        #ax.bar(labels, values, color=colors[:len(labels)])
        ax.bar(labels, values, color='skyblue')
        ax.set_title(title)
        ax.set_ylabel("Value")
        ax.set_xlabel("Category")
        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)

        # Encode to base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return jsonify({'image_base64': img_base64})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=8000)
else:
    # For production (Gunicorn will handle this)
    pass
