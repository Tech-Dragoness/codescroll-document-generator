<?php
// database connection
$servername = "localhost";
$username = "root";
$password = "";
$dbname = "sophia_college_library_website"; // Replace with your actual database name

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// SQL query to fetch staff details
$sql = "SELECT staff_type, name, qualifications, position FROM faculty ORDER BY position, staff_type";
$result = $conn->query($sql);

$faculty = [];

if ($result->num_rows > 0) {
    while($row = $result->fetch_assoc()) {
        $faculty[] = $row;
    }
} else {
    echo "No faculty records found.";
}

$conn->close();

// Convert faculty data to JSON for easy access in the frontend
echo json_encode($faculty);
?>
