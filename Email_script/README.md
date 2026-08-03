
"""
Bulk Resume Emailer
--------------------
A simple desktop GUI to send your resume to a list of email addresses via Gmail.

SETUP (one-time):
1. Go to https://myaccount.google.com/apppasswords
   - You must have 2-Step Verification turned on for your Google account.
   - Create an "App Password" for "Mail". Google gives you a 16-character code.
   - Use THAT code in this app, NOT your normal Gmail password.
2. Run this script:  python email_sender.py
   (Requires only Python's built-in libraries — nothing extra to install.)

USAGE:
- Paste recipient emails (one per line, or comma-separated).
- Pick your resume file (PDF/DOCX/etc).
- Edit the subject/body if you like (defaults are provided).
- Click "Send Emails". Progress is shown live; a summary pops up at the end.

NOTES:
- If you check "Remember me", your Gmail address + app password are saved
  in PLAIN TEXT to credentials.json next to this script, on YOUR machine
  only. Nothing is sent anywhere else. Delete that file any time to forget
  the login. Leave the box unchecked to keep it memory-only (default).
- Gmail's free-tier daily sending limit is ~500 emails/day. For a job
  outreach list this won't be an issue.
- Sends are done one-by-one with a short delay to avoid tripping spam
  filters / rate limits.
"""
