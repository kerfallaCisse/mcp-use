# Example of an MCP server runing in SSE

This is an example of an MCP server capable of reading and writting notes to user notes.

The client initialize the connection with the MCP server via a **GET** request to [http://localhost:5000/sse](http://localhost:5000/sse).

All the messages with the client and server are handle through a **POST** request to [http://localhost:5000/messages](http://localhost:5000/messages).

Follow the instuctions in this [README](../README.md) to setup the virtual environment.

To launch the notes server : `python app.py`
