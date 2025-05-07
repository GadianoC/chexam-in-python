# How to Get a Valid Gemini API Key

The application is currently showing a 401 authentication error when trying to use the Gemini Vision API. This means the API key is either invalid, expired, or doesn't have the necessary permissions.

## Steps to Get a New API Key:

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click on "Get API key" or "Create API key"
4. Copy the generated API key

## Update Your .env File:

1. Create `.env` file in the root directory of the project
2. put `GEMINI_API_KEY=your_new_api_key_here` in the `.env` file
3. Save the file

## Important Notes:

- Keep your API key confidential and never share it publicly
- The API key in the `.env.example` file is just a placeholder and won't work
- Gemini API keys may have usage limits or expire after a certain period
- If you continue to see authentication errors, verify that your Google account has access to the Gemini API

After updating the API key, restart the application to apply the changes.
