# Import necessary libraries
import tkinter as tk
import socket
import threading
import os
from tkinter import filedialog, messagebox
import time


# Global variables
connected = False
filename= " "
folderpath = " "
terminating = False

# Initialize the main window
initial = tk.Tk()
initial.title("Client Configuration")


top_frame = tk.Frame(initial)
top_frame.grid(row=0, column=0, pady=5, padx=5, sticky="w")

ip_label = tk.Label(top_frame, text="IP:")
ip_label.grid(row=0, column=0, padx=5, pady=2)

ip_entry = tk.Entry(top_frame)
ip_entry.grid(row=0, column=1, padx=5, pady=2)

port_label = tk.Label(top_frame, text="Port:")
port_label.grid(row=1, column=0, padx=5, pady=2)

port_entry = tk.Entry(top_frame)
port_entry.grid(row=1, column=1, padx=5, pady=2)

username_label = tk.Label(top_frame, text="Username:")
username_label.grid(row=2, column=0, padx=5, pady=2)

username_entry = tk.Entry(top_frame)
username_entry.grid(row=2, column=1, padx=5, pady=2)

# Middle Frame for File Name Entry and Buttons
middle_frame = tk.Frame(initial)
middle_frame.grid(row=1, column=0, pady=5, padx=5)


file_name_entry = tk.Entry(middle_frame, width=40)
file_name_entry.grid(row=0, column=0, columnspan=2, padx=5, pady=2)
file_name_entry.insert(0, "Enter file name")


# Bottom Frame for Logs and Connection Buttons
bottom_frame = tk.Frame(initial)
bottom_frame.grid(row=2, column=0, pady=5, padx=5)

logs = tk.Text(bottom_frame, height=15, width=50)
logs.grid(row=0, column=0, columnspan=3, padx=5, pady=2)

def log_message(message):
    """
    Logs a message in the logs text area.
    Parameters:
    - message (str): The message to display in the logs
    """
    global logs 
    logs.insert(tk.END, message + "\n")
    logs.see(tk.END)

def upload_file():
    """
    Handles uploading a file to the server.
    """
    global file_path, client_socket
    try:

        client_socket.sendall("Upload".encode()) # Send upload command to the server

        if not file_path:
            log_message("no file")
            return
        
        short_file_name = os.path.basename(file_path) # Get the file name without the path
        log_message(f"Uploading file: {short_file_name}")

        client_socket.sendall(short_file_name.encode())   # Send the file name to the server
        time.sleep(0.1)  # Add a short delay
        with open(file_path, "rb") as f:

              # Read the first chunk of 1024 bytes
            while True:
                file_chunk = f.read(1024)
                if not file_chunk:  
                    break        # Continue as long as there is data in the chunk
                client_socket.sendall(file_chunk)  # Send the chunk to the server
                       
        client_socket.sendall(b"EOF")

        response = client_socket.recv(1024).decode() # Receive server response
        
        if "Overwriting" in response:
            log_message(f"Server response: {response}")
        elif "upload complete" in response:
            log_message(f"Server response: {response}")

        
                  
    except Exception as e:
        log_message(f"Error sending file: {e}")

def browse_file():
    """
    Opens a file dialog for the user to select a file to upload.
    """
    global file_path
    file_path = filedialog.askopenfilename(title="Select a File")
    if file_path:
        short_file_name = os.path.basename(file_path)
        log_message(f"Selected file: {short_file_name}")


def disconnect():
    """
    Disconnects the client from the server and resets the GUI state.
    """
    global client_socket, connected
    if connected:
        try:
            # Send the disconnect command to the server
            client_socket.sendall("disconnect".encode())
            
            client_socket.close()
            log_message("Disconnected from the server.")
            connected = False
             # Disable buttons and reset the GUI state
            send_button.config(state="disabled")
            browse_button.config(state="disabled")
            disconnect_button.config(state="disabled")
            connect_button.config(state="normal")
        except Exception as e:
             # Log any errors encountered during disconnection
            log_message(f"Error during disconnection: {e}")

browse_button = tk.Button(middle_frame, text="Browse", state="disabled", command=browse_file)
browse_button.grid(row=1, column=0, padx=5, pady=2)

def listen_for_server():
    """
    Listens for messages from the server and handles disconnection.
    """
    global connected
    client_socket.settimeout(5)
    try:
        while connected:
            try:
                message = client_socket.recv(1024).decode()  # Listen for server messages
                if not message:
                    raise ConnectionError("Lost connection to the server.")
                """
                if message == "Server shutting down.":
                    log_message("Server has stopped. Disconnecting client.")
                    connected = False
                    disconnect()
                    
                    break
                """
                log_message(f"Server: {message}")
                #log_message("you are disconnected now")
            except socket.timeout:
                continue
                # Timeout occurred, no message received
             
    except (ConnectionError, OSError):
        # Handle server disconnection
        log_message("Connection to the server lost. Please reconnect.")
        connected = False
        # Disable buttons and reset the GUI state
        send_button.config(state="disabled")
        browse_button.config(state="disabled")
        disconnect_button.config(state="disabled")
        connect_button.config(state="normal")
        client_socket.close()



def connect_to_server():
    """
    Connects to the server using the provided IP, port, and username.
    """
    global client_socket, connected
    try:
        host = ip_entry.get()
        port = int(port_entry.get())
        username = username_entry.get()
        if not host or not port or not username:
            raise ValueError("Values are required")

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port)) # Connect to the server
        client_socket.sendall(username.encode()) # Send username to the server
        connected = True
        log_message(f"Connected to server at {host}:{port} as {username}")

        # Enable buttons for further actions
        send_button.config(state="normal")
        browse_button.config(state="normal")
        disconnect_button.config(state="normal")
        connect_button.config(state="disabled")
        listener_thread = threading.Thread(target=listen_for_server, daemon=True)
        listener_thread.start()

    except Exception as e:
        log_message(f"Error connecting to server: {e}")
    
def delete_file():
    """
    Sends a request to the server to delete a specified file.
    """
    global client_socket, connected, filename
    try:
        
        
        log_message("Sending delete command to server.")

        local_filename = file_name_entry.get().strip()
        

        uploading_client_name = tk.simpledialog.askstring(
            "Uploader Name", "Enter the name of the client who uploaded the file:"
        )
        print(uploading_client_name)

        if not local_filename or not uploading_client_name:
            log_message("Error: Filename or uploader's name not provided.")
            return


        
        client_socket.sendall("delete".encode()) # Send delete command
        time.sleep(0.1)  # Add a short delay
        delete_request = f"{local_filename}|{uploading_client_name}"
        client_socket.sendall(delete_request.encode())

        #client_socket.sendall(local_filename.encode())
        #client_socket.sendall(uploading_client_name.encode())
        
        log_message(f"Requested to delete file: {local_filename}")

        response = client_socket.recv(1024).decode().strip()
# Handle server response
        if response == "DELETE_SUCCESS":
            log_message(f"The file '{local_filename}' was deleted successfully.")
            
        elif response == "ERROR: File not found.":
            log_message(f"Server response: {response}")
        else:
            log_message(f"Unexpected response from server: {response}")

    
    except Exception as e:
        log_message(f"Error deleting file: {e}")

delete_button = tk.Button(middle_frame, text="Delete File", command=delete_file)
delete_button.grid(row=1, column=1, padx=5, pady=2)



def select_download_folder():
    """
    Opens a folder dialog for the user to select a folder where downloaded files will be saved.
    """
    global folderpath
    folderpath2 = filedialog.askdirectory(title="Select Folder to Save Files")
    if folderpath:
        log_message(f"Selected folder for downloads: {folderpath2}")
        return folderpath2



def download_file():
    """
    Sends a request to the server to download a specified file and saves it to the selected folder.
    """
    global client_socket
    try:
        # Prompt the user to select a folder for saving the downloaded file
        folderpath2 = select_download_folder()

        log_message("downloading")
        # Ensure a folder is selected

        if not folderpath2:
            log_message("select a folder first!")
            return
        
        # Get the file name to download from the user input
        local_filename = file_name_entry.get().strip()
        # Prompt the user for the name of the uploader of the file
        uploading_client_name = tk.simpledialog.askstring(
            "Uploader Name", "Enter the name of the client who uploaded the file:"
        )
        print(uploading_client_name)
# Check if both the file name and uploader name are provided
        if not local_filename or not uploading_client_name:
            log_message("Error: Filename or uploader's name not provided.")
            return
        
# Send the download command and necessary details to the server
        client_socket.sendall("download".encode())
        time.sleep(0.1)  # Add a short delay
        download_request = f"{local_filename}|{uploading_client_name}"
        client_socket.sendall(download_request.encode())
        #client_socket.sendall(uploading_client_name.encode())
        log_message(f"Sent download request: {download_request}")  # Debug print

# Receive the server's initial response
        response = client_socket.recv(200).decode().strip()
        log_message(f"Received server response: {response}")
         # Handle server response
        if response == "ERROR: File not found." or response == "ERROR: File does not exist on server.":
            log_message(f"Server response: {response}")
            return

        if response == "download_success":
            log_message(f"Downloading file: {local_filename}")
        # Construct the full path for saving the downloaded file
        file_path = os.path.join(folderpath2, local_filename)


# Open the file in write-binary mode and write the received data
        with open(file_path, "wb") as f:
                while True:
                    file_chunk = client_socket.recv(1024)  # Receive file data in chunks
                    if file_chunk == b"EOF": # Check for end-of-file indicator
                        break
                    f.write(file_chunk) # Write the data to the file

        time.sleep(0.1)  # Add a short delay
        log_message(f"File '{local_filename}' successfully downloaded and saved to '{file_path}'")
       # else:
       #     log_message(f"Unexpected response from server: {response}")
    except Exception as e:
        log_message(f"Error downloading file: {e}")          

download_button = tk.Button(middle_frame, text="Download File", command=download_file)
download_button.grid(row=2, column=0, columnspan=2, padx=5, pady=2)

def get_existing_files():
    """
    Sends a request to the server to retrieve a list of existing files.
    """
    try:
        # Send request to the server
        client_socket.sendall("retrieve_files".encode())

        # Receive the response
        response = client_socket.recv(4096).decode().strip()

        # Handle the response
        if response == "No files found.":
            log_message("No files available for your account.")
        elif response.startswith("ERROR"):
            log_message(f"Server error: {response}")
        else:
            log_message("Files available on the server:")
            files = response.split("\n") # Split the response into individual file entries
            for file in files:
                log_message(file)
    except Exception as e:
        log_message(f"Error retrieving files: {e}")


retrieve_button = tk.Button(middle_frame, text="Retrieve Files", command=get_existing_files)
retrieve_button.grid(row=3, column=0, columnspan=2, padx=5, pady=2)







connect_button = tk.Button(bottom_frame, text="Connect", command=connect_to_server)
connect_button.grid(row=1, column=0, padx=5, pady=2)

send_button = tk.Button(bottom_frame, text="Upload File", state="disabled", command=upload_file)
send_button.grid(row=1, column=1, padx=5, pady=2)

disconnect_button = tk.Button(bottom_frame, text="Disconnect", state="disabled", command=disconnect)
disconnect_button.grid(row=1, column=2, padx=5, pady=2)





# Handle window closing
def on_closing():
    
    if connected:
        disconnect()
    initial.destroy()

initial.protocol("WM_DELETE_WINDOW", on_closing)


# Run the application
initial.mainloop()

