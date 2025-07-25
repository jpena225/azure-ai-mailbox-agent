import os, time
from dotenv import load_dotenv

# Simple function for testing
def get_mailbox():
    return "Mailbox data retrieved successfully."

# Mock classes for testing without Azure dependencies
class MockFunctionTool:
    def __init__(self, functions):
        self.definitions = [{"name": func.__name__, "description": f"Function {func.__name__}"} for func in functions]

class MockAgent:
    def __init__(self):
        self.id = "mock-agent-123"

class MockThread:
    def __init__(self):
        self.id = "mock-thread-456"

class MockMessage:
    def __init__(self):
        self.data = {"id": "mock-message-789"}
    
    def __getitem__(self, key):
        return self.data[key]

class MockRun:
    def __init__(self):
        self.id = "mock-run-000"
        self.status = "completed"

class MockProjectClient:
    def __init__(self):
        self.agents = self
        self.threads = self
        self.messages = self
        self.runs = self
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def create_agent(self, **kwargs):
        return MockAgent()
    
    def create(self, **kwargs):
        if 'thread_id' in kwargs:
            return MockRun()
        return MockThread()
    
    def create_message(self, **kwargs):
        return MockMessage()
    
    def list(self, **kwargs):
        return [{"role": "assistant", "content": "Mock response"}]
    
    def delete_agent(self, agent_id):
        pass

# Define user functions for the agent
user_functions = [get_mailbox]

load_dotenv()

print("=== MOCK AZURE AGENT (For Testing) ===")
print("This is a simplified version that works without Azure dependencies.")
print("To use the real Azure AI agent, you need to install Microsoft C++ Build Tools.")
print()

# Use mock clients for testing
project_client = MockProjectClient()
functions = MockFunctionTool(functions=user_functions)

with project_client:
    # Create an agent with custom functions
    agent = project_client.create_agent(
        model="mock-model",
        name="my-agent",
        instructions="You are a helpful agent",
        tools=functions.definitions,
    )
    print(f"Created agent, ID: {agent.id}")

# Create a thread for communication
thread = project_client.create()
print(f"Created thread, ID: {thread.id}")

# Send a message to the thread
message = project_client.create_message(
    thread_id=thread.id,
    role="user",
    content="Hello, send an email with the datetime and weather information in New York?",
)
print(f"Created message, ID: {message['id']}")

# Create and process a run for the agent to handle the message
run = project_client.create(thread_id=thread.id, agent_id=agent.id)
print(f"Created run, ID: {run.id}")

# Simulate processing
print("Processing...")
time.sleep(2)

# Test the function
result = get_mailbox()
print(f"Function result: {result}")

print(f"Run completed with status: {run.status}")

# Fetch and log all messages from the thread
messages = project_client.list(thread_id=thread.id)
for message in messages:
    print(f"Role: {message['role']}, Content: {message['content']}")

# Delete the agent after use
project_client.delete_agent(agent.id)
print("Deleted agent")

print("\n=== TO USE REAL AZURE AGENT ===")
print("1. Install Microsoft C++ Build Tools from:")
print("   https://visualstudio.microsoft.com/visual-cpp-build-tools/")
print("2. During installation, select 'C++ build tools' workload")
print("3. Restart your terminal and run:")
print("   pip install azure-identity azure-ai-projects")
print("4. Create a .env file with your Azure credentials")
print("5. Use the original agent.py file")
