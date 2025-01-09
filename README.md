# Cloud_File_Storage_System

This project implements a server for a file-sharing system. It allows multiple clients to connect and perform actions such as uploading, downloading, deleting, and retrieving metadata about shared files. It uses a multi-threaded architecture to handle multiple client connections simultaneously and provides a graphical user interface (GUI) for server-side monitoring.

Features
File Upload: Clients can upload files to the server, with existing files being overwritten as needed.
File Download: Clients can download files uploaded by other users. The uploader is notified upon a successful download.
File Deletion: Clients can delete files they've uploaded or files uploaded by other users (if authorized).
File List Retrieval: Clients can view a list of all available files on the server.
Metadata Storage: File metadata (uploader and file name) is stored persistently in a database file.
GUI for Server: The server includes a GUI for monitoring connected clients, log messages, and other operations.

How to Run?

1. Start the Server:
  Run the server script (server.py).
  Enter a port number in the GUI.
  Choose a directory to store files.
  Click the "Start Server" button.
2.Connect Clients:
Clients can connect to the server using the same port number.


Usage
Server-Side GUI
  - Port: Enter the port on which the server will listen for client connections.
  - Logs: The GUI displays logs for client connections, file operations, and errors.

Commands Supported by Clients
  - Upload: Send a file to the server.
  - Download: Request a file from the server.
  - Delete: Remove a file from the server's storage.
  - Retrieve Files: View all available files.


