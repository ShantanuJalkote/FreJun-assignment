import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, g

app = Flask(__name__)
app.config['DATABASE'] = 'calls.db'

def get_db():
    """
    Function to get the database connection.
    This function creates a new database connection if it doesn't exist, or returns the existing connection.

    Returns:
        The SQLite database connection.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """
    Function to close the database connection at the end of each request.
    """
    if hasattr(g, 'db'):
        g.db.close()

@app.route('/initiate-call', methods=['POST'])
def initiate_call():
    """
    Endpoint to initiate a call.
    This function accepts a POST request with 'from_number' and 'to_number' as JSON data in the request body.
    It then inserts the call details into the SQLite database and returns a success message.

    Returns:
        A JSON response indicating the success of the request.
    """
    try:
        # Get the call details from the request
        from_number = request.json.get('from_number')
        to_number = request.json.get('to_number')

        # Get the current timestamp
        start_time = datetime.now().isoformat()

        # Get the database connection
        conn = get_db()

        # Insert the call details into the database
        query = "INSERT INTO calls (from_number, to_number, start_time) VALUES (?, ?, ?)"
        conn.execute(query, (from_number, to_number, start_time))
        conn.commit()

        # Return the response
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify("Input not Valid", {"Sample Input":{"from_number": 10000000, "to_number": 111111111}}), 500

@app.route('/call-report', methods=['GET'])
def get_call_report():
    """
    Endpoint for call report.
    This function accepts a GET request with 'phone' as a query parameter.
    It then queries the SQLite database for calls involving the phone number and returns the call details in a paginated format.

    Returns:
        A JSON response containing the paginated call details.
    """
    # Get the phone number from the request
    phone = request.args.get('phone')
    if not phone:
        return jsonify({"success": False, "Provide query" : "phone"}), 500

    # Get the database connection
    conn = get_db()

    # Query the database for calls
    query = f"SELECT id, from_number, to_number, start_time FROM calls WHERE from_number = ? OR to_number = ?"
    rows = conn.execute(query, (phone, phone)).fetchall()

    # Pagination
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_calls = []
    for row in rows[start_index:end_index]:
        paginated_calls.append({
            "id": row['id'],
            "from_number": row['from_number'],
            "to_number": row['to_number'],
            "start_time": row['start_time']
        })

    # Return the response
    if not paginated_calls:
        return jsonify({"success": False, "phone": "Not Valid"}), 500

    return jsonify({
        "success": True,
        "data": paginated_calls
    })

# Endpoint for updating a call record
@app.route('/update-call/<int:id>', methods=['PUT'])
def update_call(id):
    """
    Endpoint for updating a call record.
    This function accepts a PUT request with 'from_number' and 'to_number' as JSON data in the request body and an 'id' parameter in the URL.
    It then updates the call record with the specified ID in the SQLite database with the new call details and returns a success message.

    Args:
        id: The ID of the call record to be updated.

    Returns:
        A JSON response indicating the success of the request or an error message if the call record was not found.
    """
    # Get the call details from the request
    from_number = request.json.get('from_number')
    to_number = request.json.get('to_number')

    # Get the database connection
    conn = get_db()

    # Check if the call exists
    query = "SELECT * FROM calls WHERE id = ?"
    row = conn.execute(query, (id,)).fetchone()
    if not row:
        return jsonify({"error": "Call not found"}), 404

    # Update the call details in the database
    query = "UPDATE calls SET from_number = ?, to_number = ? WHERE id = ?"
    conn.execute(query, (from_number, to_number, id))
    conn.commit()

    # Return the response
    return jsonify("Call Record Updated", {"success": True})

# Endpoint for deleting a call record
@app.route('/delete-call/<int:id>', methods=['DELETE'])
def delete_call(id):
    """
    Endpoint for deleting a call record.
    This function accepts a DELETE request with an 'id' parameter in the URL.
    It then deletes the call record with the specified ID from the SQLite database and returns a success message.

    Args:
        id: The ID of the call record to be deleted.

    Returns:
        A JSON response indicating the success of the request or an error message if the call record was not found.
    """
    # Get the database connection
    conn = get_db()

    # Check if the call exists
    query = "SELECT * FROM calls WHERE id = ?"
    row = conn.execute(query, (id,)).fetchone()
    if not row:
        return jsonify({"error": "Call not found"}), 404

    # Delete the call record from the database
    query = "DELETE FROM calls WHERE id = ?"
    conn.execute(query, (id,))
    conn.commit()

    # Return the response
    return jsonify("Call Record Deleted", {"success": True})

if __name__ == '__main__':
    # Create the database table if it doesn't exist
    with sqlite3.connect(app.config['DATABASE']) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS calls (
                id INTEGER PRIMARY KEY,
                from_number TEXT NOT NULL,
                to_number TEXT NOT NULL,
                start_time TEXT NOT NULL
            )
        """)

    app.run(debug=True)
