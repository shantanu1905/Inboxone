# Inboxone

**InboxOne** is an AI-powered application designed to streamline your communication by consolidating emails, calendars, and contacts from multiple accounts into a single, easy-to-use interface. In today's fast-paced world, managing multiple email accounts and keeping track of various meetings and contacts can be overwhelming. We built InboxOne to address this challenge, providing a unified platform that not only organizes your communications but also enhances productivity with AI-driven features.

## Key Features
Our application leverages the **Nylas API**, which provides a single API for email, calendar, and contacts, making it possible to integrate and manage multiple accounts effortlessly. The AI functionalities in InboxOne, **powered by Google Gemini**, include:

- 📧 **Email Summarization:** Automatically generates concise summaries of lengthy email threads, helping you quickly understand the key points of conversations.
- ✍️ **AI-Generated Email Drafts:** Compose emails by providing simple prompts or instructions, with AI generating the full email content tailored to your needs.
- 📝 **Grammar Check:** Automatically detects and corrects grammatical errors in your emails, ensuring professional communication.
- 🤖 **Autoreply:** AI-generated responses to incoming emails, saving time and maintaining consistent communication.
- 📅 **Calendar Chatbot:** An AI-powered chatbot that answers questions about your schedule, such as upcoming meetings or events, directly from your calendar.
- 👥 **Multi-User Support:** InboxOne supports multiple users, allowing each user to create an account and manage their own emails, calendars, and contacts within the application.

## Technology Stack
- **Google Gemini:** Gemini API for  AI.
- **Nylas API:** Email, calendar, and contacts API.
- **Code:** For Backend FastAPI and Frontend ReactNative

## Setup Instructions
### Prerequisites:
- **Google Gemini Account:** Set up a API KEY for Google Gemini (It is all free to use ).
- **Nylas Account:** Create a Nylas account generate a key api , add your email provider account to nylas
- 
### Step-by-Step Setup
1. Clone the Repository:
   ```
   git clone https://github.com/shantanu1905/Inboxone.git
   ```
   
2. Add Secrets (Create a **.env** in Root folder/directory):
   ```
    HOST_URL = 127.0.0.1:8000
    
    JWT_SECRET=" Your Secret Key, it can be anything like hcbbcshh323rrd90ed&Y*^^$&" 
    #[GEMINI API KEY]
    GEMINI_API_KEYY= "Your Gemini Key Here"
   
    #[GMAIL CREDENTAILS]
    #[For this you have to create a app password in your gmail account, normal gmail password won't work]
   
    GMAIL_ADDRESS=" Your Gmail Address"
    GMAIL_PASSWORD="Your Gmail App Password"
    
    
    #[Nylas]
    API_URI = "https://api.us.nylas.com"
   
   ```
3. Create a Python Virtual Environment and Make it Active, then install required packages
   ```
   pip install -r requirements.txt
   ```
4. Navigate to **\api** path from root directory and run following command:
   ```
   python main.py
   ```
