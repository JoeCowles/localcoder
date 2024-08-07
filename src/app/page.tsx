"use client";
import React, { useState, useRef, useEffect } from 'react';
import { FaRobot, FaUser, FaCog, FaFolder } from 'react-icons/fa';

interface Message {
  sender: 'AI' | 'User' | 'System';
  content: string;
}

const API_BASE_URL = 'http://localhost:8000';

export default function Home() {
  const [directory, setDirectory] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
  const [botActions, setBotActions] = useState<string[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const consoleEndRef = useRef<HTMLDivElement>(null);
  const botActionsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const consoleSource = new EventSource(`${API_BASE_URL}/api/console_stream`);
    const botActionSource = new EventSource(`${API_BASE_URL}/api/bot_action_stream`);

    consoleSource.onmessage = (event) => {
      setConsoleOutput((prev) => [...prev, event.data]);
    };

    botActionSource.onmessage = (event) => {
      setBotActions((prev) => [...prev, event.data]);
    };

    return () => {
      consoleSource.close();
      botActionSource.close();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    consoleEndRef.current?.scrollIntoView({ behavior: "smooth" });
    botActionsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, consoleOutput, botActions]);

  const selectDirectory = async () => {
    if (!directory.trim()) {
      setMessages([...messages, { sender: 'System', content: 'Please enter a directory path.' }]);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/select_directory`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ path: directory }),
      });
      const result = await response.json();
      
      if (response.ok) {
        setMessages([{ sender: 'System', content: `Directory selected: ${directory}` }]);
        setConsoleOutput([]);
        setBotActions([]);
      } else {
        setMessages([{ sender: 'System', content: `Error: ${response.status} - ${result.detail || 'Unknown error'}` }]);
      }
    } catch (error : any) {
      console.error('Error selecting directory:', error);
      setMessages([{ sender: 'System', content: `Error selecting directory: ${error.message}` }]);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    setMessages([...messages, { sender: 'User', content: input }]);
    setInput('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/send_message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: input }),
      });
      const result = await response.json();

      if (result.ai_actions) {
        setMessages(prev => [...prev, { sender: 'System', content: result.ai_actions }]);
      }
      setMessages(prev => [...prev, { sender: 'AI', content: result.ai_response }]);
    } catch (error : any) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { sender: 'System', content: `Error sending message: ${error.message}` }]);
    }
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-gray-100">
      <header className="w-full bg-blue-600 p-4 text-center">
        <h1 className="text-2xl font-bold text-white">AI Assistant</h1>
      </header>

      <main className="flex flex-col items-center w-full max-w-6xl p-4 space-y-4">
        <div className="w-full flex flex-col items-center space-y-4">
          <div className="w-full flex space-x-2">
            <input
              type="text"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              placeholder="Paste your directory path here"
              className="flex-grow p-2 border rounded text-black"
            />
            <button
              onClick={selectDirectory}
              className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition-colors flex items-center"
            >
              <FaFolder className="mr-2" />
              Set Directory
            </button>
          </div>

          <div className="w-full h-[calc(100vh-300px)] flex flex-col bg-white rounded-lg shadow-md p-4 overflow-y-auto">
            {messages.map((message, index) => (
              <div key={index} className={`mb-4 ${message.sender === 'User' ? 'flex justify-end' : 'flex justify-start'}`}>
                <div className={`max-w-[70%] p-3 rounded-lg ${
                  message.sender === 'AI' ? 'bg-blue-100' :
                  message.sender === 'User' ? 'bg-green-100' :
                  'bg-gray-100'
                }`}>
                  <div className="flex items-center space-x-2 mb-1">
                    {message.sender === 'AI' && <FaRobot className="text-blue-500" />}
                    {message.sender === 'User' && <FaUser className="text-green-500" />}
                    {message.sender === 'System' && <FaCog className="text-gray-500" />}
                    <span className="font-bold text-black">{message.sender}:</span>
                  </div>
                  <p className="text-black whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="w-full flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
              className="flex-grow p-2 border rounded text-black"
            />
            <button
              onClick={sendMessage}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Send
            </button>
          </div>
        </div>

        <div className="w-full flex space-x-4">
          <div className="flex-1 bg-black text-green-400 rounded-lg shadow-md p-4 h-48 overflow-y-auto font-mono text-sm">
            <h3 className="text-white font-bold mb-2">Console Output:</h3>
            {consoleOutput.map((line, index) => (
              <div key={index}>{line}</div>
            ))}
            <div ref={consoleEndRef} />
          </div>
          <div className="flex-1 bg-gray-200 rounded-lg shadow-md p-4 h-48 overflow-y-auto">
            <h3 className="font-bold mb-2">Bot Actions:</h3>
            {botActions.map((action, index) => (
              <div key={index} className="text-sm">{action}</div>
            ))}
            <div ref={botActionsEndRef} />
          </div>
        </div>
      </main>
    </div>
  );
}