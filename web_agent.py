import os
import secrets
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import FunctionTool
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Use environment variable for secret key in production, generate one if not set
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Your function
def get_mailbox():
    return "Mailbox data retrieved successfully."

# Define user functions for the agent
user_functions = [get_mailbox]

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
    
    # Create agent (you might want to do this per session or reuse)
    agent = project_client.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="web-agent",
        instructions="You are a helpful agent accessible through a web interface",
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
        
        # Find the most recent assistant message
        agent_response = None
        for msg in messages:
            if msg.role == "assistant":
                # Extract text content from MessageTextContent object
                if hasattr(msg.content, '__iter__') and not isinstance(msg.content, str):
                    # Handle list of content objects
                    for content_item in msg.content:
                        if hasattr(content_item, 'text'):
                            agent_response = content_item.text.value
                            break
                elif hasattr(msg.content, 'text'):
                    # Handle single content object
                    agent_response = msg.content.text.value
                else:
                    # Fallback to string conversion
                    agent_response = str(msg.content)
                break
        
        if not agent_response:
            agent_response = "No response from agent"
        
        return jsonify({
            'user_message': user_message,
            'agent_response': agent_response,
            'status': 'success'
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

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
else:
    # For production (Gunicorn will handle this)
    pass
