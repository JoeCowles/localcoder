# AI Coding Assistant

## Overview

This project implements an AI-powered coding assistant with a web-based interface. It combines a FastAPI backend with a React frontend to provide an interactive environment where users can communicate with an AI model, execute system commands, and perform file operations within a selected directory.

## Features

- Interactive chat interface with an AI assistant
- File system operations (create, read, modify, delete)
- Command-line execution within a selected directory
- Real-time console output and bot action streaming
- Support for both Gemini and Claude AI models

## Technology Stack

### Backend

- Python 3.x
- FastAPI
- Google GenerativeAI (Gemini)
- Anthropic API (Claude)
- AsyncIO for asynchronous operations

### Frontend

- React
- TypeScript
- Tailwind CSS for styling
- React Icons for UI elements

## Setup and Installation

1. Clone the repository to your local machine.

2. Backend Setup:

   - Navigate to the project directory.
   - Install the required Python packages:
     ```
        pip install requirements.txt
     ```
   - Set up your API keys:
     - For Gemini: Set the `GOOGLE_API_KEY` environment variable.
     - For Claude: Set the `ANTHROPIC_API_KEY` environment variable.

3. Frontend Setup:
   - Ensure you have Node.js and npm installed.
   - Navigate to the frontend directory.
   - Install the required npm packages:
     ```
     npm install
     ```

## Running the Application

1. Start the Backend:

   - From the project root directory, run:
     ```
     python index.py
     ```
   - The server will start on `http://localhost:8000`.

2. Start the Frontend:

   - From the frontend directory, run:
     ```
     npm run dev
     ```
   - The React application will start, typically on `http://localhost:3000`.

3. Open your web browser and navigate to the frontend URL to use the application.

## Usage

1. **Select a Directory**:

   - Enter the full path of the directory you want to work in.
   - Click the "Set Directory" button.

2. **Interact with the AI**:

   - Type your messages or coding queries in the input field.
   - The AI will respond and can perform various actions:
     - Execute command-line instructions
     - Perform file operations (create, read, modify, delete)
     - Provide coding assistance and explanations

3. **View Real-time Feedback**:
   - Console Output: Shows the results of executed commands.
   - Bot Actions: Displays the actions being performed by the AI.

## Key Components

### Backend (`index.py`)

- `FastAPI` app setup with CORS middleware
- AI model initialization (Gemini and Claude)
- File and command execution functions
- WebSocket endpoints for real-time communication
- Message handling and AI response processing

### Frontend (`page.tsx`)

- React functional component with hooks
- State management for messages, console output, and bot actions
- API communication with the backend
- UI rendering for chat interface, console output, and bot actions

## Security Considerations

- The application allows execution of system commands and file operations. Ensure it's run in a controlled environment.
- API keys are sensitive. Use proper key management and don't expose them in the frontend.
- Implement proper input validation and sanitization, especially for file paths and system commands.

## Limitations and Future Improvements

- Error handling could be enhanced for better user feedback.
- Implement user authentication and session management.
- Add support for multiple directory workspaces.
- Enhance the AI's capabilities with more specialized coding tools and integrations.

## Contributing

Contributions to improve the project are welcome. Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature.
3. Commit your changes.
4. Push to the branch.
5. Create a new Pull Request.

---

This project showcases the integration of advanced AI models with a modern web application to create a powerful coding assistant tool.
