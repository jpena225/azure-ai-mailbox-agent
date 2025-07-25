# Azure AI Mailbox Agent

A Flask web application that provides a chat interface for interacting with Azure AI agents.

## Features

- Web-based chat interface
- Azure AI integration
- Mailbox data retrieval functionality
- Session management
- Responsive design

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your Azure credentials:
   ```
   PROJECT_ENDPOINT=your_azure_project_endpoint
   MODEL_DEPLOYMENT_NAME=your_model_deployment_name
   FLASK_SECRET_KEY=your_secret_key
   ```
5. Run the application:
   ```bash
   python web_agent.py
   ```

## Deployment

This application is configured for deployment to Azure App Service using GitHub Actions.

### Prerequisites
- Azure App Service instance
- Azure AI Project configured

### Environment Variables
Set these in your Azure App Service:
- `PROJECT_ENDPOINT`: Your Azure AI project endpoint
- `MODEL_DEPLOYMENT_NAME`: Your Azure AI model deployment name
- `FLASK_SECRET_KEY`: A secure random string for Flask sessions

## Project Structure

- `web_agent.py` - Main Flask application
- `templates/index.html` - Chat interface HTML template
- `requirements.txt` - Python dependencies
- `.github/workflows/deploy.yml` - GitHub Actions deployment workflow

## License

MIT License
