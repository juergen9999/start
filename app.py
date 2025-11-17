from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import urllib.request, json
import cgi, cgitb
import numpy as np
import pandas as pd
from cleantext import clean
from math import log
import re
import spacy
import ssl
ssl._create_default_https_context = ssl._create_stdlib_context
app = Flask(__name__)

forms=cgi.FieldStorage()

words = open("words-by-frequency.txt").read().split()
food_words = open("food.txt").read().split()
nlp = spacy.load("en_core_web_sm")

def classify_edible(item):
    # edible_keywords = [
    #     'food', 'edible', 'eat', 'consume', 'taste', 'ingest', 'nutrition',
    #     'digest', 'swallow', 'nourishment', 'snack', 'meal', 'drink'
    # ]

    for keyword in food_words:
        if (keyword == item.lower()): # redifine equal as "similar"
            return "Edible"

    return "Not Edible"

def is_noun(string):
    doc = nlp(string)

    for token in doc:
        if token.pos_ == "NOUN":
            return True

    return False

def best_match(i, s):
        wordcost = dict((k, log((i+1)*log(len(words)))) for i,k in enumerate(words))
        maxword = max(len(x) for x in words)
        candidates = enumerate(reversed(cost[max(0, i-maxword):i]))
        return min((c + wordcost.get(s[i-k-1:i], 9e999), k+1) for k,c in candidates)

def infer_spaces(s):
    """Uses dynamic programming to infer the location of spaces in a string
    without spaces."""

    # Find the best match for the i first characters, assuming cost has
    # been built for the i-1 first characters.
    # Returns a pair (match_cost, match_length).

    # Build the cost array.
    global cost
    cost = [0]
    for i in range(1,len(s)+1):
        c,k = best_match(i, s)
        cost.append(c)

    # Backtrack to recover the minimal-cost string.
    out = []
    i = len(s)
    while i>0:
        c,k = best_match(i, s)
        assert c == cost[i]
        out.append(s[i-k:i])
        i -= k

    return " ".join(reversed(out))

def clean_ingredients(ingredients):
    text =""
    for i in ingredients:
        text += (i + ",")
    text = text.replace(" ", "")

    regex = re.compile('[^a-zA-Z]')
    regex.sub('', 'ab3d*E')
    text = regex.sub('', text)
    text = text.lower()
    text = infer_spaces(text)
    text = text.replace(" sauce", "_sauce")
    text = text.replace(" sugar", "_sugar")
    text = text.replace(" oil", "_oil")
    text = text.replace(" juice", "_juice")

    nlp = spacy.load("en_core_web_sm")
    set_ingredients = set()
    items = text.split(' ')

    for item in items:
        classification = classify_edible(item)
        if((classification=="Edible")and(is_noun(item))):
            set_ingredients.add(item)
            #print(f"{item}: {classification}")

    set_ingredients.discard("teaspoon")
    set_ingredients.discard("teaspoons")
    set_ingredients.discard("tablespoon")
    set_ingredients.discard("tablespoons")
    set_ingredients.discard("pieces")
    set_ingredients.discard("piece")

    final_str = ""

    for val in set_ingredients:
        final_str += val + ","

    final_str = final_str[:-1]
    return final_str

def from_url_get_otherRareRecipes(diet, ingredients):
    # request recipes with Rare ingredients variable
    #Recipes requested = 3
    # ignore common pantry items bc they are common

    # url = "https://api.edamam.com/api/recipes/v2?app_id=fd727a17&app_key=3db153f6a682953219a9bb02b92537f9&q={}&health={}&type=any".format(os.environ.get("Rare_Ingredients"), health)
    url = "https://api.edamam.com/api/recipes/v2?app_id=fd727a17&app_key=3db153f6a682953219a9bb02b92537f9&q={ingredients}&health={health}&type=any".format(ingredients=ingredients, health=diet)
    if diet == 'none':
        url = "https://api.edamam.com/api/recipes/v2?app_id=fd727a17&app_key=3db153f6a682953219a9bb02b92537f9&q={ingredients}&type=any".format(ingredients=ingredients)
    response = urllib.request.urlopen(url)   
    recipes = response.read()
    dict = json.loads(recipes)

    # make empty array for recipes (can use recipes bc you loaded it into dict)
    recipes = []


    # get the title of recipes
    for recipe in dict["hits"]:
        print(recipe["recipe"]["ingredientLines"])
        recipe = {
          "recipeName" : recipe["recipe"]["label"],
           "urlLink" : recipe["recipe"]["url"],
           "ingredients": recipe["recipe"]["ingredients"],
        }
        recipes.append(recipe)

    
    return recipes
    #return "<p>" + str(recipes) +  "</p>"


@app.route('/', methods=["GET", "POST"])
def home():
    return render_template('home.html')

@app.route('/result', methods=["GET", "POST"])
def result():
    if request.method == "POST":
        url = request.form.get("url")

        if url:
            response = requests.get(url)
            diet = request.form.get("dietary-restriction")

            html_content = response.content
            soup = BeautifulSoup(html_content, 'html.parser')
            ingredient_elements = soup.find_all(class_ = lambda c: c and "ingredient" in c.lower())
            ingredients = [element.get_text(strip=True)+"," for element in ingredient_elements]

            if ingredients:
                print(diet)
                ingred = clean_ingredients(ingredients)
                recipes = from_url_get_otherRareRecipes(diet, ingred)
                return render_template('result.html', recipes = recipes)

        return render_template('invalid.html')

if __name__ == '__main__':
        app.run()

