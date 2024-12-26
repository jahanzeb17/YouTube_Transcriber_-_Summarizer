import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import re

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompt for summarization
prompt = """You are a YouTube video summarizer. You will take the transcript text
and summarize the entire video, providing the important summary in points
within 250 words. Please provide the summary of the text given here: """

# extract video ID from a YouTube URL
def extract_video_id(youtube_video_url):
    """
    Extracts the YouTube video ID from various YouTube URL formats.
    """
    pattern = r"(?:v=|/v/|youtu\.be/|/embed/|watch\?v=|watch/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, youtube_video_url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid YouTube URL. Could not extract video ID.")

# fetch video metadata
def get_video_metadata(video_id):
    """
    Fetches video metadata like title and channel name using YouTube's oEmbed endpoint.
    """
    try:
        response = requests.get(f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json")
        if response.status_code == 200:
            data = response.json()
            return data.get("title"), data.get("author_name")
        else:
            return "Unknown Title", "Unknown Channel"
    except Exception as e:
        return "Unknown Title", "Unknown Channel"

# transcript data from YouTube videos
def extract_transcript_details(video_id):
   
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item["text"] for item in transcript_list])
        return transcript
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

# generate summary
def generate_gemini_content(transcript_text, prompt):
   
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + transcript_text)
    return response.text

# Streamlit app layout
st.title("YouTube Video Transcriber and Summarizer")

# Input YouTube link
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    try:
        video_id = extract_video_id(youtube_link)

        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)

        title, channel = get_video_metadata(video_id)
        st.markdown(f"**Title:** {title}")
        st.markdown(f"**Channel:** {channel}")

        if st.button("Generate Transcript and Summary"):
            transcript_text = extract_transcript_details(video_id)

            if "Error" in transcript_text:
                st.error(transcript_text)
            else:
                with st.spinner("Generating summary..."):
                    summary = generate_gemini_content(transcript_text, prompt)
                
                st.markdown("### Transcript")
                st.text_area("Transcript", transcript_text, height=300, disabled=True)
                st.download_button("Download Transcript", transcript_text, file_name="Transcript.txt", mime="text/plain")

                st.markdown("### Summary")
                st.write(summary)

                st.download_button("Download Summary", summary, file_name="summary.txt", mime="text/plain")

    except ValueError as ve:
        st.error(str(ve))