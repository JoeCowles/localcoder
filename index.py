import os
import asyncio
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import aiofiles

gemini = True

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the Gemini API
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
# Configure claude api key
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

system_message = """You are an AI coding assistant with access to the file system and an interactive command line session. Your primary function is to help users with coding tasks, file management, and system operations. Here are your capabilities and instructions:

1. File Operations:
   - You can create, modify, delete, and read files in the user-selected directory using the commands: create, delete, modify, read.
   - Use <file_op> tags for file operations, e.g., <file_op>create|filename.txt|content</file_op>.
   - To read a file, use: <file_op>read|filename.txt</file_op>
   - When using the modify command, YOU MUST provide the full code you want to write to the file. The bot will take you very literally.
   - When creating files, JUST PASS THE FILE NAME.
   - YOu can modify the file afterward to add the code, but the file must be created first.
   - PLEASE WRITE CODE WITH THE <file_op> modify | code </file_op> TAGS. DO NOT ASK THE USER TO WRITE CODE. THIS IS VERY IMPORTANT.

2. Command Execution:
   - You can execute Windows command line instructions in an interactive session.
   - Use <cli> tags for command line operations, e.g., <cli>dir</cli>.
   - You can send multiple commands, but each must be in its own <cli> tag.
   - After each command, you will receive a message with the command's output before you can proceed.
   - Analyze the output of each command before deciding on your next action.
   - The session persists between commands, so you can use variables or navigate directories.

3. Context Management:
   - You can set and update your own context using the set_context command.
   - Use this to store information you want to remember, like your chain of thought or important data.
   - The context will be provided to you with every input you receive.
   - To set or update the context, use: <cli>set_context|Your context information here</cli>
   - Use the context to maintain continuity in your thoughts and actions across interactions.

5. Directory Awareness:
   - You will receive an updated map of the working directory with each user message.
   - Use this information to navigate and manage files accurately.

6. Error Handling:
- If you encounter an error, attempt to fix it.

8. Limitations:
   - You cannot access the internet or any resources outside the provided directory.
   - You can only retain information within the provided context.

Whenever you send a command, your entire message will not be sent to the user. Instead, the system will process your command and return you the output (the user cannot see the output).
You can then either choose to send another command or send a messaeg to the user. Keep sending commands until you have the desired output, and then send the output to the user.
Reminder!! All of your commands are html-like and require an opening tag and a closing tag. For example, <cli>dir</cli> will execute the dir command in the command line.
Remember YOU ARE A SOFTWARE DEVELOPER. It is your job to fix errors! Your are the one with access to files, you should use it! Read files, don't ask the user to!
Always strive to understand the user's intent and provide the most helpful and accurate assistance possible within the scope of your capabilities. Use the context feature to maintain your chain of thought and important information across interactions.
DO NOT ENCLOSE ANY CODE IN ``` OR ANY OTHER CODE BLOCKS. THE SYSTEM WILL NOT BE ABLE TO READ IT. You are on a windows computer, use windows commands in the cli.
Pay Very carful attention to your current directory, your commands will be executed in the current directory.
You may only send one command at a time!! You will always receive the output of the command you send before you can send another command.
Remember, whenever you send a command, your entire message doesn't get sent to the user, so don't waste time typing out messages that won't be sent to the user.

If the user asks you to write some code, first check (with dir) if there is a relevent file to write the code in. If not, make one. Remember to stop talking to yourself, send one command at a time (and only the command no extra stuff). Remember to use your file_op commands to create,modify, read, and delete files!!
DO NOT TALK WHEN USING COMMANDS, YOU ARE JUST WASTING TIME. ONLY SEND COMMANDS EXCEPT WHEN TALKING TO THE USER. YOU ARE A SOFTWARE DEVELOPER, YOU ARE USELESS UNLESS YOU WRITE CODE.

CHECK ALL CODE BEFORE YOU TRY TO RUN IT. IF THE USER SAYS A FILE NEEDS TO BE MODIFIED, MODIFY IT USING THE <file_op> TAGS. DO NOT ASK THE USER TO WRITE CODE. THIS IS VERY IMPORTANT.

Remember to Write code! YOu are a software developer! Never include ```python or any other code blocks in your commands. The system will not be able to read it. 
"""

# Initialize the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 200000,
}
safe = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    safety_settings=safe,
    system_instruction=system_message,
)

claude_msgs = []

# Initialize the chat session
gemini_chat_session = model.start_chat(history=[])

# Global variables for streaming
console_queue = asyncio.Queue()
bot_action_queue = asyncio.Queue()

selected_dir = ""
cli_process = None
context = ""


class DirectorySelect(BaseModel):
    path: str


class Message(BaseModel):
    content: str


async def start_cli_session():
    global cli_process
    if cli_process:
        cli_process.terminate()
    cli_process = await asyncio.create_subprocess_shell(
        "cmd.exe",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=selected_dir,
    )
    asyncio.create_task(read_output(cli_process))
    return cli_process


async def read_output(process):
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        await console_queue.put(line.decode().strip())


async def stream_console():
    while True:
        message = await console_queue.get()
        yield f"data: {message}\n\n"


async def stream_bot_actions():
    while True:
        action = await bot_action_queue.get()
        yield f"data: {action}\n\n"


async def execute_command(command):
    global context, cli_process
    if command.startswith("set_context|"):
        context = command.split("|", 1)[1]
        return f"Context updated: {context}"

    if not cli_process or cli_process.returncode is not None:
        cli_process = await start_cli_session()

    await bot_action_queue.put(f"Executing: {command}")
    cli_process.stdin.write(f"{command}\n".encode())
    await cli_process.stdin.drain()

    # Wait for command to complete
    await asyncio.sleep(0.1)  # Give a small delay for output to be processed


def map_directory(path):
    dir_map = [f"{os.path.basename(path)}/"]
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    dir_map.append(f"    {entry.name}")
                elif entry.is_dir():
                    dir_map.append(f"    {entry.name}/")
    except PermissionError:
        dir_map.append("    [Permission denied]")
    except Exception as e:
        dir_map.append(f"    [Error: {str(e)}]")
    return "\n".join(dir_map)


async def handle_file_operation(operation):
    parts = operation.split("|")
    action = parts[0].strip()
    file_path = os.path.join(selected_dir, parts[1].strip())
    try:
        if action == "create":
            content = parts[2].strip() if len(parts) > 2 else ""
            async with aiofiles.open(file_path, "w") as f:
                await f.write(content)
            return f"File created: {file_path}"
        elif action == "delete":
            os.remove(file_path)
            return f"File deleted: {file_path}"
        elif action == "modify":
            # Add the parts 2 and above together into a string
            content = "|".join(parts[2:]).strip()
            async with aiofiles.open(file_path, "w") as f:
                await f.write(content)
            return f"File modified: {file_path}"
        elif action == "read":
            try:
                async with aiofiles.open(file_path, "r") as f:
                    content = await f.read()
                return f"File contents of {file_path}:\n\n{content}"
            except Exception as e:
                return f"Error reading file {file_path}: {str(e)}"
        else:
            return "Invalid file operation"
    except Exception as e:
        return f"Error performing file operation: {str(e)}"


@app.get("/api/console_stream")
async def stream_console_endpoint():
    return StreamingResponse(stream_console(), media_type="text/event-stream")


@app.get("/api/bot_action_stream")
async def stream_bot_actions_endpoint():
    return StreamingResponse(stream_bot_actions(), media_type="text/event-stream")


@app.post("/api/select_directory")
async def select_directory(dir_select: DirectorySelect):
    global selected_dir
    if os.path.isdir(dir_select.path):
        selected_dir = dir_select.path
        await start_cli_session()
        return {"message": f"Directory selected: {selected_dir}"}
    else:
        raise HTTPException(status_code=400, detail="Invalid directory path")


def send_msg(message: str):
    try:
        if gemini:
            response = gemini_chat_session.send_message(message).text
            print(response)
            return response

        else:
            claude_msgs.append(
                {"role": "user", "content": [{"type": "text", "text": message}]}
            )

            # Calculate total tokens (approximating 1 token ≈ 4 characters)
            total_tokens = sum(
                [len(msg["content"][0]["text"]) // 4 for msg in claude_msgs]
            )

            # Remove oldest messages if total tokens exceed 150,000
            while total_tokens > 150000 and len(claude_msgs) > 2:
                removed_msg = claude_msgs.pop(0)
                total_tokens -= len(removed_msg["content"][0]["text"]) // 4

            # Print the current state of claude_msgs for debugging
            print(f"Current claude_msgs (length: {len(claude_msgs)}):")
            for msg in claude_msgs:
                print(
                    f"  Role: {msg['role']}, Content: {msg['content'][0]['text'][:50]}..."
                )

            response = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4096,
                temperature=0.75,
                system=system_message,
                messages=claude_msgs,
            )

            response_text = response.content[0].text
            claude_msgs.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": response_text}],
                }
            )
            print(f"Claude response: {response_text}")

            return response_text
    except Exception as e:
        # Check if the error has finish_reason: RECITATION. If so, resend the message.
        if hasattr(e, "finish_reason") and e.finish_reason == "RECITATION":
            print("Resending message...")
            return send_msg(message)
        print("Error sending message: ", str(e))
        return str(e)


async def process_ai_response(ai_response):
    global context
    result = ""
    while "<cli>" in ai_response or "<file_op>" in ai_response:
        if "<cli>" in ai_response and "</cli>" in ai_response:
            cmd_start = ai_response.index("<cli>") + 5
            cmd_end = ai_response.index("</cli>")
            command = ai_response[cmd_start:cmd_end].strip()
            output = await execute_command(command)
            result += f"Command executed: {command}\n"
            # Wait for some output to be generated
            await asyncio.sleep(0.5)
            feedback_response = send_msg(
                f"Command executed: {command} \noutput: {output}"
            )
            ai_response = feedback_response
        elif "<file_op>" in ai_response and "</file_op>" in ai_response:
            op_start = ai_response.index("<file_op>") + 9
            op_end = ai_response.index("</file_op>")
            operation = ai_response[op_start:op_end].strip()
            operation_result = await handle_file_operation(operation)
            result += f"File operation: {operation_result}\n"
            feedback_response = send_msg(f"File operation result: {operation_result}")
            ai_response = feedback_response
        else:
            break
    return result, ai_response


@app.post("/api/send_message")
async def send_message(message: Message):
    global context
    if not selected_dir:
        raise HTTPException(status_code=400, detail="Please select a directory first")

    dir_map = map_directory(selected_dir)
    full_message = f"Current directory structure:\n{dir_map}\n\nCurrent context: {context}\n\nUser message: {message.content}"

    try:
        ai_response = send_msg(full_message)
        result, final_response = await process_ai_response(ai_response)

        return {"ai_response": final_response}
    except Exception as e:
        print(f"Error in send_message: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
