// GET REAUEST IN JS


jsonMsg = {"TYPE" : "USERS" , "EMAIL" : "djndwwdwdw@gmail.com"}
const fetchPromise = fetch(`http://localhost:5555/check_node?message=${encodeURIComponent(JSON.stringify(jsonMsg))}`, {
    method: 'get',
    headers: {
        'Content-Type': 'application/json',
    }
});

let statusCode = 0;
let responseMessage;

fetchPromise
    .then(response => {
        //console.log(response);
        statusCode = response.status;
        console.log(statusCode);
        return response.json();
    })
    .then(data => {
        // Store the response result in a variable
        const responseMessage = data;
        console.log(responseMessage)
    })
    .catch((error) => {
        console.error('Error:', error);
    });




// POST REQUEST IN JS

/*
jsonMsg = {"TYPE" : "USERS" , "EMAIL" : "hwnjqndnqdwdwjhdekqw@gmail.com" , "PASSWORD" : '32edw2'}
const fetchPromise = fetch('http://localhost:5555/credentials', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify(jsonMsg)
});

let statusCode = 0;
let responseMessage;

fetchPromise
    .then(response => {
        //console.log(response);
        statusCode = response.status;
        return response.json();
    })
    .then(data => {
        // Store the response result in a variable
        const responseMessage = data;
        console.log(responseMessage)
    })
    .catch((error) => {
        console.error('Error:', error);
    });

*/

