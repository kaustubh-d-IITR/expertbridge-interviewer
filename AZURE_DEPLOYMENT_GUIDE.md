# How to Fix Your Azure Deployment for ExpertBridge

## The Problem
Your current Azure deployment (`gpt-audio`) is designed for **Speech Input/Output Only**.
Our system sends **Text** (from Deepgram) to the brain, but `gpt-audio` rejects it with Error 400: *"This model requires... audio."*

**Solution:** You need a standard **Text/Multimodal** model like `gpt-4o` or `gpt-4o-mini`.

---

## Step-by-Step Fix (Azure AI Foundry)

1.  **Log in to Azure AI Foundry**
    - Go to [https://ai.azure.com/](https://ai.azure.com/)
    - Select your project (e.g., `expertbridge-foundry`).

2.  **Go to Deployments**
    - In the left sidebar, click on **Deployments** (under "My assets" or "Management").

3.  **Create New Deployment**
    - Click the **+ Create deployment** button.
    - Select **From base models**.

4.  **Select the Correct Model**
    - In the search bar, type `gpt-4o`.
    - **CRITICAL:** Select the standard **`gpt-4o`** (or `gpt-4o-mini`).
    - **DO NOT** select anything with "Audio" or "Realtime" in the name.
    - Click **Confirm**.

5.  **Configure Deployment**
    - **Deployment Name:** `gpt-4o`
      *(Keep it simple. Lowercase, no spaces).*
    - **Model Version:** Select `2024-05-13` (or the latest "Default" option).
    - **Tokens per Minute Rate Limit:** Set to default (e.g., 10k or 30k).
    - Click **Deploy**.

6.  **Wait 1 Minute**
    - The deployment will say "Succeeded" quickly.

---

## Update Your Secrets

Once the deployment is created, go back to your **Streamlit App code**.

1.  Open `.streamlit/secrets.toml` (or your `.env` file).
2.  Update the **Deployment Name** to match exact name you just created:

```toml
# ... other keys ...
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4o"
```

3.  **Reboot the App.**
4.  It will now work perfectly!
