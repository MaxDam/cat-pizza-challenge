from cat.mad_hatter.decorators import hook, tool
from pydantic import BaseModel, Field, ValidationError, field_validator
import enum
from typing import Dict, Optional
from cat.log import log
from .conversational_form import ConversationalForm
import random

KEY = "pizza_challenge"

language = "Italian"

menu = {
    "Margherita": "Pomodoro, mozzarella fresca, basilico.",
    "Peperoni": "Pomodoro, mozzarella, peperoni.",
    "Romana": "Pomodoro, mozzarella, prosciutto.",
    "Quattro Formaggi": "Gorgonzola, mozzarella, parmigiano, taleggio.",
    "Capricciosa": "Pomodoro, mozzarella, prosciutto, funghi, carciofi, olive.",
    "Vegetariana": "Pomodoro, mozzarella, peperoni, cipolla, olive, melanzane.",
    "Bufalina": "Pomodoro, mozzarella di bufala, pomodorini, basilico.",
    "Diavola": "Pomodoro, mozzarella, salame piccante, peperoncino.",
    "Pescatora": "Pomodoro, mozzarella, frutti di mare (cozze, vongole, gamberi).",
    "Rucola": "Pomodoro, mozzarella, prosciutto crudo, rucola, scaglie di parmigiano."
}


# Pizza order object (from scratch implementation)
class PizzaOrder(BaseModel):

    pizza_type: str | None = None
    address: str | None = None
    phone: str | None = None
    
    @field_validator("pizza_type")
    @classmethod
    def validate_pizza_type(cls, pizza_type: str):
        log.info("VALIDATIONS")

        if pizza_type in [None, ""]:
            return

        pizza_types = list(menu.keys())

        if pizza_type not in pizza_types:
            raise ValueError(f"{pizza_type} is not present in the menù (translating everything in {language} language)")

    @classmethod
    def get_prompt_examples(cls):
        return [
            {
                "sentence": "I want to order a pizza",
                "json": [None, None, None],
                "updatedJson": [None, None, None]
            },
            {
                "sentence": "I live in Via Roma 1",
                "json": ["Margherita", None, None],
                "updatedJson": ["Margherita", "Via Roma 1", None]
            }
        ]


'''
# Pizza order object (for kor implementation)
class PizzaOrder(BaseModel):

    pizza_type: str = Field(
        default=None,
        description="This is the type of pizza.",
        examples=[
            ("I would like a Margherita", "Margherita"),
            ("I like Capricciosa", "Capricciosa")
        ],
    )
    address: str = Field(
        default=None,
        description="This is the address.",
        examples=[
            ("My address is via Pia 22", "via Pia 22"),
            ("I live in Via Roma 1", "Via Roma 1")
        ],
    )
    phone: str = Field(
        default=None,
        description="This is the telephone number.",
        examples=[
            ("My telephon number is 333123123", "333123123"),
            ("the number is 3493366443", "3493366443")
        ],
    )
'''    


# Order pizza start intent
@tool(return_direct=True)
def start_order_pizza_intent(details, cat):
    '''I would like to order a pizza
    I'll take a pizza'''

    log.critical("\n ----------- INTENT START ----------- \n")

    # create a new conversational form
    cform = ConversationalForm(model=PizzaOrder(), cat=cat, lang=language)
    #cform = ConversationalForm(model=PizzaOrder(pizza_type='', address='', phone=''), cat=cat, lang=language)
    cat.working_memory[KEY] = cform

    _, response = execute_dialogue(cform, cat)
    return response


# Order pizza stop intent
@tool()
def stop_order_pizza_intent(input, cat):
    '''I don't want to order pizza anymore, 
    I want to give up on the order, 
    go back to normal conversation'''

    del cat.working_memory[KEY]
    log.critical("\n ----------- INTENT STOP ----------- \n")
    return input


# Get pizza menu
@tool()
def ask_menu(input, cat):
    '''What is on the menu?
    Which types of pizza do you have?
    Can I see the pizza menu?
    I want a menu'''

    log.critical("\n ----------- INTENT MENU ----------- \n")
    response = "The available pizzas are the following:"
    for pizza, ingredients in menu.items():
        response += f"\n - {pizza} with the following ingredients: {ingredients}"
    response += f", (translating everything in {language} language)"

    return response


# Acquires user information through a dialogue with the user
@hook
def agent_fast_reply(fast_reply: Dict, cat) -> Dict:

    if KEY not in cat.working_memory.keys():
        log.critical("\n ----------- NO KEY ----------- \n")
        return fast_reply
        
    log.critical("\n ----------- INTENT ACTIVE ----------- \n")

    cform = cat.working_memory[KEY]

    # Execute the dialogue
    return_direct, response = execute_dialogue(cform, cat)

    # If return_direct => skip chain and return result
    if return_direct:
        return { "output": response }
        
    return


# TODO: hook to use instead of agent_fast_reply
@hook
def before_cat_reads_message(user_message_json: dict, cat) -> dict:
    #user_message_json["text"] = "my custom prompt"
    return user_message_json


# Execute the dialogue
def execute_dialogue(cform, cat):

    return_direct = True
    try:
        model_is_updated = cform.update_from_user_response()
        #if not model_is_updated: return_direct = False
    except ValidationError as e:
        message = e.errors()[0]["msg"]
        response = cat.llm(message)
        return_direct = True
        return return_direct, response

    if cform.is_completed():
        return_direct, response = execute_action(cform, cat)
        del cat.working_memory[KEY]
    else:
        cat.working_memory[KEY] = cform
        #return_direct, response = cform.ask_missing_information_without_chain()
        return_direct, response = cform.ask_missing_information_with_chain()

    return return_direct, response


# Complete the action
def execute_action(cform, cat):
    return_direct = True
    x = random.randint(0, 6)
    
    # Crea il nome del file con il formato "pizzaX.jpg"
    filename = f'pizza{x}.jpg'
    result = "<h3>PIZZA CHALLENGE - ORDER COMPLETED<h3><br>" 
    result += "<table border=0>"
    result += "<tr>"
    result += "   <td>Pizza Type</td>"
    result += f"  <td>{cform.model.pizza_type}</td>"
    result += "</tr>"
    result += "<tr>"
    result += "   <td>Address</td>"
    result += f"  <td>{cform.model.address}</td>"
    result += "</tr>"
    result += "<tr>"
    result += "   <td>Phone Number</td>"
    result += f"  <td>{cform.model.phone}</td>"
    result += "</tr>"
    result += "</table>"
    result += "<br>"                                                                                                     
    result += "Thanks for your order.. your pizza is on its way!"
    result += "<br><br>"
    result += f"<img style='width:400px' src='https://maxdam.github.io/cat-pizza-challenge/img/order/pizza{random.randint(0, 6)}.jpg'>"
    return return_direct, result
