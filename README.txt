YOUR PLAN — TERMUX INSTALLATION

This is a local personal finance tracker built with Python, Flask, and SQLite.
It tracks income, daily spending, savings deposits, and a savings goal. Currency display is PHP (₱).

1. Install Termux from a trusted source such as F-Droid or the official Termux GitHub.
2. Open Termux and run:

   pkg update && pkg upgrade -y
   pkg install python -y
   pip install flask
   mkdir -p ~/your-plan
   cd ~/your-plan

3. Put app.py in ~/your-plan.
   If you downloaded the ZIP, extract it and copy app.py into that folder.

4. Start the app:

   python app.py

5. Open your Android browser and visit:

   http://127.0.0.1:5000

To stop the server, return to Termux and press CTRL+C.

Your data is saved in your-plan.db beside app.py. Back up this file regularly.
The app is intended for local use on your phone. Do not expose the server to the public internet.
This is a basic tracker, not a bank connection or a substitute for professional financial advice.
