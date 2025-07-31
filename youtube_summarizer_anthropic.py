import os
import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import requests

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import tiktoken
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Environment variable
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def sanitize_filename(name: str) -> str:
    """Remove or replace invalid filename characters."""
    return re.sub(r'[<>:"/\\|?*]', '', name).replace(' ', '_')

class YouTubeSubtitleSummarizer:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.max_tokens_per_chunk = 3000

    def extract_video_id(self, url: str) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if parsed.hostname == "youtu.be":
            return parsed.path[1:]
        if "v" in query:
            return query["v"][0]
        raise ValueError(f"Cannot extract video ID from URL: {url}")

    def extract_playlist_ids(self, url: str) -> List[str]:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if "list" in query:
            playlist_id = query["list"][0]
            logging.info(f"Detected playlist ID: {playlist_id}")
            # NOTE: This uses a placeholder — replace with YouTube Data API for real playlist support
            raise NotImplementedError("Playlist support requires YouTube Data API integration.")
        return []

    def get_subtitles(self, video_id: str) -> str:
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try native English
            try:
                transcript = transcript_list.find_transcript(["en"])
                if not transcript.is_generated:
                    logging.info("✓ Found official English subtitles")
                    return self._format_transcript(transcript.fetch())
            except:
                pass

            # Try auto-generated English
            try:
                transcript = transcript_list.find_generated_transcript(["en"])
                logging.info("✓ Found auto-generated English subtitles")
                return self._format_transcript(transcript.fetch())
            except:
                pass

            # Try translations
            for transcript in transcript_list:
                try:
                    translated = transcript.translate("en")
                    logging.info(f"✓ Translated subtitles from {transcript.language_code}")
                    return self._format_transcript(translated.fetch())
                except:
                    continue

            raise Exception("No English or translatable subtitles found.")
        except Exception as e:
            raise RuntimeError(f"Subtitle extraction failed: {e}")

    def _format_transcript(self, raw: List[Dict]) -> str:
        text = TextFormatter().format_transcript(raw)
        return re.sub(r'\s+', ' ', text).strip()

    def count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def split_text(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, buffer = [], ""

        for sentence in sentences:
            test = f"{buffer} {sentence}".strip()
            if self.count_tokens(test) > self.max_tokens_per_chunk:
                if buffer:
                    chunks.append(buffer.strip())
                    buffer = sentence
                else:
                    words = sentence.split()
                    chunk = ""
                    for word in words:
                        test = f"{chunk} {word}".strip()
                        if self.count_tokens(test) > self.max_tokens_per_chunk:
                            if chunk:
                                chunks.append(chunk.strip())
                                chunk = word
                        else:
                            chunk = test
                    buffer = chunk
            else:
                buffer = test

        if buffer:
            chunks.append(buffer.strip())
        return chunks

    def summarize_chunk(self, text: str, part: int, total: int) -> str:
        system_msg = (
            "You are an expert in creating concise, educational summaries. "
            "Summarize this transcript segment using clear markdown structure, "
            "highlighting key concepts, insights, and examples. Use bullet points, "
            "headers, and bold formatting for key terms."
        )
        user_msg = (
            f"Summarize the following transcript (Part {part} of {total}):\n\n{text}"
        )

        try:
            # response = self.client.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[
            #         {"role": "system", "content": system_msg},
            #         {"role": "user", "content": user_msg}
            #     ],
            #     max_tokens=1000,
            #     temperature=0.3
            # )
            from openai import OpenAI

            client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            )
            response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://ichsanulamal.github.io/digital-garden", # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "Youtube Summarizer", # Optional. Site title for rankings on openrouter.ai.
            },
            extra_body={},
            model="mistralai/mistral-7b-instruct:free",
            messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"> ⚠️ Error summarizing part {part}: {e}"

    def merge_summaries(self, summaries: List[str], title: str) -> str:
        doc = f"# {title or 'YouTube Video Summary'}\n\n"
        doc += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        doc += f"*Total sections: {len(summaries)}*\n\n"

        if len(summaries) > 1:
            doc += "## Table of Contents\n\n"
            for i in range(len(summaries)):
                doc += f"- [Part {i+1}](#part-{i+1})\n"
            doc += "\n---\n\n"

        for i, summary in enumerate(summaries, 1):
            if len(summaries) > 1:
                doc += f"## Part {i}\n\n"
            doc += summary + "\n\n"
            if i < len(summaries):
                doc += "---\n\n"

        return doc

    def get_video_title(self, video_id: str) -> str:
        try:
            html = requests.get(f"https://www.youtube.com/watch?v={video_id}").text
            match = re.search(r"<title>([^<]+)</title>", html)
            if match:
                return re.sub(r" - YouTube$", "", match.group(1))
        except:
            pass
        return "YouTube Video Summary"

    def summarize_video(self, video_url: str) -> str:
        try:
            logging.info("Extracting video ID...")
            video_id = self.extract_video_id(video_url)
            title = self.get_video_title(video_id)

            logging.info("Fetching subtitles...")
            subtitles = self.get_subtitles(video_id)

            logging.info("Splitting into chunks...")
            chunks = self.split_text(subtitles)

            logging.info("Summarizing content...")
            summaries = [
                self.summarize_chunk(chunk, i + 1, len(chunks))
                for i, chunk in enumerate(chunks)
            ]

            final_doc = self.merge_summaries(summaries, title)
            output_file = sanitize_filename(title) + ".md"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_doc)

            logging.info(f"✓ Summary saved to: {output_file}")
            return output_file

        except Exception as e:
            logging.error(f"❌ Failed to summarize video: {e}")
            raise

def main():
    api_key = os.getenv("OPENAI_API_KEY") or input("Enter OpenAI API key: ")
    summarizer = YouTubeSubtitleSummarizer(api_key)
    url = input("Enter YouTube video or playlist URL: ")

    try:
        if "list=" in url:
            summarizer.extract_playlist_ids(url)  # Currently placeholder
        else:
            summary_file = summarizer.summarize_video(url)
            with open(summary_file, "r", encoding="utf-8") as f:
                preview = f.read(700)
                logging.info(f"\nPreview:\n{'-'*60}\n{preview}\n{'-'*60}")
    except Exception as e:
        logging.error(f"Processing failed: {e}")

if __name__ == "__main__":
    main()
