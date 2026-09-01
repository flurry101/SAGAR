# 🎙️ Voice Assistant Integration Guide (Frontend)

Hello! Since you don't have Docker installed to run the Vexyl Voice Gateway locally, I have securely exposed my running backend to the internet so you can test the frontend UI easily.

### Step 1: Update your Environment Variables
1. Open the `frontend` folder on your machine.
2. Find the `.env` file (create it if you only have `.env.example`).
3. Add or update the WebSocket URL to point to my secure tunnel:
   ```env
   VITE_VEXYL_WS_URL=wss://chatty-houses-play.loca.lt
   ```
*(Note: It must start with `wss://`, not `https://`!)*

### Step 2: Run the Frontend
Run the frontend just like you normally do:
```bash
npm run dev
```

### Step 3: Test the Voice Integration
Click the floating blue microphone button in the bottom-right corner of the website. 
Your audio will stream securely over the internet into my laptop's Docker container, process the response with the Copilot AI, and speak back to you!

---

**Troubleshooting:**
- If the button says "Disconnected" or fails to connect immediately, let me know! It means my laptop might have gone to sleep or the tunnel disconnected. I can easily generate a new link for you in 5 seconds.
- You do **not** need to touch anything in the `backend` folder. I am handling all of that on my end.
