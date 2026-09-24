### Setup

This project was made in a uv environment. Learn about uv [here](https://docs.astral.sh/uv/). See `pyproject.toml`
for a list of required dependencies.

- Create a Mastadon application

- Make sure the following enviroment variables are set to valid values:
  ```
  MASTODON_API_KEY
  MASTODON_API_SECRET
  MASTODON_REDIRECT_URI
  MASTODON_API_ACCESS_TOKEN
  ```

### Running the Code

All functions can be run throug `main.py` with one command line argument. Make sure you are in the
same directory as the file (`src`). The different run modes are specified below:

```
python main.py get-access-token     # Get an access token for the platform crawler
python main.py crawl-keywords       # Crawl Mastodon for posts related to keywords in seeds.py
python main.py crawl-users          # Find users related to the natural disaster
python main.py info-graph           # Construct an information diffusion network from the collected posts
python main.py user-graph           # Construct a user network from the collected users
python main.py network-measures     # Get network measures and distributions from the user network
python main.py generate-wordcloud   # Generate a word cloud from llm_keywords.txt
```

### More Information

See `CSE_472__Project_I_Report__Abrams.pdf` for more information on data collection and analysis methods used in this project.
