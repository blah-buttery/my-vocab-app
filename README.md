# Vocab study web app
The Vocabulary Study Web App is a web-based learning tool designed to
empower users with advanced vocabulary through personalized and interactive
study sessions. It integrates with popular external resources like OpenAI's
whisper, chatgpt, and Merriam-Webster's dictionary. Creating a highly
interactive learning experience.

upload .csv file of word you want to learn the definintion of
study sessions
	-whisper records you say the definition, click card to see definition
	 and stop recording  
	-chatgpt grades your definition and gives you tips to improve
	-sm-2 algorithm schedules when you should study the word next

## Getting Started

from the "vocab app" directory run

flask --app vocab run --debug

### Prerequisites

Flask              3.0.
Jinja2             3.1.3
openai             1.14.1
supabase           2.4.0
