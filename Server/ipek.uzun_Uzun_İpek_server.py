
#Import necessary libraries 
import socket
import threading
from tkinter import Tk, Label, Button, Entry, filedialog, Listbox, END
import os

# Global variables
clients = {}  # Tracks connected clients: {client_name: socket}
client_sockets = []

server_socket = None
file_storage_path = None
files_dict = {}  
terminate = False
database = "database.txt" # Filename for storing metadata about uploaded files
database_file = None  #

def log_message(message):
    """Logs a message to the server's log box in the GUI.
    
    Args:
        message (str): The message to log.
    """
    global log_box
    
    log_box.insert(END, f"{message}\n")
    log_box.see(END)  # Automatically scroll to the latest message


def upload(client_name, client_socket):
    """
    Handles file upload from a client.
    Parameters:
    - client_name (str): Name of the client uploading the file
    - client_socket (socket): The socket object representing the client's connection
    """
    
    global files_dict, file_storage_path, database_file
    try:
        # Receive filename
        filename = client_socket.recv(1024).decode()

        # If no filename is received, send an error message to the client and log it
        if not filename:
            client_socket.sendall("ERROR: No filename received.".encode())
            log_message("ERROR: No filename received.")
            return

        # Construct the file path using client_name and filename
        file_path = os.path.join(file_storage_path, f"{client_name}_{filename}")

        # Check if the user has already uploaded a file with the same name
        if client_name in files_dict and filename in files_dict[client_name]:
            # Notify the client that the file will be overwritten
            client_socket.sendall(f"Overwriting file {filename}.".encode())
            log_message(f"File {filename} from {client_name} already exists. Overwriting.")
            # Remove the existing file
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            # Notify the client that the file upload process has started
            client_socket.sendall("File upload complete".encode())
            log_message(f"File {filename} from {client_name} upload initiated.")

        # Open the file in write-binary mode and start receiving file chunks
        with open(file_path, "wb") as f:
            while True:
                file_chunk = client_socket.recv(1024)
                if not file_chunk:
                    # If the connection is closed unexpectedly, log the issue and exit
                    log_message(f"Connection lost while receiving file '{filename}' from {client_name}.")
                    return
                if file_chunk.endswith(b"EOF"):  # 'EOF' marks the end of the file
                    f.write(file_chunk[:-3])  # Write the data excluding 'EOF'
                    break
                f.write(file_chunk) # Write the received chunk to the file
            log_message(f"File '{filename}' from {client_name} received and saved.")

        # Update the files dictionary to include the new file
        if client_name not in files_dict:
            files_dict[client_name] = []
        if filename not in files_dict[client_name]:
            files_dict[client_name].append(filename)

        # Update the database file to reflect the latest file uploads
            
        try:
         with open(database_file, "w") as db:
            # Write each client-file mapping to the database file
            for client_name, filenames in files_dict.items():
                for filename in filenames:
                    db.write(f"{client_name},{filename}\n")
        except Exception as e:
         log_message(f"Error updating database file: {e}")

    except Exception as e:
        # Log any errors that occur during the file upload process
        log_message(f"Error receiving file from {client_name}: {e}")




def delete(client_name, client_socket):
    """
    Handles file deletion requests from a client.
    Parameters:
    - client_name (str): The name of the client requesting the deletion
    - client_socket (socket): The socket object representing the client's connection
    """
     
    global files_dict, file_storage_path, database_file
    try:
        while True:
            log_message("Trying to delete")
            # Receive filename and uploader's name
            delete_request =  client_socket.recv(1024).decode()
            parts = delete_request.split('|')
            local_filename = parts[0]
            uploading_client_name  = parts[1]
            #local_filename = client_socket.recv(1024).decode()
            #uploading_client_name = client_socket.recv(1024).decode()

             # Check if both filename and uploader's name are provided
            if not local_filename or not uploading_client_name:
                client_socket.sendall("ERROR: Missing filename or uploader's name.".encode())
                log_message("Server: Missing filename or uploader's name.")
                return
            
            # Verify that the file exists in the server's records
            if uploading_client_name not in files_dict or local_filename not in files_dict[uploading_client_name]:
                client_socket.sendall("ERROR: File not found.".encode())
                log_message(f"Server: File '{local_filename}' not found or unauthorized access by {client_name}.")
                return
            
            # Construct the file path
            delete_file_path = os.path.join(file_storage_path, f"{uploading_client_name}_{local_filename}")

            if os.path.exists(delete_file_path):
                # Delete the file from the server's storage
                os.remove(delete_file_path)  
                log_message(f"File '{local_filename}' from {uploading_client_name} deleted successfully.")
                client_socket.sendall("DELETE_SUCCESS".encode())

                 # Update the files dictionary and database
                files_dict[uploading_client_name].remove(local_filename) 
                if not files_dict[uploading_client_name]: # Remove the key if no files remain
                    del files_dict[uploading_client_name]

                 # Update the database file to reflect the deletion
                    
                try:
                 with open(database_file, "w") as db:
                    for client_name, filenames in files_dict.items():
                      for filename in filenames:
                        db.write(f"{client_name},{filename}\n")
                except Exception as e:
                    log_message(f"Error updating database file: {e}")
            else:
                # If the file does not exist on the server, notify the client
                client_socket.sendall("ERROR: File not found on server.".encode())
                log_message("ERROR: File not found on server.")
            break

    except Exception as e:
        # Handle any exceptions and notify the client
        client_socket.sendall(f"DELETE_ERROR {e}".encode())
        log_message(f"Error during file deletion for {client_name}: {e}")

def download_file(client_socket, client_name):
    """
    Handles file download requests from a client.
    Parameters:
    - client_socket (socket): The socket object representing the client's connection
    - client_name (str): The name of the client requesting the download
    """
    ("hiiiiiiiiii")

    global files_dict, file_storage_path, clients
    try:
        log_message("hi")
        # Receive filename and uploader's name
        download_request =  client_socket.recv(1024).decode()
        log_message(f"Received download request: {download_request}")  # Debug print
        parts = download_request.split('|')
        localfilename = parts[0]
        uploading_client_name  = parts[1]
        log_message("received local file name and uploading client name")
        
        #localfilename = client_socket.recv(1024).decode()
        #uploading_client_name = client_socket.recv(1024).decode()

         # Check if both filename and uploader's name are provided
        if not localfilename or not uploading_client_name:
            client_socket.sendall("ERROR: Missing filename or uploader's name.".encode())
            log_message("Server: Missing filename or uploader's name.")
            return
        # Verify that the file exists in the server's records
        if uploading_client_name not in files_dict or localfilename not in files_dict[uploading_client_name]:
            client_socket.sendall("ERROR: File not found.".encode())
            log_message("ERROR: File not found.")
            return
        # Construct the file path
        file_path = os.path.join(file_storage_path, f"{uploading_client_name}_{localfilename}")

        if not os.path.exists(file_path):
             # If the file does not exist on the server, notify the client
            client_socket.sendall("ERROR: File does not exist on server.".encode())
            log_message("ERROR: File does not exist on server.")
            return
        log_message("trying to notify the uploader")
        # Notify the uploader about the download,
        
        if uploading_client_name in clients:
            uploader_socket = clients[uploading_client_name]
            try:
                notification = f"Your file '{localfilename}' was downloaded by {client_name}."
                uploader_socket.sendall(notification.encode())
                log_message(f"Notified uploader {uploading_client_name} about the download.")
            except Exception as e:
                log_message(f"Error notifying uploader: {e}")

        # Send download success message
        client_socket.sendall("download_success".encode())
        log_message(f"Sending file '{localfilename}' to {client_name}.")

        # Send the file data
        with open(file_path, "rb") as f:
            while True:
                file_chunk = f.read(1024)
                if not file_chunk:
                    break
                client_socket.sendall(file_chunk)
        client_socket.sendall(b"EOF") # Indicate end of file transfer
        log_message(f"File '{localfilename}' sent successfully to {client_name}.")

    except Exception as e:
         # Handle any exceptions and notify the client
        client_socket.sendall(f"ERROR: {e}".encode())
        log_message(f"Error during file download for {client_name}: {e}")

def retrieve_existing_file(client_socket, client_name):
    """
    Sends a list of all existing files on the server to the requesting client.
    Parameters:
    - client_socket (socket): The socket object representing the client's connection
    - client_name (str): The name of the client requesting the file list
    """

    global files_dict
    try:
        # If no files are found, notify the client
        if not files_dict:
            client_socket.sendall("No files found.".encode())
            log_message("No files found.")
            return
        
         # Prepare a list of all files with their respective uploaders
        file_list = []
        for owner, files in files_dict.items():
            for file in files:
                file_list.append(f"{file} (Uploaded by: {owner})")

         # Send the list of files to the client
        file_list_str = "\n".join(file_list)
        client_socket.sendall(file_list_str.encode())

        log_message(f"Sent file list to {client_name}.")

    except Exception as e:
        # Handle any exceptions and notify the client
        error_message = f"ERROR: {e}"
        log_message(f"Error while sending the list of filenames: {e}")
        client_socket.sendall(error_message.encode())

def client_commands(client_socket, client_name):
    global terminate
    """
    Handles commands sent by a connected client.
    Parameters:
    - client_socket (socket): The socket object representing the client's connection
    - client_name (str): The name of the client sending commands
    """
    
    try:
        while not terminate:
            # Receive a command from the client
            command = client_socket.recv(1024).decode()
            # If no command is received, log the disconnection and exit
            if not command:
                log_message(f"{client_name} disconnected.")
                break
            log_message(f"Received command: {command}") 

             # Match the command and execute the appropriate function
            if command == "Upload":
                upload(client_name, client_socket)
            elif command == "delete":
                delete(client_name, client_socket)
            elif command == "download":
                download_file(client_socket, client_name)
            elif command == "retrieve_files":
                retrieve_existing_file(client_socket, client_name)
            elif command == "disconnect":
                # Handle client disconnection
                client_socket.close()
                if client_name in clients:
                    del clients[client_name]
                log_message(f"{client_name} disconnected from server.")
                break
            else:
                 # Handle unknown commands
                #client_socket.sendall("ERROR: Unknown command.".encode())
                log_message(f"Unknown command '{command}' from {client_name}. burda mı sorun acabaaa")


    except Exception as e:
         # Log any errors that occur during command handling
        log_message(f"Error: {e}")
    finally:
        # Clean up on client disconnection
        if client_name in clients:
            del clients[client_name]
        client_socket.close()

def accept_clients():
    """
    Accepts incoming client connections and assigns a thread to handle their commands.
    """
    global server_socket, terminate
    while not terminate:
        try:
            # Accept a new client connection
            client_socket, client_address = server_socket.accept()
            if terminate:
                client_socket.close()
                break
            # Receive client name
            client_name = client_socket.recv(1024).decode()
            # Validate the client name
            if not client_name:
                log_message("Connection rejected: No client name received.")
                client_socket.close()
                continue

            if client_name in clients:
                # Reject duplicate client names
                client_socket.sendall(f"ERROR: Name '{client_name}' is already in use.".encode())
                log_message(f"Connection rejected: Name '{client_name}' is already in use.")
                client_socket.close()
            else:
                # Add the client to the list and start a thread for handling commands
                client_sockets.append(client_socket)
                clients[client_name] = client_socket
                threading.Thread(target=client_commands, args=(client_socket, client_name), daemon=True).start()
                log_message(f"{client_name} joined the server.")

        except Exception as e:
              # Log errors that occur while accepting clients
            if not terminate:
                log_message(f"Error accepting client: {e}")

def load_files_from_database():
    """
    Loads the existing file records from the database file into the `files_dict`.
    """
    global database_file, files_dict
    files_dict.clear()  # Clear the existing dictionary
    # Check if the database file exists
    if not os.path.exists(database_file):
        return

    with open(database_file, "r") as db:
           # Read each line in the database and update the files_dict
        for line in db:
            line = line.strip()
            if line:
                owner_name, filename = line.split(",", 1)
                if owner_name not in files_dict:
                    files_dict[owner_name] = []
                if filename not in files_dict[owner_name]:
                    files_dict[owner_name].append(filename)
# Initialize the main window
root = Tk()
root.title("Server Configuration")

Label(root, text="Port:").grid(row=0, column=0, padx=5, pady=5)
port_entry = Entry(root)
port_entry.grid(row=0, column=1, padx=5, pady=5)

def start_server():
    """
    Starts the server, initializes the database, and begins listening for clients.
    """
    global server_socket, file_storage_path, terminate, database_file
    terminate = False
    try:
        # Start server and begin listening for clients
         # Get the port number from the user
        port_input = port_entry.get().strip()
        if not port_input.isdigit():
            log_message("Error: Please enter a valid numeric port number.")
            return
        port = int(port_input)

        # Ask the user to select the file storage directory
        file_storage_path = filedialog.askdirectory(title="Select File Storage Directory")

        if not file_storage_path:
            log_message("You did not select the file path.")
            return
        
        # Initialize the database file
        database_file = os.path.join(file_storage_path, database)
        if not os.path.exists(database_file):
            with open(database_file, "w") as db:
                pass  # Create an empty database file

        # Load existing files from the database
        load_files_from_database()

         # Create and configure the server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(16)

        log_message(f"Server started listening on port {port}. Files will be saved in {file_storage_path}")
         # Start a thread to accept client connections
        accept_thread = threading.Thread(target=accept_clients, daemon=True)
        accept_thread.start()

    except Exception as e:
        # Log errors that occur during server startup
        if not terminate:
            log_message(f"Error starting server: {e}")

def stop_server():
    """
    Stops the server, closes all client connections, and cleans up resources.
    """
    global server_socket, terminate
    terminate = True # Set the terminate flag to true
    for client_socket in client_sockets:
        try:
            #client_socket.sendall("disconnect".encode()) 
            #client_socket.close()
            print("client socket closed")
        except Exception as e:
            log_message(f"Error closing client socket: {e}")
    if server_socket:
        try:
            client_socket.sendall("Server shutting down.".encode())
            server_socket.close() # Close the server socket
            server_socket = None
            print("server socket closed")
        except Exception as e:
            log_message(f"Error closing server socket: {e}")
    # Close all active client sockets

    
    log_message("Server stopped.")

log_box = Listbox(root, width=60, height=20)
log_box.grid(row=2, column=0, columnspan=2, padx=5, pady=5)

start_button = Button(root, text="Start Server", command=start_server)
start_button.grid(row=1, column=0, padx=5, pady=5)

stop_button = Button(root, text="Stop Server", command=stop_server)
stop_button.grid(row=1, column=1, padx=5, pady=5)

def on_closing():
    """
    Handles the event when the server GUI window is closed.
    """
    stop_server()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
