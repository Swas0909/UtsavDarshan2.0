# TODO: Fix Google OAuth 400 Error

## Completed Tasks
- [x] Update config.py to load Google OAuth credentials from environment variables instead of hardcoding them.
- [x] Make the redirect URI configurable via environment variable.
- [x] Add debug logging in the callback function to see the exact error from Google.
- [x] Update app.py to use the configurable redirect URI and add logging.

## Pending Tasks
- [ ] Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in your .env file.
- [ ] Ensure the GOOGLE_REDIRECT_URI matches exactly what's configured in Google Console.
- [ ] Test the login flow.
