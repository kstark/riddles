import interactions
import requests
from bs4 import BeautifulSoup
import os
import random
from urllib.parse import urlencode

PAGE_COUNT=445

def get_search_url_and_params(term: str):
    return f"https://www.riddles.com/search", {"word": term}


def get_page_url_and_params(page: int):
    return f"https://www.riddles.com/riddles", {"page": str(page)}


def get_result_soup(url: str, params: dict[str, str], follow_random_page=False):
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text)

    if follow_random_page:
        max_page = find_max_page(soup)
        if max_page != 1:
            params = params.copy()
            page = random.randint(1, max_page)
            params['page'] = str(page)
            response = requests.get(url, params=params)
            soup = BeautifulSoup(response.text)
    
    return soup


def get_riddles(soup):
    riddle_soups = soup.findAll('div', class_='panel', id=lambda x: x and x.startswith('riddle-'))
    return [extract_riddle(r) for r in riddle_soups]


def find_max_page(soup):
    try:
        page_soup = soup.find('ul', class_='pagination')
        max_page = page_soup.findAll('a', rel=None)[-1].text
        return int(max_page)
    except Exception:
        return 1

def extract_riddle(soup):
    question = soup.find(class_='hidden-print').next_sibling.strip()
    answer = soup.find(class_='collapse').text.strip()

    button = soup.find('button', class_='riddle-vote-y')
    if button:
        likes = int(button.attrs['data-value']) - 1
        dislikes = int(button.attrs['data-value2'])
    else:
        likes, dislikes = 0, 0
    return {
        "question": question,
        "answer": answer,
        "likes": likes,
        "dislikes": dislikes,
    }


def format_riddle(riddle: dict):
    return (
        f"{riddle['question']}\n\n"
        + f"||"
        + f"{riddle['answer']}\n"
        + f"👍{riddle['likes']:,} 👎{riddle['dislikes']:,}"
        + f"||"
    )

bot = interactions.Client(token=os.getenv("DISCORD_TOKEN"))

@bot.command(
    name="riddle",
    description="RIDDLES",
    options=[
        interactions.Option(
            name="search",
            description="Optional word to search for",
            type=interactions.OptionType.STRING,
            required=False,
        )
    ]
)
async def riddle(ctx: interactions.CommandContext, search: str):
    if search:
        url, params = get_search_url_and_params(search)
        soup = get_result_soup(url, params, follow_random_page=True)
    else:
        page = random.randint(1, PAGE_COUNT)
        url, params = get_page_url_and_params(page)
        soup = get_result_soup(url, params, follow_random_page=False)

    riddles = get_riddles(soup)
    if not riddles:
        await ctx.send(f"**Oops!**\n\nCouldn't find any riddles")
    else:
        result = random.choice(riddles)

        await ctx.send(format_riddle(result))

bot.start()
