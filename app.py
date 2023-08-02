import streamlit as st
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chat_models import ChatOpenAI
import requests
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import List, Optional, Type
from fuzzywuzzy import fuzz
import json
import os 
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

BASE_URL = os.getenv("BASE_URL")
openai_api_key=os.getenv("OPENAI_API_KEY")
TOKEN =os.getenv("TOKEN") #Trello's Token
API_KEY =os.getenv("API_KEY")

def get_all_boards():
    try:
        url = f'{BASE_URL}members/me/boards'
        query = {
            'key': API_KEY,
            'token': TOKEN
        }
        response = requests.get(url, params=query)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
    except ValueError as e:
        st.error(f"Error parsing response as JSON: {e}")
    return []

def get_all_members_on_board(board_id):
    url = f'{BASE_URL}boards/{board_id}/members'
    query = {
        'key': API_KEY,
        'token': TOKEN
    }
    response = requests.get(url, params=query)
    response.raise_for_status()
    return response.json()

def fuzzy_search_member(board_id, member_name):
    members = get_all_members_on_board(board_id)
    matches = [(member, fuzz.ratio(member_name, member['fullName'])) for member in members]
    best_match = max(matches, key=lambda match: match[1])
    return best_match[0] if best_match[1] > 40 else None


def get_all_lists_on_board(board_id):
    try:
        url = f'{BASE_URL}boards/{board_id}/lists'
        query = {
            'key': API_KEY,
            'token': TOKEN
        }
        response = requests.get(url, params=query)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
    except json.JSONDecodeError as e:
        st.error(f"Error decoding response as JSON: {e}")
    return []

def get_all_cards_on_board(board_id):
    try:
        url = f'{BASE_URL}boards/{board_id}/cards'
        query = {
            'key': API_KEY,
            'token': TOKEN
        }
        response = requests.get(url, params=query)
        response.raise_for_status()
        
        # Check if the server returned a response
        if response.status_code != 200:
            st.error(f"Error: Received status code {response.status_code}")
            return None

        # Check if the response is not empty
        if not response.text:
            st.error("Error: Received empty response")
            return None

        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
    except json.JSONDecodeError as e:
        st.error(f"Error decoding response as JSON: {e}")
    return None

def make_comment_on_card(card_id, comment):
    try:
        url = f'{BASE_URL}cards/{card_id}/actions/comments'
        query = {
            'key': API_KEY,
            'token': TOKEN,
            'text': comment
        }
        response = requests.post(url, params=query)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
    except ValueError as e:
        st.error(f"Error parsing response as JSON: {e}")
    return []

def move_card_to_list(card_id, list_id):
    try:
        url = f'{BASE_URL}cards/{card_id}'
        query = {
            'key': API_KEY,
            'token': TOKEN,
            'idList': list_id
        }
        response = requests.put(url, params=query)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
    except ValueError as e:
        st.error(f"Error parsing response as JSON: {e}")
    return []

def fuzzy_search_board(board_name):
    boards = get_all_boards()
    matches = [(board, fuzz.ratio(board_name, board['name'])) for board in boards]
    best_match = max(matches, key=lambda match: match[1])
    return best_match[0] if best_match[1] > 40 else None

def fuzzy_search_card(board_id, card_name):
    cards = get_all_cards_on_board(board_id)
    matches = [(card, fuzz.ratio(card_name, card['name'])) for card in cards]
    best_match = max(matches, key=lambda match: match[1])
    return best_match[0] if best_match[1] > 40 else None

def fuzzy_search_list(board_id, list_name):
    lists = get_all_lists_on_board(board_id)
    matches = [(lst, fuzz.ratio(list_name, lst['name'])) for lst in lists]
    best_match = max(matches, key=lambda match: match[1])
    return best_match[0] if best_match[1] > 40 else None

def move_card_to_list_fuzzy(board_name, card_name, list_name):
    board = fuzzy_search_board(board_name)
    if not board:
        st.write(f"No board found with name {board_name}")
        return
    card = fuzzy_search_card(board['id'], card_name)
    if not card:
        st.write(f"No card found with name {card_name}")
        return
    lst = fuzzy_search_list(board['id'], list_name)
    if not lst:
        st.write(f"No list found with name {list_name}")
        return
    move_card_to_list(card['id'], lst['id'])

def comment_on_card_fuzzy(board_name, card_name, comment):
    board = fuzzy_search_board(board_name)
    if not board:
        st.write(f"No board found with name {board_name}")
        return
    card = fuzzy_search_card(board['id'], card_name)
    if not card:
        st.write(f"No card found with name {card_name}")
        return
    make_comment_on_card(card['id'], comment)

def add_member_to_card_fuzzy(board_name, card_name, member_name):
    board = fuzzy_search_board(board_name)
    if not board:
        st.write(f"No board found with name {board_name}")
        return
    card = fuzzy_search_card(board['id'], card_name)
    if not card:
        st.write(f"No card found with name {card_name}")
        return
    member = fuzzy_search_member(board['id'], member_name)
    if not member:
        st.write(f"No member found with name {member_name}")
        return
    url = f'{BASE_URL}cards/{card["id"]}/idMembers'
    query = {
        'key': API_KEY,
        'token': TOKEN,
        'value': member['id']
    }
    response = requests.post(url, params=query)
    response.raise_for_status()
    return response.json()

def create_card_on_board_fuzzy(board_name, list_name, card_name):
    board = fuzzy_search_board(board_name)
    if not board:
        st.write(f"No board found with name {board_name}")
        return
    lst = fuzzy_search_list(board['id'], list_name)
    if not lst:
        st.write(f"No list found with name {list_name}")
        return
    url = f'{BASE_URL}cards'
    query = {
        'key': API_KEY,
        'token': TOKEN,
        'idList': lst['id'],
        'name': card_name
    }
    response = requests.post(url, params=query)
    response.raise_for_status()
    return response.json()

class FuzzySearchCardInput(BaseModel):
    """Input for Fuzzy Search Card."""

    board_id: str = Field(..., description="ID of the board")
    card_name: str = Field(..., description="Name of the card to search")

class FuzzySearchCardTool(BaseTool):
    name = "fuzzy_search_card"
    description = "Useful for when you need to find a card on a board using fuzzy search. You should input the board ID and the name of the card."

    def _run(self, board_id: str, card_name: str):
        best_match_card = fuzzy_search_card(board_id, card_name)

        return best_match_card

    def _arun(self, board_id: str, card_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = FuzzySearchCardInput

class FuzzySearchListInput(BaseModel):
    """Input for Fuzzy Search List."""

    board_id: str = Field(..., description="ID of the board")
    list_name: str = Field(..., description="Name of the list to search")

class FuzzySearchListTool(BaseTool):
    name = "fuzzy_search_list"
    description = "Useful for when you need to find a list on a board using fuzzy search. You should input the board ID and the name of the list."

    def _run(self, board_id: str, list_name: str):
        best_match_list = fuzzy_search_list(board_id, list_name)

        return best_match_list

    def _arun(self, board_id: str, list_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = FuzzySearchListInput


class MoveCardToListFuzzyInput(BaseModel):
    """Input for Move Card To List Fuzzy."""

    board_name: str = Field(..., description="Name of the board")
    card_name: str = Field(..., description="Name of the card")
    list_name: str = Field(..., description="Name of the list")

class MoveCardToListFuzzyTool(BaseTool):
    name = "move_card_to_list_fuzzy"
    description = "Useful for when you need to move a card to a list on a board using fuzzy search. You should input the board name, card name and list name."

    def _run(self, board_name: str, card_name: str, list_name: str):
        move_card_to_list_fuzzy(board_name, card_name, list_name)

    def _arun(self, board_name: str, card_name: str, list_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = MoveCardToListFuzzyInput


class CommentOnCardFuzzyInput(BaseModel):
    """Input for Comment On Card Fuzzy."""

    board_name: str = Field(..., description="Name of the board")
    card_name: str = Field(..., description="Name of the card")
    comment: str = Field(..., description="Comment to be added")

class CommentOnCardFuzzyTool(BaseTool):
    name = "comment_on_card_fuzzy"
    description = "Useful for when you need to comment on a card on a board using fuzzy search. You should input the board name, card name and the comment."

    def _run(self, board_name: str, card_name: str, comment: str):
        comment_on_card_fuzzy(board_name, card_name, comment)

    def _arun(self, board_name: str, card_name: str, comment: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = CommentOnCardFuzzyInput

# class CreateCardOnBoardInput(BaseModel):
#     """Input for Create Card On Board."""

#     board_name: str = Field(..., description="Name of the board")
#     card_name: str = Field(..., description="Name of the card to be created")

# class CreateCardOnBoardTool(BaseTool):
#     name = "create_card_on_board"
#     description = "Useful for when you need to create a card on a board. You should input the board name and the card name."

#     def _run(self, board_name: str, card_name: str):
#         created_card = create_card_on_board(board_name, card_name)

#         return created_card

#     def _arun(self, board_name: str, card_name: str):
#         raise NotImplementedError("This tool does not support async")

#     args_schema: Optional[Type[BaseModel]] = CreateCardOnBoardInput


class AddMemberToCardFuzzyInput(BaseModel):
    """Input for Add Member To Card Fuzzy."""

    board_name: str = Field(..., description="Name of the board")
    card_name: str = Field(..., description="Name of the card")
    member_name: str = Field(..., description="Name of the member to be added")

class AddMemberToCardFuzzyTool(BaseTool):
    name = "add_member_to_card_fuzzy"
    description = "Useful for when you need to add a member to a card on a board using fuzzy search. You should input the board name, card name and the member name."

    def _run(self, board_name: str, card_name: str, member_name: str):
        added_member = add_member_to_card_fuzzy(board_name, card_name, member_name)

        return added_member

    def _arun(self, board_name: str, card_name: str, member_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = AddMemberToCardFuzzyInput

class CreateCardOnBoardFuzzyInput(BaseModel):
    """Input for Create Card On Board Fuzzy."""

    board_name: str = Field(..., description="Name of the board")
    list_name: str = Field(..., description="Name of the list")
    card_name: str = Field(..., description="Name of the card to be created")

class CreateCardOnBoardFuzzyTool(BaseTool):
    name = "create_card_on_board_fuzzy"
    description = "Useful for when you need to create a card on a list on a board using fuzzy search. You should input the board name, list name and the card name."

    def _run(self, board_name: str, list_name: str, card_name: str):
        created_card = create_card_on_board_fuzzy(board_name, list_name, card_name)

        return created_card

    def _arun(self, board_name: str, list_name: str, card_name: str):
        raise NotImplementedError("This tool does not support async")

    args_schema: Optional[Type[BaseModel]] = CreateCardOnBoardFuzzyInput

tools = CommentOnCardFuzzyTool(), MoveCardToListFuzzyTool(), FuzzySearchListTool(), FuzzySearchCardTool(), AddMemberToCardFuzzyTool(), CreateCardOnBoardFuzzyTool()

llm = ChatOpenAI(temperature=0, model="gpt-4-0613", openai_api_key=openai_api_key)

agent = initialize_agent(tools, llm, agent=AgentType.OPENAI_FUNCTIONS, verbose=True)

st.title("Trello with Function Calling and Pydantic")

command = st.text_input("Input your command for Trello")
st.write("***Things you can do: Create a card, Move a card to a new list, Commment on a card, Add Members to cards***")

if st.button("Enter"):
    if command:
        # Process the command using the agent
        response = agent.run(command)
        st.write(response)