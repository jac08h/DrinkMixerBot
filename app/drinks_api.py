import requests
import os
import logging
from random import choice

from app.exceptions import *

MAX_INGREDIENTS_IN_DRINK = 16

logger = logging.getLogger(__name__)

try:
    api_key = os.environ['COCKTAIL_DB_API_KEY']
    api_url = f'https://www.thecocktaildb.com/api/json/v2/{api_key}/'
except KeyError:
    api_key = 1
    api_url = f'https://www.thecocktaildb.com/api/json/v1/{api_key}/'


is_empty = lambda s: (s is None or len(s) == 0)

def get_all_ingredients():
    """
    Return list of all available ingredients from API

    Returns:
        list

    Raises:
        APIError: error connecting to the API
    """
    url = f'{api_url}list.php?i=list'
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error('Error connecting to the API')
        raise APIConnectionError(url)

    data = r.json()
    ingredients = [d['strIngredient1'] for d in data['drinks']]
    logger.info(ingredients)

    return ingredients

def get_drink_by_id(drink_id):
    """
    Return drink info by id

    Args:
        drink_id (str)

    Returns:
        drink dict from API

    Raises:
        APIError: error connecting to the API
        InvalidUserInput: no drinks with the ingredient
    """
    url = f'{api_url}/lookup.php?i={drink_id}'

    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error('Error connecting to the API')
        raise APIConnectionError(url)

    try:
        data = r.json()
        return data['drinks'][0]
    except ValueError:
        raise InvalidUserInput(f'Invalid ingredient {drink_id}')

def get_random_drink():
    """
    Returns a random drink

    Returns:
        dict
    """

    url = f'{api_url}/random.php'
    try:
        r = requests.get(url)
        return r.json()['drinks'][0]
    except requests.exceptions.RequestException as e:
        logging.error('Error connecting to the API')
        raise APIConnectionError(url)

def get_drinks_by_ingredients(ingredients):
    """
    Returns list of drinks which contain the ingredient

    Args:
        ingredients (str)
    Returns:
        list[dicts]: list of dictionaries that contain info about the drink
            dict keys: strDrink, strDinkThumb, idDrink
    Raises:
        APIError: error connecting to the API
        InvalidUserInput: no drinks with the ingredients
    """
    url = f'{api_url}/filter.php?i={ingredients}'

    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        logging.error('Error connecting to the API')
        raise APIConnectionError(url)

    data = r.json()['drinks']
    if data == 'None Found':
        raise NoDrinksFound
    else:
        return data

def get_random_drink_id_by_ingredients(ingredients):
    """
    Get random drink from all drinks that contain the ingredients

    Args:
        ingredients (str)

    Returns:
        str - id of the random drink
    """
    drinks = get_drinks_by_ingredients(ingredients)
    random_drink = choice(drinks)

    return random_drink['idDrink']


def clean_up_ingredients(drink_dict):
    """
    Return dict with all ingredients (measure + name) in `ingredients` key.

    Args:
        drink_dict (dict): drink dict from API
    Returns:
        dict
    """

    ingredients_list = []
    for i in range(1, MAX_INGREDIENTS_IN_DRINK+1):
        ingredient = f'strIngredient{i}'
        measure = f'strMeasure{i}'

        if is_empty(drink_dict[ingredient]):
            break
        else:
            if is_empty(drink_dict[measure]):
                ingredients_list.append(drink_dict[ingredient])
            else:
                ingredients_list.append(f"{drink_dict[measure]} {drink_dict[ingredient]}")

    drink_dict['ingredients'] = '\n'.join(ingredients_list)
    return drink_dict


if __name__ == '__main__':
    x = get_random_drink_id_by_ingredients('vodka,orange_juice')
    print(x)
