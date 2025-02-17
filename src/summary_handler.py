import json
import time
import boto3
import asyncio
import os
from datetime import datetime
from pathlib import Path


class SummaryHandler:
    """
    A class to handle real-time meeting summary generation using AWS Bedrock.

    This class manages the creation, updating, and display of meeting summaries
    by processing transcript data and generating summaries using AWS Bedrock's AI models.

    Attributes:
        bedrock_client: AWS Bedrock client instance
        summary_file (Path): Path to the output summary file
        transcript_file: Path to the transcript file being processed
        last_summary_time (float): Timestamp of last summary update
        current_display (str): Current summary content being displayed
        console_type (str): Type of console display mode
        prompt_template (str): Template for formatting summary prompts
    """

    def __init__(self, config: dict, console_type=None):
        """
        Initialize the SummaryHandler with AWS credentials and configuration.

        Args:
            config (dict): Configuration dictionary containing AWS credentials and settings
            console_type (str, optional): Type of console display to use. Defaults to None.
        """
        # Initialize AWS Bedrock client and setup summary handling
        self.bedrock_client = boto3.client(
            service_name='bedrock-runtime',
            region_name=config['region'],
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key']
        )
        self.summary_file = self.setup_summary_file()
        self.transcript_file = None
        self.last_summary_time = time.time()
        self.current_display = "Waiting for meeting content...\n"
        self.console_type = console_type
        self.prompt_template = self.load_prompt_template()
        
        if self.console_type == "summary":
            self.clear_and_print_initial()

    def clear_and_print_initial(self):
        """Clear the console and display the initial summary header."""
        os.system('cls' if os.name == 'nt' else 'clear')  # Handle both Windows and Unix
        print("=== Meeting Summary ===")
        print("\nInitializing...\n")
        print("============================")

    def create_prompt(self, conversation_text: str) -> str:
        """
        Create a formatted prompt for the Bedrock API using the conversation transcript.

        Args:
            conversation_text (str): The transcript text to be summarized

        Returns:
            str: Formatted prompt string for Bedrock
        """
        return f"""
        <direction>
        Create concise meeting notes from this transcript:
        </direction>
        <date>
        {datetime.now().strftime('%m-%d-%Y')}
        </date>
        <transcript>
        {conversation_text}
        </transcript>
        <format>
        {self.prompt_template}
        </format>
        <direction>
        After you've created your response, double-check one more time to make sure that you're following the template and not adding anything outside of
        what I asked for. It's very important that you check to remove any content or styling I specifically said I didn't want!!
        </direction>
        """
    async def display_summary(self):
        """
        Continuously monitor and update the meeting summary display.
        
        This asynchronous method checks for new transcript content every 5 seconds
        and generates updated summaries every 20 seconds when new content is available.
        
        Raises:
            Exception: If there's an error during summary generation or display
        """
        try:
            while True:
                current_time = time.time()
                if current_time - self.last_summary_time >= 20:  # Update summary every 20 seconds
                    conversation_text = self.format_conversation()
                    if conversation_text:
                        summary_update = await self.generate_summary(conversation_text)
                        if summary_update:
                            self.summary_file.write_text(summary_update)
                            self.update_display(summary_update)
                            self.last_summary_time = current_time
                await asyncio.sleep(5)  # Check for updates every 5 seconds
        except Exception as e:
            print(f"\nError in summary display: {e}")

    def format_conversation(self) -> str:
        """
        Read and format the content from the most recent transcript file.

        Returns:
            str: Formatted conversation text from the latest transcript,
                 or empty string if no transcript is available
        """
        transcript_dir = Path('output/transcripts')
        if transcript_dir.exists():
            transcript_files = list(transcript_dir.glob('transcript_*.txt'))
            if transcript_files:
                latest_transcript = max(transcript_files, key=lambda x: x.stat().st_mtime)
                with open(latest_transcript, 'r', encoding='utf-8') as transcript_reader:
                    return transcript_reader.read()
        return ""

    async def generate_summary(self, conversation_text: str) -> str:
        """
        Generate a summary of the conversation using AWS Bedrock.

        Args:
            conversation_text (str): The transcript text to be summarized

        Returns:
            str: Generated summary text
        """
        bedrock_prompt = self.create_prompt(conversation_text)
        return await self.invoke_bedrock(bedrock_prompt)
            
    async def invoke_bedrock(self, bedrock_prompt: str) -> str:
        """
        Make an API call to AWS Bedrock for summary generation.

        Args:
            bedrock_prompt (str): Formatted prompt for the Bedrock API

        Returns:
            str: Generated response from Bedrock API
        """
        bedrock_request = {
            "prompt": f"\n\nHuman: {bedrock_prompt}\n\nAssistant:",
            "max_tokens_to_sample": 2048,
            "temperature": 0.0,  # Use deterministic output
            "top_p": 1,
            "stop_sequences": ["\n\nHuman:"]
        }

        bedrock_response = self.bedrock_client.invoke_model(
            body=json.dumps(bedrock_request),
            modelId="anthropic.claude-v2",
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(bedrock_response['body'].read())
        return response_body.get('completion', '').strip()

    def load_prompt_template(self) -> str:
        """
        Load the custom prompt template from the configuration file.

        Returns:
            str: Content of the prompt template file
        """
        template_path = Path(__file__).parent.parent / 'config' / 'prompt_template.txt'
        with open(template_path, 'r', encoding='utf-8') as prompt_template:
            return prompt_template.read()
        
    def setup_summary_file(self) -> Path:
        """
        Create and initialize the summary file with timestamp.

        Returns:
            Path: Path object pointing to the created summary file
        """
        Path('output/meeting_notes').mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        summary_file = Path(f'output/meeting_notes/meeting_notes_{timestamp}.md')
        summary_file.write_text("Waiting for meeting content...\n")
        return summary_file

    def update_display(self, new_content: str):
        """
        Update the console display with new summary content.

        Args:
            new_content (str): New summary content to display
        """
        if new_content != self.current_display and self.console_type == "summary":
            os.system('cls' if os.name == 'nt' else 'clear')
            print("=== Meeting Summary ===\n")
            print(new_content)
            print("\n============================")
            print(f"\nLast updated: {datetime.now().strftime('%I:%M:%S %p')}")
            self.current_display = new_content