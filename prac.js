const { google } = require('googleapis');

// Set up the Google Drive API client
const auth = new google.auth.GoogleAuth({
    keyFile: 'path/to/credentials.json',
    scopes: ['https://www.googleapis.com/auth/drive'],
});

const drive = google.drive({ version: 'v3', auth });

// Example: List all files in Google Drive
async function listFiles() {
    try {
        const response = await drive.files.list({
            pageSize: 10,
            fields: 'nextPageToken, files(id, name)',
        });

        const files = response.data.files;
        if (files.length) {
            console.log('Files:');
            files.forEach((file) => {
                console.log(`${file.name} (${file.id})`);
            });
        } else {
            console.log('No files found.');
        }
    } catch (error) {
        console.error('Error listing files:', error);
    }
}

// Call the function to list files
listFiles();